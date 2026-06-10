import os
import sys
import logging

# Add the parent directory to the path so we can import from core/services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from services.db import supabase
from clerk_backend_api import Clerk

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_users():
    """
    Fetches all users from Clerk and upserts them into the Supabase users table.
    """
    if not settings.CLERK_SECRET_KEY:
        logger.error("CLERK_SECRET_KEY is not set in environment.")
        return

    logger.info("Initializing Clerk client...")
    clerk = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)
    
    logger.info("Fetching users from Clerk...")
    try:
        # Fetch up to 100 users for this simple sync. If you have thousands, 
        # you would need to implement pagination using offset/limit.
        response = clerk.users.list(limit=100)
        
        # In newer clerk-backend-api versions, response might be a list or have a data attribute
        users = response if isinstance(response, list) else getattr(response, "data", [])
        
        if not users:
            logger.info("No users found in Clerk.")
            return
            
        logger.info(f"Found {len(users)} users. Syncing to Supabase...")
        
        success_count = 0
        for user in users:
            # Extract data
            user_id = user.id
            first_name = user.first_name or ""
            last_name = user.last_name or ""
            image_url = user.image_url or ""
            
            # Extract primary email
            primary_email = ""
            if hasattr(user, "email_addresses") and user.email_addresses:
                for email_obj in user.email_addresses:
                    if getattr(email_obj, "id", None) == getattr(user, "primary_email_address_id", None):
                        primary_email = getattr(email_obj, "email_address", "")
                        break
                # Fallback to first email if primary not found
                if not primary_email and len(user.email_addresses) > 0:
                    primary_email = getattr(user.email_addresses[0], "email_address", "")
            
            user_data = {
                "id": user_id,
                "email": primary_email,
                "first_name": first_name,
                "last_name": last_name,
                "image_url": image_url
            }
            
            try:
                supabase.table("users").upsert(user_data).execute()
                logger.info(f"Upserted user {user_id} ({primary_email})")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to upsert user {user_id}: {str(e)}")
                
        logger.info(f"Sync complete! Successfully synced {success_count} out of {len(users)} users.")
        
    except Exception as e:
        logger.error(f"Error fetching users from Clerk: {str(e)}", exc_info=True)

if __name__ == "__main__":
    sync_users()

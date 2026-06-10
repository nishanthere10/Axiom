import logging
from fastapi import APIRouter, Request, HTTPException, status
from svix.webhooks import Webhook, WebhookVerificationError
from core.config import settings
from services.db import supabase

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/clerk")
async def clerk_webhook(request: Request):
    """
    Webhook endpoint to sync Clerk users with the Supabase users table.
    """
    secret = settings.CLERK_WEBHOOK_SECRET
    if not secret:
        logger.error("CLERK_WEBHOOK_SECRET is missing")
        raise HTTPException(status_code=500, detail="Server misconfiguration")

    # Get the headers
    headers = request.headers
    svix_id = headers.get("svix-id")
    svix_timestamp = headers.get("svix-timestamp")
    svix_signature = headers.get("svix-signature")

    if not svix_id or not svix_timestamp or not svix_signature:
        logger.error("Missing svix headers")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing svix headers"
        )

    # Get the raw body
    payload = await request.body()

    # Verify the signature
    wh = Webhook(secret)
    try:
        event = wh.verify(payload, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        })
    except WebhookVerificationError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    except Exception as e:
        logger.error(f"Error verifying webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification error")

    # Handle the event
    event_type = event.get("type")
    data = event.get("data", {})
    user_id = data.get("id")

    if not user_id:
        return {"status": "ignored", "reason": "No user ID"}

    logger.info(f"Received Clerk webhook: {event_type} for user {user_id}")

    try:
        if event_type in ["user.created", "user.updated"]:
            email_addresses = data.get("email_addresses", [])
            primary_email = ""
            if email_addresses:
                # Find primary email if available, otherwise just use the first one
                primary_id = data.get("primary_email_address_id")
                primary_email_obj = next(
                    (e for e in email_addresses if e.get("id") == primary_id),
                    email_addresses[0]
                )
                primary_email = primary_email_obj.get("email_address", "")

            user_data = {
                "id": user_id,
                "email": primary_email,
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
                "image_url": data.get("image_url", "")
            }

            # Upsert into Supabase
            supabase.table("users").upsert(user_data).execute()
            logger.info(f"Successfully upserted user {user_id} into Supabase")

        elif event_type == "user.deleted":
            # Delete from Supabase
            supabase.table("users").delete().eq("id", user_id).execute()
            logger.info(f"Successfully deleted user {user_id} from Supabase")
            
        else:
            logger.debug(f"Ignored unhandled event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing webhook data for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")

    return {"status": "success"}

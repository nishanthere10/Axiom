import logging
import hmac
import hashlib
import json
import asyncio
from fastapi import APIRouter, Request, Header, HTTPException, status, BackgroundTasks
from svix.webhooks import Webhook, WebhookVerificationError
from core.config import settings
from services.db import get_supabase, supabase

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/clerk")
async def clerk_webhook(request: Request):
    """
    Webhook endpoint to sync Clerk users with the Supabase users table.
    
    SECURITY FIX: Enhanced verification with timing attack protection.
    """
    import time
    
    # SECURITY FIX: Start timing for constant execution time
    start_time = time.time()
    
    secret = settings.CLERK_WEBHOOK_SECRET
    if not secret:
        logger.error("CLERK_WEBHOOK_SECRET is missing")
        # SECURITY: Still maintain minimum execution time even on config error
        await asyncio.sleep(0.1)
        raise HTTPException(status_code=500, detail="Server misconfiguration")

    # Get the headers
    headers = request.headers
    svix_id = headers.get("svix-id")
    svix_timestamp = headers.get("svix-timestamp")
    svix_signature = headers.get("svix-signature")

    # Get the raw body
    payload = await request.body()

    verification_success = False
    event = None

    # Always attempt verification, even with missing headers
    try:
        if svix_id and svix_timestamp and svix_signature:
            # Verify the signature
            wh = Webhook(secret)
            event = wh.verify(payload, {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature,
            })
            verification_success = True
    except WebhookVerificationError:
        verification_success = False
    except Exception:
        verification_success = False

    # SECURITY FIX: Ensure minimum execution time
    min_execution_time = 0.05  # 50ms minimum
    elapsed = time.time() - start_time
    if elapsed < min_execution_time:
        await asyncio.sleep(min_execution_time - elapsed)

    # Handle verification results
    if not verification_success:
        if not svix_id or not svix_timestamp or not svix_signature:
            logger.warning("Clerk webhook rejected: missing svix headers")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing svix headers"
            )
        else:
            logger.warning("Clerk webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )

    # Handle the verified event
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
        # SECURITY: Generic error message to prevent information disclosure
        raise HTTPException(status_code=500, detail="Database operation failed")

    return {"status": "success"}

@router.post("/github/push")
async def github_push_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
):
    """
    POST /webhooks/github/push
    Public endpoint — called by GitHub. Verified via HMAC-SHA256.
    Triggers incremental sync for the affected repository.
    
    SECURITY FIX: Constant-time verification to prevent timing attacks.
    """
    import time
    
    # SECURITY FIX: Start timing to ensure constant execution time
    start_time = time.time()
    body = await request.body()
    
    # SECURITY FIX: Always perform HMAC verification first, regardless of other conditions
    # This prevents timing attacks that could differentiate between missing repos and invalid signatures
    
    verification_success = False
    repo_data = None
    
    try:
        # Parse payload (do this early to catch malformed JSON)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}
        
        repo_full_name = payload.get("repository", {}).get("full_name", "")
        
        if repo_full_name:
            # Lookup repo (but don't fail yet - continue to HMAC verification)
            db = get_supabase("webhook")  # SECURITY FIX: Use webhook context
            repo_res = (
                db.table("github_repositories")
                .select("id, user_id, webhook_secret, workspace_id")
                .eq("repository_name", repo_full_name.split('/')[-1] if '/' in repo_full_name else "")
                .eq("repository_owner", repo_full_name.split('/')[0] if '/' in repo_full_name else "")
                .eq("is_active", True)
                .execute()
            )
            
            if repo_res.data:
                repo_data = repo_res.data[0]
                secret = repo_data.get("webhook_secret", "")
                
                if secret and x_hub_signature_256:
                    # Perform HMAC verification
                    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
                    expected_sig = "sha256=" + mac.hexdigest()
                    
                    # SECURITY: Constant-time comparison
                    if hmac.compare_digest(expected_sig, x_hub_signature_256):
                        verification_success = True
        
        # SECURITY FIX: Ensure minimum execution time to prevent timing attacks
        min_execution_time = 0.1  # 100ms minimum
        elapsed = time.time() - start_time
        if elapsed < min_execution_time:
            await asyncio.sleep(min_execution_time - elapsed)
        
        # Now handle the request based on verification results
        if not verification_success:
            if not repo_data:
                logger.warning("Webhook rejected: repository not found or inactive: %s", repo_full_name)
                raise HTTPException(status_code=404, detail="Repository not found")
            elif not repo_data.get("webhook_secret"):
                logger.warning("Webhook rejected: no secret configured for repo: %s", repo_full_name)
                raise HTTPException(status_code=403, detail="Webhook not configured")
            else:
                logger.warning("HMAC verification failed for repo %s", repo_full_name)
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Handle specific GitHub events
        if x_github_event == "ping":
            return {"ok": True, "message": "ping received"}

        if x_github_event != "push":
            return {"ok": True, "message": f"Ignoring event: {x_github_event}"}

        if not repo_full_name:
            raise HTTPException(status_code=400, detail="Missing repository.full_name")

        # Queue incremental sync as background task
        from services.context_providers.github_provider import github_provider

        background_tasks.add_task(
            github_provider.sync_incremental,
            user_id=repo_data["user_id"],
            repo_id=repo_data["id"],
            resource_id=repo_full_name,
            workspace_id=repo_data.get("workspace_id"),
        )

        logger.info("Queued incremental sync for %s (webhook trigger)", repo_full_name)
        return {"ok": True, "message": "Sync queued"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Webhook processing error: %s", e, exc_info=True)
        # SECURITY: Generic error message to prevent information disclosure
        raise HTTPException(status_code=500, detail="Webhook processing failed")

import logging
import hmac
import hashlib
import json
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
    """
    body = await request.body()

    if x_github_event == "ping":
        return {"ok": True, "message": "ping received"}

    if x_github_event != "push":
        return {"ok": True, "message": f"Ignoring event: {x_github_event}"}

    payload = json.loads(body)
    repo_full_name = payload.get("repository", {}).get("full_name")
    if not repo_full_name:
        raise HTTPException(status_code=400, detail="Missing repository.full_name")

    # Lookup repo
    db = get_supabase()
    repo_res = (
        db.table("github_repositories")
        .select("id, user_id, webhook_secret, workspace_id")
        .eq("repository_name", repo_full_name.split('/')[-1])
        .eq("repository_owner", repo_full_name.split('/')[0])
        .eq("is_active", True)
        .execute()
    )
    if not repo_res.data:
        return {"ok": False, "message": "Repository not found"}

    repo = repo_res.data[0]

    # Verify HMAC
    secret = repo.get("webhook_secret", "")
    if secret:
        expected_sig = "sha256=" + hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_hub_signature_256 or ""):
            logger.warning("HMAC verification failed for repo %s", repo_full_name)
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Queue incremental sync as background task
    from services.context_providers.github_provider import github_provider

    background_tasks.add_task(
        github_provider.sync_incremental,
        user_id=repo["user_id"],
        repo_id=repo["id"],
        resource_id=repo_full_name,
        workspace_id=repo.get("workspace_id"),
    )

    logger.info("Queued incremental sync for %s (webhook trigger)", repo_full_name)
    return {"ok": True, "message": "Sync queued"}

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from io import BytesIO
from core.auth import get_current_user
from services.export.export_service import generate_export

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/{session_type}/{session_id}/{format_type}")
async def export_document(
    session_type: str, 
    session_id: str, 
    format_type: str, 
    user_id: str = Depends(get_current_user)
):
    """
    Export a research or comparison session.
    session_type: "research" | "comparison"
    format_type: "markdown" | "adr" | "pdf"
    """
    if session_type not in ["research", "comparison"]:
        raise HTTPException(status_code=400, detail="Invalid session type")
    
    if format_type not in ["markdown", "adr", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format type")
        
    import time
    start_time = time.time()
        
    file_bytes, content_type = generate_export(session_type, session_id, format_type, user_id)
    
    filename = f"atlas-{session_type}-{format_type}-{session_id}"
    if format_type == "pdf":
        extension = "pdf"
    else:
        extension = "md"
        
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}.{extension}"'
    }
    
    try:
        from services.metrics_service import emit_export_requested
        latency_ms = int((time.time() - start_time) * 1000)
        emit_export_requested(user_id=user_id, export_type=format_type, latency_ms=latency_ms)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to emit export metric: {e}")
    
    if format_type == "pdf":
        # Streaming response is better for binary PDF data
        return StreamingResponse(BytesIO(file_bytes), media_type=content_type, headers=headers)
    else:
        return Response(content=file_bytes, media_type=content_type, headers=headers)

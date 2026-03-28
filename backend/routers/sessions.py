"""Sessions router - Create and manage attendance sessions."""

import uuid
from fastapi import APIRouter, HTTPException, Depends, Header
from datetime import datetime, timedelta, timezone

from models import CreateSessionRequest, SessionResponse, TokenResponse
from database import get_supabase, get_admin_client
from config import get_settings

router = APIRouter()


def get_current_teacher(authorization: str = Header(...)):
    """Extract and verify teacher from Supabase Auth token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    db_anon = get_supabase()
    db_admin = get_admin_client()
    
    try:
        user_response = db_anon.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check role using admin client to bypass RLS
        teacher_result = db_admin.table("teachers").select("*").eq("id", user_response.user.id).execute()
        if not teacher_result.data:
            raise HTTPException(status_code=403, detail="Only teachers can manage sessions")
            
        return {"sub": user_response.user.id, "role": "teacher"}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token validation failed")


@router.post("/create", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest, teacher=Depends(get_current_teacher)):
    """
    Create a new attendance session.
    Teacher selects subject and class. Date/time auto-filled.
    """
    db = get_admin_client()
    teacher_uuid = teacher["sub"]

    # Deactivate any existing active sessions for this teacher
    db.table("sessions").update({"is_active": False}).eq(
        "teacher_id", teacher_uuid
    ).eq("is_active", True).execute()

    # Create new session
    session_data = {
        "teacher_id": teacher_uuid,
        "subject": request.subject,
        "class": request.class_name,
        "is_active": True,
    }
    result = db.table("sessions").insert(session_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create session")

    session = result.data[0]
    return SessionResponse(
        id=session["id"],
        teacher_id=session["teacher_id"],
        subject=session["subject"],
        class_name=session["class"],
        start_time=session["start_time"],
        is_active=session["is_active"],
    )


@router.get("/{session_id}/token", response_model=TokenResponse)
async def generate_token(session_id: str, teacher=Depends(get_current_teacher)):
    """
    Generate a new short-lived token for QR code.
    Called every 30 seconds to rotate the QR.
    """
    db = get_admin_client()
    settings = get_settings()

    # Verify session exists and is active using admin client
    session = db.table("sessions").select("*").eq("id", session_id).eq("is_active", True).execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found or inactive")

    # Generate secure token
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.token_expiry_seconds)

    # Store token
    token_data = {
        "session_id": session_id,
        "token": token,
        "expires_at": expires_at.isoformat(),
    }
    db.table("session_tokens").insert(token_data).execute()

    # Build QR data URL
    qr_data = f"smartattendance://mark?token={token}"

    return TokenResponse(
        token=token,
        expires_at=expires_at.isoformat(),
        session_id=session_id,
        qr_data=qr_data,
    )


@router.get("/{session_id}")
async def get_session(session_id: str, teacher=Depends(get_current_teacher)):
    """Get session details."""
    db = get_admin_client()
    session = db.table("sessions").select("*").eq("id", session_id).execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.data[0]


@router.post("/{session_id}/end")
async def end_session(session_id: str, teacher=Depends(get_current_teacher)):
    """Teacher manually ends a session."""
    db = get_admin_client()
    db.table("sessions").update({"is_active": False}).eq("id", session_id).execute()
    return {"message": "Session ended", "session_id": session_id}


@router.get("/active/list")
async def list_active_sessions(teacher=Depends(get_current_teacher)):
    """List all active sessions for current teacher."""
    db = get_admin_client()
    teacher_uuid = teacher["sub"]
    result = db.table("sessions").select("*").eq(
        "teacher_id", teacher_uuid
    ).eq("is_active", True).execute()
    return result.data

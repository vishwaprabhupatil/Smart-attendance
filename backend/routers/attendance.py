"""Attendance router - Mark and query attendance."""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from datetime import datetime, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import MarkAttendanceRequest, AttendanceResponse, AttendanceRecord
from database import get_supabase, get_admin_client
from config import get_settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_current_user(authorization: str = Header(...)):
    """Extract and verify user from Supabase Auth token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    db = get_supabase()
    
    try:
        user_response = db.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token validation failed")


@router.post("/mark", response_model=AttendanceResponse)
@limiter.limit("10/minute")
async def mark_attendance(request_body: MarkAttendanceRequest, request: Request):
    """
    Mark attendance for a student.
    Validates: token exists, not expired, student not already marked.
    """
    db = get_admin_client()
    settings = get_settings()

    # 1. Validate token
    token_result = db.table("session_tokens").select(
        "*, sessions(*)"
    ).eq("token", request_body.token).execute()

    if not token_result.data:
        raise HTTPException(status_code=400, detail="Invalid token")

    token_record = token_result.data[0]

    # 2. Check token expiry
    expires_at = datetime.fromisoformat(token_record["expires_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    if now > expires_at:
        return AttendanceResponse(
            success=False,
            message="❌ Session Expired - QR code has expired. Ask your teacher to refresh.",
        )

    # 3. Check session is active
    session = token_record.get("sessions")
    if not session or not session.get("is_active"):
        return AttendanceResponse(
            success=False,
            message="❌ Session is no longer active.",
        )

    # 4. Validate student exists
    student_result = db.table("students").select("*").eq(
        "student_id", request_body.student_id
    ).execute()

    if not student_result.data:
        raise HTTPException(status_code=404, detail="Student not found")

    student = student_result.data[0]
    session_id = token_record["session_id"]

    # 5. Check student is in the correct class
    if student["class"] != session["class"]:
        return AttendanceResponse(
            success=False,
            message="❌ You are not enrolled in this class.",
        )

    # 6. Check late window
    session_start = datetime.fromisoformat(session["start_time"].replace("Z", "+00:00"))
    minutes_late = (now - session_start).total_seconds() / 60
    if minutes_late > settings.max_late_minutes:
        return AttendanceResponse(
            success=False,
            message=f"❌ Late marking window closed ({settings.max_late_minutes} min max).",
        )

    # 7. Check duplicate attendance
    existing = db.table("attendance").select("id").eq(
        "student_id", student["id"]
    ).eq("session_id", session_id).execute()

    if existing.data:
        return AttendanceResponse(
            success=False,
            message="❌ Already Marked - You have already marked attendance for this session.",
        )

    # 8. Mark attendance
    attendance_data = {
        "student_id": student["id"],
        "session_id": session_id,
        "status": "present",
    }
    db.table("attendance").insert(attendance_data).execute()

    return AttendanceResponse(
        success=True,
        message="✅ Attendance Marked Successfully!",
        student_name=student["name"],
        session_id=session_id,
    )


@router.get("/session/{session_id}")
async def get_session_attendance(session_id: str, user=Depends(get_current_user)):
    """
    Get attendance list for a session.
    Returns all students marked present.
    """
    db = get_admin_client()

    result = db.table("attendance").select(
        "*, students(name, student_id)"
    ).eq("session_id", session_id).execute()

    records = []
    for record in result.data:
        student = record.get("students", {})
        records.append(AttendanceRecord(
            id=record["id"],
            student_id=student.get("student_id", ""),
            student_name=student.get("name", ""),
            timestamp=record["timestamp"],
            status=record["status"],
        ))

    return {
        "session_id": session_id,
        "total_present": len(records),
        "records": records,
    }

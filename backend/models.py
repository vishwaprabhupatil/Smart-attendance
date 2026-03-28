"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Auth ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    user_id: str = Field(..., description="student_id or teacher_id")
    password: str
    role: str = Field(..., pattern="^(student|teacher)$")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    name: str


# ─── Sessions ────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    subject: str
    class_name: str = Field(..., alias="class")

    class Config:
        populate_by_name = True


class SessionResponse(BaseModel):
    id: str
    teacher_id: str
    subject: str
    class_name: str
    start_time: str
    is_active: bool


class TokenResponse(BaseModel):
    token: str
    expires_at: str
    session_id: str
    qr_data: str  # Full URL for QR encoding


# ─── Attendance ──────────────────────────────────────────────────────────────

class MarkAttendanceRequest(BaseModel):
    student_id: str
    token: str
    timestamp: Optional[str] = None
    device_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AttendanceResponse(BaseModel):
    success: bool
    message: str
    student_name: Optional[str] = None
    session_id: Optional[str] = None


class AttendanceRecord(BaseModel):
    id: str
    student_id: str
    student_name: str
    timestamp: str
    status: str

"""Authentication router - Login for Students and Teachers using Native Supabase Auth."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from models import LoginRequest, LoginResponse
from database import get_supabase
from config import get_settings

router = APIRouter()

def get_email_from_id(user_id: str, role: str) -> str:
    """Map student_id or teacher_id to a dummy email for Supabase Auth."""
    return f"{user_id.lower()}@{role}.attendance.com"

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint using Native Supabase Auth.
    Maps user_id (student/teacher ID) to a dummy email.
    """
    db = get_supabase()
    email = get_email_from_id(request.user_id, request.role)

    try:
        # Authenticate with Supabase
        print(f"Attempting login for: {email}")
        if db.auth is None:
            raise Exception("db.auth is None before login attempt")
            
        auth_response = db.auth.sign_in_with_password({
            "email": email,
            "password": request.password
        })

        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_uuid = auth_response.user.id
        access_token = auth_response.session.access_token

        # Fetch profile from public tables (students or teachers)
        table = "students" if request.role == "student" else "teachers"
        profile_result = db.table(table).select("*").eq("id", user_uuid).execute()

        if not profile_result.data:
            raise HTTPException(status_code=404, detail="User profile not found")

        profile = profile_result.data[0]

        return LoginResponse(
            access_token=access_token,
            role=request.role,
            user_id=request.user_id,
            name=profile["name"],
        )

    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or connection error",
        )

@router.post("/register/student")
async def register_student(student_id: str, name: str, class_name: str, password: str):
    """Register a new student using Supabase Auth (Admin)."""
    from database import get_admin_client
    db = get_admin_client()
    email = get_email_from_id(student_id, "student")

    try:
        # 1. Create user in Supabase Auth (using service role key from database.py)
        auth_user = db.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })

        if not auth_user.user:
            raise HTTPException(status_code=400, detail="Failed to create auth user")

        # 2. Create profile in students table
        db.table("students").insert({
            "id": auth_user.user.id,
            "student_id": student_id,
            "name": name,
            "class": class_name
        }).execute()

        return {"message": "Student registered", "id": auth_user.user.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/register/teacher")
async def register_teacher(teacher_id: str, name: str, subject: str, password: str):
    """Register a new teacher using Supabase Auth (Admin)."""
    from database import get_admin_client
    db = get_admin_client()
    email = get_email_from_id(teacher_id, "teacher")

    try:
        # 1. Create user in Supabase Auth
        auth_user = db.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })

        if not auth_user.user:
            raise HTTPException(status_code=400, detail="Failed to create auth user")

        # 2. Create profile in teachers table
        db.table("teachers").insert({
            "id": auth_user.user.id,
            "teacher_id": teacher_id,
            "name": name,
            "subject": subject
        }).execute()

        return {"message": "Teacher registered", "id": auth_user.user.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

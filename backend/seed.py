"""Seed script to populate test data in Supabase using Native Auth."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import get_admin_client

def get_email(user_id, role):
    return f"{user_id.lower()}@{role}.attendance.com"

def seed():
    db = get_admin_client()

    # Seed Teachers
    teachers = [
        {"teacher_id": "T001", "name": "Dr. Sharma", "subject": "Mathematics", "password": "teacher123"},
        {"teacher_id": "T002", "name": "Prof. Patel", "subject": "Physics", "password": "teacher123"},
    ]
    
    print("--- Seeding Teachers ---")
    for t in teachers:
        email = get_email(t["teacher_id"], "teacher")
        try:
            # Check if profile exists
            existing_profile = db.table("teachers").select("id").eq("teacher_id", t["teacher_id"]).execute()
            if not existing_profile.data:
                print(f"Creating profile for {t['name']}...")
                uid = None
                try:
                    # Try to create auth user
                    auth_user = db.auth.admin.create_user({
                        "email": email,
                        "password": t["password"],
                        "email_confirm": True
                    })
                    uid = auth_user.user.id
                    print(f"  Auth user created")
                except Exception:
                    # User might already exist in Auth, try to find them
                    # In a real app we'd search, but for seeding we can just try to sign in or use a more advanced admin tool.
                    # As a workaround for this seed, let's assume if it fails, they exist and we'll need their UID.
                    # We can use admin.list_users() to find them.
                    users_res = db.auth.admin.list_users()
                    for u in users_res:
                        if u.email == email:
                            uid = u.id
                            print(f"  Existing auth user found: {uid}")
                            break
                
                if uid:
                    db.table("teachers").insert({
                        "id": uid,
                        "teacher_id": t["teacher_id"],
                        "name": t["name"],
                        "subject": t["subject"]
                    }).execute()
                    print(f"  [SUCCESS] Teacher and profile synchronized")
                else:
                    print(f"  [ERROR] Could not find/create auth user for {email}")
            else:
                print(f"--- Teacher {t['name']} profile already exists")
        except Exception as e:
            print(f"[ERROR] Seeding teacher {t['teacher_id']}: {str(e)}")

    # Seed Students
    students = [
        {"student_id": "S001", "name": "Rahul Kumar", "class": "CS-B", "password": "student123"},
        {"student_id": "S002", "name": "Priya Singh", "class": "CS-B", "password": "student123"},
        {"student_id": "S003", "name": "Amit Verma", "class": "CS-B", "password": "student123"},
    ]
    
    print("\n--- Seeding Students ---")
    for s in students:
        email = get_email(s["student_id"], "student")
        try:
            existing_profile = db.table("students").select("id").eq("student_id", s["student_id"]).execute()
            if not existing_profile.data:
                print(f"Creating profile for {s['name']}...")
                uid = None
                try:
                    auth_user = db.auth.admin.create_user({
                        "email": email,
                        "password": s["password"],
                        "email_confirm": True
                    })
                    uid = auth_user.user.id
                    print(f"  Auth user created")
                except Exception:
                    users_res = db.auth.admin.list_users()
                    for u in users_res:
                        if u.email == email:
                            uid = u.id
                            print(f"  Existing auth user found: {uid}")
                            break
                
                if uid:
                    db.table("students").insert({
                        "id": uid,
                        "student_id": s["student_id"],
                        "name": s["name"],
                        "class": s["class"]
                    }).execute()
                    print(f"  [SUCCESS] Student and profile synchronized")
                else:
                    print(f"  [ERROR] Could not find/create auth user for {email}")
            else:
                print(f"--- Student {s['name']} profile already exists")
        except Exception as e:
            print(f"[ERROR] Seeding student {s['student_id']}: {str(e)}")

    print("\n--- Seeding complete! ---")

if __name__ == "__main__":
    seed()

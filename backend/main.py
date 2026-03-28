"""FastAPI main application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers import auth, sessions, attendance

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Smart Attendance System",
    description="Production-ready QR-based attendance system",
    version="1.0.0",
)

# Apply rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - allow Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])


@app.get("/")
async def root():
    return {"message": "Smart Attendance System API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

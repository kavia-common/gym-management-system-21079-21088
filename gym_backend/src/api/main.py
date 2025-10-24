from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from src.database.connection import init_db
from src.api.routes import auth, memberships, classes, trainers, bookings, dashboard

# Load environment variables
load_dotenv()

# Initialize FastAPI app with metadata for OpenAPI documentation
app = FastAPI(
    title="Gym Management System API",
    description="Backend API for gym management including authentication, memberships, classes, trainers, and bookings",
    version="1.0.0",
    openapi_tags=[
        {"name": "Authentication", "description": "User registration, login, and authentication"},
        {"name": "Memberships", "description": "Membership plans and member memberships"},
        {"name": "Classes", "description": "Class schedules and management"},
        {"name": "Trainers", "description": "Trainer profiles and schedules"},
        {"name": "Bookings", "description": "Class bookings and attendance"},
        {"name": "Dashboard", "description": "Dashboard metrics for different user roles"}
    ]
)

# Configure CORS to allow frontend origin
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "*"],  # Allow both specific origin and wildcard for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(memberships.router)
app.include_router(classes.router)
app.include_router(trainers.router)
app.include_router(bookings.router)
app.include_router(dashboard.router)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and create admin user on startup"""
    init_db()
    print("✅ Database initialized successfully")

# PUBLIC_INTERFACE
@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        dict: Status message
    """
    return {"message": "Gym Management System API is healthy", "status": "ok"}

# PUBLIC_INTERFACE
@app.get("/health", tags=["Health"])
def health():
    """
    Alternative health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy"}

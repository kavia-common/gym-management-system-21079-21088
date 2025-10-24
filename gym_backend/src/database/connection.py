import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment variable or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gym_management.db")

# Create engine - for SQLite, we need check_same_thread=False
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# PUBLIC_INTERFACE
def get_db():
    """
    Database session dependency for FastAPI routes.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# PUBLIC_INTERFACE
def init_db():
    """
    Initialize database tables and create initial admin user if configured.
    """
    from src.database.models import User
    from src.auth.password import get_password_hash
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create initial admin user if environment variables are set
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if admin_email and admin_password:
        db = SessionLocal()
        try:
            # Check if admin already exists
            existing_admin = db.query(User).filter(User.email == admin_email).first()
            if not existing_admin:
                # Ensure password is within bcrypt's 72-byte limit
                safe_password = admin_password[:72] if len(admin_password) > 72 else admin_password
                admin_user = User(
                    email=admin_email,
                    hashed_password=get_password_hash(safe_password),
                    full_name="System Administrator",
                    role="admin"
                )
                db.add(admin_user)
                db.commit()
                print(f"✅ Initial admin user created: {admin_email}")
            else:
                print(f"ℹ️ Admin user already exists: {admin_email}")
        except Exception as e:
            print(f"⚠️ Error creating admin user: {e}")
            db.rollback()
        finally:
            db.close()

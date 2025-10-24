from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from src.database.connection import Base

class UserRole(str, enum.Enum):
    """User role enumeration"""
    admin = "admin"
    member = "member"
    trainer = "trainer"

class MembershipStatus(str, enum.Enum):
    """Membership status enumeration"""
    active = "active"
    expired = "expired"
    cancelled = "cancelled"

class BookingStatus(str, enum.Enum):
    """Booking status enumeration"""
    confirmed = "confirmed"
    cancelled = "cancelled"
    waitlisted = "waitlisted"

class User(Base):
    """User model representing all system users (admin, members, trainers)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.member)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    memberships = relationship("Membership", back_populates="member", foreign_keys="Membership.member_id")
    trainer_profile = relationship("Trainer", back_populates="user", uselist=False)
    bookings = relationship("Booking", back_populates="member", foreign_keys="Booking.member_id")

class MembershipPlan(Base):
    """Membership plan templates (e.g., Basic, Premium, VIP)"""
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    duration_days = Column(Integer, nullable=False)  # Duration in days
    price = Column(Integer, nullable=False)  # Price in cents to avoid float issues
    features = Column(Text)  # JSON string of features
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    memberships = relationship("Membership", back_populates="plan")

class Membership(Base):
    """Active membership linking a member to a plan"""
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(SQLEnum(MembershipStatus), nullable=False, default=MembershipStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    member = relationship("User", back_populates="memberships", foreign_keys=[member_id])
    plan = relationship("MembershipPlan", back_populates="memberships")

class Trainer(Base):
    """Trainer profile with additional information"""
    __tablename__ = "trainers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    bio = Column(Text)
    specialties = Column(Text)  # Comma-separated or JSON
    certifications = Column(Text)  # Comma-separated or JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="trainer_profile")
    classes = relationship("ClassSchedule", back_populates="trainer")

class ClassSchedule(Base):
    """Scheduled fitness classes"""
    __tablename__ = "class_schedules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    room = Column(String)
    capacity = Column(Integer, nullable=False, default=20)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trainer = relationship("Trainer", back_populates="classes")
    bookings = relationship("Booking", back_populates="class_schedule")

class Booking(Base):
    """Booking for a class by a member"""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("class_schedules.id"), nullable=False)
    status = Column(SQLEnum(BookingStatus), nullable=False, default=BookingStatus.confirmed)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    member = relationship("User", back_populates="bookings", foreign_keys=[member_id])
    class_schedule = relationship("ClassSchedule", back_populates="bookings")
    attendance = relationship("Attendance", back_populates="booking", uselist=False)

class Attendance(Base):
    """Attendance record for a booking"""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, unique=True)
    attended = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    booking = relationship("Booking", back_populates="attendance")

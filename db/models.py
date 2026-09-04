from datetime import datetime
from typing import Optional, List
from sqlalchemy import BigInteger, String, ForeignKey, DateTime, Text, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="client", nullable=False)  # client, instructor, admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    bookings: Mapped[List["Booking"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    instructor_profile: Mapped[Optional["Instructor"]] = relationship(back_populates="user")

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    schedules: Mapped[List["Schedule"]] = relationship(back_populates="category", cascade="all, delete-orphan")

class Instructor(Base):
    __tablename__ = "instructors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="instructor_profile")
    schedules: Mapped[List["Schedule"]] = relationship(back_populates="instructor", cascade="all, delete-orphan")

class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    room: Mapped[Optional[str]] = mapped_column(String(64))

    category: Mapped["Category"] = relationship(back_populates="schedules")
    instructor: Mapped["Instructor"] = relationship(back_populates="schedules")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="schedule", cascade="all, delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("user_id", "schedule_id", name="uq_user_schedule"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedule.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="bookings")

    schedule: Mapped["Schedule"] = relationship(back_populates="bookings")
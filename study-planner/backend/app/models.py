"""ORM models for the study planner."""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    exam_date = Column(Date, nullable=False)
    difficulty = Column(Integer, default=3)   # 1 (easy) - 5 (hard)
    priority = Column(Integer, default=3)     # 1 (low)  - 5 (high)
    hours_needed = Column(Float, default=10.0)  # total estimated hours to prepare
    hours_completed = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("StudySession", back_populates="subject", cascade="all, delete-orphan")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    session_date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    completed = Column(Boolean, default=False)
    notes = Column(String, default="")

    subject = relationship("Subject", back_populates="sessions")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)  # "user" | "assistant"
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

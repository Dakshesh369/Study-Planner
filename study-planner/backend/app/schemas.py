from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    name: str
    exam_date: date
    difficulty: int = Field(3, ge=1, le=5)
    priority: int = Field(3, ge=1, le=5)
    hours_needed: float = Field(10.0, gt=0)


class SubjectOut(BaseModel):
    id: int
    name: str
    exam_date: date
    difficulty: int
    priority: int
    hours_needed: float
    hours_completed: float

    class Config:
        from_attributes = True


class PlanRequest(BaseModel):
    subjects: List[SubjectCreate]
    daily_hours_available: float = Field(3.0, gt=0, le=16)
    start_date: Optional[date] = None
    plan_days: int = Field(14, gt=0, le=90)


class SessionOut(BaseModel):
    id: int
    subject_id: int
    subject_name: str
    session_date: date
    hours: float
    completed: bool

    class Config:
        from_attributes = True


class PlanResponse(BaseModel):
    sessions: List[SessionOut]
    ai_summary: str
    warnings: List[str] = []


class CheckinRequest(BaseModel):
    session_id: int
    completed: bool
    notes: Optional[str] = ""


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str

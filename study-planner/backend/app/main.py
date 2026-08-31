from datetime import date
from typing import List

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, ai
from .database import engine, get_db, Base
from .scheduler import generate_schedule, SubjectInput

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Study Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_enabled": bool(ai.ANTHROPIC_API_KEY)}


@app.post("/api/plan", response_model=schemas.PlanResponse)
def create_plan(req: schemas.PlanRequest, db: Session = Depends(get_db)):
    if not req.subjects:
        raise HTTPException(400, "At least one subject is required.")

    start = req.start_date or date.today()

    # Reset existing data for this demo (single-user hackathon scope)
    db.query(models.StudySession).delete()
    db.query(models.Subject).delete()
    db.commit()

    db_subjects = []
    for s in req.subjects:
        row = models.Subject(
            name=s.name,
            exam_date=s.exam_date,
            difficulty=s.difficulty,
            priority=s.priority,
            hours_needed=s.hours_needed,
            hours_completed=0.0,
        )
        db.add(row)
        db_subjects.append(row)
    db.commit()
    for row in db_subjects:
        db.refresh(row)

    scheduler_input = [
        SubjectInput(
            id=row.id, name=row.name, exam_date=row.exam_date,
            difficulty=row.difficulty, priority=row.priority,
            hours_needed=row.hours_needed, hours_completed=row.hours_completed,
        )
        for row in db_subjects
    ]

    sessions, warnings = generate_schedule(
        scheduler_input, req.daily_hours_available, start, req.plan_days
    )

    session_rows = []
    for sess in sessions:
        row = models.StudySession(
            subject_id=sess.subject_id,
            session_date=sess.session_date,
            hours=sess.hours,
            completed=False,
        )
        db.add(row)
        session_rows.append((row, sess.subject_name))
    db.commit()
    for row, _ in session_rows:
        db.refresh(row)

    sessions_out = [
        schemas.SessionOut(
            id=row.id, subject_id=row.subject_id, subject_name=name,
            session_date=row.session_date, hours=row.hours, completed=row.completed,
        )
        for row, name in session_rows
    ]

    ai_summary = ai.summarize_plan(
        subjects=[{"name": s.name, "exam_date": str(s.exam_date), "difficulty": s.difficulty,
                   "priority": s.priority, "hours_needed": s.hours_needed} for s in db_subjects],
        sessions=[{"subject": s.subject_name, "date": str(s.session_date), "hours": s.hours}
                  for s in sessions_out],
        warnings=warnings,
    )

    return schemas.PlanResponse(sessions=sessions_out, ai_summary=ai_summary, warnings=warnings)


@app.get("/api/plan", response_model=List[schemas.SessionOut])
def get_plan(db: Session = Depends(get_db)):
    rows = db.query(models.StudySession).join(models.Subject).all()
    return [
        schemas.SessionOut(
            id=r.id, subject_id=r.subject_id, subject_name=r.subject.name,
            session_date=r.session_date, hours=r.hours, completed=r.completed,
        )
        for r in rows
    ]


@app.get("/api/subjects", response_model=List[schemas.SubjectOut])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(models.Subject).all()


@app.post("/api/checkin")
def checkin(req: schemas.CheckinRequest, db: Session = Depends(get_db)):
    session = db.query(models.StudySession).filter(models.StudySession.id == req.session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    session.completed = req.completed
    session.notes = req.notes or ""
    if req.completed:
        subject = db.query(models.Subject).filter(models.Subject.id == session.subject_id).first()
        if subject:
            subject.hours_completed += session.hours
    db.commit()
    return {"status": "ok"}


@app.post("/api/chat", response_model=schemas.ChatResponse)
def chat(req: schemas.ChatRequest, db: Session = Depends(get_db)):
    subjects = db.query(models.Subject).all()
    context = {
        "subjects": [
            {"name": s.name, "exam_date": str(s.exam_date), "hours_needed": s.hours_needed,
             "hours_completed": s.hours_completed} for s in subjects
        ]
    }
    db.add(models.ChatMessage(role="user", content=req.message))
    reply = ai.chat_reply(req.message, context)
    db.add(models.ChatMessage(role="assistant", content=reply))
    db.commit()
    return schemas.ChatResponse(reply=reply)

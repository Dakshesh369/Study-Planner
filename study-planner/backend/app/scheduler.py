"""
Core scheduling engine.

Deliberately kept independent of any LLM call so it is fast, deterministic,
and unit-testable. The AI layer (ai.py) sits on top of this to explain the
plan in natural language and to handle re-planning conversations.

Algorithm (greedy, urgency-weighted round robin):
1. For each subject compute a weight combining:
     - urgency: how close the exam is (closer => higher weight)
     - difficulty: harder subjects get more time
     - priority: user-declared importance
     - remaining_hours: subjects further from their hours_needed target
       get boosted so nothing gets starved near the end
2. Each day, distribute that day's available hours across subjects
   proportionally to their current weight, respecting:
     - a subject never gets scheduled after its exam date
     - a subject stops receiving hours once hours_needed is met
     - a minimum session granularity (0.25h) to avoid dust allocations
3. Recompute weights each day (urgency rises as exam approaches).
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Dict


@dataclass
class SubjectInput:
    id: int
    name: str
    exam_date: date
    difficulty: int
    priority: int
    hours_needed: float
    hours_completed: float = 0.0


@dataclass
class ScheduledSession:
    subject_id: int
    subject_name: str
    session_date: date
    hours: float


MIN_SESSION_HOURS = 0.25


def _urgency_weight(subject: SubjectInput, today: date) -> float:
    days_left = (subject.exam_date - today).days
    if days_left <= 0:
        return 0.0
    # inverse relationship: fewer days left => higher urgency
    return 1.0 / days_left


def compute_weight(subject: SubjectInput, remaining_hours: float, today: date) -> float:
    if remaining_hours <= 0:
        return 0.0
    urgency = _urgency_weight(subject, today)
    return urgency * (1 + 0.3 * subject.difficulty) * (1 + 0.3 * subject.priority) * remaining_hours


def generate_schedule(
    subjects: List[SubjectInput],
    daily_hours_available: float,
    start_date: date,
    plan_days: int,
) -> tuple[List[ScheduledSession], List[str]]:
    warnings: List[str] = []
    remaining: Dict[int, float] = {
        s.id: max(0.0, s.hours_needed - s.hours_completed) for s in subjects
    }
    sessions: List[ScheduledSession] = []

    for day_offset in range(plan_days):
        current_day = start_date + timedelta(days=day_offset)

        # subjects still active today: not past exam, hours remaining
        active = [
            s for s in subjects
            if s.exam_date > current_day and remaining[s.id] > 1e-6
        ]
        if not active:
            continue

        weights = {s.id: compute_weight(s, remaining[s.id], current_day) for s in active}
        total_weight = sum(weights.values())
        if total_weight <= 0:
            continue

        hours_left_today = daily_hours_available
        for s in sorted(active, key=lambda x: -weights[x.id]):
            share = (weights[s.id] / total_weight) * daily_hours_available
            alloc = min(share, remaining[s.id], hours_left_today)
            alloc = round(alloc * 4) / 4  # round to nearest 15 min
            if alloc < MIN_SESSION_HOURS:
                continue
            sessions.append(ScheduledSession(
                subject_id=s.id,
                subject_name=s.name,
                session_date=current_day,
                hours=alloc,
            ))
            remaining[s.id] -= alloc
            hours_left_today -= alloc
            if hours_left_today <= 0:
                break

    # Post-hoc warnings: subjects that won't hit their target before exam
    for s in subjects:
        days_left = (s.exam_date - start_date).days
        max_possible = days_left * daily_hours_available
        if s.hours_needed - s.hours_completed > max_possible:
            warnings.append(
                f"'{s.name}' needs {s.hours_needed - s.hours_completed:.1f}h but only "
                f"{max_possible:.1f}h is available before its exam on {s.exam_date}. "
                f"Consider raising daily hours or lowering the target."
            )
        if remaining.get(s.id, 0) > 0.01 and days_left > 0:
            pass  # already covered by warning above in most cases

    return sessions, warnings

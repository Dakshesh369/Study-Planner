from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.scheduler import generate_schedule, SubjectInput


TODAY = date(2026, 9, 1)


def make_subject(id, name, days_until_exam, difficulty=3, priority=3, hours_needed=10.0, hours_completed=0.0):
    return SubjectInput(
        id=id, name=name, exam_date=TODAY + timedelta(days=days_until_exam),
        difficulty=difficulty, priority=priority,
        hours_needed=hours_needed, hours_completed=hours_completed,
    )


def test_no_session_scheduled_after_exam_date():
    subjects = [make_subject(1, "Math", days_until_exam=3, hours_needed=20)]
    sessions, _ = generate_schedule(subjects, daily_hours_available=4, start_date=TODAY, plan_days=14)
    assert all(s.session_date < TODAY + timedelta(days=3) for s in sessions)


def test_never_exceeds_daily_hours_available():
    subjects = [
        make_subject(1, "Math", days_until_exam=10, hours_needed=40),
        make_subject(2, "Physics", days_until_exam=10, hours_needed=40),
        make_subject(3, "Chem", days_until_exam=10, hours_needed=40),
    ]
    sessions, _ = generate_schedule(subjects, daily_hours_available=3, start_date=TODAY, plan_days=10)
    daily_totals = {}
    for s in sessions:
        daily_totals[s.session_date] = daily_totals.get(s.session_date, 0) + s.hours
    for total in daily_totals.values():
        assert total <= 3 + 1e-6


def test_never_exceeds_hours_needed_per_subject():
    subjects = [make_subject(1, "Math", days_until_exam=14, hours_needed=5)]
    sessions, _ = generate_schedule(subjects, daily_hours_available=4, start_date=TODAY, plan_days=14)
    total = sum(s.hours for s in sessions if s.subject_id == 1)
    assert total <= 5 + 1e-6


def test_more_urgent_subject_gets_scheduled_first():
    subjects = [
        make_subject(1, "UrgentExam", days_until_exam=2, hours_needed=4),
        make_subject(2, "FarExam", days_until_exam=30, hours_needed=4),
    ]
    sessions, _ = generate_schedule(subjects, daily_hours_available=4, start_date=TODAY, plan_days=30)
    urgent_first_day = min(s.session_date for s in sessions if s.subject_id == 1)
    far_first_day = min(s.session_date for s in sessions if s.subject_id == 2)
    assert urgent_first_day <= far_first_day


def test_higher_difficulty_and_priority_gets_more_total_hours():
    subjects = [
        make_subject(1, "HardHighPriority", days_until_exam=14, difficulty=5, priority=5, hours_needed=100),
        make_subject(2, "EasyLowPriority", days_until_exam=14, difficulty=1, priority=1, hours_needed=100),
    ]
    sessions, _ = generate_schedule(subjects, daily_hours_available=4, start_date=TODAY, plan_days=14)
    hard_total = sum(s.hours for s in sessions if s.subject_id == 1)
    easy_total = sum(s.hours for s in sessions if s.subject_id == 2)
    assert hard_total > easy_total


def test_warning_generated_when_not_enough_time_before_exam():
    subjects = [make_subject(1, "Impossible", days_until_exam=2, hours_needed=100)]
    _, warnings = generate_schedule(subjects, daily_hours_available=2, start_date=TODAY, plan_days=14)
    assert len(warnings) == 1
    assert "Impossible" in warnings[0]


def test_empty_subject_list_returns_empty_schedule():
    sessions, warnings = generate_schedule([], daily_hours_available=4, start_date=TODAY, plan_days=14)
    assert sessions == []
    assert warnings == []


def test_already_completed_hours_reduce_remaining_allocation():
    subjects = [make_subject(1, "Math", days_until_exam=14, hours_needed=10, hours_completed=9)]
    sessions, _ = generate_schedule(subjects, daily_hours_available=4, start_date=TODAY, plan_days=14)
    total = sum(s.hours for s in sessions)
    assert total <= 1 + 1e-6

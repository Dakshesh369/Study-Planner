import { useState } from "react";
import { colorForIndex } from "../subjectColors";

const emptySubject = () => ({
  name: "",
  exam_date: "",
  difficulty: 3,
  priority: 3,
  hours_needed: 10,
});

export default function Onboarding({ onGenerate, loading, error }) {
  const [subjects, setSubjects] = useState([emptySubject()]);
  const [dailyHours, setDailyHours] = useState(3);
  const [planDays, setPlanDays] = useState(14);

  const updateSubject = (idx, field, value) => {
    setSubjects((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s))
    );
  };

  const addSubject = () => setSubjects((prev) => [...prev, emptySubject()]);
  const removeSubject = (idx) =>
    setSubjects((prev) => prev.filter((_, i) => i !== idx));

  const canSubmit =
    subjects.length > 0 &&
    subjects.every((s) => s.name.trim() && s.exam_date) &&
    !loading;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    onGenerate({
      subjects: subjects.map((s) => ({
        ...s,
        difficulty: Number(s.difficulty),
        priority: Number(s.priority),
        hours_needed: Number(s.hours_needed),
      })),
      daily_hours_available: Number(dailyHours),
      plan_days: Number(planDays),
    });
  };

  return (
    <div className="onboarding">
      <div className="onboarding-intro">
        <p className="eyebrow">Set up</p>
        <h1>What are you preparing for?</h1>
        <p className="lede">
          Add every subject with an upcoming exam. The planner weighs how
          close each date is, how hard the material is, and how you rank it
          — then builds a day-by-day schedule around your available hours.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card-stack">
        {subjects.map((s, idx) => (
          <div
            className="subject-card"
            key={idx}
            style={{ "--accent": colorForIndex(idx) }}
          >
            <div className="subject-card-tab" />
            <div className="subject-card-body">
              <div className="field-row">
                <label>
                  <span>Subject</span>
                  <input
                    type="text"
                    placeholder="e.g. Organic Chemistry"
                    value={s.name}
                    onChange={(e) => updateSubject(idx, "name", e.target.value)}
                    required
                  />
                </label>
                <label>
                  <span>Exam date</span>
                  <input
                    type="date"
                    value={s.exam_date}
                    onChange={(e) => updateSubject(idx, "exam_date", e.target.value)}
                    required
                  />
                </label>
              </div>
              <div className="field-row three">
                <label>
                  <span>Difficulty</span>
                  <select
                    value={s.difficulty}
                    onChange={(e) => updateSubject(idx, "difficulty", e.target.value)}
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>
                        {n} {n === 1 ? "· easy" : n === 5 ? "· brutal" : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Priority</span>
                  <select
                    value={s.priority}
                    onChange={(e) => updateSubject(idx, "priority", e.target.value)}
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>
                        {n} {n === 1 ? "· low" : n === 5 ? "· critical" : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Hours needed</span>
                  <input
                    type="number"
                    min="1"
                    step="0.5"
                    value={s.hours_needed}
                    onChange={(e) => updateSubject(idx, "hours_needed", e.target.value)}
                  />
                </label>
              </div>
              {subjects.length > 1 && (
                <button
                  type="button"
                  className="link-btn remove-btn"
                  onClick={() => removeSubject(idx)}
                >
                  Remove subject
                </button>
              )}
            </div>
          </div>
        ))}

        <button type="button" className="add-subject-btn" onClick={addSubject}>
          + Add another subject
        </button>

        <div className="onboarding-settings">
          <label>
            <span>Hours available per day</span>
            <input
              type="number"
              min="0.5"
              step="0.5"
              value={dailyHours}
              onChange={(e) => setDailyHours(e.target.value)}
            />
          </label>
          <label>
            <span>Plan length (days)</span>
            <input
              type="number"
              min="1"
              max="90"
              value={planDays}
              onChange={(e) => setPlanDays(e.target.value)}
            />
          </label>
        </div>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" className="primary-btn" disabled={!canSubmit}>
          {loading ? "Building your plan…" : "Generate my study plan"}
        </button>
      </form>
    </div>
  );
}

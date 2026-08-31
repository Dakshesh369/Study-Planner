import { useState, useEffect } from "react";
import Onboarding from "./components/Onboarding";
import PlanTimeline from "./components/PlanTimeline";
import SubjectLegend from "./components/SubjectLegend";
import ChatPanel from "./components/ChatPanel";
import { api } from "./api";
import "./App.css";

export default function App() {
  const [stage, setStage] = useState("onboarding"); // onboarding | dashboard
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [aiSummary, setAiSummary] = useState("");
  const [warnings, setWarnings] = useState([]);
  const [aiEnabled, setAiEnabled] = useState(false);

  useEffect(() => {
    api.health().then((h) => setAiEnabled(h.ai_enabled)).catch(() => {});
  }, []);

  const handleGenerate = async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.createPlan(payload);
      setSessions(res.sessions);
      setAiSummary(res.ai_summary);
      setWarnings(res.warnings || []);
      const subjectRes = await api.getSubjects();
      setSubjects(subjectRes);
      setStage("dashboard");
    } catch (err) {
      setError("Couldn't generate a plan — check that the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (session) => {
    const nextCompleted = !session.completed;
    setSessions((prev) =>
      prev.map((s) => (s.id === session.id ? { ...s, completed: nextCompleted } : s))
    );
    try {
      await api.checkin({ session_id: session.id, completed: nextCompleted });
      const subjectRes = await api.getSubjects();
      setSubjects(subjectRes);
    } catch {
      setSessions((prev) =>
        prev.map((s) => (s.id === session.id ? { ...s, completed: session.completed } : s))
      );
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">▚</span>
          <span className="brand-name">Plotline</span>
        </div>
        <div className="topbar-right">
          {stage === "dashboard" && (
            <button className="ghost-btn" onClick={() => setStage("onboarding")}>
              New plan
            </button>
          )}
          <span className={`ai-badge ${aiEnabled ? "on" : "off"}`}>
            {aiEnabled ? "Claude AI active" : "Offline coach mode"}
          </span>
        </div>
      </header>

      <main className="main-area">
        {stage === "onboarding" && (
          <Onboarding onGenerate={handleGenerate} loading={loading} error={error} />
        )}

        {stage === "dashboard" && (
          <div className="dashboard">
            <div className="dashboard-main">
              {aiSummary && (
                <div className="summary-card">
                  <p className="eyebrow">Coach's take</p>
                  <p>{aiSummary}</p>
                </div>
              )}
              {warnings.length > 0 && (
                <div className="warning-card">
                  {warnings.map((w, i) => (
                    <p key={i}>⚠ {w}</p>
                  ))}
                </div>
              )}
              <h2>Your schedule</h2>
              <p className="hint">Click a block to mark it done as you go.</p>
              <PlanTimeline
                sessions={sessions}
                subjectOrder={subjects.map((s) => s.name)}
                onToggle={handleToggle}
              />
            </div>
            <aside className="dashboard-side">
              <SubjectLegend subjects={subjects} />
              <ChatPanel />
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}

import { buildColorMap } from "../subjectColors";

function groupByDate(sessions) {
  const map = new Map();
  for (const s of sessions) {
    if (!map.has(s.session_date)) map.set(s.session_date, []);
    map.get(s.session_date).push(s);
  }
  return [...map.entries()].sort(([a], [b]) => (a < b ? -1 : 1));
}

function formatDay(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  return {
    weekday: d.toLocaleDateString(undefined, { weekday: "short" }),
    day: d.getDate(),
    month: d.toLocaleDateString(undefined, { month: "short" }),
  };
}

export default function PlanTimeline({ sessions, subjectOrder, onToggle }) {
  const colorMap = buildColorMap(subjectOrder);
  const days = groupByDate(sessions);
  const maxHours = Math.max(1, ...days.map(([, s]) => s.reduce((a, b) => a + b.hours, 0)));

  if (days.length === 0) {
    return <p className="empty-note">No sessions scheduled yet.</p>;
  }

  return (
    <div className="timeline">
      {days.map(([date, daySessions]) => {
        const { weekday, day, month } = formatDay(date);
        const totalHours = daySessions.reduce((a, b) => a + b.hours, 0);
        return (
          <div className="timeline-day" key={date}>
            <div className="timeline-date">
              <span className="timeline-weekday">{weekday}</span>
              <span className="timeline-daynum">{day}</span>
              <span className="timeline-month">{month}</span>
            </div>
            <div className="timeline-bar-col">
              <div
                className="timeline-stack"
                style={{ height: `${Math.max(24, (totalHours / maxHours) * 160)}px` }}
              >
                {daySessions.map((s) => (
                  <div
                    key={s.id}
                    className={`timeline-block ${s.completed ? "completed" : ""}`}
                    style={{
                      flexGrow: s.hours,
                      background: colorMap[s.subject_name],
                    }}
                    title={`${s.subject_name} — ${s.hours}h`}
                    onClick={() => onToggle(s)}
                  >
                    <span className="block-label">{s.subject_name}</span>
                    <span className="block-hours mono">{s.hours}h</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="timeline-total mono">{totalHours.toFixed(2)}h</div>
          </div>
        );
      })}
    </div>
  );
}

import { buildColorMap } from "../subjectColors";

export default function SubjectLegend({ subjects }) {
  const colorMap = buildColorMap(subjects.map((s) => s.name));
  return (
    <div className="legend">
      <h3>Subjects</h3>
      <div className="legend-list">
        {subjects.map((s) => {
          const pct = Math.min(
            100,
            Math.round((s.hours_completed / s.hours_needed) * 100)
          );
          return (
            <div className="legend-item" key={s.id}>
              <div className="legend-header">
                <span
                  className="legend-dot"
                  style={{ background: colorMap[s.name] }}
                />
                <span className="legend-name">{s.name}</span>
                <span className="legend-date mono">{s.exam_date}</span>
              </div>
              <div className="legend-track">
                <div
                  className="legend-fill"
                  style={{ width: `${pct}%`, background: colorMap[s.name] }}
                />
              </div>
              <div className="legend-meta mono">
                {s.hours_completed.toFixed(1)} / {s.hours_needed}h · {pct}%
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

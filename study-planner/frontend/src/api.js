const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export const api = {
  health: () => request("/api/health"),
  createPlan: (payload) =>
    request("/api/plan", { method: "POST", body: JSON.stringify(payload) }),
  getPlan: () => request("/api/plan"),
  getSubjects: () => request("/api/subjects"),
  checkin: (payload) =>
    request("/api/checkin", { method: "POST", body: JSON.stringify(payload) }),
  chat: (message) =>
    request("/api/chat", { method: "POST", body: JSON.stringify({ message }) }),
};

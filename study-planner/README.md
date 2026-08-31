# Plotline — AI Study Planner

A study planner that turns a list of exams into a day-by-day schedule, explains
its own reasoning in plain language, and coaches the student through a chat
panel when they fall behind.

---

## 1. Problem

Students juggling multiple exams struggle with a specific, recurring failure:
they know *what* they need to study, but not *how to split limited time
across it in a way that reflects urgency, difficulty, and importance*. Manual
planning tends to either ignore deadlines (equal time per subject) or panic
around the nearest exam and starve everything else. When a student inevitably
misses a day, most planners don't adapt — the plan just goes stale.

## 2. AI Solution

Plotline splits the problem into two layers on purpose:

- **A deterministic scheduling engine** (`backend/app/scheduler.py`) does the
  actual time allocation. It scores each subject every day by
  `urgency × difficulty × priority × hours remaining`, then distributes that
  day's available hours proportionally to the score. This is intentionally
  *not* left to an LLM — the allocation needs to be reproducible, fast, and
  provably correct (see Testing below), and a rules-based algorithm is the
  right tool for that job.
- **An AI coaching layer** (`backend/app/ai.py`, via the Claude API) sits on
  top of the schedule. It explains *why* the plan looks the way it does in
  plain language, and powers a chat assistant that answers study-technique
  questions ("I fell behind", "explain spaced repetition") and can point the
  student back to regenerating their plan when circumstances change. If no
  API key is configured, the app runs in "offline coach mode" with rule-based
  responses — no feature is lost, only the AI text becomes templated instead
  of freshly generated, which matters for a live demo with flaky wifi.

This mirrors how production AI features are usually built: a reliable,
testable core with an LLM layered on top for the parts that genuinely need
natural language, not the whole system routed through a model.

## 3. Architecture

```
┌──────────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│   React (Vite) SPA    │  ───────────────────▶  │   FastAPI backend         │
│  Onboarding · Timeline│  ◀───────────────────  │   /api/plan  /api/chat    │
│  Legend · Chat panel  │                         │   /api/checkin /health   │
└──────────────────────┘                         └────────────┬─────────────┘
                                                                │
                                          ┌─────────────────────┼─────────────────────┐
                                          ▼                                           ▼
                              scheduler.py (deterministic)                 ai.py (Claude API)
                              urgency-weighted greedy allocator             summary + chat coach
                                          │
                                          ▼
                                  SQLite (SQLAlchemy)
                          subjects · study_sessions · chat_messages
```

**Backend:** Python, FastAPI, SQLAlchemy, SQLite.
**Frontend:** React 19 + Vite, plain CSS (no framework — custom design system).
**AI:** Anthropic Claude API (`claude-sonnet-4-6`), with a rule-based fallback.

## 4. Build

```
study-planner/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI routes
│   │   ├── scheduler.py   # deterministic scheduling algorithm
│   │   ├── ai.py          # Claude API integration + fallback
│   │   ├── models.py      # SQLAlchemy ORM models
│   │   ├── schemas.py     # Pydantic request/response models
│   │   └── database.py    # SQLite session setup
│   ├── tests/
│   │   └── test_scheduler.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Onboarding.jsx     # subject intake form
    │   │   ├── PlanTimeline.jsx   # color-coded day-by-day timeline
    │   │   ├── SubjectLegend.jsx  # per-subject progress bars
    │   │   └── ChatPanel.jsx      # AI coach chat
    │   ├── api.js
    │   ├── subjectColors.js
    │   ├── App.jsx / App.css
    │   └── index.css              # design tokens
    ├── .env.example
    └── package.json
```

### Design decisions worth calling out for a demo/presentation

- **Why split scheduler vs. AI?** So the core logic is unit-testable and
  never "hallucinates" a schedule that double-books hours or schedules past
  an exam date — see `test_scheduler.py`.
- **Why SQLite?** Zero setup for a hackathon; swap `DATABASE_URL` in
  `database.py` for Postgres in one line for production.
- **Why does the API still work with no key set?** So a demo never breaks on
  stage because of a missing/rate-limited API key — the fallback logic in
  `ai.py` produces genuinely useful (if less varied) text.
- **UI direction:** the timeline visualizes each day as a stacked bar,
  colored per subject — literally like highlighter marks on a paper planner
  — so priority and workload are visible at a glance, not just listed in a
  table.

## 5. Test

Run the automated test suite (scheduler logic — the part that must be
provably correct):

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

8 tests covering:
- no session is ever scheduled after a subject's exam date
- daily allocation never exceeds `daily_hours_available`
- a subject never receives more than its `hours_needed`
- more urgent exams get scheduled earlier
- higher difficulty/priority subjects receive proportionally more time
- a warning is raised when a target is mathematically impossible in the time left
- empty input produces empty output (no crash)
- already-completed hours reduce further allocation correctly

**Manual/API testing:** every endpoint (`/api/health`, `/api/plan`,
`/api/chat`, `/api/checkin`, `/api/subjects`) was smoke-tested end-to-end via
curl during development, including the offline-AI fallback path.

**Suggested demo test:** add a subject with an exam in 2 days needing 100
hours — the app will schedule what it can and surface a warning that the
target isn't achievable, rather than silently failing.

## 6. Deploy

**Backend (Render / Railway / Fly.io — any container/Python host):**
```bash
cd backend
pip install -r requirements.txt
# set ANTHROPIC_API_KEY as an environment variable in your host's dashboard (optional)
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Frontend (Vercel / Netlify):**
```bash
cd frontend
npm install
npm run build         # outputs to dist/
# set VITE_API_URL to your deployed backend URL as a build-time env var
```
Point the static host at `frontend/dist`.

**Local run (for the demo):**
```bash
# terminal 1
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# terminal 2
cd frontend && npm install && npm run dev
```
Then open the Vite dev URL (typically `http://localhost:5173`).

## 7. Present

**One-line pitch:** "Plotline turns your exam list into a schedule that
adapts to urgency and difficulty automatically, and coaches you through it
like a study buddy who never gets tired."

**Suggested demo flow:**
1. Add 2-3 subjects with different exam dates/difficulty — show the
   AI-generated summary explaining *why* the schedule looks the way it does.
2. Point out the color-coded timeline — urgency is visually obvious.
3. Click a block to mark it complete — show the subject's progress bar move.
4. Open the chat panel, ask "I fell behind on Calculus, what should I do?" —
   show the coach respond, then regenerate the plan to show it adapts.
5. Mention the offline-fallback design as an engineering decision, not a
   limitation — the app is demo-safe even without network access to the AI API.

**Talking points for judges:**
- Clear separation of deterministic logic (tested, provable) vs. generative
  AI (explanatory, conversational) — a realistic pattern for production AI
  products, not "wrap everything in a prompt."
- Full loop: input → AI-assisted planning → tracking → adaptive replanning.
- Built and tested in one session: 8 passing unit tests, working API, working UI.

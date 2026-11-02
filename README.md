# CareerPilot AI — Personalized Career & Placement Workspace

CareerPilot AI is a local-first Flask application for students and early-career developers. It combines profile-based career analysis, a seven-agent workflow, a persistent learning roadmap, contextual career chat, job-description matching, a what-if simulator, mock interviews, application tracking, resume structure checks, and report exports.

## Features in this package

- Account registration/login with password hashing and per-user data queries.
- Student profile and seven-agent career analysis with role skills, gaps, readiness factors, and explainability.
- Personalized assistant using saved profile, analysis, learning tasks, recent chat, local knowledge notes, optional local Ollama, and deterministic fallback answers.
- Saved learning roadmap with persistent task statuses.
- Job-description matching using curated skill recognition and common aliases (not a commercial ATS engine).
- Career skill what-if simulator.
- Mock interview with answer-level practice rubric and saved history. Scores are heuristic practice feedback, not hiring predictions.
- Application create/list/edit/delete with status and match score.
- Manual skill-progress and assistant feedback records.
- Local resume upload for PDF/DOCX/TXT, text extraction, basic section/keyword checks, and suggestions. Scanned image PDFs are not supported.
- JSON career report, CSV export, and browser print-to-PDF.
- Dashboard with a multi-agent orchestration map, module capability cards, agent activity, evaluation counts, responsive dark command-center UI, and local knowledge notes.

## Requirements

- Python 3.10 or newer (Python 3.13 is supported by the source; use the latest stable Python available on your system).
- Internet only for the first dependency install.
- Optional: Ollama installed locally and a model such as `llama3.2:3b` pulled for local model-generated answers. Core workflows use fallbacks if Ollama is unavailable.

## Run on Windows

1. Extract the ZIP to a normal folder, for example `Downloads\CareerPilot-AI-Advanced-Updated`.
2. Double-click `SETUP_AND_RUN.bat`.
3. Wait for dependency installation and the Flask server to start.
4. Open `http://127.0.0.1:5000` in Edge or Chrome.
5. Create an account, enter your name and target role, add current skills, save the profile, and run Career Intelligence.

Alternative PowerShell commands from this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Optional Ollama setup

```powershell
ollama pull llama3.2:3b
ollama serve
```

Keep Ollama running in its own terminal, then start CareerPilot in another terminal. Set `CAREERPILOT_MODEL` if you use a different installed model.

## Configuration

- `CAREERPILOT_SECRET`: long random session secret. Set before public use; the default is for local development only.
- `CAREERPILOT_MODEL`: local Ollama model (default `llama3.2:3b`).
- `CAREERPILOT_DB_PATH`: optional path to SQLite database.
- `CAREERPILOT_KNOWLEDGE_DIR`: optional local knowledge directory.
- `CAREERPILOT_COOKIE_SECURE=true`: only when served over HTTPS.
- `CAREERPILOT_DEBUG=true`: development debugging; keep false for normal use.

## Your data and privacy

The database is created at `data/careerpilot.db`. Profile, analysis, chat, tasks, applications, projects, and extracted resume text stay in that local SQLite database. Uploaded resume contents are not sent to a hosted API by this application. Back up the database before replacing project files. The source ZIP intentionally excludes your database, virtual environment, and Git metadata.

## Tests

From this folder, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check static/app.js
```

The tests use a temporary SQLite database and mock Ollama, so they do not need to download or run a model.

## Known boundaries — not represented as completed

- No live job-board API is connected; the app only analyses job descriptions pasted by the user.
- Resume checks are basic local structure checks, not an official ATS score. Scanned-image OCR is not included.
- Interview scoring is a transparent heuristic practice rubric; no validated hiring prediction or AI evaluation of tone/body language is claimed.
- Audio/video interview recording and transcription, external email/calendar actions, browser extension, institutional administration, hosted multi-user deployment, and vector-embedding retrieval are not connected in this local version.
- Before public deployment, add formal CSRF protection, login rate limiting, a production WSGI server, HTTPS, and a security/accessibility review.

See `PRD.md`, `DESIGN.md`, `ARCHITECTURE.md`, `UPGRADE_NOTES.md`, and `REMAINING_WORK.md` for scope and technical notes.

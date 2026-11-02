# Product Requirements Document — CareerPilot AI

## 1. Product vision

CareerPilot AI is a local-first, personalized career and placement guidance application for students and early-career developers. It converts a student's current skills, target role, goals, and project evidence into explainable career analysis and practical next steps.

## 2. Problem statement

Students often receive generic advice that does not reflect their current skills or target role. Career preparation is also fragmented across skill learning, portfolio building, job descriptions, mock interviews, and application tracking. CareerPilot brings these activities into one saved workspace.

## 3. Intended users

- Students preparing for internships and campus placements
- Early-career developers planning a role transition
- Project demonstrators who need to explain a role-aligned career workflow

## 4. Main user journey

1. Create an account and log in.
2. Enter a career profile and target role.
3. Run the seven-agent career analysis.
4. Review role-required skills, matched skills, gaps, readiness factors, and learning tasks.
5. Ask context-aware questions using the assistant.
6. Practice against a job description and use the simulator/interview modules.
7. Save portfolio projects, track applications, record progress, and review reports.

## 5. Functional requirements

| ID | Requirement | Current implementation |
|---|---|---|
| FR-01 | Account registration and login | Implemented with SQLite and password hashing |
| FR-02 | Save a per-user profile | Implemented |
| FR-03 | Generate role-based career analysis | Implemented with seven specialist agents |
| FR-04 | Show matched skills and gaps | Implemented for curated role definitions |
| FR-05 | Explain readiness score factors | Implemented with heuristic factors |
| FR-06 | Create and persist learning tasks | Implemented; status persists in SQLite |
| FR-07 | Give personalized assistant answers | Implemented using profile/analysis/roadmap context, local knowledge, optional Ollama, and fallback responses |
| FR-08 | Match a pasted job description | Implemented for recognized skill terms |
| FR-09 | Simulate the effect of adding skills | Implemented |
| FR-10 | Run a practice interview and save score/history | Implemented with heuristic scoring |
| FR-11 | Track portfolio projects and job applications | Implemented for create/list workflows |
| FR-12 | Record skill progress and feedback | Implemented |
| FR-13 | Display activity, evaluation metrics, and report | Implemented |
| FR-14 | Preserve chat history between sessions | Implemented for authenticated users |
| FR-15 | Upload and review resume structure | Implemented for text-based PDF, DOCX, and TXT; scanned-image OCR is not included |
| FR-16 | Edit/delete portfolio projects and application records | Implemented with user-scoped CRUD endpoints |
| FR-17 | Export a career report | JSON report, CSV download, and browser print-to-PDF are implemented |

## 6. Non-functional requirements

- Local operation without a hosted AI API
- Persistent SQLite storage for account and activity data
- User-specific data access checks on authenticated routes
- Beginner-friendly UI and clear error messages
- Basic responsive styling
- Model failure should not disable the core deterministic workflows

## 7. Success criteria for a student demo

- A user can register, log in, save a target role and skills, and run analysis.
- Analysis produces a role skill map, gap list, learning tasks, and readiness explanation.
- The assistant uses saved context and can answer “what should I learn first?” with a concrete action.
- A roadmap status change remains after reload.
- Job matching, simulator, mock interview, project tracking, application tracking, evaluation, and report routes respond correctly.

## 8. Out of scope for this version

Live job-board APIs, scanned-image OCR, audio/video interview analysis, external email/calendar actions, browser extension, multi-tenant institutional administration, cloud hosting, and production compliance/security certification.

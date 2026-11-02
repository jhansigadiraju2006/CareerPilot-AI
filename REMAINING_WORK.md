# Remaining Work and Honest Scope Boundary

## Implemented in the current local package

- [x] Account registration/login and per-user route checks.
- [x] Profile save/load and seven-agent career analysis.
- [x] Personalized assistant with chat history, local knowledge retrieval, optional Ollama, and deterministic fallback.
- [x] Persistent roadmap and task status updates.
- [x] Curated skill matching with common aliases for pasted job descriptions.
- [x] Career simulator, mock interview with answer-level practice rubric, project/application CRUD, manual progress and feedback.
- [x] Local resume parsing for selectable-text PDF, DOCX, and TXT; size/type checks; basic structure score and suggestions.
- [x] JSON report, CSV export, browser print-to-PDF, dashboard and evaluation endpoints.
- [x] Automated smoke tests for auth, chat, roadmap, resume upload, report export, CRUD isolation, interview rubric and invalid inputs.

## Still needed for a production-grade product

- [ ] Live job-board APIs: requires selecting providers, developer credentials, usage terms, and attribution; scraping is intentionally not included.
- [ ] Scanned-PDF OCR and deeper resume parsing; requires OCR dependency and more test fixtures.
- [ ] Vector-embedding RAG for large knowledge libraries; current local notes use keyword overlap.
- [ ] Audio/video interview recording/transcription; requires explicit consent, browser/device testing, retention controls and accessibility design.
- [ ] External email/calendar actions and browser extension; these require provider integrations and user authorization.
- [ ] Formal CSRF protection, login throttling, production WSGI server, HTTPS, secrets management and a security review before internet exposure.
- [ ] Full keyboard/screen-reader/contrast/mobile audit and CI pipeline.
- [ ] Schema migration framework and database backup/restore UI.

## Score interpretation

Career readiness, resume structure, job match, and mock-interview scores are heuristic learning aids. They are not validated employment predictions and do not guarantee a placement or interview.

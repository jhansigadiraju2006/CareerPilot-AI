# UX and UI Design — CareerPilot AI

## Visual direction

A dark, professional “career command center” designed for a student to see their target role, current skills, gaps, readiness indicators, and next actions without navigating between separate tools. The interface uses a fixed sidebar on wide screens, cards/panels for data, and a responsive layout for smaller screens.

## Navigation structure

- **Command Center:** top-level career snapshot and assistant
- **Career Twin:** current profile compared with target role
- **Skill Graph:** required skills and current match/gap status
- **Learning:** saved roadmap and task status controls
- **Resume Studio:** local PDF/DOCX/TXT extraction, structure checklist, and actionable feedback
- **Job Intelligence:** paste a job description and view match/gaps
- **Career Simulator:** model how adding skills affects coverage
- **Mock Interview:** role-aware questions, answer input, score, and history
- **Portfolio Builder:** add and review projects
- **Application Tracker:** record company, role, status, match score, and notes
- **Agent Activity:** view specialist-agent execution trail
- **Evaluation:** review operational counts and failure metrics
- **Reports:** inspect the aggregated career report

## Interaction rules

- Save the profile before running analysis; do not analyze unsaved form values.
- Use explicit success/error text rather than silently ignoring failed writes.
- Escape dynamic content before inserting it into HTML; chat uses text nodes.
- Keep roadmap status in the database, not only in browser memory.
- Preserve recent assistant messages after reload by retrieving authenticated history.
- Provide a usable fallback when the local model is unavailable.
- Resume parsing is local, size-limited, and reports when scanned-image text cannot be extracted.
- Project/application edit and delete actions are scoped to the signed-in user.
- Make heuristic scores understandable and avoid presenting them as guaranteed outcomes.

## Accessibility and usability checklist

- Inputs should have visible labels and understandable placeholders.
- Status should be conveyed in text as well as color.
- Buttons should have descriptive action names.
- Keyboard users should be able to navigate controls and submit the chat input with Enter.
- Print styles should make report content readable on paper.
- Remaining work: perform a formal keyboard-only, screen-reader, contrast, and mobile-device review before production use.


## Command-center complexity layer

The home dashboard includes a visible orchestration pipeline, on-demand module cards, and a high-level local data-flow strip. These are a product overview of the existing workflows, not a claim that each module is an always-running background agent or that external job boards are connected. The pipeline communicates the sequence from profile context through role-skill analysis, learning planning, and readiness explanation.

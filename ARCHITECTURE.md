# Architecture — CareerPilot AI

## Current implementation

```text
Browser (HTML + CSS + JavaScript)
              |
              | JSON over same-origin HTTP
              v
        Flask application
              |
       +------+----------------+
       |                       |
       v                       v
   Services layer          Orchestrator
       |                       |
       |                 7 specialist agents
       |                       |
       +-----------+-----------+
                   |
          +--------+---------+
          |                  |
          v                  v
       SQLite DB       Local knowledge notes
          |                  |
          +--------+---------+
                   |
             Optional Ollama
            (local LLM runtime)
```

## Components

- `app.py`: routes, authentication session checks, input validation, and API responses.
- `services.py`: profile persistence, job-description skill matching, personalized chat context, conversation history, and response fallback.
- `orchestrator.py`: validates an optional model-generated execution plan, runs specialist agents in dependency order, logs activity, and composes analysis output.
- `agents/agents.py`: deterministic role skills, learning task guidance, resume evidence checks, readiness estimate, interview prompts, and project suggestions.
- `db.py`: SQLite schema initialization and transaction context manager, including persistent resume assessment metadata.
- Resume Studio route: extracts selectable text from TXT/PDF/DOCX locally and stores the extracted text and basic assessment per user.
- Export routes: CSV career report; browser print can be used to save the rendered report as PDF.
- `knowledge.py`: small local text knowledge base and keyword-overlap retrieval.
- `ollama_client.py`: optional Ollama adapter; errors are converted into a fallback signal.
- `templates/index.html`, `static/style.css`, `static/app.js`: user interface and client-side API interactions.

## Data flow

1. User saves a profile in `profiles`.
2. `Orchestrator.analyze()` uses specialist agents and logs activity in `activities`.
3. The JSON analysis is stored in `analyses` and returned to the browser.
4. Learning tasks are stored in `learning_tasks`; status updates are scoped to the signed-in user.
5. Chat composes profile, latest analysis, roadmap, saved resume assessment, local knowledge, and recent conversation history. Ollama is attempted if available; otherwise a contextual deterministic response is returned. Both user and assistant messages are saved in `conversations`.
6. Job analyses, interviews, projects, applications, progress, simulations, and feedback are saved in separate SQLite tables.

## Configuration

- `CAREERPILOT_SECRET`: session signing secret; set a long random value before deployment.
- `CAREERPILOT_MODEL`: Ollama model name; default `llama3.2:3b`.
- `CAREERPILOT_DB_PATH`: optional SQLite database path override.
- `CAREERPILOT_KNOWLEDGE_DIR`: optional local knowledge directory override.

## Architectural constraints

The current app is a single Flask process with SQLite and a browser-rendered interface. The model planner is optional and can fall back to deterministic planning. The local knowledge retrieval is simple keyword overlap, not a full embedding/vector RAG pipeline. A future production version can split the API, worker/agent runtime, model gateway, document processing, and analytics store, but this version deliberately preserves the existing Flask stack to avoid breaking local data and setup.

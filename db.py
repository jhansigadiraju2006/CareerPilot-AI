
import sqlite3
from contextlib import contextmanager
from config import DB_PATH


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    c = sqlite3.connect(DB_PATH)
    try:
        c.executescript('''
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiles(
    user_id INTEGER PRIMARY KEY,
    name TEXT DEFAULT '',
    college TEXT DEFAULT '',
    target_role TEXT DEFAULT '',
    skills TEXT DEFAULT '',
    experience_level TEXT DEFAULT 'Beginner',
    goals TEXT DEFAULT '',
    certifications TEXT DEFAULT '',
    projects TEXT DEFAULT '',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analyses(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    analysis_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    agent TEXT,
    action TEXT,
    status TEXT,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    role TEXT,
    message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    rating TEXT,
    context TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_analyses(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    job_text TEXT,
    result_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interviews(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    role TEXT,
    difficulty TEXT,
    score INTEGER,
    feedback TEXT,
    questions_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    description TEXT,
    skills TEXT,
    status TEXT DEFAULT 'Planned',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    company TEXT,
    role TEXT,
    status TEXT DEFAULT 'Applied',
    match_score INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS progress(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    skill TEXT,
    score INTEGER,
    source TEXT DEFAULT 'manual',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulations(
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    target_role TEXT,
    added_skills TEXT,
    coverage_before INTEGER,
    coverage_after INTEGER,
    gaps_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    target_role TEXT DEFAULT '',
    week_number INTEGER NOT NULL DEFAULT 1,
    skill TEXT NOT NULL,
    task TEXT NOT NULL,
    priority TEXT DEFAULT 'Medium',
    status TEXT NOT NULL DEFAULT 'Not Started',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_learning_tasks_user
ON learning_tasks(user_id);

CREATE TABLE IF NOT EXISTS resume_documents(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    extracted_text TEXT NOT NULL DEFAULT '',
    analysis_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
''')
    finally:
        c.close()


init_db()


@contextmanager
def get_db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row

    try:
        yield c
        c.commit()
    finally:
        c.close()

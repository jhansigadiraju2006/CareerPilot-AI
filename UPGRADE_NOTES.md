# Upgrade Notes

This package keeps the existing Flask + SQLite architecture to avoid an unnecessary rewrite and to make it easier to preserve an existing local database.

Implemented upgrades include:
- local resume upload and section checks for TXT/PDF/DOCX;
- persistent resume assessment metadata in a per-user SQLite table;
- report CSV export;
- edit/delete endpoints for portfolio projects and applications, scoped to the current user;
- answer-level mock interview rubric and practice-only disclaimer;
- common aliases for skill matching;
- resume context available to the personalized assistant and report;
- expanded smoke tests.

The uploaded source ZIP does not include a user's SQLite database, `.venv`, `.git`, or backup copies. To preserve prior data, back up the original `data/careerpilot.db` and copy it into the extracted package's `data` folder before first launch.

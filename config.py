import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("CAREERPILOT_DB_PATH", str(BASE_DIR / "data" / "careerpilot.db"))).expanduser()
KNOWLEDGE_DIR = Path(os.getenv("CAREERPILOT_KNOWLEDGE_DIR", str(BASE_DIR / "data" / "knowledge"))).expanduser()
# Set CAREERPILOT_SECRET to a long random value before deployment.
SECRET_KEY = os.getenv("CAREERPILOT_SECRET", "local-development-only-change-me")
MODEL = os.getenv("CAREERPILOT_MODEL", "llama3.2:3b")

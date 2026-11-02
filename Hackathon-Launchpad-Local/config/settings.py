import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_AGENT_ID = os.getenv("SARVAM_AGENT_ID", "")
SAMVAAD_API_KEY = os.getenv("SAMVAAD_API_KEY", "")
SAMVAAD_ORG_ID = os.getenv("SAMVAAD_ORG_ID", "")
SAMVAAD_WORKSPACE_ID = os.getenv("SAMVAAD_WORKSPACE_ID", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "")

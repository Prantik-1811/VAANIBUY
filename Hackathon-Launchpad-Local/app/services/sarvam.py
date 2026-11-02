import os
from pathlib import Path

from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

def get_sarvam_client():
    key = os.getenv("SARVAM_API_KEY")
    if not key:
        raise RuntimeError("SARVAM_API_KEY is not configured in .env")
    return SarvamAI(api_subscription_key=key)

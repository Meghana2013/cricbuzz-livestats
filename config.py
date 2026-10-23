"""Application configuration. Secrets are read from the .env file, never hard-coded."""
import os

from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")
REQUEST_TIMEOUT = 15      # seconds
MAX_RETRIES = 3

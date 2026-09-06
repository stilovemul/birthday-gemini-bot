import os
from pathlib import Path
from datetime import timezone, timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

# Load environment variables from local, project, or user home .env
load_dotenv(BASE_DIR / ".env")
load_dotenv(Path.home() / ".env")
load_dotenv()

# Moscow Timezone (UTC+3)
MSK_TZ = timezone(timedelta(hours=3))

# Environment Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_GEMINI_BOT_TOKEN") or ""
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "157236577"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Storage Paths
BIRTHDAYS_FILE = DATA_DIR / "birthdays.json"
SENT_HISTORY_FILE = DATA_DIR / "sent_history.json"
NOTES_FILE = DATA_DIR / "notes.json"

# Birthday settings
REMIND_DAYS_BEFORE = [7, 3, 1, 0]
DAILY_CHECK_HOUR = 9
DAILY_CHECK_MINUTE = 0

# Yandex OAuth Token
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN", "")


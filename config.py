import json
import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# מי מקבל את הסיכום היומי במייל - רשימה מופרדת בפסיקים ב-env, למשל:
# RECIPIENT_EMAILS=parent1@example.com,parent2@example.com
RECIPIENT_EMAILS = [
    e.strip()
    for e in os.environ.get("RECIPIENT_EMAILS", "").split(",")
    if e.strip()
]

# מיפוי שם הקבוצה כפי שהוא מופיע בעמודה B בגיליון -> שם הילד המשויך.
# מוגדר כמחרוזת JSON ב-env כדי שלא יהיה מידע אישי בקוד עצמו, למשל:
# GROUP_TO_CHILD_JSON={"כיתה ב׳ שדות": "ילד א", "גן שיבולת": "ילד ב"}
GROUP_TO_CHILD = json.loads(os.environ.get("GROUP_TO_CHILD_JSON", "{}"))

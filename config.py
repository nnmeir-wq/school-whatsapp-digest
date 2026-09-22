import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID", "1dJu-7PFSTsNx9lOE_zGPgVy3dfB8yqli8KbRXTyBVOU"
)

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# מי מקבל את הסיכום היומי במייל
RECIPIENT_EMAILS = [
    "nn.meir@gmail.com",
    "tal.nitzan.33@gmail.com",
]

# מיפוי שם הקבוצה כפי שהוא מופיע בעמודה B בגיליון -> שם הילד המשויך
GROUP_TO_CHILD = {
    "גן שיבולת תשפ״ז 🌾": "תבור (בן 4)",
    "כיתה ב׳ שדות 🌱❤️": "יערי (בת 8)",
    "ה׳ בנות שדות 🎀 (תשפ״ז)- מור רביבו": "כרמל (בת 10)",
    "כיתה ו׳ המתוקות- הורים": "אריאל (בת 12)",
}

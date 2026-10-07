import logging
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import config
import mailer
import sheets_client
import summarizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")


def digest_date_label(now: datetime) -> str:
    """The run is scheduled for 23:07 Israel time, covering messages up
    to that night. A legitimate on-time run only ever executes in the
    23:00-23:59 hour; if it's running at any other local hour, GitHub's
    scheduler delayed it past midnight, so the messages it's reading
    still belong to the PREVIOUS calendar day, not the day it happens
    to execute on."""
    target = now if now.hour == 23 else now - timedelta(days=1)
    return target.strftime("%d/%m/%Y")


def group_by_child(rows):
    grouped = {}
    for row in rows:
        text = row["text"].strip()
        if not text:
            continue
        group_name = row["group"]
        child = config.GROUP_TO_CHILD.get(group_name, f"קבוצה לא מזוהה: {group_name}")
        entry = f"[{row['timestamp']}] {text}" if row["timestamp"] else text
        grouped.setdefault(child, []).append(entry)
    return grouped


def main():
    date_label = digest_date_label(datetime.now(ISRAEL_TZ))

    try:
        rows, first_row, last_row = sheets_client.read_rows()
    except Exception as e:
        logger.exception("Failed to read from Google Sheets")
        mailer.send_failure_alert(f"קריאת הגיליון נכשלה: {e}")
        sys.exit(1)

    if not rows:
        logger.info("No rows found in the sheet - sending 'no updates' email.")
        try:
            mailer.send_no_updates(date_label)
        except Exception as e:
            logger.exception("Failed to send 'no updates' email")
            sys.exit(1)
        return

    grouped = group_by_child(rows)

    try:
        summary_html = summarizer.summarize(grouped)
    except Exception as e:
        logger.exception("Failed to summarize via the Claude API")
        mailer.send_failure_alert(f"קריאת ה-API של קלוד נכשלה: {e}")
        sys.exit(1)

    try:
        mailer.send_digest(summary_html, date_label)
    except Exception as e:
        logger.exception("Failed to send the digest email")
        mailer.send_failure_alert(f"שליחת המייל נכשלה: {e}")
        sys.exit(1)

    try:
        sheets_client.delete_rows(first_row, last_row)
        logger.info("Deleted processed rows %s-%s from the sheet", first_row, last_row)
    except Exception as e:
        logger.exception("Failed to delete processed rows")
        mailer.send_failure_alert(
            "המייל נשלח בהצלחה, אך מחיקת השורות שעובדו מהגיליון נכשלה - "
            f"ייתכן שאותן הודעות יופיעו שוב בסיכום מחר. סיבה: {e}"
        )
        sys.exit(1)

    logger.info("Done.")


if __name__ == "__main__":
    main()

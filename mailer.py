import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)


def _html_to_plain_fallback(html: str) -> str:
    text = re.sub(r"(?i)</(h1|h2|h3|li|p|div)>", "\n", html)
    text = re.sub(r"(?i)<li[^>]*>", "- ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _send_email(subject: str, html_body: str, plain_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.SMTP_USER
    msg["To"] = ", ".join(config.RECIPIENT_EMAILS)
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_USER, config.RECIPIENT_EMAILS, msg.as_string())


def send_digest(content_html: str, date_label: str) -> None:
    """Isolated entry point for delivering the daily digest.

    This is the ONLY function main.py calls to deliver the finished digest.
    To switch the delivery channel to WhatsApp later, replace the body of
    this function with a call to the WhatsApp MCP service - nothing else
    in the project needs to change.
    """
    subject = f"סיכום הודעות בית ספר - {date_label}"
    wrapped_html = f"""\
<html dir="rtl" lang="he">
  <body style="font-family: Arial, Helvetica, sans-serif; direction: rtl; text-align: right; line-height: 1.5;">
    <h1 style="font-size: 20px;">סיכום הודעות בית ספר - {date_label}</h1>
    {content_html}
  </body>
</html>
"""
    plain_body = _html_to_plain_fallback(content_html)
    _send_email(subject, wrapped_html, plain_body)
    logger.info("Digest email sent to %s", config.RECIPIENT_EMAILS)


def send_no_updates(date_label: str) -> None:
    send_digest("<p>אין עדכונים היום מקבוצות בית הספר.</p>", date_label)


def send_failure_alert(error_message: str) -> None:
    subject = "האוטומציה של סיכום הודעות בית הספר נכשלה היום"
    html_body = (
        "<p>האוטומציה של סיכום הודעות בית הספר נכשלה היום ולא נשלח סיכום.</p>"
        f"<p>סיבת הכשל:</p><pre>{error_message}</pre>"
    )
    plain_body = f"האוטומציה נכשלה היום ולא נשלח סיכום.\n\nסיבת הכשל:\n{error_message}"
    try:
        _send_email(subject, html_body, plain_body)
    except Exception:
        logger.exception("Failed to send the failure-alert email as well")

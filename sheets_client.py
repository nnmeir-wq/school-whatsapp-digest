import json
import logging

import gspread
from dateutil import parser as date_parser
from google.oauth2.service_account import Credentials

import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _load_credentials():
    raw = config.GOOGLE_SERVICE_ACCOUNT_JSON
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")
    if raw.strip().startswith("{"):
        info = json.loads(raw)
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    return Credentials.from_service_account_file(raw, scopes=SCOPES)


def _open_sheet():
    creds = _load_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
    return spreadsheet.sheet1


def _looks_like_data_row(row):
    """Heuristic: a real data row starts with a parseable timestamp in column A."""
    if not row or not row[0].strip():
        return False
    try:
        date_parser.parse(row[0], dayfirst=True)
        return True
    except (ValueError, OverflowError):
        return False


def read_rows():
    """Reads all current rows from the sheet.

    Returns (rows, first_row_number, last_row_number) where the row numbers
    are 1-indexed sheet row numbers, used later to delete exactly the rows
    that were read (in case new messages arrive while we're processing).
    Returns ([], None, None) if there is no data.
    """
    sheet = _open_sheet()
    all_values = sheet.get_all_values()
    if not all_values:
        return [], None, None

    start_idx = 0 if _looks_like_data_row(all_values[0]) else 1
    data_values = all_values[start_idx:]
    if not data_values:
        return [], None, None

    rows = []
    for r in data_values:
        timestamp = r[0].strip() if len(r) > 0 else ""
        group = r[1].strip() if len(r) > 1 else ""
        text = r[2] if len(r) > 2 else ""
        if not (timestamp or group or text.strip()):
            continue
        rows.append({"timestamp": timestamp, "group": group, "text": text})

    first_row_number = start_idx + 1
    last_row_number = len(all_values)
    logger.info(
        "Read %d data rows from sheet (rows %d-%d)",
        len(rows),
        first_row_number,
        last_row_number,
    )
    return rows, first_row_number, last_row_number


def delete_rows(first_row_number, last_row_number):
    if first_row_number is None:
        return
    sheet = _open_sheet()
    sheet.delete_rows(first_row_number, last_row_number)

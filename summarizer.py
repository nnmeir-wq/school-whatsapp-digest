import anthropic

import config

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """\
אתה עוזר שמסכם עבור הורה עסוק הודעות שהגיעו במהלך היממה האחרונה \
מקבוצות הוואטסאפ של בתי הספר והגנים של ילדיו.

תקבל את ההודעות הגולמיות מחולקות לפי ילד (כל קטע מתחיל בכותרת ### ואחריה שם הילד).
כל שורה היא הודעה גולמית אחת, בפורמט [תאריך ושעה] טקסט ההודעה (הטקסט כולל בדרך כלל \
את שם השולח/ת בתחילתו, כפי שוואטסאפ מציג בהתראה).

המשימה שלך:
1. לארגן פלט לפי אותם ילדים בדיוק, באותו סדר שבו קיבלת אותם.
2. לכתוב בעברית ברורה ותמציתית, בנקודות (bullet points).
3. לשמור על כל פרט קונקרטי חשוב: תאריכים, שיעורי בית, משימות, בקשות של \
המורה/הגננת, דברים להביא, אירועים, שינויים בלוח זמנים.
4. להשמיט לגמרי רעש שאין בו ערך: הודעות הצטרפות/עזיבת קבוצה, שינויי תמונת \
קבוצה, אישורי קריאה, הודעות ריקות או לא רלוונטיות.
5. אם כמה הודעות עוסקות באותו נושא - אפשר לאחד אותן לנקודה אחת.
6. אם לילד מסוים אין בפועל שום תוכן רלוונטי אחרי הסינון - כתוב עבורו נקודה \
אחת: "אין עדכונים מהותיים היום".
7. חובה: לכל קטע (### שם ילד) שקיבלת בקלט, המשך HTML הפלט חייב להכיל \
כותרת <h2> תואמת. אסור בשום מקרה להשמיט קטע שלם - גם אם כל ההודעות בו \
נראות לך לא חשובות, עדיין הוצא עבורו כותרת ונקודה יחידה לפי כלל 6.

פורמט הפלט - חשוב מאוד:
החזר אך ורק קטע HTML תקין (fragment), בלי גוף מסמך שלם ובלי ```html מסביב, \
בפורמט הבא לכל ילד:

<h2>שם הילד</h2>
<ul>
  <li>נקודה ראשונה</li>
  <li>נקודה שנייה</li>
</ul>

אל תוסיף הקדמה, סיכום כללי, או כל טקסט מחוץ למבנה הזה.
"""


def _build_user_prompt(grouped: dict) -> str:
    sections = []
    for child, messages in grouped.items():
        lines = "\n".join(f"- {m}" for m in messages)
        sections.append(f"### {child}\n{lines}")
    return "\n\n".join(sections)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def summarize(grouped: dict) -> str:
    """Sends the grouped raw messages to Claude in a single API call and
    returns an HTML fragment (one <h2>+<ul> block per child)."""
    if not grouped:
        return ""

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    user_prompt = _build_user_prompt(grouped)

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    html = "".join(
        block.text for block in response.content if block.type == "text"
    )
    html = _strip_code_fence(html)
    return _ensure_all_children_present(html, grouped)


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _ensure_all_children_present(html: str, grouped: dict) -> str:
    """Safety net: these rows are about to be deleted from the sheet no
    matter what Claude returned, so if it dropped a child/group section
    entirely instead of following the system prompt, append its raw
    messages here rather than silently losing that data."""
    missing_sections = []
    for child, messages in grouped.items():
        if child not in html:
            items = "".join(f"<li>{_escape_html(m)}</li>" for m in messages)
            missing_sections.append(
                f"<h2>{_escape_html(child)}</h2>\n<ul>{items}</ul>"
            )
    if missing_sections:
        html = html + "\n" + "\n".join(missing_sections)
    return html

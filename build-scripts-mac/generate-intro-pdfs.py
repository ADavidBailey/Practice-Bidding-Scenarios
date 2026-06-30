#!/usr/bin/env python3
"""Generate per-lesson {name}_Intro.pdf files for the coaching-non-rotated collection.

For each coaching-non-rotated/<name>.pbn, read the matching btn/<name>.btn,
extract its /*@chat ... @chat*/ block, and render a one-page intro PDF styled to
match the Baker-Bridge intro PDFs (US Letter, Arial, royal-blue all-caps title,
red H/D & black S/C suit symbols, ~11pt body). Lessons with no .btn or no @chat
get no PDF.

The .btn @chat blocks are NOT modified — they remain the source of truth for the
BBO Practice Bidding Table (dlr/ files). This script only reads them, so it is
safe to re-run any time a @chat block changes.

The Bridge Classroom app's "Intro" button fetches {baseUrl}/<name>_Intro.pdf and
auto-opens it when a lesson opens.

Requires: reportlab  (pip install --user reportlab)
Usage:    python3 build-scripts-mac/generate-intro-pdfs.py
"""
import os
import re
import json
import html

import reportlab.rl_config
reportlab.rl_config.invariant = 1  # deterministic output: no embedded timestamp,
#                                    so re-running churns git only when @chat changes.

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

# Paths derived from this script's location (parent of build-scripts-mac).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COACH = os.path.join(PROJECT_ROOT, "coaching-non-rotated")
BTN = os.path.join(PROJECT_ROOT, "btn")
FONTDIR = "/System/Library/Fonts/Supplemental"  # macOS Arial (carries suit glyphs)

# --- fonts: real Arial, to match the Baker-Bridge intros ---
pdfmetrics.registerFont(TTFont("Arial", f"{FONTDIR}/Arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", f"{FONTDIR}/Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", f"{FONTDIR}/Arial Italic.ttf"))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", f"{FONTDIR}/Arial Bold Italic.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                              italic="Arial-Italic", boldItalic="Arial-BoldItalic")

BLUE = HexColor(0x1a1ab3)   # royal-blue title
RED = "#d32f2f"
LINK = "#1976d2"

# Sized up for senior / super-senior readability (was 16/12.5/11).
TITLE = ParagraphStyle("title", fontName="Arial-Bold", fontSize=22, leading=27,
                       textColor=BLUE, spaceAfter=16)
HEAD = ParagraphStyle("head", fontName="Arial-Bold", fontSize=17, leading=22,
                      textColor=HexColor(0x000000), spaceBefore=12, spaceAfter=5)
BODY = ParagraphStyle("body", fontName="Arial", fontSize=15, leading=21,
                      textColor=HexColor(0x111111), spaceAfter=4)
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=20, firstLineIndent=-15)

# !C/!S black, !D/!H red, !N -> "NT" — same convention as the app's chat renderer.
SUIT = {"C": ("♣", None), "S": ("♠", None),
        "D": ("♦", RED), "H": ("♥", RED), "N": ("NT", None)}


def inline(text):
    """Escape text, then apply !suit symbols and URL links as reportlab markup."""
    out = []
    for part in re.split(r"(![CDHSN]|https?://[^\s]+)", text):
        if re.fullmatch(r"![CDHSN]", part):
            sym, col = SUIT[part[1]]
            out.append(f'<font color="{col}">{sym}</font>' if col else sym)
        elif re.match(r"https?://", part):
            u = html.escape(part)
            out.append(f'<a href="{u}" color="{LINK}"><u>{u}</u></a>')
        else:
            out.append(html.escape(part))
    return "".join(out)


def extract_chat(btn_text):
    m = re.search(r"/\*@chat\s*([\s\S]*?)@chat\*/", btn_text)
    return m.group(1).strip() if m else None


# BBO's Practice Bidding Table does not wrap text, so the @chat is hard-wrapped
# near BBO's ~65-char limit — every line ends with a return. reflow() rejoins
# those forced wraps into flowing paragraphs (reportlab then wraps to the page),
# while keeping the author's intended breaks. A break is INTENDED (kept) when the
# line ends a thought (terminal punctuation) or is a deliberate short line; a
# break is INCIDENTAL (joined) when a long prose line stops without punctuation.
# The two cases sit in non-overlapping length clusters (<=26 vs >=62 displayed
# chars across all lessons), so the split is unambiguous. The btn/ source is never
# modified. To force a break, end the line with . ! ? : , keep it under ~50
# displayed chars, or make it a bullet.
_WRAP_THRESHOLD = 50


def _displayed_len(s):
    """Length as BBO shows it: !C/!D/!H/!S render as a single suit glyph."""
    return len(re.sub(r"!([CDHSN])", "x", s))


def _is_structural(s):
    t = s.strip()
    return (not t) or t.startswith("---") or t[:2] in ("• ", "- ", "* ") \
        or bool(re.match(r"https?://", t))


def reflow(text):
    """Return logical lines: forced wraps joined, intended breaks preserved."""
    out, buf = [], ""

    def flush():
        nonlocal buf
        if buf:
            out.append(buf)
            buf = ""

    for line in text.splitlines():
        s = line.rstrip()
        if _is_structural(s):
            flush()
            out.append(s.strip())
            continue
        t = s.strip()
        buf = (buf + " " + t).strip() if buf else t
        if t[-1:] in ".!?:" or _displayed_len(t) < _WRAP_THRESHOLD:
            flush()
    flush()
    return out


def load_names():
    """Map lesson id -> display name from coaching-non-rotated/toc.json (best effort)."""
    names = {}
    try:
        toc = json.load(open(os.path.join(COACH, "toc.json")))
        for cat in toc.get("categories", []):
            for lesson in cat.get("lessons", []):
                if lesson.get("id"):
                    names[lesson["id"]] = lesson.get("name") or lesson["id"]
    except Exception:
        pass
    return names


def build(name, title, chat):
    story = [Paragraph(title.upper(), TITLE)]
    lines = chat.splitlines()
    # Drop a leading "--- X" that just restates the scenario title.
    if lines and lines[0].startswith("---"):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    for s in reflow("\n".join(lines)):
        if not s:
            story.append(Spacer(1, 8))
            continue
        heading = re.match(r"^---\s*(.+)$", s)
        if heading:
            story.append(Paragraph(inline(heading.group(1)), HEAD))
        elif s[:2] in ("• ", "- ", "* "):
            story.append(Paragraph(inline(s), BULLET))
        else:
            story.append(Paragraph(inline(s), BODY))
    SimpleDocTemplate(
        os.path.join(COACH, f"{name}_Intro.pdf"), pagesize=LETTER,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch, topMargin=0.9 * inch, bottomMargin=inch,
        title=f"{title} — Introduction", author="David Bailey Scenarios",
    ).build(story)


def main():
    names = load_names()
    made, skipped = [], []
    for pbn in sorted(os.listdir(COACH)):
        if not pbn.endswith(".pbn"):
            continue
        base = pbn[:-4]
        btn = os.path.join(BTN, f"{base}.btn")
        if not os.path.exists(btn):
            skipped.append((base, "no .btn"))
            continue
        chat = extract_chat(open(btn, encoding="utf-8", errors="replace").read())
        if not chat:
            skipped.append((base, "no @chat"))
            continue
        build(base, names.get(base) or base.replace("_", " "), chat)
        made.append(base)
    print(f"Generated {len(made)} intro PDFs into coaching-non-rotated/")
    for b in made:
        print("  +", f"{b}_Intro.pdf")
    if skipped:
        print(f"\nSkipped {len(skipped)} (no intro):")
        for b, why in skipped:
            print("  -", b, f"({why})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate a Convention Card Summary (HTML) comparing all active convention cards.

Usage:
    python3 convention_card_summary.py
"""
import os
import re
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PROJECT_ROOT

BBSA_DIR = os.path.join(PROJECT_ROOT, "bbsa")
BTN_DIR = os.path.join(PROJECT_ROOT, "btn")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "docs", "Convention_Card_Summary.html")

# Column order: GIB, DEFAULT, SPECIALS first, then alphabetical
PRIORITY_ORDER = ["21GF-GIB", "21GF-DEFAULT", "21GF-SPECIALS"]


def parse_bbsa(filepath):
    """Parse a bbsa file into {key: value} dict."""
    settings = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if " = " not in line:
                continue
            key, val = line.rsplit(" = ", 1)
            if key == "Not defined":
                continue
            settings[key] = val.strip()
    return settings


def get_canonical_keys():
    """Get canonical key order from DEFAULT."""
    default_path = os.path.join(BBSA_DIR, "21GF-DEFAULT.bbsa")
    keys = []
    with open(default_path, "r") as f:
        for line in f:
            line = line.strip()
            if " = " not in line:
                continue
            key = line.rsplit(" = ", 1)[0]
            if key in ("Not defined", "Opponent type"):
                continue
            keys.append(key)
    return keys


def count_scenarios(card_name):
    """Count how many scenarios use this card (NS and EW)."""
    ns_count = 0
    ew_count = 0
    for f in os.listdir(BTN_DIR):
        if not f.endswith(".btn") or f.startswith(".") or f.startswith("-"):
            continue
        filepath = os.path.join(BTN_DIR, f)
        with open(filepath, "r") as fh:
            for line in fh:
                if line.startswith("# convention-card-ns:") and card_name in line:
                    ns_count += 1
                elif line.startswith("# convention-card-ew:") and card_name in line:
                    ew_count += 1
    return ns_count, ew_count


def _esc(text):
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_summary():
    """Generate the Convention_Card_Summary.html file."""
    # Find all active bbsa files
    bbsa_files = sorted(
        f[:-5] for f in os.listdir(BBSA_DIR)
        if f.endswith(".bbsa") and not os.path.isdir(os.path.join(BBSA_DIR, f))
    )

    if not bbsa_files:
        print("No bbsa files found")
        return

    # Order columns: priority first, then alphabetical
    ordered = []
    for name in PRIORITY_ORDER:
        if name in bbsa_files:
            ordered.append(name)
    for name in bbsa_files:
        if name not in ordered:
            ordered.append(name)

    # Parse all cards
    cards = {}
    for name in ordered:
        filepath = os.path.join(BBSA_DIR, f"{name}.bbsa")
        cards[name] = parse_bbsa(filepath)

    # Get canonical keys
    canonical_keys = get_canonical_keys()

    # Count scenarios per card
    scenario_counts = {}
    for name in ordered:
        ns, ew = count_scenarios(name)
        scenario_counts[name] = (ns, ew)

    # Filter to only show rows where at least one card has value != "0"
    visible_keys = []
    for key in canonical_keys:
        if any(cards[name].get(key, "0") != "0" for name in ordered):
            visible_keys.append(key)

    # Short display names for column headers
    def short_name(name):
        name = name.replace("21GF-", "")
        return name

    # Build HTML
    h = []
    h.append('<!DOCTYPE html>')
    h.append('<html lang="en">')
    h.append('<head>')
    h.append('  <meta charset="UTF-8">')
    h.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h.append('  <title>Convention Card Summary</title>')
    h.append('  <style>')
    h.append('    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;')
    h.append('           font-size: 13px; max-width: 1600px; margin: 30px auto; padding: 20px;')
    h.append('           background: #f5f5f5; color: #333; }')
    h.append('    h1 { color: #222; text-align: center; font-size: 22px; margin-bottom: 5px; }')
    h.append('    .subtitle { text-align: center; color: #666; margin-bottom: 25px; }')
    h.append('    .nav-btn { display: inline-block; padding: 6px 14px; background: #0077b6; color: #fff;')
    h.append('              border-radius: 4px; text-decoration: none; font-size: 12px; margin: 0 4px; }')
    h.append('    .nav-btn:hover { background: #005f8a; }')
    h.append('    .main-table { background: #fff; border-radius: 8px; padding: 15px;')
    h.append('                  box-shadow: 0 2px 4px rgba(0,0,0,0.08); overflow-x: auto; }')
    h.append('    table { border-collapse: collapse; width: 100%; }')
    h.append('    th { background: #f0f0f0; font-weight: 600; text-align: center; padding: 6px 4px;')
    h.append('         border-bottom: 2px solid #ddd; font-size: 11px; white-space: nowrap;')
    h.append('         vertical-align: bottom; }')
    h.append('    th:first-child { text-align: left; min-width: 220px; cursor: default; }')
    h.append('    th:not(:first-child) { cursor: pointer; }')
    h.append('    td { padding: 3px 4px; border-bottom: 1px solid #eee; text-align: center;')
    h.append('         font-size: 12px; }')
    h.append('    td:first-child { text-align: left; white-space: nowrap; }')
    h.append('    tr:hover td { background: #f8f8f8; cursor: pointer; }')
    h.append('    tr.highlighted td { background: #fff3cd !important; }')
    h.append('    .col-highlighted { background: #e8f4fd !important; }')
    h.append('    tr.highlighted .col-highlighted { background: #d4e9c7 !important; }')
    h.append('    .v1 { font-weight: bold; color: #0077b6; }')
    h.append('    .v0 { color: #ccc; }')
    h.append('    .scenario-count { font-size: 10px; color: #888; font-weight: normal; }')
    h.append('    .section-row td { background: #f7f7f7; font-weight: 600; font-size: 11px;')
    h.append('                      color: #555; padding-top: 8px; border-bottom: 1px solid #ddd; }')
    h.append('    .rotate-header { writing-mode: vertical-rl; text-orientation: mixed;')
    h.append('                     transform: rotate(180deg); min-height: 100px;')
    h.append('                     display: inline-block; }')
    h.append('  </style>')
    h.append('</head>')
    h.append('<body>')
    h.append('  <h1>Convention Card Summary</h1>')
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    h.append(f'  <p class="subtitle">{len(ordered)} convention cards &mdash; Generated {ts}')
    h.append(f'    &mdash; <a class="nav-btn" href="./">Dashboard</a>')
    h.append(f'    <a class="nav-btn" href="Scenario_Summary.html">Scenario Summary</a></p>')

    # Main table
    h.append('  <div class="main-table">')
    h.append('    <table>')

    # Header row with rotated card names
    h.append('      <tr>')
    h.append('        <th>Setting</th>')
    for name in ordered:
        sn = short_name(name)
        ns, ew = scenario_counts[name]
        count_parts = []
        if ns > 0:
            count_parts.append(f"{ns} NS")
        if ew > 0:
            count_parts.append(f"{ew} EW")
        count_str = ", ".join(count_parts) if count_parts else "0"
        h.append(f'        <th><div class="rotate-header">{_esc(sn)}</div>')
        h.append(f'            <div class="scenario-count">{count_str}</div></th>')
    h.append('      </tr>')

    # Data rows
    for key in visible_keys:
        h.append('      <tr>')
        h.append(f'        <td>{_esc(key)}</td>')
        for name in ordered:
            val = cards[name].get(key, "0")
            if val == "1":
                h.append(f'        <td class="v1">1</td>')
            elif val == "0":
                h.append(f'        <td class="v0">&middot;</td>')
            else:
                h.append(f'        <td>{_esc(val)}</td>')
        h.append('      </tr>')

    h.append('    </table>')
    h.append('  </div>')
    h.append('  <script>')
    h.append('    var table = document.querySelector("table");')
    h.append('    var highlightedCol = -1;')
    h.append('    table.addEventListener("click", function(e) {')
    h.append('      var th = e.target.closest("th");')
    h.append('      if (th) {')
    h.append('        var col = Array.from(th.parentNode.children).indexOf(th);')
    h.append('        if (col > 0) {')
    h.append('          var cells = table.querySelectorAll(".col-highlighted");')
    h.append('          cells.forEach(function(c) { c.classList.remove("col-highlighted"); });')
    h.append('          if (col === highlightedCol) { highlightedCol = -1; return; }')
    h.append('          highlightedCol = col;')
    h.append('          table.querySelectorAll("tr").forEach(function(r) {')
    h.append('            if (r.children[col]) r.children[col].classList.add("col-highlighted");')
    h.append('          });')
    h.append('        }')
    h.append('        return;')
    h.append('      }')
    h.append('      var row = e.target.closest("tr");')
    h.append('      if (row && !row.querySelector("th")) {')
    h.append('        var prev = document.querySelector("tr.highlighted");')
    h.append('        if (prev && prev !== row) prev.classList.remove("highlighted");')
    h.append('        row.classList.toggle("highlighted");')
    h.append('      }')
    h.append('    });')
    h.append('  </script>')
    h.append('</body>')
    h.append('</html>')

    content = "\n".join(h)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(content)

    print(f"Summary written to {OUTPUT_FILE}")
    print(f"  {len(ordered)} cards, {len(visible_keys)} settings shown (of {len(canonical_keys)} total)")


if __name__ == "__main__":
    generate_summary()

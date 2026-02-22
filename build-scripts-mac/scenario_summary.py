#!/usr/bin/env python3
"""
Generate a Scenario Summary document (HTML) showing per-scenario
deal counts, filter counts, filter-out counts, and elapsed times.

Usage:
    python3 scenario_summary.py              # All scenarios
    python3 scenario_summary.py "1N*"        # Filter by pattern
"""
import fnmatch
import json
import os
import re
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import FOLDERS, OPERATIONS_ORDER, PROJECT_ROOT
from utils.properties import get_bba_works

TIMING_FILE = os.path.join(PROJECT_ROOT, "build-data", "pipeline-timing.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "docs", "Scenario_Summary.html")

# Columns for ET: operation names and their short display headers
OP_COLUMNS = [
    ("dlr", "dlr"),
    ("pbs", "pbs"),
    ("pbn", "pbn"),
    ("rotate", "rotate"),
    ("bba", "bba"),
    ("filter", "filter"),
    ("filterStats", "fStats"),
    ("biddingSheet", "bSheet"),
    ("quiz", "quiz"),
    ("package", "package"),
]


def count_boards(file_path: str) -> int:
    """Count [Board occurrences in a PBN file."""
    if not os.path.exists(file_path):
        return 0
    regex = re.compile(r"\[Board")
    count = 0
    with open(file_path, "r") as f:
        for line in f:
            if regex.search(line):
                count += 1
    return count


def get_scenarios(pattern: str) -> list:
    """Get scenario names from btn/ folder, optionally filtered by pattern."""
    btn_dir = FOLDERS["btn"]
    btn_files = [f[:-4] for f in os.listdir(btn_dir)
                 if f.endswith('.btn') and not f.startswith('.') and not f.startswith('-')]

    if pattern == "*":
        return sorted(btn_files)

    return sorted(f for f in btn_files if fnmatch.fnmatch(f, pattern))


def format_et(seconds: float) -> str:
    """Format elapsed time concisely."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m{secs:.0f}s"


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_summary(pattern: str = "*"):
    """Generate the Scenario_Summary.html file."""
    scenarios = get_scenarios(pattern)
    if not scenarios:
        print(f"No scenarios found matching: {pattern}")
        return

    # Load timing data
    timing = {}
    if os.path.exists(TIMING_FILE):
        with open(TIMING_FILE, "r") as f:
            timing = json.load(f)
    else:
        print(f"Note: No timing data found at {TIMING_FILE}")
        print("  Run the pipeline to generate timing data.")

    # Collect data for each scenario
    rows = []
    for scenario in scenarios:
        deals = count_boards(os.path.join(FOLDERS["pbn"], f"{scenario}.pbn"))
        filtered = count_boards(os.path.join(FOLDERS["bba_filtered"], f"{scenario}.pbn"))
        filtered_out = count_boards(os.path.join(FOLDERS["bba_filtered_out"], f"{scenario}.pbn"))

        et = timing.get(scenario, {})
        op_times = []
        total_et = 0.0
        for op_name, _ in OP_COLUMNS:
            t = et.get(op_name)
            if t is not None:
                op_times.append(format_et(t))
                total_et += t
            else:
                op_times.append("-")

        rows.append({
            "name": scenario,
            "deals": deals,
            "filtered": filtered,
            "filtered_out": filtered_out,
            "op_times": op_times,
            "total_et": format_et(total_et) if total_et > 0 else "-",
        })

    # Compute top-10 summaries
    filter_pcts = []
    for row in rows:
        if row["deals"] > 0 and get_bba_works(row["name"]):
            pct = (row["filtered"] / row["deals"]) * 100
            filter_pcts.append((row["name"], pct, row["filtered"], row["deals"]))
    filter_pcts.sort(key=lambda x: x[1])
    lowest_filter = filter_pcts[:10]

    deal_rows = [(row["name"], row["deals"]) for row in rows if 0 < row["deals"] < 500]
    deal_rows.sort(key=lambda x: x[1])
    lowest_deals = deal_rows[:10]

    pipeline_ops = {op for op, _ in OP_COLUMNS}
    et_rows = []
    for row in rows:
        et = timing.get(row["name"], {})
        total = sum(v for k, v in et.items() if k in pipeline_ops)
        if total > 0:
            et_rows.append((row["name"], total))
    et_rows.sort(key=lambda x: -x[1])
    longest_et = et_rows[:10]

    # Build HTML
    h = []
    h.append('<!DOCTYPE html>')
    h.append('<html lang="en">')
    h.append('<head>')
    h.append('  <meta charset="UTF-8">')
    h.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h.append('  <title>Scenario Summary</title>')
    h.append('  <style>')
    h.append('    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;')
    h.append('           font-size: 13px; max-width: 1400px; margin: 30px auto; padding: 20px;')
    h.append('           background: #f5f5f5; color: #333; }')
    h.append('    h1 { color: #222; text-align: center; font-size: 22px; margin-bottom: 5px; }')
    h.append('    .subtitle { text-align: center; color: #666; margin-bottom: 25px; }')
    h.append('    .nav-btn { display: inline-block; padding: 6px 14px; background: #0077b6; color: #fff;')
    h.append('              border-radius: 4px; text-decoration: none; font-size: 12px; margin: 0 4px; }')
    h.append('    .nav-btn:hover { background: #005f8a; }')
    h.append('    .summaries { display: flex; gap: 20px; margin-bottom: 25px; }')
    h.append('    .summary-card { background: #fff; border-radius: 8px; padding: 15px 20px;')
    h.append('                    box-shadow: 0 2px 4px rgba(0,0,0,0.08); flex: 1; }')
    h.append('    .summary-card h3 { margin: 0 0 10px 0; font-size: 14px; color: #333; }')
    h.append('    table { border-collapse: collapse; width: 100%; }')
    h.append('    .main-table { background: #fff; border-radius: 8px; padding: 15px;')
    h.append('                  box-shadow: 0 2px 4px rgba(0,0,0,0.08); overflow-x: auto; }')
    h.append('    th { background: #f0f0f0; font-weight: 600; text-align: right; padding: 6px 8px;')
    h.append('         border-bottom: 2px solid #ddd; font-size: 12px; white-space: nowrap; }')
    h.append('    th:first-child { text-align: left; }')
    h.append('    td { padding: 4px 8px; border-bottom: 1px solid #eee; text-align: right;')
    h.append('         font-size: 12px; white-space: nowrap; }')
    h.append('    td:first-child { text-align: left; }')
    h.append('    tr:hover td { background: #f8f8f8; }')
    h.append('    .totals td { font-weight: bold; border-top: 2px solid #ddd; }')
    h.append('    .summary-card td, .summary-card th { font-size: 12px; }')
    h.append('    .summary-card th { background: transparent; border-bottom: 1px solid #ddd; }')
    h.append('  </style>')
    h.append('</head>')
    h.append('<body>')
    h.append('  <h1>Scenario Summary</h1>')
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    h.append(f'  <p class="subtitle">{len(rows)} scenarios &mdash; Generated {ts}')
    h.append(f'    &mdash; <a class="nav-btn" href="./">Dashboard</a>')
    h.append(f'    <a class="nav-btn" href="Convention_Card_Summary.html">Convention Cards</a></p>')

    # Side-by-side summaries
    h.append('  <div class="summaries">')

    # Lowest Filter Rate
    h.append('    <div class="summary-card">')
    h.append('      <h3>Lowest Filter Rate</h3>')
    h.append('      <table>')
    h.append('        <tr><th>#</th><th style="text-align:left">Scenario</th><th>Filt</th><th>Deals</th><th>Rate</th></tr>')
    for i, (name, pct, filt, deals) in enumerate(lowest_filter, 1):
        h.append(f'        <tr><td>{i}</td><td style="text-align:left">{_esc(name)}</td><td>{filt}</td><td>{deals}</td><td>{pct:.1f}%</td></tr>')
    h.append('      </table>')
    h.append('    </div>')

    # Lowest Deal Counts
    h.append('    <div class="summary-card">')
    h.append('      <h3>Lowest Deal Counts</h3>')
    h.append('      <table>')
    h.append('        <tr><th>#</th><th style="text-align:left">Scenario</th><th>Deals</th></tr>')
    for i, (name, deals) in enumerate(lowest_deals, 1):
        h.append(f'        <tr><td>{i}</td><td style="text-align:left">{_esc(name)}</td><td>{deals}</td></tr>')
    h.append('      </table>')
    h.append('    </div>')

    # Longest Total ET
    h.append('    <div class="summary-card">')
    h.append('      <h3>Longest Total ET</h3>')
    h.append('      <table>')
    if longest_et:
        h.append('        <tr><th>#</th><th style="text-align:left">Scenario</th><th>Total ET</th></tr>')
        for i, (name, total) in enumerate(longest_et, 1):
            h.append(f'        <tr><td>{i}</td><td style="text-align:left">{_esc(name)}</td><td>{format_et(total)}</td></tr>')
    else:
        h.append('        <tr><td><em>No timing data available.</em></td></tr>')
    h.append('      </table>')
    h.append('    </div>')

    h.append('  </div>')

    # Main table
    op_headers = [hdr for _, hdr in OP_COLUMNS]
    h.append('  <div class="main-table">')
    h.append('    <table>')
    h.append('      <tr>')
    h.append('        <th>Scenario</th><th>Deals</th><th>Filtered</th><th>Flt-Out</th>')
    for hdr in op_headers:
        h.append(f'        <th>{_esc(hdr)}</th>')
    h.append('        <th>Total</th>')
    h.append('      </tr>')

    total_deals = 0
    total_filtered = 0
    total_filtered_out = 0

    for row in rows:
        deals_str = str(row["deals"]) if row["deals"] > 0 else "-"
        filt_str = str(row["filtered"]) if row["filtered"] > 0 else "-"
        fout_str = str(row["filtered_out"]) if row["filtered_out"] > 0 else "-"

        total_deals += row["deals"]
        total_filtered += row["filtered"]
        total_filtered_out += row["filtered_out"]

        h.append('      <tr>')
        h.append(f'        <td>{_esc(row["name"])}</td><td>{deals_str}</td><td>{filt_str}</td><td>{fout_str}</td>')
        for t in row["op_times"]:
            h.append(f'        <td>{t}</td>')
        h.append(f'        <td>{row["total_et"]}</td>')
        h.append('      </tr>')

    # Totals row
    h.append('      <tr class="totals">')
    h.append(f'        <td>Total</td><td>{total_deals}</td><td>{total_filtered}</td><td>{total_filtered_out}</td>')
    for _ in op_headers:
        h.append('        <td>-</td>')
    h.append('        <td>-</td>')
    h.append('      </tr>')

    h.append('    </table>')
    h.append('  </div>')
    h.append('</body>')
    h.append('</html>')

    content = "\n".join(h)
    with open(OUTPUT_FILE, "w") as f:
        f.write(content)

    print(f"Summary written to {OUTPUT_FILE}")
    print(f"  {len(rows)} scenarios, {total_deals} total deals")


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*"
    generate_summary(pattern)

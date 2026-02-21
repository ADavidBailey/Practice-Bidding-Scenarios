#!/usr/bin/env python3
"""
Generate a Scenario Summary document (Markdown) showing per-scenario
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
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "Documents", "Scenario_Summary.md")

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


def generate_summary(pattern: str = "*"):
    """Generate the Scenario_Summary.md file."""
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
    # Lowest filtered/deals percent (only scenarios with deals > 0 and bba-works=true)
    filter_pcts = []
    for row in rows:
        if row["deals"] > 0 and get_bba_works(row["name"]):
            pct = (row["filtered"] / row["deals"]) * 100
            filter_pcts.append((row["name"], pct, row["filtered"], row["deals"]))
    filter_pcts.sort(key=lambda x: x[1])
    lowest_filter = filter_pcts[:10]

    # Lowest deal counts (only scenarios with deals > 0)
    deal_rows = [(row["name"], row["deals"]) for row in rows if 0 < row["deals"] < 500]
    deal_rows.sort(key=lambda x: x[1])
    lowest_deals = deal_rows[:10]

    # Longest total ET (only pipeline operations, not release etc.)
    pipeline_ops = {op for op, _ in OP_COLUMNS}
    et_rows = []
    for row in rows:
        et = timing.get(row["name"], {})
        total = sum(v for k, v in et.items() if k in pipeline_ops)
        if total > 0:
            et_rows.append((row["name"], total))
    et_rows.sort(key=lambda x: -x[1])
    longest_et = et_rows[:10]

    # Build markdown
    lines = []
    lines.append("# Scenario Summary")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Scenarios: {len(rows)}")
    lines.append("")

    # Top-10 lowest filter rate
    lines.append("## Lowest Filter Rate (Filtered / Deals)")
    lines.append("")
    lines.append("| # | Scenario | Filtered | Deals | Rate |")
    lines.append("| ---: | :--- | ---: | ---: | ---: |")
    for i, (name, pct, filt, deals) in enumerate(lowest_filter, 1):
        lines.append(f"| {i} | {name} | {filt} | {deals} | {pct:.1f}% |")
    lines.append("")

    # Top-10 lowest deal counts
    lines.append("## Lowest Deal Counts")
    lines.append("")
    lines.append("| # | Scenario | Deals |")
    lines.append("| ---: | :--- | ---: |")
    for i, (name, deals) in enumerate(lowest_deals, 1):
        lines.append(f"| {i} | {name} | {deals} |")
    lines.append("")

    # Top-10 longest ET
    lines.append("## Longest Total ET")
    lines.append("")
    if longest_et:
        lines.append("| # | Scenario | Total ET |")
        lines.append("| ---: | :--- | ---: |")
        for i, (name, total) in enumerate(longest_et, 1):
            lines.append(f"| {i} | {name} | {format_et(total)} |")
    else:
        lines.append("*No timing data available. Run the pipeline to generate.*")
    lines.append("")

    # Main table header
    op_headers = [h for _, h in OP_COLUMNS]
    header = "| Scenario | Deals | Filtered | Flt-Out | " + " | ".join(op_headers) + " | Total |"
    separator = "|" + "|".join(["-" * (len(c) + 2) for c in
        ["Scenario", "Deals", "Filtered", "Flt-Out"] + op_headers + ["Total"]]) + "|"

    # Right-align numeric columns
    align = "| :--- | ---: | ---: | ---: |" + " ---: |" * len(op_headers) + " ---: |"

    lines.append(header)
    lines.append(align)

    # Data rows
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

        cols = [row["name"], deals_str, filt_str, fout_str] + row["op_times"] + [row["total_et"]]
        lines.append("| " + " | ".join(cols) + " |")

    # Totals row
    lines.append("| " + " | ".join([
        "**Total**",
        f"**{total_deals}**",
        f"**{total_filtered}**",
        f"**{total_filtered_out}**",
    ] + ["-"] * len(op_headers) + ["-"]) + " |")

    lines.append("")

    # Write output
    content = "\n".join(lines)
    with open(OUTPUT_FILE, "w") as f:
        f.write(content)

    print(f"Summary written to {OUTPUT_FILE}")
    print(f"  {len(rows)} scenarios, {total_deals} total deals")


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*"
    generate_summary(pattern)

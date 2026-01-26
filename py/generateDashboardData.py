#!/usr/bin/env python3
"""
Generate dashboard data from activity logs and git history.
Embeds data directly into dashboard.html for file:// protocol compatibility.
"""
import json
import os
import subprocess
import re
from datetime import datetime, timedelta
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_activity_log():
    """Load and parse activity-log.json"""
    log_path = os.path.join(PROJECT_ROOT, 'activity-log.json')
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            return json.load(f)
    return {"version": 1, "events": []}


def get_git_commits(days=365):
    """Get git commits from the past N days"""
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    try:
        result = subprocess.run(
            ['git', 'log', f'--since={since_date}', '--format=%H|%ai|%s'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 2)
                if len(parts) == 3:
                    commits.append({
                        'hash': parts[0][:8],
                        'date': parts[1],
                        'message': parts[2]
                    })
        return commits
    except Exception as e:
        print(f"Error getting git commits: {e}")
        return []


def get_scenario_count():
    """Count the number of PBS scenario files"""
    pbs_dir = os.path.join(PROJECT_ROOT, 'PBS')
    if os.path.exists(pbs_dir):
        # Count files without extensions (PBS format)
        count = 0
        for f in os.listdir(pbs_dir):
            file_path = os.path.join(pbs_dir, f)
            if os.path.isfile(file_path) and not f.startswith('.'):
                count += 1
        return count
    return 0


def aggregate_events_by_month(events, type_filter=None):
    """Aggregate events by month (YYYY-MM format)"""
    monthly = defaultdict(int)
    for event in events:
        if type_filter and event.get('type') != type_filter:
            continue
        ts = event.get('timestamp', '')
        if ts:
            month = ts[:7]  # "2026-01"
            monthly[month] += 1
    return dict(sorted(monthly.items()))


def aggregate_commits_by_month(commits):
    """Aggregate commits by month"""
    monthly = defaultdict(int)
    for commit in commits:
        date_str = commit.get('date', '')
        if date_str:
            # Format: "2026-01-26 14:30:00 -0500"
            month = date_str[:7]
            monthly[month] += 1
    return dict(sorted(monthly.items()))


def calculate_session_stats(events):
    """Calculate total session time in minutes"""
    total_minutes = 0
    for event in events:
        if event.get('type') == 'session_end':
            duration = event.get('details', {}).get('durationMinutes', 0)
            if duration:
                total_minutes += duration
    return total_minutes


def get_last_12_months():
    """Get list of last 12 month labels"""
    months = []
    now = datetime.now()
    for i in range(12, -1, -1):
        date = now - timedelta(days=i * 30)
        months.append(date.strftime('%Y-%m'))
    return months


def format_month_labels(months):
    """Format month keys to readable labels"""
    labels = []
    for m in months:
        try:
            date = datetime.strptime(m, '%Y-%m')
            labels.append(date.strftime('%b %y'))
        except:
            labels.append(m)
    return labels


def generate_dashboard_data():
    """Generate all dashboard data"""
    log = load_activity_log()
    events = log.get('events', [])
    commits = get_git_commits()

    # Get last 12 months for consistent chart labels
    months = get_last_12_months()

    # Aggregate data
    file_saves_by_month = aggregate_events_by_month(events, 'file_save')
    pipeline_runs_by_month = aggregate_events_by_month(events, 'pipeline_run')
    commits_by_month = aggregate_commits_by_month(commits)

    # Fill in zeros for months with no data
    for m in months:
        file_saves_by_month.setdefault(m, 0)
        pipeline_runs_by_month.setdefault(m, 0)
        commits_by_month.setdefault(m, 0)

    # Sort and extract values for charts
    sorted_months = sorted(months)
    labels = format_month_labels(sorted_months)

    return {
        "generatedAt": datetime.now().isoformat(),
        "summary": {
            "totalScenarios": get_scenario_count(),
            "totalFileSaves": len([e for e in events if e.get('type') == 'file_save']),
            "totalPipelineRuns": len([e for e in events if e.get('type') == 'pipeline_run']),
            "totalSessionMinutes": calculate_session_stats(events),
            "totalCommits": len(commits)
        },
        "charts": {
            "labels": labels,
            "fileSaves": [file_saves_by_month.get(m, 0) for m in sorted_months],
            "pipelineRuns": [pipeline_runs_by_month.get(m, 0) for m in sorted_months],
            "commits": [commits_by_month.get(m, 0) for m in sorted_months]
        },
        "recentActivity": events[-20:] if events else [],
        "recentCommits": commits[:10] if commits else []
    }


def embed_data_in_html(dashboard_data):
    """Update dashboard.html with embedded data"""
    html_path = os.path.join(PROJECT_ROOT, 'dashboard.html')

    with open(html_path, 'r') as f:
        html = f.read()

    # Create the data script
    data_json = json.dumps(dashboard_data, indent=2)
    data_script = f'const DASHBOARD_DATA = {data_json};'

    # Check if DASHBOARD_DATA already exists and replace it
    pattern = r'const DASHBOARD_DATA = \{[\s\S]*?\};'
    if re.search(pattern, html):
        html = re.sub(pattern, data_script, html)
    else:
        # Insert before closing </head> tag
        html = html.replace('</head>', f'    <script>\n{data_script}\n    </script>\n</head>')

    with open(html_path, 'w') as f:
        f.write(html)

    print(f"Dashboard data embedded in {html_path}")


def main():
    print("Generating dashboard data...")

    dashboard_data = generate_dashboard_data()

    # Save JSON file (for debugging/inspection)
    json_path = os.path.join(PROJECT_ROOT, 'dashboard-data.json')
    with open(json_path, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    print(f"Dashboard data saved to {json_path}")

    # Embed data in HTML
    embed_data_in_html(dashboard_data)

    # Print summary
    summary = dashboard_data['summary']
    print(f"\nSummary:")
    print(f"  Scenarios: {summary['totalScenarios']}")
    print(f"  File saves logged: {summary['totalFileSaves']}")
    print(f"  Pipeline runs logged: {summary['totalPipelineRuns']}")
    print(f"  Session time: {summary['totalSessionMinutes']} minutes")
    print(f"  Git commits (past year): {summary['totalCommits']}")


if __name__ == '__main__':
    main()

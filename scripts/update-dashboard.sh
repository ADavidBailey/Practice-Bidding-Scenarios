#!/bin/bash
# Update dashboard and push to GitHub Pages
# Run by launchd at 3:00 AM daily

cd /Users/adavidbailey/Practice-Bidding-Scenarios

echo "$(date): Starting dashboard update"

# Generate dashboard data
/usr/bin/python3 py/generateDashboardData.py

# Check if there are changes to commit
if git diff --quiet dashboard.html dashboard-data.json; then
    echo "$(date): No changes to commit"
else
    echo "$(date): Committing and pushing changes"
    git add dashboard.html dashboard-data.json
    git commit -m "Daily dashboard update"
    git push
    echo "$(date): Push complete"
fi

echo "$(date): Dashboard update finished"

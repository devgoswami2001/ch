#!/bin/bash

cd /home/ubuntu/ch || exit 1

# Get latest changes from GitHub
git pull origin main

# Stage everything
git add -A

# Commit only if something changed
if ! git diff --cached --quiet; then
    git commit -m "Auto Backup $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
else
    echo "$(date): No changes."
fi

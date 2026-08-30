#!/usr/bin/env bash
# Example agent-friendly script to open local repositories in code editor
REPO_DIR="${1:-$HOME/workspace}"

if [ ! -d "$REPO_DIR" ]; then
    echo "Directory $REPO_DIR does not exist."
    exit 1
fi

echo "Scanning git repositories in $REPO_DIR..."
find "$REPO_DIR" -maxdepth 3 -name ".git" -type d | while read -r gitdir; do
    repo=$(dirname "$gitdir")
    echo "Found repository: $repo"
done

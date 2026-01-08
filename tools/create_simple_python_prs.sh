#!/bin/bash

# Simple test script to create a few Python PRs
REPO_NAME="Pathik-Nandi/codereview-hackathon"
BASE_BRANCH="master"

export GITHUB_TOKEN=${GITHUB_TOKEN}

echo "Creating 3 test Python PRs..."

# Create PR 1: SQL Injection
BRANCH_NAME="python-test-pr-1"
git checkout -b $BRANCH_NAME $BASE_BRANCH
echo 'import sqlite3

class AuthService:
    def authenticate(self, username, password):
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        # SQL Injection vulnerability
        query = f"SELECT * FROM users WHERE username = '\'''{username}'\'' AND password = '\'''{password}'\''"
        cursor.execute(query)
        return cursor.fetchone() is not None' > src/python/app/vulnerable_auth.py

git add . && git commit -m "Add vulnerable authentication - SQL injection risk"
git push -u origin $BRANCH_NAME
gh pr create --title "Add Authentication System" --body "Implements user authentication with database lookup" --base $BASE_BRANCH --head $BRANCH_NAME

# Create PR 2: Hardcoded Secrets
BRANCH_NAME="python-test-pr-2" 
git checkout -b $BRANCH_NAME $BASE_BRANCH
echo 'class Config:
    # Hardcoded secrets - security issue
    DATABASE_URL = "postgresql://admin:SuperSecret123@localhost:5432/myapp"
    API_KEY = "fake_api_key_12345"
    STRIPE_SECRET = "fake_stripe_key_67890"' > src/python/app/bad_config.py

git add . && git commit -m "Add configuration with hardcoded secrets"
git push -u origin $BRANCH_NAME
gh pr create --title "Add Application Configuration" --body "Sets up database and API configuration" --base $BASE_BRANCH --head $BRANCH_NAME

# Create PR 3: Resource Leaks
BRANCH_NAME="python-test-pr-3"
git checkout -b $BRANCH_NAME $BASE_BRANCH  
echo 'import json

class FileProcessor:
    def process_file(self, file_path):
        # Resource leak - file not closed
        file = open(file_path, "r")
        data = json.load(file)
        # File handle not closed properly
        return len(data) if data else 0' > src/python/app/leaky_processor.py

git add . && git commit -m "Add file processing with resource leaks"
git push -u origin $BRANCH_NAME  
gh pr create --title "Add File Processing" --body "Implements file upload and processing" --base $BASE_BRANCH --head $BRANCH_NAME

git checkout $BASE_BRANCH
echo "✅ Created 3 test Python PRs successfully!"
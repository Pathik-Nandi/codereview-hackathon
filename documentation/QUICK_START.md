# Quick Start Guide

Get the Multi-Agent PR Review System up and running in minutes!

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.8+** installed
- ✅ **PostgreSQL 12+** running
- ✅ **Git** installed
- ✅ **GitHub Personal Access Token** with `repo` and `read:org` scopes

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd codereview
```

## Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip3 install -r requirements.txt
```

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example or create new
cp .env.example .env  # if available
# OR
nano .env
```

Add the following configuration:

```properties
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPOSITORY=owner/repo

# Database Configuration
DB_HOST=localhost
DB_PORT=5433
DB_NAME=pr_analysis
DB_USER=postgres
DB_PASSWORD=your_password_here

# Optional: Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-token
SLACK_CHANNEL_ID=your-channel-id

# Flask Configuration
FLASK_PORT=5000
```

### Get Your GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`
4. Copy the generated token
5. Paste it in your `.env` file

## Step 4: Set Up the Database

Run the automated database setup script:

```bash
# Make the script executable
chmod +x setup_database.sh

# Run the setup
./setup_database.sh
```

This will:
- ✅ Verify prerequisites
- ✅ Test database connection
- ✅ Create database if needed
- ✅ Create all required tables
- ✅ Verify table creation

**Alternative (Manual):**
```bash
python3 create_tables.py
```

## Step 5: Start the Application

```bash
python3 main.py
```

You should see output like:

```
2025-12-21T10:30:00.123456Z [info] Static Analysis Agent enabled
2025-12-21T10:30:00.123567Z [info] Security Agent enabled
2025-12-21T10:30:00.123678Z [info] Code Quality Agent enabled
2025-12-21T10:30:00.123789Z [info] Context Agent enabled
2025-12-21T10:30:00.123890Z [info] Coverage & Metrics Agent enabled
2025-12-21T10:30:00.234567Z [info] Starting PR Review System on port 5000
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.13:5000
```

🎉 **The application is now running!**

## Step 6: Test the API

### 1. Health Check

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "multi-agent-pr-review",
  "version": "1.0.0"
}
```

### 2. Analyze a PR

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "owner/repo",
    "pr_number": 123
  }'
```

Replace `owner/repo` with your GitHub repository and `123` with an actual PR number.

### 3. Get User Analytics

```bash
curl -X POST http://localhost:5000/api/analytics/user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "start_date": "2024-01-01"
  }'
```

## Common Usage Scenarios

### Scenario 1: Analyze a Single PR

```bash
# Analyze PR #42 from myorg/myrepo
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "myorg/myrepo",
    "pr_number": 42
  }' | jq .
```

### Scenario 2: Get Developer Insights

```bash
# Get insights for developer john-doe
curl http://localhost:5000/api/dashboard/user/john-doe/insights | jq .
```

### Scenario 3: List All PRs for a User

```bash
# List PRs by email
curl -X POST http://localhost:5000/api/prs/list \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "limit": 50
  }' | jq .
```

### Scenario 4: Check Auto-Merge Eligibility

```bash
# Evaluate if PR can be auto-merged
curl -X POST http://localhost:5000/api/auto-merge/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "myorg/myrepo",
    "pr_number": 42
  }' | jq .
```

## Configuration Options

### Agent Configuration

Edit `config/settings.yaml` to customize agent behavior:

```yaml
dispatcher:
  strategy: "file_based"  # round_robin, security_first, fixed
  preferred_agent: "static_analysis"

agents:
  static_analysis:
    enabled: true
    severity_threshold: "medium"
    languages:
      python:
        enabled: true
        tools: [pylint, flake8]
      
  security:
    enabled: true
    fail_on_high: true
    
  code_quality:
    enabled: true
    max_complexity: 15
```

### Database Configuration

Configure database in `.env`:

```properties
# PostgreSQL Connection
DB_HOST=localhost
DB_PORT=5433
DB_NAME=pr_analysis
DB_USER=postgres
DB_PASSWORD=secure_password

# Connection Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## Troubleshooting

### Issue: "Database connection failed"

**Solution:**
1. Check if PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   # OR
   pg_isready -h localhost -p 5433
   ```

2. Verify credentials in `.env` file

3. Test connection manually:
   ```bash
   psql -h localhost -p 5433 -U postgres -d pr_analysis
   ```

### Issue: "GitHub API rate limit exceeded"

**Solution:**
1. Check your GitHub token is correctly set in `.env`
2. Verify token has required scopes
3. Wait for rate limit to reset (check headers in response)

### Issue: "Module not found" errors

**Solution:**
```bash
# Reinstall dependencies
pip3 install -r requirements.txt

# Verify installation
pip3 list | grep -E "(flask|PyGithub|sqlalchemy)"
```

### Issue: Port 5000 already in use

**Solution:**
Change the port in `.env`:
```properties
FLASK_PORT=8080
```

Then restart the application.

## Next Steps

Now that your system is running:

1. **📖 Read the API docs**: [API Reference](API_REFERENCE.md)
2. **🏗️ Understand the architecture**: [Architecture](ARCHITECTURE.md)
3. **⚙️ Configure for your needs**: [Configuration Guide](CONFIGURATION.md)
4. **🔧 Set up webhooks**: Configure GitHub webhooks for automatic PR analysis
5. **📊 Explore analytics**: Use analytics endpoints to track team performance

## Production Deployment

For production deployment:

1. **Use a production WSGI server**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 main:app
   ```

2. **Set up reverse proxy** (Nginx/Apache)

3. **Enable HTTPS** with SSL certificates

4. **Configure environment variables** securely

5. **Set up monitoring** and logging

6. **Enable database backups**

7. **Configure rate limiting**

See [Installation Guide](INSTALLATION.md) for detailed production setup.

## Getting Help

- **Documentation**: Check the [documentation folder](.)
- **Troubleshooting**: [Troubleshooting Guide](TROUBLESHOOTING.md)
- **FAQ**: [Frequently Asked Questions](FAQ.md)
- **Architecture**: [System Architecture](ARCHITECTURE.md)

## Quick Reference

### Important Files

- `main.py` - Main application entry point
- `.env` - Environment configuration
- `config/settings.yaml` - Agent configuration
- `requirements.txt` - Python dependencies
- `setup_database.sh` - Database setup script

### Key Directories

- `agents/` - All analysis agents
- `models/` - Database models and data structures
- `services/` - External service integrations
- `utils/` - Utility functions and helpers
- `documentation/` - Complete documentation

### Useful Commands

```bash
# Start application
python3 main.py

# Run in background
nohup python3 main.py > app.log 2>&1 &

# Check application status
curl http://localhost:5000/health

# View logs (if running in background)
tail -f app.log

# Stop application (if running in background)
pkill -f "python3 main.py"
```

---

**You're all set!** 🚀

Start analyzing PRs and improving code quality across your team!

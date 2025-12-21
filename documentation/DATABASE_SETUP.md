# Database Setup Guide

This guide explains how to set up the PostgreSQL database for the PR Analysis System using the automated setup script.

## Prerequisites

Before running the setup script, ensure you have:

1. **PostgreSQL Server** installed and running
   - Default port: 5432 (or 5433 as configured in your .env)
   
2. **Python 3.8+** installed
   ```bash
   python3 --version
   ```

3. **Required Python packages** installed
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Environment variables** configured in `.env` file

## Quick Start

To set up all database tables, simply run:

```bash
./setup_database.sh
```

That's it! The script will:
- ✅ Verify all prerequisites
- ✅ Test database connection
- ✅ Create database if it doesn't exist
- ✅ Create all required tables
- ✅ Verify table creation
- ✅ Display table information

## Database Tables Created

The script creates the following tables:

### 1. **pr_analysis** (Main Table)
Stores complete PR analysis results including:
- PR identification (repository, pr_number, pr_id)
- Author information (login, email, name)
- PR metadata (branches, files changed, lines added/deleted)
- Analysis results (issues by severity, agent breakdown)
- Quality scores (overall, security, maintainability)
- Coverage metrics (estimated coverage, test ratio, complexity)

### 2. **pr_issues** (Issues Table)
Stores individual issues found during analysis:
- Issue classification (agent, type, severity, category)
- Issue location (file path, line number)
- Issue details (title, description, recommendation)
- Code snippets and metadata

### 3. **pr_metrics** (Metrics Table)
Stores detailed code metrics for each PR:
- Coverage metrics (code/test files, test methods, coverage %)
- Complexity metrics (average, max, high complexity methods)
- Quality metrics (duplicates, long methods, magic numbers)
- Security metrics (hardcoded secrets, injection risks)
- Pattern counts (TODOs, console logs, eval usage)

### 4. **user_statistics** (User Stats Table)
Aggregated statistics per user:
- PR counts and issue distribution
- Average scores (quality, security, maintainability, coverage)
- Trend indicators (improving, declining, stable)
- Common issues and improvement areas
- Best/worst PR references

### 5. **best_practices** (Best Practices Table)
Stores best practice recommendations:
- Practice information (category, issue type, priority)
- Content (title, description, recommendation)
- Examples (bad vs good practices)
- Applicability (languages, tags)

### 6. **user_analytics** (Analytics Snapshots Table)
Time-series analytics data per user:
- Analysis period information
- Quality metrics over time
- Issue statistics and trends
- Code metrics and averages
- Best/bad practices identified
- Personalized recommendations

## Configuration

The script reads database configuration from the `.env` file:

```properties
# Database Configuration
DB_HOST=localhost
DB_PORT=5433
DB_NAME=pr_analysis
DB_USER=postgres
DB_PASSWORD=postgres
```

Make sure these values match your PostgreSQL setup.

## Manual Setup (Alternative)

If you prefer to set up tables manually, you can use Python:

```bash
python3 create_tables.py
```

Or use the database service in your application:

```python
from services.database_service import DatabaseService

db_service = DatabaseService()
db_service.create_tables()
```

## Troubleshooting

### Connection Failed

If you get a connection error:

1. **Check if PostgreSQL is running:**
   ```bash
   sudo systemctl status postgresql
   # or
   pg_isready -h localhost -p 5433
   ```

2. **Verify database credentials** in `.env` file

3. **Check if database exists:**
   ```bash
   psql -h localhost -p 5433 -U postgres -l
   ```

### Permission Denied

If you get permission errors:

1. **Make sure the script is executable:**
   ```bash
   chmod +x setup_database.sh
   ```

2. **Check PostgreSQL user permissions:**
   ```sql
   -- Connect to PostgreSQL
   psql -h localhost -p 5433 -U postgres
   
   -- Check user permissions
   \du
   
   -- Grant permissions if needed
   ALTER USER postgres CREATEDB;
   ```

### Tables Already Exist

If tables already exist, the script will skip creation. To recreate tables:

```sql
-- Connect to database
psql -h localhost -p 5433 -U postgres -d pr_analysis

-- Drop all tables (CAUTION: This deletes all data!)
DROP TABLE IF EXISTS user_analytics CASCADE;
DROP TABLE IF EXISTS best_practices CASCADE;
DROP TABLE IF EXISTS user_statistics CASCADE;
DROP TABLE IF EXISTS pr_metrics CASCADE;
DROP TABLE IF EXISTS pr_issues CASCADE;
DROP TABLE IF EXISTS pr_analysis CASCADE;

-- Then run the setup script again
```

### Missing Python Packages

If you get import errors:

```bash
# Install all required packages
pip3 install -r requirements.txt

# Or install specific packages
pip3 install sqlalchemy psycopg2-binary
```

## Verifying Setup

After setup, verify tables were created:

```bash
# Connect to database
psql -h localhost -p 5433 -U postgres -d pr_analysis

# List all tables
\dt

# Show table structure
\d pr_analysis
\d pr_issues
\d pr_metrics
\d user_statistics
\d best_practices
\d user_analytics

# Count rows (should be 0 for new setup)
SELECT COUNT(*) FROM pr_analysis;
```

## Index Information

The tables include optimized indexes for common queries:

- **pr_analysis**: Composite indexes on repository+pr_number, author+date, email+repo
- **pr_issues**: Indexes on pr_analysis_id, agent_name, issue_type, severity
- **user_statistics**: Index on author_login (unique), author_email, last_pr_date
- **user_analytics**: Composite indexes on author+date, email+date

These indexes ensure fast queries for:
- Finding PRs by repository and PR number
- Searching by author email
- Analytics queries by date range
- Issue filtering by severity and type

## Next Steps

After database setup:

1. **Run the application:**
   ```bash
   python3 main.py
   ```

2. **Test the API endpoints:**
   ```bash
   # Analyze a PR
   curl -X POST http://localhost:5000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"repository": "owner/repo", "pr_number": 123}'
   
   # Get user analytics
   curl -X POST http://localhost:5000/api/analytics/user \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
   ```

3. **Verify data persistence** by checking the database after analyzing PRs

## Database Maintenance

### Backup Database

```bash
# Backup entire database
pg_dump -h localhost -p 5433 -U postgres pr_analysis > backup.sql

# Backup specific tables
pg_dump -h localhost -p 5433 -U postgres pr_analysis \
  -t pr_analysis -t pr_issues > backup_prs.sql
```

### Restore Database

```bash
# Restore from backup
psql -h localhost -p 5433 -U postgres pr_analysis < backup.sql
```

### Clear All Data (Keep Tables)

```sql
-- Connect to database
psql -h localhost -p 5433 -U postgres -d pr_analysis

-- Truncate all tables (removes data, keeps structure)
TRUNCATE TABLE user_analytics CASCADE;
TRUNCATE TABLE best_practices CASCADE;
TRUNCATE TABLE user_statistics CASCADE;
TRUNCATE TABLE pr_metrics CASCADE;
TRUNCATE TABLE pr_issues CASCADE;
TRUNCATE TABLE pr_analysis CASCADE;
```

## Support

For issues or questions:
1. Check the main application logs
2. Verify PostgreSQL logs
3. Review the `.env` configuration
4. Ensure all prerequisites are met

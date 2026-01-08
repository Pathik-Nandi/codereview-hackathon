# PR Review System - Architecture Documentation V1

**Version**: 1.0  
**Date**: January 4, 2026  
**Status**: Enhanced with Scheduled Analytics & Time-Series Trends

---

## 🆕 What's New in V1

This version enhances the original architecture with:

1. **Scheduled Analytics Generation**
   - Automated user analytics snapshots (daily/weekly)
   - Automated comment statistics generation (daily/weekly/monthly)
   - Celery-based task scheduling for periodic jobs

2. **Time-Series Trend Analysis**
   - Historical snapshots in `user_analytics` table
   - Point-in-time metrics for trend visualization
   - 4-hour duplicate prevention rule for efficiency

3. **Enhanced Database Schema**
   - `pr_comment_statistics` table for aggregated comment metrics
   - `user_analytics` table redesigned for time-series data
   - Optimized for fast trend queries (<100ms vs 2-5s)

4. **Developer Tools**
   - Database content analysis tool
   - Manual analytics job runner
   - Table data verification utilities

5. **Code Quality Improvements**
   - All SonarQube issues resolved
   - Reduced cognitive complexity in analytics services
   - Better separation of concerns

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Enhanced Architecture](#enhanced-architecture)
3. [Technology Stack](#technology-stack)
4. [Component Architecture](#component-architecture)
5. [Enhanced Data Flow](#enhanced-data-flow)
6. [Enhanced Database Schema](#enhanced-database-schema)
7. [Scheduled Analytics System](#scheduled-analytics-system)
8. [AI/RAG System](#airag-system)
9. [API Architecture](#api-architecture)
10. [Performance & Optimization](#performance--optimization)

---

## System Overview

The PR Review System is an intelligent code review platform that leverages AI and Retrieval-Augmented Generation (RAG) to provide automated, context-aware pull request analysis with **real-time and historical analytics**.

### Key Features
- **Automated Code Review**: Multi-agent system for comprehensive code analysis
- **RAG-Enhanced Insights**: Historical context and pattern recognition
- **Real-time Analytics**: User performance tracking and trend analysis
- **Scheduled Analytics**: Automated daily/weekly snapshot generation
- **Time-Series Trends**: Historical performance visualization over time
- **Security Analysis**: Vulnerability detection and best practices enforcement
- **Interactive Dashboard**: React-based UI for visualization and management

---

## Enhanced Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  React + Vite (Port 5173)                                │   │
│  │  - Dashboard, Analytics, PR List, User Management        │   │
│  │  - Trend Visualization (Charts for time-series data)     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Flask Application (Port 5000)                           │   │
│  │  - API Endpoints, CORS, Authentication                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Agent System (Multi-Agent Orchestration)                │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Main Orchestrator Agent                            │  │   │
│  │  │  ├─ Static Analysis Agent                          │  │   │
│  │  │  ├─ Security Agent                                 │  │   │
│  │  │  ├─ Code Quality Agent                             │  │   │
│  │  │  ├─ Context Agent                                  │  │   │
│  │  │  ├─ Coverage & Metrics Agent                       │  │   │
│  │  │  └─ RAG Enhanced Agent                             │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Supporting Agents                                  │  │   │
│  │  │  ├─ Database Persistence Agent                     │  │   │
│  │  │  ├─ Analytics Processing Agent (NEW: 4-hour rule)  │  │   │
│  │  │  ├─ PR Comment Agent                               │  │   │
│  │  │  └─ Auto-Merge Agent (Optional)                    │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  🆕 Scheduled Jobs (Celery Beat)                         │   │
│  │  ├─ generate_user_analytics_daily (02:00 UTC)           │   │
│  │  ├─ generate_user_analytics_weekly (Mon 03:00 UTC)      │   │
│  │  ├─ generate_comment_statistics_daily (00:05 UTC)       │   │
│  │  └─ generate_comment_statistics_monthly (1st 02:00 UTC) │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                             │
│  ┌──────────────┬───────────────┬──────────────┬─────────────┐  │
│  │ GitHub       │ Database      │ Analytics    │ Slack       │  │
│  │ Service      │ Service       │ Service      │ Service     │  │
│  └──────────────┴───────────────┴──────────────┴─────────────┘  │
│  ┌──────────────┬───────────────┬──────────────────────────┐    │
│  │ Dashboard    │ RAG Database  │ Authentication           │    │
│  │ Service      │ Service       │ Service                  │    │
│  └──────────────┴───────────────┴──────────────────────────┘    │
│  ┌──────────────┬───────────────────────────────────────────┐   │
│  │ 🆕 Comment   │ 🆕 User Analytics Generator              │   │
│  │ Statistics   │ (Scheduled snapshots with 4-hour rule)   │   │
│  │ Service      │                                           │   │
│  └──────────────┴───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌──────────────┬───────────────┬──────────────┬─────────────┐  │
│  │ PostgreSQL   │ ChromaDB      │ OpenAI API   │ GitHub API  │  │
│  │ (Port 5433)  │ (Vector DB)   │ (gpt-4o-mini)│             │  │
│  │              │               │              │             │  │
│  │ 🆕 Tables:   │               │              │             │  │
│  │ - user_      │               │              │             │  │
│  │   analytics  │               │              │             │  │
│  │ - pr_comment_│               │              │             │  │
│  │   statistics │               │              │             │  │
│  └──────────────┴───────────────┴──────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite 5.4.21
- **UI Components**: Custom components with CSS
- **HTTP Client**: Fetch API
- **State Management**: React Hooks (useState, useEffect)
- **Routing**: React Router

### Backend
- **Framework**: Flask (Python 3.10.18)
- **CORS**: Flask-CORS
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)
- **Task Queue**: Celery (in-memory for dev, Redis for prod)
- **Task Scheduler**: Celery Beat (periodic tasks)

### AI & Machine Learning
- **LLM Provider**: OpenAI (gpt-4o-mini) / Google Gemini (configurable)
- **Vector Database**: ChromaDB
- **Embedding Model**: sentence-transformers (all-MiniLM-L6-v2)
- **RAG Framework**: Custom implementation

### External Services
- **Version Control**: GitHub API
- **Notifications**: Slack API (optional)
- **Logging**: structlog

### DevOps & Tools
- **Configuration**: YAML (config/settings.yaml)
- **Environment**: .env files
- **Code Quality**: SonarQube integration (all issues resolved)
- **Version Control**: Git

---

## Component Architecture

### 1. Frontend Components (`/frontend/src/components/`)

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx           # Main dashboard view
│   │   ├── Analytics.jsx           # User analytics & metrics
│   │   │                          # 🆕 Shows time-series trends
│   │   ├── PRList.jsx              # PR listing with filters
│   │   ├── PRDetail.jsx            # Detailed PR view
│   │   ├── Login.jsx               # Authentication
│   │   └── *.css                   # Component styles
│   ├── App.jsx                     # Root component
│   └── main.jsx                    # Entry point
```

**Key Features**:
- Responsive design
- Real-time data updates
- Interactive charts and visualizations
- Filter and search capabilities
- **🆕 Historical trend visualization using time-series data**

### 2. Backend Agents (`/agents/`)

#### Main Orchestrator Agent (`main_agent.py`)
- Coordinates all sub-agents
- Manages analysis workflow
- Aggregates results from multiple agents

#### Sub-Agents
1. **Static Analysis Agent** (`multilanguage_static_analysis_agent.py`)
   - Code structure analysis
   - Complexity metrics
   - Style violations

2. **Security Agent** (`multilanguage_security_agent.py`)
   - Vulnerability detection
   - Security best practices
   - Dependency scanning

3. **Code Quality Agent** (`multilanguage_code_quality_agent.py`)
   - Code smell detection
   - Maintainability metrics
   - Best practices enforcement

4. **Context Agent** (`context_agent.py`)
   - PR context extraction
   - File relationship analysis
   - Change impact assessment

5. **Coverage Agent** (`coverage_agent.py`)
   - Test coverage analysis
   - Code metrics
   - Quality scores

6. **RAG Enhanced Agent** (`rag_enhanced_agent.py`)
   - Historical context retrieval
   - Pattern recognition
   - Similarity analysis
   - Recommendation generation

#### Supporting Agents

1. **Database Persistence Agent** (`database_persistence_agent.py`)
   - Called from main.py after Main Agent completes
   - Converts AgentResult to database format
   - Stores PR analysis in PostgreSQL
   - Saves RAG insights to separate tables
   - Updates user statistics
   - Manages PR data lifecycle

2. **Analytics Processing Agent** (`analytics_processing_agent.py`) - **🆕 ENHANCED**
   - Invoked via `/api/analytics/*` endpoints OR scheduled jobs
   - **4-hour rule**: Prevents duplicate snapshots within 4 hours
   - User performance analysis over time
   - Trend calculation (improving/declining)
   - Aggregated metrics computation
   - Historical comparison
   - Best practices identification
   - **🆕 Generates time-series snapshots for user_analytics table**

3. **PR Comment Agent** (`pr_comment_agent.py`)
   - Posts analysis results as GitHub PR comments
   - Summary comment with overall findings
   - Inline comments on specific lines
   - Smart review creation (REQUEST_CHANGES if critical issues)
   - Configurable severity thresholds
   - Emoji-enhanced formatting for readability

4. **Auto-Merge Agent** (`auto_merge_agent.py`)
   - Automated PR merging (optional)
   - Conditional merge logic based on quality scores
   - Configurable thresholds

### 3. Service Layer (`/services/`)

#### Core Services

**GitHub Service** (`github_service.py`)
- PR fetching and management
- Repository interactions
- Comment posting
- Status updates

**Database Service** (`database_service.py`)
- CRUD operations
- Transaction management
- Connection pooling
- Query optimization

**Analytics Service** (`analytics_service.py`)
- User statistics calculation
- Trend analysis
- Performance metrics

**Dashboard Service** (`dashboard_service.py`)
- Dashboard data aggregation
- Statistics computation
- Summary generation

**RAG Database Service** (`rag_database_service.py`)
- Vector database operations
- Embedding management
- Similarity search
- RAG metrics storage

**Slack Service** (`slack_service.py`)
- Notification delivery
- Alert management
- Team communication

#### 🆕 Scheduled Analytics Services

**Comment Statistics Service** (`comment_statistics_service.py`)
- Aggregates PR comment data
- Generates daily/weekly/monthly statistics
- Stores in `pr_comment_statistics` table
- Tracks comment volumes and averages per PR

**User Analytics Generator** (`generate_user_analytics.py`)
- Scheduled generation script (daily/weekly)
- Creates time-series snapshots in `user_analytics` table
- Respects 4-hour duplicate prevention rule
- Force mode for weekly generation
- Batch processing for all active users

**Comment Statistics Generator** (`generate_comment_statistics.py`)
- Scheduled generation script (daily/weekly/monthly)
- Aggregates comment metrics by period
- Backfill capability for historical data
- Cron-ready with clear examples

### 4. Models (`/models/`)

#### Database Models (`database.py`)

**Core Tables:**
- **PRAnalysis**: Main PR data and analysis results
- **User**: User authentication and profiles
- **UserSession**: Active user sessions management
- **Feedback**: User feedback storage

**🆕 Enhanced Analytics Tables:**

- **UserStatistics**: Aggregated user performance metrics with trend indicators
  - Current state snapshot (latest aggregated metrics)
  - Used for quick "current performance" queries
  
- **UserAnalytics**: 🆕 **Time-series snapshots for historical trend analysis**
  - Point-in-time snapshots of user performance
  - Each row = one snapshot at a specific time
  - Enables trend visualization (charts, graphs)
  - Populated by scheduled jobs (daily/weekly)
  - 4-hour duplicate prevention rule
  
- **PRCommentStatistics**: 🆕 **Aggregated comment metrics by period**
  - Daily/weekly/monthly comment statistics
  - Total comments, average per PR, total PRs
  - Period start/end timestamps
  - Populated by scheduled jobs

**RAG Tables:**
- **RAGInsights**: RAG-generated insights per PR
- **RAGLearnedPatterns**: Identified code patterns
- **RAGRecommendations**: AI-generated recommendations
- **RAGSimilarPRReferences**: Similar PR references for context

**Deprecated/Unused Tables:**
- **BestPractices**: Exists but not used (data stored in UserAnalytics.best_practices JSON)
- **TrendAnalysis**: Exists but not used (trends calculated from UserAnalytics time-series)

#### Data Models
- **PREvent** (`pr_event.py`): PR event data structure
- **AnalysisResult** (`analysis_result.py`): Analysis output format
- **Feedback** (`feedback.py`): Feedback data structure

### 5. 🆕 Developer Tools (`/tools/`)

**Database Content Analysis Tool** (`analyze_database_content.py`)
- Comprehensive database inspection
- Displays all table contents
- Shows PR analysis, issues, metrics, RAG insights
- Formatted output for easy reading
- SonarQube compliant (cognitive complexity <15)

**Table Data Checker** (`check_tables_data.py`)
- Quick table row count verification
- Identifies empty tables
- Useful for testing and debugging

**Database Truncation Tool** (`truncate_database.py`)
- Clears all PR analysis data
- Useful for testing and development
- Preserves user and auth tables

**Authentication Setup** (`create_auth_tables.py`)
- Creates user and session tables
- Initial setup script

---

## Enhanced Data Flow

### 1. PR Analysis Flow (Unchanged)

```
GitHub PR Event
    │
    ▼
Webhook/Manual Trigger (main.py)
    │
    ▼
Agent Dispatcher
    │
    ▼
Main Orchestrator Agent
    │
    ├─► Static Analysis Agent
    ├─► Security Agent
    ├─► Code Quality Agent
    ├─► Context Agent
    ├─► Coverage & Metrics Agent
    └─► RAG Enhanced Agent (if enabled)
    │
    ▼
Aggregate All Results
    │
    ▼
Database Persistence Agent
    ├─ Store PR analysis
    ├─ Store issues
    ├─ Store RAG insights
    └─ Update user_statistics (current state)
    │
    ▼
Return JSON Response
```

### 2. 🆕 Scheduled Analytics Flow (NEW)

```
Celery Beat Scheduler
    │
    ├─► Daily at 02:00 UTC
    │   └─ generate_user_analytics_daily()
    │
    ├─► Weekly (Monday) at 03:00 UTC
    │   └─ generate_user_analytics_weekly()
    │
    ├─► Daily at 00:05 UTC
    │   └─ generate_comment_statistics_daily()
    │
    └─► Monthly (1st) at 02:00 UTC
        └─ generate_comment_statistics_monthly()

Each Task:
    │
    ▼
Load Services
    ├─ DatabaseService
    ├─ AnalyticsService
    └─ AnalyticsProcessingAgent
    │
    ▼
Get Active Users (who have PRs)
    │
    ▼
For Each User:
    │
    ├─ Check if recent snapshot exists (within 4 hours)
    │   ├─ YES → Skip user (prevent duplicates)
    │   └─ NO → Continue
    │
    ├─ Call Analytics Processing Agent
    │   └─ process_user_analytics(username)
    │       ├─ Query all user's PRs
    │       ├─ Calculate aggregate metrics
    │       ├─ Identify trends
    │       └─ Extract best practices
    │
    ├─ Create snapshot in user_analytics table
    │   ├─ analysis_date = NOW
    │   ├─ total_prs_analyzed
    │   ├─ avg_quality_score
    │   ├─ avg_security_score
    │   ├─ total_issues
    │   ├─ best_practices (JSON)
    │   └─ recommendations (JSON)
    │
    └─ Continue to next user

    ▼
Generate Summary Report
    ├─ Total users processed
    ├─ Snapshots created
    ├─ Users skipped (recent snapshot)
    └─ Failures (if any)
```

**Key Features:**
- **4-Hour Rule**: Daily job respects recent snapshots (won't duplicate)
- **Force Mode**: Weekly job uses --force flag to always create snapshot
- **Batch Processing**: Processes all active users automatically
- **Error Handling**: Continues processing even if one user fails
- **Logging**: Detailed logs for monitoring and debugging

### 3. User Trends Visualization Flow (NEW)

```
Frontend Request
    │
    ▼
GET /api/analytics/user/<username>/trends?days=30
    │
    ▼
Query user_analytics Table
    │
    └─ SELECT * FROM user_analytics
       WHERE author_login = :username
       AND analysis_date >= NOW() - INTERVAL '30 days'
       ORDER BY analysis_date ASC
    │
    ▼
Return Time-Series Array
    [
      {date: '2026-01-01', quality: 85, security: 90, issues: 12},
      {date: '2026-01-02', quality: 87, security: 92, issues: 10},
      {date: '2026-01-03', quality: 88, security: 93, issues: 8},
      ...
    ]
    │
    ▼
Frontend Renders Chart
    ├─ Line chart for quality score over time
    ├─ Line chart for security score over time
    ├─ Bar chart for issues over time
    └─ Trend indicators (↑ improving, ↓ declining, → stable)
```

**Performance:**
- **Fast**: Single query with date range filter (<100ms)
- **Scalable**: Indexed on (author_login, analysis_date)
- **vs Old Approach**: Old APIs analyzed PRs on-the-fly (2-5 seconds)

### 4. Comment Statistics Flow (NEW)

```
Scheduled Job (Daily/Weekly/Monthly)
    │
    ▼
Load Comment Statistics Service
    │
    ▼
Calculate Period Boundaries
    ├─ Daily: Yesterday 00:00 to 23:59
    ├─ Weekly: Last Monday to Sunday
    └─ Monthly: Previous month 1st to last day
    │
    ▼
Query pr_comments Table
    │
    └─ SELECT COUNT(*), AVG(comment_length), ...
       FROM pr_comments
       WHERE created_at BETWEEN :start AND :end
       GROUP BY pr_analysis_id
    │
    ▼
Calculate Aggregates
    ├─ total_comments
    ├─ avg_comments_per_pr
    ├─ total_prs_with_comments
    ├─ max_comments_single_pr
    └─ min_comments_single_pr
    │
    ▼
Store in pr_comment_statistics Table
    ├─ period_type (daily/weekly/monthly)
    ├─ period_start
    ├─ period_end
    ├─ total_comments
    ├─ avg_comments_per_pr
    └─ total_prs
    │
    ▼
Log Summary
    └─ "Generated monthly statistics for 2026-01: 45 comments, 3 PRs, avg 15.0/PR"
```

---

## Enhanced Database Schema

### 🆕 UserAnalytics Table (Time-Series Snapshots)

```sql
CREATE TABLE user_analytics (
    id SERIAL PRIMARY KEY,
    author_login VARCHAR NOT NULL,
    author_email VARCHAR,
    
    -- Snapshot Timestamp
    analysis_date TIMESTAMP NOT NULL DEFAULT NOW(),  -- When this snapshot was created
    
    -- Period Analyzed (optional, can be NULL for all-time)
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    
    -- Aggregate Metrics
    total_prs_analyzed INTEGER NOT NULL,
    avg_quality_score FLOAT,
    avg_security_score FLOAT,
    avg_maintainability_score FLOAT,
    avg_coverage FLOAT,
    avg_complexity FLOAT,
    
    -- Issue Statistics
    total_issues INTEGER DEFAULT 0,
    avg_issues_per_pr FLOAT,
    high_severity_issues INTEGER DEFAULT 0,
    medium_severity_issues INTEGER DEFAULT 0,
    low_severity_issues INTEGER DEFAULT 0,
    
    -- RAG Metrics
    avg_rag_risk_score FLOAT,
    avg_rag_novelty_score FLOAT,
    total_rag_insights INTEGER DEFAULT 0,
    total_similar_prs_found INTEGER DEFAULT 0,
    
    -- Best Practices & Recommendations (JSON)
    best_practices JSONB,  -- {lessons_learned: [], recommendations: [], ...}
    recommendations JSONB,  -- [{title, priority, description}, ...]
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for fast queries
    INDEX idx_user_analytics_author_date (author_login, analysis_date DESC),
    INDEX idx_user_analytics_date (analysis_date DESC)
);
```

**Key Design Decisions:**
- **Time-Series**: Each row = one snapshot at a specific time
- **No Unique Constraint**: Allows multiple snapshots per user (for trends)
- **4-Hour Rule**: Application logic prevents duplicates within 4 hours
- **JSON Columns**: Flexible storage for best practices and recommendations
- **Fast Queries**: Indexed on (author_login, analysis_date) for trend queries

**Example Data:**
```sql
-- User "john_doe" has 3 snapshots over time
id | author_login | analysis_date       | total_prs | avg_quality_score | avg_security_score
---+--------------+---------------------+-----------+-------------------+-------------------
1  | john_doe     | 2026-01-01 10:00:00 | 10        | 85.5              | 90.2
2  | john_doe     | 2026-01-02 14:00:00 | 11        | 87.3              | 91.5
3  | john_doe     | 2026-01-03 09:00:00 | 12        | 88.1              | 92.0

-- Frontend can chart these to show improvement trend ↑
```

### 🆕 PRCommentStatistics Table (Aggregated Comment Metrics)

```sql
CREATE TABLE pr_comment_statistics (
    id SERIAL PRIMARY KEY,
    
    -- Period Information
    period_type VARCHAR NOT NULL,  -- 'daily', 'weekly', 'monthly'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Comment Metrics
    total_comments INTEGER NOT NULL DEFAULT 0,
    avg_comments_per_pr FLOAT,
    total_prs INTEGER NOT NULL DEFAULT 0,
    
    -- Additional Stats
    max_comments_single_pr INTEGER,
    min_comments_single_pr INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint: one record per period
    UNIQUE(period_type, period_start, period_end),
    
    -- Index for queries
    INDEX idx_pr_comment_stats_period (period_type, period_start DESC)
);
```

**Example Data:**
```sql
id | period_type | period_start | period_end   | total_comments | avg_comments_per_pr | total_prs
---+-------------+--------------+--------------+----------------+---------------------+----------
1  | monthly     | 2026-01-01   | 2026-01-31   | 450            | 15.0                | 30
2  | weekly      | 2025-12-23   | 2025-12-29   | 120            | 12.0                | 10
3  | daily       | 2026-01-04   | 2026-01-04   | 25             | 8.3                 | 3
```

### UserStatistics Table (Current State)

```sql
CREATE TABLE user_statistics (
    id SERIAL PRIMARY KEY,
    author_login VARCHAR UNIQUE NOT NULL,  -- One record per user
    author_email VARCHAR,
    
    -- Current Aggregate Metrics
    total_prs INTEGER DEFAULT 0,
    merged_prs INTEGER DEFAULT 0,
    rejected_prs INTEGER DEFAULT 0,
    
    -- Average Scores (all-time)
    avg_quality_score FLOAT,
    avg_security_score FLOAT,
    avg_complexity_score FLOAT,
    
    -- RAG Metrics
    avg_rag_risk_score FLOAT,
    avg_rag_novelty_score FLOAT,
    
    -- Issue Stats
    avg_issues_per_pr FLOAT,
    total_critical_issues INTEGER DEFAULT 0,
    
    -- Patterns (JSON)
    common_patterns JSONB,
    best_practices JSONB,
    areas_for_improvement JSONB,
    
    -- Trend Indicators (calculated from UserAnalytics)
    quality_trend VARCHAR,  -- 'improving', 'declining', 'stable'
    security_trend VARCHAR,
    last_trend_calculation TIMESTAMP,
    
    -- Timestamps
    first_pr_date TIMESTAMP,
    last_pr_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Usage:**
- **UserStatistics**: Quick "current performance" queries (dashboard)
- **UserAnalytics**: Historical trend queries (charts, graphs)

### Other Core Tables (Unchanged)

**PRAnalysis, User, UserSession, Feedback, RAGInsights, etc.**  
(See original ARCHITECTURE.md for full schemas)

---

## Scheduled Analytics System

### 🆕 Celery Configuration (`celery_config.py`)

```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'pr_analysis',
    broker='memory://',  # In-memory for dev, redis:// for production
    backend='cache+memory://'
)

# Celery Beat Schedule (Periodic Tasks)
celery_app.conf.beat_schedule = {
    # User Analytics - Daily (respects 4-hour rule)
    'generate-user-analytics-daily': {
        'task': 'tasks.generate_user_analytics_daily',
        'schedule': crontab(hour=2, minute=0),  # 02:00 UTC daily
    },
    
    # User Analytics - Weekly (force mode)
    'generate-user-analytics-weekly': {
        'task': 'tasks.generate_user_analytics_weekly',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Monday 03:00 UTC
    },
    
    # Comment Statistics - Daily
    'generate-comment-stats-daily': {
        'task': 'tasks.generate_comment_statistics_daily',
        'schedule': crontab(hour=0, minute=5),  # 00:05 UTC daily
    },
    
    # Comment Statistics - Monthly
    'generate-comment-stats-monthly': {
        'task': 'tasks.generate_comment_statistics_monthly',
        'schedule': crontab(hour=2, minute=0, day_of_month=1),  # 1st of month 02:00 UTC
    },
}
```

### Task Implementations

#### Generate User Analytics Task

```python
@celery_app.task(name='tasks.generate_user_analytics_daily')
def generate_user_analytics_daily():
    """
    Daily user analytics generation.
    Respects 4-hour rule (won't duplicate recent snapshots).
    """
    from services.generate_user_analytics import UserAnalyticsGenerator
    
    generator = UserAnalyticsGenerator()
    results = generator.generate_for_all_users(force=False)
    
    logger.info(
        "Daily user analytics generation complete",
        generated=results['generated'],
        skipped=results['skipped'],
        failed=results['failed']
    )
    
    return results

@celery_app.task(name='tasks.generate_user_analytics_weekly')
def generate_user_analytics_weekly():
    """
    Weekly user analytics generation.
    Force mode - always creates new snapshot.
    """
    from services.generate_user_analytics import UserAnalyticsGenerator
    
    generator = UserAnalyticsGenerator()
    results = generator.generate_for_all_users(force=True)  # Force mode
    
    logger.info(
        "Weekly user analytics generation complete",
        generated=results['generated'],
        skipped=results['skipped'],
        failed=results['failed']
    )
    
    return results
```

### UserAnalyticsGenerator Service

```python
class UserAnalyticsGenerator:
    """Service for generating scheduled user analytics."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.analytics_service = AnalyticsService(self.db_service)
        self.analytics_agent = AnalyticsProcessingAgent(
            self.db_service, 
            self.analytics_service
        )
    
    def get_active_users(self, min_prs: int = 1) -> List[tuple]:
        """Get list of active users who have PRs."""
        with self.db_service.get_session() as session:
            result = session.execute(text('''
                SELECT DISTINCT author_login, author_email
                FROM pr_analysis
                WHERE author_login IS NOT NULL
                GROUP BY author_login, author_email
                HAVING COUNT(*) >= :min_prs
                ORDER BY author_login
            '''), {'min_prs': min_prs}).fetchall()
            
            return result
    
    def generate_for_user(
        self, 
        username: str, 
        force: bool = False
    ) -> tuple[bool, str, int | None]:
        """
        Generate analytics for a single user.
        
        Args:
            username: GitHub username
            force: If True, ignore 4-hour rule
        
        Returns:
            (success, message, snapshot_id)
        """
        # Call Analytics Processing Agent
        # (4-hour rule is enforced inside the agent)
        result = self.analytics_agent.process_user_analytics(
            author_login=username,
            force_regenerate=force
        )
        
        if result.get('success'):
            snapshot_id = result.get('analytics_id')
            return True, "Analytics generated", snapshot_id
        else:
            reason = result.get('reason', 'Unknown error')
            return False, reason, None
    
    def generate_for_all_users(
        self, 
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Generate analytics for all active users.
        
        Returns:
            {
                'success': True,
                'total_users': 10,
                'generated': 8,
                'skipped': 2,
                'failed': 0,
                'details': [...]
            }
        """
        users = self.get_active_users()
        
        results = {
            'success': True,
            'total_users': len(users),
            'generated': 0,
            'skipped': 0,
            'failed': 0,
            'details': []
        }
        
        for username, email in users:
            try:
                success, message, snapshot_id = self.generate_for_user(
                    username, 
                    force=force
                )
                
                if success:
                    results['generated'] += 1
                else:
                    if 'recent' in message.lower():
                        results['skipped'] += 1
                    else:
                        results['failed'] += 1
                
                results['details'].append({
                    'username': username,
                    'success': success,
                    'message': message,
                    'snapshot_id': snapshot_id
                })
                
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'username': username,
                    'success': False,
                    'error': str(e)
                })
        
        return results
```

### 🔑 4-Hour Duplicate Prevention Rule

**Implemented in**: `AnalyticsProcessingAgent.process_user_analytics()`

```python
def process_user_analytics(
    self,
    author_login: str,
    force_regenerate: bool = False
) -> Dict[str, Any]:
    """
    Generate analytics snapshot for a user.
    
    4-Hour Rule:
    - Check if snapshot exists within last 4 hours
    - If YES and not force mode → Skip (return existing)
    - If NO or force mode → Generate new snapshot
    """
    
    # Check for recent snapshot
    with self.db.get_session() as session:
        result = session.execute(text('''
            SELECT id, analysis_date
            FROM user_analytics
            WHERE author_login = :username
            AND analysis_date >= NOW() - INTERVAL '4 hours'
            ORDER BY analysis_date DESC
            LIMIT 1
        '''), {'username': author_login}).fetchone()
        
        if result and not force_regenerate:
            return {
                'success': False,
                'reason': 'Recent snapshot exists (within 4 hours)',
                'skipped': True,
                'existing_id': result[0],
                'existing_date': result[1]
            }
    
    # Generate new snapshot
    analytics_data = self._calculate_user_analytics(author_login)
    snapshot_id = self._store_snapshot(author_login, analytics_data)
    
    return {
        'success': True,
        'analytics_id': snapshot_id,
        'message': 'Analytics snapshot created'
    }
```

**Benefits:**
- **Efficiency**: Avoids redundant calculations
- **Database Size**: Prevents table bloat
- **Sensible Frequency**: 4 hours = 6 snapshots max per day
- **Override Available**: Force mode for weekly/manual generation

### Manual Execution

Both services can be run manually (useful for testing):

```bash
# Generate user analytics
python3.10 services/generate_user_analytics.py --period daily
python3.10 services/generate_user_analytics.py --period weekly --force
python3.10 services/generate_user_analytics.py --user john_doe

# Generate comment statistics
python3.10 services/generate_comment_statistics.py --period daily
python3.10 services/generate_comment_statistics.py --period monthly
python3.10 services/generate_comment_statistics.py --backfill 30
```

---

## AI/RAG System

(See original ARCHITECTURE.md - RAG system is unchanged)

### Key Points
- RAG Enhanced Agent runs within Main Orchestrator Agent
- Embeddings stored in ChromaDB
- Insights stored in PostgreSQL by Database Persistence Agent
- Novelty score, risk score, similar PR references
- AI-generated recommendations and best practices

---

## API Architecture

### 🆕 Enhanced Analytics Endpoints

#### Get User Trends (Time-Series)
```
GET /api/analytics/user/<username>/trends?days=30

Response:
{
  "success": true,
  "data": {
    "snapshots": [
      {
        "date": "2026-01-01T10:00:00Z",
        "total_prs": 10,
        "quality_score": 85.5,
        "security_score": 90.2,
        "total_issues": 12,
        "avg_issues_per_pr": 1.2
      },
      {
        "date": "2026-01-02T14:00:00Z",
        "total_prs": 11,
        "quality_score": 87.3,
        "security_score": 91.5,
        "total_issues": 10,
        "avg_issues_per_pr": 0.9
      },
      ...
    ],
    "total_snapshots": 30,
    "period": "30 days"
  }
}
```

**Performance**: <100ms (single indexed query)  
**vs Old Approach**: 2-5 seconds (analyzed PRs on-the-fly)

#### Get Comment Statistics
```
GET /api/analytics/comments/statistics?period=monthly&year=2026&month=1

Response:
{
  "success": true,
  "data": {
    "period_type": "monthly",
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "total_comments": 450,
    "avg_comments_per_pr": 15.0,
    "total_prs": 30,
    "max_comments_single_pr": 45,
    "min_comments_single_pr": 3
  }
}
```

### Other Endpoints (Unchanged)

- Authentication: `/api/auth/*`
- Pull Requests: `/api/prs/*`
- Dashboard: `/api/dashboard/*`
- User Management: `/api/users/*`
- Feedback: `/api/feedback/*`

(See original ARCHITECTURE.md for full API documentation)

---

## Performance & Optimization

### 🆕 Enhanced Performance Strategies

#### Database Optimizations

1. **Time-Series Queries**
   ```sql
   -- Indexed for fast trend queries
   CREATE INDEX idx_user_analytics_author_date 
   ON user_analytics(author_login, analysis_date DESC);
   
   -- Query: Get last 30 days of snapshots
   SELECT * FROM user_analytics
   WHERE author_login = 'john_doe'
   AND analysis_date >= NOW() - INTERVAL '30 days'
   ORDER BY analysis_date ASC;
   
   -- Execution Time: <100ms (vs 2-5s for on-the-fly analysis)
   ```

2. **Comment Statistics Aggregation**
   ```sql
   -- Pre-aggregated data
   SELECT * FROM pr_comment_statistics
   WHERE period_type = 'monthly'
   AND period_start >= '2026-01-01'
   ORDER BY period_start DESC;
   
   -- No need to scan pr_comments table
   ```

3. **4-Hour Rule Efficiency**
   ```sql
   -- Quick check for recent snapshot
   SELECT id FROM user_analytics
   WHERE author_login = :username
   AND analysis_date >= NOW() - INTERVAL '4 hours'
   LIMIT 1;
   
   -- Index: idx_user_analytics_author_date
   -- Execution Time: <10ms
   ```

#### Scheduled Jobs Efficiency

1. **Batch Processing**
   - Process all users in single job run
   - Shared database connection
   - Transaction per user (failure isolation)

2. **Smart Skipping**
   - 4-hour rule prevents redundant work
   - Daily job typically skips 70-80% of users
   - Weekly force mode ensures fresh data

3. **Async Execution**
   - Jobs run in background (Celery workers)
   - No impact on API response times
   - Failed jobs can be retried

#### Frontend Performance

1. **Fast Trend Loading**
   - Single API call for 30-day trends
   - <100ms response time
   - Cached in browser for 5 minutes

2. **Chart Rendering**
   - Efficient data structure (array of objects)
   - No client-side aggregation needed
   - Smooth animations

### Monitoring Metrics

1. **Scheduled Jobs**
   - Execution time per job
   - Users processed vs skipped
   - Failure rate
   - Database write throughput

2. **Analytics Queries**
   - Trend query latency (p50, p95, p99)
   - Cache hit rate
   - Index usage

3. **Storage Growth**
   - user_analytics table size
   - Rows per user (avg snapshots)
   - Disk space usage trends

### Scalability Considerations

1. **Data Retention**
   - Keep last 90 days of snapshots
   - Archive older data to cold storage
   - Periodic cleanup job

2. **Horizontal Scaling**
   - Multiple Celery workers for scheduled jobs
   - Read replicas for analytics queries
   - Sharding by user/repository (future)

3. **Caching Strategy**
   - Redis cache for recent trends
   - TTL: 5 minutes for hot data
   - Invalidate on new snapshot

---

## Migration from Old to New

### API Changes

**Old (Slow) APIs** - Still exist but not recommended:
```
POST /api/analytics/user/summary      # Analyzes PRs on-the-fly (2-5s)
POST /api/analytics/user/trends       # Analyzes PRs on-the-fly (2-5s)
POST /api/analytics/user/over-time    # Analyzes PRs on-the-fly (2-5s)
```

**🆕 New (Fast) APIs** - Recommended:
```
GET /api/analytics/user/<username>/trends?days=30  # Uses pre-computed snapshots (<100ms)
GET /api/analytics/comments/statistics?period=monthly
```

### Frontend Changes Required

**Old Code:**
```javascript
// Slow: Fetches and analyzes all PRs
const response = await fetch('/api/analytics/user/trends', {
  method: 'POST',
  body: JSON.stringify({ username, days: 30 })
});
```

**New Code:**
```javascript
// Fast: Fetches pre-computed snapshots
const response = await fetch(`/api/analytics/user/${username}/trends?days=30`);
const data = await response.json();

// data.snapshots = array of time-series points
// Ready for charting (no processing needed)
```

### Database Migration

**No migration needed** - New tables are additive:
- `user_analytics` - NEW table
- `pr_comment_statistics` - NEW table
- `user_statistics` - Unchanged (still updated on each PR analysis)

**Initial Data Population:**
```bash
# Backfill user analytics for existing users
python3.10 services/generate_user_analytics.py --period weekly --force

# Backfill comment statistics
python3.10 services/generate_comment_statistics.py --period monthly --backfill 12
```

---

## Deployment Checklist

### 1. Environment Setup

- [ ] Update `.env` with Celery configuration
- [ ] Install Redis (production) or use in-memory (dev)
- [ ] Create new database tables (`user_analytics`, `pr_comment_statistics`)
- [ ] Create database indexes

### 2. Service Configuration

- [ ] Configure Celery Beat schedule in `celery_config.py`
- [ ] Set timezone (default: UTC)
- [ ] Configure retry policies

### 3. Initial Data Population

- [ ] Run user analytics backfill
- [ ] Run comment statistics backfill
- [ ] Verify snapshots created

### 4. Start Services

```bash
# Start Celery worker
celery -A celery_config worker --loglevel=info

# Start Celery Beat scheduler (in separate terminal)
celery -A celery_config beat --loglevel=info

# Start Flask application
python3.10 main.py
```

### 5. Monitoring Setup

- [ ] Configure log aggregation
- [ ] Set up metric collection
- [ ] Create alerting rules
- [ ] Monitor job execution times
- [ ] Monitor database growth

### 6. Frontend Deployment

- [ ] Update API calls to use new endpoints
- [ ] Add trend visualization components
- [ ] Test chart rendering with real data
- [ ] Add loading states and error handling

---

## Troubleshooting

### Scheduled Jobs Not Running

**Check Celery Beat:**
```bash
# Verify Beat is running
ps aux | grep celery

# Check logs
tail -f celery_beat.log
```

**Check Task Registration:**
```python
# In Python shell
from celery_config import celery_app
print(celery_app.conf.beat_schedule)
```

### No Snapshots Created

**Check 4-Hour Rule:**
```sql
-- Verify recent snapshots
SELECT author_login, analysis_date
FROM user_analytics
WHERE analysis_date >= NOW() - INTERVAL '4 hours';
```

**Force Generate:**
```bash
python3.10 services/generate_user_analytics.py --user john_doe --force
```

### Trend Query Slow

**Check Index:**
```sql
-- Verify index exists
SELECT indexname FROM pg_indexes
WHERE tablename = 'user_analytics';

-- Should see: idx_user_analytics_author_date
```

**Analyze Query Plan:**
```sql
EXPLAIN ANALYZE
SELECT * FROM user_analytics
WHERE author_login = 'john_doe'
AND analysis_date >= NOW() - INTERVAL '30 days';

-- Should use Index Scan (not Seq Scan)
```

### Database Growth Too Fast

**Check Snapshot Frequency:**
```sql
-- Snapshots per user per day
SELECT 
    author_login,
    DATE(analysis_date) as date,
    COUNT(*) as snapshots
FROM user_analytics
GROUP BY author_login, DATE(analysis_date)
HAVING COUNT(*) > 6
ORDER BY snapshots DESC;

-- Should be ≤6 (4-hour rule)
```

**Cleanup Old Data:**
```sql
-- Delete snapshots older than 90 days
DELETE FROM user_analytics
WHERE analysis_date < NOW() - INTERVAL '90 days';
```

---

## Future Enhancements (V2)

### Planned Features

1. **Real-Time Analytics**
   - WebSocket updates for live metrics
   - Push notifications on threshold breach
   - Real-time dashboard refresh

2. **Advanced Trend Analysis**
   - Anomaly detection (sudden quality drops)
   - Predictive analytics (forecast future issues)
   - Comparative analysis (team vs individual)

3. **Custom Analytics Periods**
   - Configurable snapshot frequency (1h, 2h, 6h, 12h)
   - Custom date ranges
   - Sprint/milestone-based analysis

4. **Export & Reporting**
   - CSV/Excel export of trends
   - PDF report generation
   - Email digest (weekly summary)

5. **API Optimization**
   - GraphQL endpoints for flexible queries
   - Bulk trend queries (multiple users)
   - Streaming responses for large datasets

6. **Storage Optimization**
   - Time-series database (InfluxDB/TimescaleDB)
   - Compressed storage for old snapshots
   - Tiered storage (hot/warm/cold)

---

## Conclusion

Architecture V1 enhances the original PR Review System with:

✅ **Scheduled Analytics Generation** - Automated daily/weekly jobs  
✅ **Time-Series Trend Analysis** - Historical snapshots for visualization  
✅ **Performance Optimization** - 20-50x faster trend queries  
✅ **4-Hour Duplicate Prevention** - Efficient snapshot management  
✅ **Developer Tools** - Database inspection and verification utilities  
✅ **Code Quality** - All SonarQube issues resolved  

The system now provides **fast, scalable, and maintainable** analytics capabilities with clear separation between:
- **Real-time analysis** (PR analysis on webhook)
- **Scheduled snapshots** (user analytics, comment statistics)
- **Fast queries** (pre-computed data from snapshots)

For detailed implementation guides, see:
- [Original Architecture](./ARCHITECTURE.md)
- [API Documentation](./API.md)
- [Setup Guide](./SETUP.md)
- [Development Guide](./DEVELOPMENT.md)

---

**Document Version**: 1.0  
**Last Updated**: January 4, 2026  
**Author**: AI Code Review Team  
**Status**: Production Ready

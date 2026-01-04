# Analytics Architecture

## Overview

The PR Review System includes a sophisticated analytics subsystem that tracks user performance over time, generates insights, and provides actionable recommendations. This document details the architecture of the analytics system.

---

## Table of Contents

1. [System Components](#system-components)
2. [Data Storage](#data-storage)
3. [Analytics Processing Agent](#analytics-processing-agent)
4. [Data Flow](#data-flow)
5. [Scheduled Jobs](#scheduled-jobs)
6. [API Endpoints](#api-endpoints)
7. [The 4-Hour Rule](#the-4-hour-rule)
8. [RAG Metrics Integration](#rag-metrics-integration)

---

## System Components

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     ANALYTICS SUBSYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Analytics Processing Agent                               │ │
│  │  (agents/analytics_processing_agent.py)                   │ │
│  │  - Core calculation engine                                 │ │
│  │  - Aggregates PR data                                      │ │
│  │  - Generates metrics and recommendations                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              ▲                                  │
│                              │                                  │
│  ┌────────────┬─────────────┴──────────────┬─────────────────┐ │
│  │            │                             │                  │ │
│  │  Scheduler │      API Endpoints          │  Post-PR Hook   │ │
│  │  (Celery)  │      (Flask)                │  (main.py)      │ │
│  └────────────┴────────────────────────────┴─────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Database Service                                         │ │
│  │  (services/database_service.py)                           │ │
│  │  - Saves to user_analytics table                          │ │
│  │  - Queries historical data                                 │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL Database                                      │ │
│  │  - user_analytics table (snapshots)                        │ │
│  │  - pr_analysis table (source data)                         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Storage

### Two-Tier Storage Architecture

#### 1. PR-Level Data (`pr_analysis` table)
- **Purpose**: Store individual PR analysis results
- **Retention**: Permanent historical record
- **Usage**: Source data for analytics calculation
- **Updated**: Every time a PR is analyzed

**Key Fields:**
- `author_login`, `author_email`, `pr_number`, `repository`
- `total_issues`, `critical_issues`, `high_issues`, `medium_issues`, `low_issues`
- `quality_score`, `security_score`, `maintainability_score`
- `analysis_summary` (JSON) - Agent breakdown
- `rag_insights` (JSON) - RAG data with novelty_score, tips, similar_prs
- `analyzed_at` - Timestamp

#### 2. User-Level Snapshots (`user_analytics` table)
- **Purpose**: Store pre-computed aggregated analytics
- **Retention**: Time-series snapshots (daily/weekly)
- **Usage**: Fast dashboard queries
- **Updated**: Scheduled jobs + after PR analysis (with 4-hour rule)

**Key Fields:**

```sql
CREATE TABLE user_analytics (
    -- Identity
    id                          SERIAL PRIMARY KEY,
    author_login                VARCHAR(255) NOT NULL,
    author_email                VARCHAR(255),
    author_name                 VARCHAR(255),
    
    -- Time Period
    analysis_date               TIMESTAMP NOT NULL,      -- When snapshot was created
    period_start                TIMESTAMP,               -- Analysis window start
    period_end                  TIMESTAMP,               -- Analysis window end
    total_prs_analyzed          INTEGER DEFAULT 0,
    
    -- Quality Scores (Aggregated)
    avg_quality_score           FLOAT,                   -- Average 0-100
    avg_security_score          FLOAT,
    avg_maintainability_score   FLOAT,
    avg_coverage                FLOAT,
    avg_complexity              FLOAT,
    
    -- Issue Statistics (Aggregated)
    total_issues                INTEGER DEFAULT 0,
    avg_issues_per_pr           FLOAT,
    critical_issues             INTEGER DEFAULT 0,
    high_issues                 INTEGER DEFAULT 0,
    medium_issues               INTEGER DEFAULT 0,
    low_issues                  INTEGER DEFAULT 0,
    
    -- Code Metrics (Aggregated)
    total_files_changed         INTEGER DEFAULT 0,
    total_lines_added           INTEGER DEFAULT 0,
    total_lines_deleted         INTEGER DEFAULT 0,
    avg_files_per_pr            FLOAT,
    avg_lines_per_pr            FLOAT,
    
    -- Trends (JSON)
    quality_trend               JSON,   -- {direction: "improving", change: 5.2, ...}
    security_trend              JSON,
    coverage_trend              JSON,
    
    -- RAG Metrics (Extracted from pr_analysis.rag_insights)
    rag_risk_trend              JSON,
    rag_novelty_trend           JSON,
    avg_rag_risk_score          FLOAT,                   -- 0-1, higher=more risk
    avg_rag_novelty_score       FLOAT,                   -- 0-1, higher=more novel
    total_rag_insights          INTEGER DEFAULT 0,       -- PRs with RAG data
    total_similar_prs_found     INTEGER DEFAULT 0,       -- Similar PRs referenced
    total_rag_recommendations   INTEGER DEFAULT 0,       -- RAG tips given
    high_risk_prs               JSON,   -- [{pr_number, risk_score, reasons}, ...]
    novel_contributions         JSON,   -- [{pr_number, novelty_score, details}, ...]
    patterns_learned            JSON,   -- [pattern1, pattern2, ...]
    rag_insights_summary        JSON,   -- {lessons_learned, pitfalls, best_practices}
    
    -- Practices & Recommendations (JSON Arrays)
    best_practices              JSON,   -- [{practice, frequency, examples}, ...]
    bad_practices               JSON,   -- [{practice, frequency, severity}, ...]
    recommendations             JSON,   -- [{title, priority, description}, ...]
    
    -- Distributions (JSON)
    agent_breakdown             JSON,   -- Issues by agent
    issue_distribution          JSON,   -- Issues by type/severity
    
    -- Metadata
    processing_time_ms          INTEGER,
    created_at                  TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for fast queries
    INDEX idx_user_analytics_login_date (author_login, analysis_date),
    INDEX idx_user_analytics_email_date (author_email, analysis_date)
);
```

---

## Analytics Processing Agent

### Location
`agents/analytics_processing_agent.py`

### Responsibilities

#### 1. Primary Method: `process_user_analytics()`
**Purpose**: Entry point for generating user analytics with smart scheduling

```python
def process_user_analytics(
    author_login: str,
    author_email: Optional[str] = None,
    author_name: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Process analytics for a user with smart scheduling.
    Only runs if analytics haven't been generated recently (within last 4 hours).
    """
```

**Flow:**
1. Check if recent snapshot exists (< 4 hours old)
2. If exists and not forced → Skip (return existing)
3. Else → Call `analyze_user_over_time()`
4. Save results to `user_analytics` table
5. Return analytics with snapshot ID

#### 2. Core Method: `analyze_user_over_time()`
**Purpose**: Perform comprehensive user analysis over a date range

```python
def analyze_user_over_time(
    author_login: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_prs: int = 5
) -> Dict[str, Any]:
    """
    Analyze user's PR history over a time range.
    Returns comprehensive analysis with metrics, trends, recommendations.
    """
```

**Steps:**
1. **Fetch PRs**: Query `pr_analysis` table filtered by author + date range
2. **Calculate Metrics**:
   - `_calculate_quality_metrics()` - Issue counts, averages
   - `_calculate_code_scores()` - Quality/security/maintainability averages
   - `_calculate_rag_metrics()` - Extract RAG data from each PR's rag_insights JSON
   - `_analyze_trends()` - Time-series trend analysis
   - `_identify_best_practices()` - Positive patterns
   - `_identify_bad_practices()` - Negative patterns
   - `_generate_improvement_recommendations()` - Actionable suggestions
   - `_analyze_issue_distribution()` - Issue grouping
   - `_analyze_agent_performance()` - Agent effectiveness
3. **Return Analysis**: Comprehensive JSON with all metrics

#### 3. Helper Methods

##### `_get_user_prs_in_range()`
```sql
SELECT * FROM pr_analysis
WHERE author_login = :author_login
  AND analyzed_at >= :start_date
  AND analyzed_at <= :end_date
ORDER BY analyzed_at DESC
```

##### `_calculate_rag_metrics()`
**Purpose**: Extract and aggregate RAG insights from individual PRs

```python
def _calculate_rag_metrics(self, prs: List[Any]) -> Dict[str, Any]:
    """
    Extract RAG metrics from pr.rag_insights JSON field.
    Calculates averages, trends, and aggregates high-risk/novel PRs.
    """
```

**Extracts from each PR:**
- `rag_insights.novelty_score` → Average novelty
- `rag_insights.risk_score` → Average risk
- `rag_insights.similar_prs_found` → Total similar PRs
- `rag_insights.tips` → Total tips count
- `rag_insights.recommendations` → Total recommendations

**Returns:**
```json
{
  "avg_novelty_score": 0.65,
  "avg_risk_score": 0.35,
  "total_insights": 25,
  "total_similar_prs": 87,
  "total_recommendations": 45,
  "high_risk_prs": [
    {"pr_number": 123, "risk_score": 0.85, "reasons": ["SQL injection", ...]},
    {"pr_number": 145, "risk_score": 0.78, "reasons": ["Hardcoded secrets"]}
  ],
  "novel_contributions": [
    {"pr_number": 156, "novelty": 0.92, "details": "New microservice pattern"}
  ],
  "novelty_trend": {"direction": "increasing", "change": 8.5},
  "risk_trend": {"direction": "improving", "change": -12.3}
}
```

---

## Data Flow

### Path 1: Scheduled Jobs (Primary)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Celery Beat Scheduler                                        │
│    (celery_config.py)                                           │
│                                                                 │
│    Daily at 02:00 UTC:   generate_user_analytics_daily()       │
│    Weekly Monday 03:00:  generate_user_analytics_weekly()      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Celery Task                                                  │
│    @celery_app.task(name='tasks.generate_user_analytics_daily')│
│                                                                 │
│    generator = UserAnalyticsGenerator()                         │
│    result = generator.generate_for_all_users(force=False)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. User Analytics Generator                                     │
│    (services/generate_user_analytics.py)                        │
│                                                                 │
│    Step 1: Get active users from pr_analysis                    │
│    Step 2: For each user:                                       │
│            analytics_agent.process_user_analytics()             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Analytics Processing Agent                                   │
│    (agents/analytics_processing_agent.py)                       │
│                                                                 │
│    process_user_analytics():                                    │
│      ├─ Check 4-hour rule                                       │
│      ├─ analyze_user_over_time()                                │
│      │   ├─ Fetch PRs from pr_analysis                          │
│      │   ├─ Calculate all metrics                               │
│      │   ├─ Extract RAG insights from rag_insights JSON         │
│      │   └─ Generate recommendations                            │
│      └─ db_service.save_user_analytics()                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Database Service                                             │
│    (services/database_service.py)                               │
│                                                                 │
│    save_user_analytics():                                       │
│      INSERT INTO user_analytics (...)                           │
│      VALUES (metrics, trends, RAG data, recommendations, ...)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ✅ SAVED IN DATABASE
```

### Path 2: After PR Analysis (Real-time)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. PR Analysis Completes                                        │
│    (main.py: analyze_pr() endpoint)                             │
│                                                                 │
│    After PR saved to pr_analysis:                               │
│      analytics_agent.process_user_analytics(                    │
│          author_login, email, name, force=False                 │
│      )                                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              [SAME FLOW AS PATH 1 - Through Analytics Agent]
                             │
                             ▼
                    ✅ SAVED IN DATABASE
```

### Path 3: Manual API Call

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. API Endpoint                                                 │
│    POST /api/analytics/user/<author_login>/analyze              │
│                                                                 │
│    analytics_agent.process_user_analytics(                      │
│        author_login, force=True  # Override 4-hour rule         │
│    )                                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              [SAME FLOW AS PATH 1 - Through Analytics Agent]
                             │
                             ▼
                    ✅ SAVED IN DATABASE
```

---

## Scheduled Jobs

### Configuration
Location: `celery_config.py`

### Job Definitions

#### 1. Daily Analytics Generation
```python
@celery_app.task(name='tasks.generate_user_analytics_daily')
def generate_user_analytics_daily():
    """
    Generate analytics for all active users daily.
    Respects 4-hour rule - only generates if > 4 hours since last run.
    """
    generator = UserAnalyticsGenerator()
    result = generator.generate_for_all_users(force=False)
    return result
```

**Schedule**: Every day at 02:00 UTC
```python
'schedule': crontab(hour=2, minute=0)
```

**Behavior**:
- Processes all users with ≥1 PR
- Respects 4-hour rule (skips if recent snapshot exists)
- Returns summary: `{generated: X, skipped: Y, failed: Z}`

#### 2. Weekly Analytics Generation
```python
@celery_app.task(name='tasks.generate_user_analytics_weekly')
def generate_user_analytics_weekly():
    """
    Generate analytics for all active users weekly.
    Forces regeneration regardless of last run time.
    """
    generator = UserAnalyticsGenerator()
    result = generator.generate_for_all_users(force=True)
    return result
```

**Schedule**: Every Monday at 03:00 UTC
```python
'schedule': crontab(day_of_week=1, hour=3, minute=0)
```

**Behavior**:
- Processes all users with ≥1 PR
- Forces regeneration (ignores 4-hour rule)
- Creates weekly snapshot regardless of recent analytics

### Celery Beat Schedule
```python
celery_app.conf.beat_schedule = {
    'generate-user-analytics-daily': {
        'task': 'tasks.generate_user_analytics_daily',
        'schedule': crontab(hour=2, minute=0),  # Daily at 02:00 UTC
    },
    'generate-user-analytics-weekly': {
        'task': 'tasks.generate_user_analytics_weekly',
        'schedule': crontab(day_of_week=1, hour=3, minute=0),  # Monday 03:00 UTC
    }
}
```

---

## API Endpoints

### 1. User Summary
```
POST /api/analytics/user/summary
```

**Purpose**: Quick 30-day analytics snapshot

**Request Body**:
```json
{
  "email": "user@example.com",
  "days": 30  // optional, default: 30
}
```

**Response**:
```json
{
  "author_login": "username",
  "author_email": "user@example.com",
  "period_days": 30,
  "total_prs": 25,
  "code_scores": {
    "overall_quality": {"average": 85.5, "min": 72, "max": 94},
    "security": {"average": 78.2, "min": 65, "max": 88}
  },
  "quality_metrics": {
    "avg_issues_per_pr": 5.68,
    "severity_distribution": {
      "critical": 2,
      "high": 15,
      "medium": 78,
      "low": 47
    }
  },
  "top_best_practices": [...],
  "top_bad_practices": [...],
  "trends": {...},
  "summary_text": "Over the last 30 days..."
}
```

**Data Source**:
1. Fetch author_login from `pr_analysis` by email
2. Call `analytics_agent.analyze_user_over_time(start_date=now-30days, min_prs=1)`
3. Format and return subset of analysis

### 2. User Recommendations
```
POST /api/analytics/user/recommendations
```

**Purpose**: Personalized improvement recommendations (90 days)

**Request Body**:
```json
{
  "email": "user@example.com",
  "days": 90,  // optional, default: 90
  "priority": "high"  // optional filter: critical, high, medium, low
}
```

**Response**:
```json
{
  "author_login": "username",
  "author_email": "user@example.com",
  "analysis_period_days": 90,
  "total_recommendations": 12,
  "recommendations": [
    {
      "title": "Focus on security",
      "priority": "high",
      "description": "12 security issues found in last 90 days...",
      "impact": "Reduce critical security vulnerabilities by 50%",
      "actionable_steps": [...]
    }
  ]
}
```

**Data Source**:
1. Fetch author_login from `pr_analysis` by email
2. Call `analytics_agent.analyze_user_over_time(start_date=now-90days, min_prs=5)`
3. Extract and filter `improvement_recommendations`

### 3. User Trends
```
POST /api/analytics/user/trends
```

**Purpose**: Quality trends over time (180 days)

**Request Body**:
```json
{
  "email": "user@example.com",
  "days": 180  // optional, default: 180
}
```

**Response**:
```json
{
  "author_login": "username",
  "author_email": "user@example.com",
  "analysis_period_days": 180,
  "trend_analysis": {
    "quality": {"direction": "improving", "change": 5.2},
    "security": {"direction": "stable", "change": 0.3},
    "novelty": {"direction": "increasing", "change": 8.5}
  },
  "code_scores": {
    "overall_quality": {...},
    "security": {...}
  }
}
```

**Data Source**:
1. Fetch author_login from `pr_analysis` by email
2. Call `analytics_agent.analyze_user_over_time(start_date=now-180days, min_prs=10)`
3. Return `trend_analysis` and `code_scores`

### Common Pattern

All three endpoints follow the same pattern:
```
API Request → Get author_login from email
            → Call analytics_agent.analyze_user_over_time()
            → Format and return specific subset of analysis
```

**Key Differences**:
| Endpoint        | Time Range | Min PRs | Focus                          |
|----------------|-----------|---------|--------------------------------|
| summary        | 30 days   | 1       | Quick snapshot + narrative     |
| recommendations| 90 days   | 5       | Actionable improvement tips    |
| trends         | 180 days  | 10      | Historical trend analysis      |

---

## The 4-Hour Rule

### Purpose
Prevent duplicate analytics generation within a 4-hour window to:
- Reduce database load
- Avoid wasted computation
- Maintain consistent snapshots

### Implementation

Location: `agents/analytics_processing_agent.py`

```python
def process_user_analytics(author_login, force=False):
    if not force:
        # Get latest analytics snapshot
        latest = db_service.get_latest_user_analytics(author_login)
        
        if latest:
            time_since_last = datetime.now(timezone.utc) - latest.analysis_date
            
            if time_since_last < timedelta(hours=4):
                # Skip - recent analytics exists
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'Recent analytics exists',
                    'last_run': latest.analysis_date,
                    'analytics_id': latest.id
                }
    
    # Generate new analytics
    analytics_result = analyze_user_over_time(...)
    saved = db_service.save_user_analytics(analytics_result)
    return analytics_result
```

### When Applied
- ✅ Scheduled jobs (daily)
- ✅ After PR analysis hook
- ❌ Weekly scheduled job (force=True)
- ❌ Manual API calls with force parameter

### Benefits
1. **Efficiency**: Reduces redundant calculations
2. **Consistency**: Maintains stable snapshots for dashboard
3. **Performance**: Lowers database write operations
4. **Cost**: Saves compute resources

### Override
Use `force=True` parameter to bypass the 4-hour rule:
```python
analytics_agent.process_user_analytics(
    author_login="username",
    force=True  # Regenerate regardless of last run time
)
```

---

## RAG Metrics Integration

### Overview
RAG (Retrieval-Augmented Generation) insights from individual PR analyses are aggregated into user analytics.

### Source Data
Each PR's `rag_insights` JSON field in `pr_analysis` table contains:

```json
{
  "novelty_score": 0.65,           // 0-1, higher = more novel
  "risk_score": 0.35,              // 0-1, higher = more risk
  "similar_prs_found": 5,
  "similar_prs": [
    {"pr_number": 123, "similarity": 0.85, "pr_title": "..."},
    {"pr_number": 145, "similarity": 0.72, "pr_title": "..."}
  ],
  "tips": [
    "Consider using prepared statements",
    "Add input validation"
  ],
  "recommendations": "...",
  "lessons_learned": "...",
  "potential_pitfalls": "...",
  "best_practices": "...",
  "patterns_identified": ["file_types:py,js", "size:medium"]
}
```

### Extraction Process

Method: `_calculate_rag_metrics(prs)` in Analytics Processing Agent

```python
def _calculate_rag_metrics(self, prs: List[Any]) -> Dict[str, Any]:
    """Extract and aggregate RAG metrics from individual PRs."""
    
    novelty_scores = []
    risk_scores = []
    high_risk_prs = []
    novel_contributions = []
    total_similar_prs = 0
    total_tips = 0
    
    for pr in prs:
        if pr.rag_insights:
            insights = json.loads(pr.rag_insights)
            
            # Extract novelty
            novelty = insights.get('novelty_score')
            if novelty is not None:
                novelty_scores.append(novelty)
                if novelty >= 0.8:  # Highly novel
                    novel_contributions.append({
                        'pr_number': pr.pr_number,
                        'novelty_score': novelty,
                        'details': insights.get('patterns_identified', [])
                    })
            
            # Extract risk
            risk = insights.get('risk_score')
            if risk is not None:
                risk_scores.append(risk)
                if risk >= 0.7:  # High risk
                    high_risk_prs.append({
                        'pr_number': pr.pr_number,
                        'risk_score': risk,
                        'reasons': insights.get('potential_pitfalls', '').split('\n')
                    })
            
            # Count similar PRs
            total_similar_prs += insights.get('similar_prs_found', 0)
            
            # Count tips
            total_tips += len(insights.get('tips', []))
    
    return {
        'avg_novelty_score': round(mean(novelty_scores), 3) if novelty_scores else None,
        'avg_risk_score': round(mean(risk_scores), 3) if risk_scores else None,
        'total_insights': len([p for p in prs if p.rag_insights]),
        'total_similar_prs': total_similar_prs,
        'total_recommendations': total_tips,
        'high_risk_prs': high_risk_prs,
        'novel_contributions': novel_contributions,
        'novelty_trend': self._calculate_trend(novelty_scores, 'novelty'),
        'risk_trend': self._calculate_trend(risk_scores, 'risk')
    }
```

### Stored in `user_analytics` Table

RAG-related fields:
```sql
avg_rag_novelty_score       FLOAT     -- Average novelty (0-1)
avg_rag_risk_score          FLOAT     -- Average risk (0-1)
total_rag_insights          INTEGER   -- PRs with RAG data
total_similar_prs_found     INTEGER   -- Similar PRs referenced
total_rag_recommendations   INTEGER   -- Tips given
high_risk_prs               JSON      -- High-risk PR details
novel_contributions         JSON      -- Novel PR details
rag_novelty_trend           JSON      -- Trend analysis
rag_risk_trend              JSON      -- Trend analysis
```

### Usage in Dashboard

1. **Novelty Badge**: Show user's average novelty score
2. **Risk Alert**: Highlight high-risk PRs
3. **Learning Progress**: Track how user improves over time
4. **Similar Work**: Show patterns in user's contributions
5. **Personalized Tips**: Display aggregated recommendations

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANALYTICS ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            TRIGGER POINTS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │  Celery Beat │    │  After PR    │    │  Manual API  │                 │
│  │  Scheduler   │    │  Analysis    │    │  Call        │                 │
│  │  (Daily/     │    │  (Real-time) │    │  (On-demand) │                 │
│  │   Weekly)    │    │              │    │              │                 │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│         │                   │                   │                          │
│         └───────────────────┴───────────────────┘                          │
│                             │                                               │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS PROCESSING AGENT                               │
│                (agents/analytics_processing_agent.py)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  process_user_analytics(author_login, email, name, force)                  │
│    │                                                                         │
│    ├─► Check 4-Hour Rule                                                    │
│    │     └─► Skip if recent snapshot exists (unless force=True)             │
│    │                                                                         │
│    └─► analyze_user_over_time(author_login, start_date, end_date)          │
│          │                                                                   │
│          ├─► 1. Fetch PRs from Database                                     │
│          │     SELECT * FROM pr_analysis                                    │
│          │     WHERE author_login = :login                                  │
│          │     AND analyzed_at BETWEEN :start AND :end                      │
│          │                                                                   │
│          ├─► 2. Calculate Quality Metrics                                   │
│          │     • Total issues, avg issues per PR                            │
│          │     • Severity distribution (critical/high/medium/low)           │
│          │     • Files changed, lines added/deleted                         │
│          │                                                                   │
│          ├─► 3. Calculate Code Scores                                       │
│          │     • Average quality score                                      │
│          │     • Average security score                                     │
│          │     • Average maintainability                                    │
│          │                                                                   │
│          ├─► 4. Extract RAG Metrics                                         │
│          │     • Parse rag_insights JSON from each PR                       │
│          │     • Calculate avg novelty_score, risk_score                    │
│          │     • Aggregate similar_prs_found, tips                          │
│          │     • Identify high-risk and novel PRs                           │
│          │                                                                   │
│          ├─► 5. Analyze Trends                                              │
│          │     • Time-series analysis of scores                             │
│          │     • Direction (improving/declining/stable)                     │
│          │     • Rate of change                                             │
│          │                                                                   │
│          ├─► 6. Identify Best Practices                                     │
│          │     • Extract from analysis_summary                              │
│          │     • Rank by frequency                                          │
│          │                                                                   │
│          ├─► 7. Identify Bad Practices                                      │
│          │     • Extract from analysis_summary                              │
│          │     • Rank by severity and frequency                             │
│          │                                                                   │
│          ├─► 8. Generate Recommendations                                    │
│          │     • Analyze recurring issues                                   │
│          │     • Identify skill gaps                                        │
│          │     • Prioritize actionable improvements                         │
│          │                                                                   │
│          └─► 9. Return Comprehensive Analysis JSON                          │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE SERVICE                                    │
│                    (services/database_service.py)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  save_user_analytics(analytics_data)                                        │
│    │                                                                         │
│    └─► INSERT INTO user_analytics (                                         │
│          author_login, author_email, author_name,                           │
│          analysis_date, period_start, period_end,                           │
│          avg_quality_score, avg_security_score,                             │
│          total_issues, avg_issues_per_pr,                                   │
│          quality_trend, security_trend,                                     │
│          avg_rag_novelty_score, avg_rag_risk_score,                         │
│          high_risk_prs, novel_contributions,                                │
│          best_practices, bad_practices, recommendations,                    │
│          ...                                                                 │
│        ) VALUES (...)                                                        │
│                                                                             │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        POSTGRESQL DATABASE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  user_analytics (Time-series snapshots)                     │           │
│  │  • One row per snapshot per user                             │           │
│  │  • Indexed by (author_login, analysis_date)                  │           │
│  │  • Contains aggregated metrics and trends                    │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                              ▲                                              │
│                              │ Queries for analysis                         │
│                              │                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  pr_analysis (Source data)                                   │           │
│  │  • One row per PR                                            │           │
│  │  • Contains rag_insights JSON                                 │           │
│  │  • Source for calculating user analytics                     │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API CONSUMERS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  • Dashboard UI (React frontend)                                            │
│  • Analytics API Endpoints (/api/analytics/user/*)                          │
│  • Reporting Tools                                                           │
│  • Admin Dashboards                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Query Performance
- **Indexes**: `(author_login, analysis_date)` for fast time-range queries
- **Expected Response Time**: 
  - Single user, 30 days: ~100-300ms
  - Single user, 180 days: ~300-800ms
  - All users (scheduled): ~5-30s depending on user count

### Optimization Opportunities
1. **Caching**: Cache recent analytics snapshots in Redis (TTL: 4 hours)
2. **Pagination**: For large result sets in dashboards
3. **Materialized Views**: Pre-compute common aggregations
4. **Async Processing**: Use Celery for on-demand analytics generation
5. **Partial Updates**: Only recalculate changed metrics (future enhancement)

---

## Future Enhancements

1. **Comparative Analytics**: Compare user performance against team averages
2. **Goal Tracking**: Set and track improvement goals
3. **Notifications**: Alert users of significant trends
4. **Export**: Download analytics as PDF/CSV
5. **Custom Time Ranges**: Allow users to specify custom date ranges
6. **Real-time Updates**: WebSocket updates for live dashboards
7. **Machine Learning**: Predict future trends, recommend personalized learning paths

---

## Related Documentation

- [Main Architecture](./ARCHITECTURE.md) - Overall system architecture
- [RAG Enhanced Agent](../agents/rag_enhanced_agent.py) - RAG insights generation
- [Database Schema](./create_tables.sql) - Complete database schema
- [API Documentation](./API.md) - REST API endpoints

---

## Conclusion

The Analytics Architecture provides a robust, scalable system for tracking and improving user performance over time. By leveraging scheduled jobs, smart caching (4-hour rule), and comprehensive metrics including RAG insights, the system delivers actionable intelligence to help developers improve their code quality continuously.

**Key Takeaways:**
- ✅ Single source of truth: Analytics Processing Agent
- ✅ Two-tier storage: PR-level + User-level snapshots
- ✅ Smart scheduling: 4-hour rule prevents redundant computation
- ✅ Comprehensive metrics: Quality, security, RAG insights, trends
- ✅ Multiple triggers: Scheduled, real-time, on-demand
- ✅ Fast queries: Pre-computed snapshots for dashboard

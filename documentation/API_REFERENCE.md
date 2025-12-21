# API Reference

Complete API documentation for the Multi-Agent PR Review System.

## Base URL

```
http://localhost:5000
```

For production, replace with your server URL.

## Table of Contents

1. [Health Check](#health-check)
2. [PR Analysis](#pr-analysis)
3. [GitHub Webhook](#github-webhook)
4. [Dashboard APIs](#dashboard-apis)
5. [Analytics APIs](#analytics-apis)
6. [PR Management APIs](#pr-management-apis)
7. [Auto-Merge APIs](#auto-merge-apis)

---

## Health Check

### GET /health

Check if the API server is running.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "multi-agent-pr-review",
  "version": "1.0.0"
}
```

---

## PR Analysis

### POST /api/analyze

Analyze a Pull Request using the multi-agent system.

**Request Body:**
```json
{
  "repository": "owner/repo",
  "pr_number": 123,
  "agent_type": "security"  // optional
}
```

**Parameters:**
- `repository` (string, required): GitHub repository in format "owner/repo"
- `pr_number` (integer, required): Pull Request number
- `agent_type` (string, optional): Specific agent to use
  - Options: `static_analysis`, `security`, `code_quality`, `context`, `coverage`
  - If not specified, uses the main orchestrator with all agents

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "myorg/myrepo",
    "pr_number": 42
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Analysis completed",
  "pr_number": 42,
  "repository": "myorg/myrepo",
  "agent_used": "Main Orchestrator Agent",
  "success": true,
  "execution_time": 15.23,
  "issues_found": 28,
  "critical_issues": 2,
  "high_issues": 5,
  "medium_issues": 15,
  "low_issues": 6,
  "issues": [
    {
      "file": "src/main.py",
      "line": 45,
      "column": 10,
      "type": "SECURITY",
      "severity": "critical",
      "code": "HARDCODED_SECRET",
      "message": "Possible hardcoded credential detected",
      "suggestion": "Use environment variables or config files",
      "metadata": {
        "tool": "pattern-analysis",
        "language": "python"
      }
    }
  ],
  "metrics": {
    "files_changed": 8,
    "lines_added": 145,
    "lines_deleted": 32,
    "estimated_coverage": 75.5,
    "complexity_score": 12.3
  },
  "agent_breakdown": {
    "static_analysis": 10,
    "security": 3,
    "code_quality": 12,
    "context": 2,
    "coverage": 1
  },
  "database_id": 156  // if database persistence is enabled
}
```

**Status Codes:**
- `200 OK`: Analysis completed successfully
- `400 Bad Request`: Missing or invalid parameters
- `404 Not Found`: PR not found
- `500 Internal Server Error`: Analysis failed

---

## GitHub Webhook

### POST /webhook/github

Receive GitHub webhook events for automated PR analysis.

**Headers:**
- `X-Hub-Signature-256`: GitHub webhook signature for verification

**Request Body:** (GitHub webhook payload)
```json
{
  "action": "opened",
  "pull_request": { ... },
  "repository": { ... }
}
```

**Response:**
```json
{
  "message": "Analysis completed",
  "pr_number": 123,
  "agent_used": "Main Orchestrator Agent"
}
```

**Status Codes:**
- `200 OK`: Webhook processed
- `401 Unauthorized`: Invalid signature
- `500 Internal Server Error`: Processing failed

---

## Dashboard APIs

### 1. Get User Insights

**GET** `/api/dashboard/user/<author_login>/insights`

Get comprehensive insights for a user including best practices, bad practices, and recommendations.

**Example:**
```bash
curl http://localhost:5000/api/dashboard/user/john-doe/insights
```

**Response:**
```json
{
  "author_login": "john-doe",
  "total_prs": 45,
  "quality_score": 82.5,
  "best_practices": [
    {
      "category": "Security",
      "title": "Excellent Security Awareness",
      "description": "You consistently avoid security vulnerabilities",
      "score": 100.0
    }
  ],
  "bad_practices": [
    {
      "category": "Quality",
      "title": "Magic Numbers",
      "occurrences": 23,
      "severity": "medium"
    }
  ],
  "recommendations": [
    "Use named constants instead of magic numbers",
    "Improve test coverage by 10%"
  ]
}
```

### 2. Get User Statistics

**GET** `/api/dashboard/user/<author_login>/statistics`

Get statistical summary for a user.

**Example:**
```bash
curl http://localhost:5000/api/dashboard/user/john-doe/statistics
```

**Response:**
```json
{
  "author_login": "john-doe",
  "author_email": "john@example.com",
  "total_prs": 45,
  "total_issues": 587,
  "avg_quality_score": 82.5,
  "avg_security_score": 95.2,
  "avg_maintainability_score": 78.3,
  "avg_coverage": 73.5,
  "severity_distribution": {
    "critical": 8,
    "high": 45,
    "medium": 234,
    "low": 300
  },
  "trends": {
    "quality": "improving",
    "security": "stable",
    "coverage": "improving"
  },
  "common_issues": ["MAGIC_NUMBER", "NO_PRINT", "TODO_FOUND"],
  "improvement_areas": ["Code Coverage", "Code Complexity"],
  "strengths": ["Security Practices", "Clean Code"],
  "first_pr_date": "2024-01-15T10:30:00Z",
  "last_pr_date": "2024-12-20T15:45:00Z"
}
```

### 3. Get User PRs

**GET** `/api/dashboard/user/<author_login>/prs?limit=20`

Get recent PRs for a user.

**Query Parameters:**
- `limit` (integer, optional): Number of PRs to return (default: 20)

**Example:**
```bash
curl "http://localhost:5000/api/dashboard/user/john-doe/prs?limit=10"
```

**Response:**
```json
{
  "author_login": "john-doe",
  "total": 10,
  "prs": [
    {
      "id": 156,
      "repository": "myorg/myrepo",
      "pr_number": 42,
      "pr_title": "Add new feature",
      "pr_url": "https://github.com/myorg/myrepo/pull/42",
      "total_issues": 12,
      "quality_score": 85.5,
      "security_score": 100.0,
      "analyzed_at": "2024-12-20T10:30:00Z",
      "severity_counts": {
        "critical": 0,
        "high": 1,
        "medium": 8,
        "low": 3
      }
    }
  ]
}
```

### 4. Get Repository Statistics

**GET** `/api/dashboard/repository/<owner>/<repo>/stats`

Get aggregated statistics for a repository.

**Example:**
```bash
curl http://localhost:5000/api/dashboard/repository/myorg/myrepo/stats
```

**Response:**
```json
{
  "repository": "myorg/myrepo",
  "total_prs": 156,
  "total_contributors": 12,
  "avg_quality_score": 83.2,
  "avg_security_score": 96.5,
  "total_issues": 2340,
  "issue_distribution": {
    "critical": 34,
    "high": 156,
    "medium": 987,
    "low": 1163
  },
  "top_contributors": [
    {"login": "john-doe", "prs": 45, "avg_score": 85.2},
    {"login": "jane-smith", "prs": 38, "avg_score": 88.5}
  ]
}
```

### 5. Get Repository Insights

**GET** `/api/dashboard/repository/<owner>/<repo>/insights`

Get comprehensive insights for a repository.

**Example:**
```bash
curl http://localhost:5000/api/dashboard/repository/myorg/myrepo/insights
```

**Response:**
```json
{
  "repository": "myorg/myrepo",
  "health_score": 84.5,
  "trends": {
    "quality": "improving",
    "activity": "high"
  },
  "common_issues": ["MAGIC_NUMBER", "NO_PRINT"],
  "best_practices": ["Good test coverage", "Consistent code style"],
  "recommendations": [
    "Reduce code complexity in core modules",
    "Improve error handling"
  ]
}
```

### 6. Get PR Analysis Details

**GET** `/api/dashboard/pr/<owner>/<repo>/<pr_number>`

Get detailed analysis for a specific PR.

**Example:**
```bash
curl http://localhost:5000/api/dashboard/pr/myorg/myrepo/42
```

**Response:**
```json
{
  "id": 156,
  "repository": "myorg/myrepo",
  "pr_number": 42,
  "pr_title": "Add new feature",
  "pr_url": "https://github.com/myorg/myrepo/pull/42",
  "author_login": "john-doe",
  "author_email": "john@example.com",
  "total_issues": 12,
  "severity_distribution": {
    "critical": 0,
    "high": 1,
    "medium": 8,
    "low": 3
  },
  "agent_breakdown": {
    "static_analysis": 5,
    "security": 0,
    "code_quality": 6,
    "context": 0,
    "coverage": 1
  },
  "scores": {
    "overall_quality": 85.5,
    "security": 100.0,
    "maintainability": 78.3
  },
  "coverage_metrics": {
    "estimated_coverage": 75.5,
    "test_to_code_ratio": 0.45,
    "complexity_score": 12.3
  },
  "analyzed_at": "2024-12-20T10:30:00Z",
  "analysis_duration_ms": 15234
}
```

### 7. Initialize Database

**POST** `/api/dashboard/init-db`

Initialize or recreate database tables (admin endpoint).

**Example:**
```bash
curl -X POST http://localhost:5000/api/dashboard/init-db
```

**Response:**
```json
{
  "status": "success",
  "message": "Database tables created successfully"
}
```

---

## Analytics APIs

### 1. Analyze User Over Time

**GET** `/api/analytics/user/<author_login>/analyze`

Analyze user's performance over a time range.

**Query Parameters:**
- `start_date` (string, optional): ISO format date (YYYY-MM-DD)
- `end_date` (string, optional): ISO format date (YYYY-MM-DD)
- `days` (integer, optional): Number of days to look back
- `min_prs` (integer, optional): Minimum PRs required (default: 5)

**Example:**
```bash
curl "http://localhost:5000/api/analytics/user/john-doe/analyze?days=90&min_prs=5"
```

**Response:**
```json
{
  "success": true,
  "author_login": "john-doe",
  "analysis_period": {
    "start_date": "2024-09-21",
    "end_date": "2024-12-20",
    "total_prs": 28,
    "days": 90
  },
  "code_scores": {
    "overall_quality": {
      "average": 82.2,
      "min": 65.0,
      "max": 95.5,
      "rating": "Good"
    },
    "security": {
      "average": 100.0,
      "min": 100.0,
      "max": 100.0,
      "rating": "Excellent"
    },
    "maintainability": {
      "average": 70.8,
      "min": 45.0,
      "max": 88.0,
      "rating": "Fair"
    }
  },
  "quality_metrics": {
    "total_issues": 587,
    "avg_issues_per_pr": 20.96,
    "severity_distribution": {
      "critical": 74,
      "high": 18,
      "medium": 423,
      "low": 72
    }
  },
  "best_practices": [
    {
      "category": "Security",
      "title": "Excellent Security Awareness",
      "description": "You consistently avoid security vulnerabilities",
      "score": 100.0,
      "occurrences": 0
    }
  ],
  "bad_practices": [
    {
      "category": "Quality",
      "title": "Magic Numbers",
      "occurrences": 458,
      "severity": "medium",
      "example": "Use named constants for values like 100, 200"
    }
  ],
  "trend_analysis": {
    "quality": {
      "direction": "improving",
      "change_percent": 5.2,
      "recent_avg": 85.0,
      "older_avg": 79.8
    }
  },
  "improvement_recommendations": [
    {
      "area": "Code Quality",
      "priority": "medium",
      "current_score": 82.2,
      "target_score": 85.0,
      "actions": [
        "Eliminate magic numbers by using named constants",
        "Reduce method complexity in core modules"
      ]
    }
  ]
}
```

### 2. Get User Analytics Summary

**GET** `/api/analytics/user/<author_login>/summary?days=30`

Get quick analytics summary for user.

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze (default: 30)

**Example:**
```bash
curl "http://localhost:5000/api/analytics/user/john-doe/summary?days=30"
```

**Response:**
```json
{
  "author_login": "john-doe",
  "period_days": 30,
  "total_prs": 10,
  "code_scores": {
    "overall_quality": 84.5,
    "security": 100.0,
    "maintainability": 76.2
  },
  "quality_metrics": {
    "avg_issues_per_pr": 18.5,
    "severity_distribution": {
      "critical": 2,
      "high": 8,
      "medium": 95,
      "low": 80
    }
  },
  "top_best_practices": [
    "Excellent Security Awareness",
    "Good Test Coverage",
    "Clean Code Structure"
  ],
  "top_bad_practices": [
    "Magic Numbers",
    "Long Methods",
    "TODO Comments"
  ],
  "trends": {
    "quality": "improving",
    "security": "stable",
    "coverage": "improving"
  }
}
```

### 3. Get User Recommendations

**GET** `/api/analytics/user/<author_login>/recommendations`

Get personalized improvement recommendations.

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze (default: 90)
- `priority` (string, optional): Filter by priority (critical, high, medium, low)

**Example:**
```bash
curl "http://localhost:5000/api/analytics/user/john-doe/recommendations?priority=high"
```

**Response:**
```json
{
  "author_login": "john-doe",
  "analysis_period_days": 90,
  "total_recommendations": 5,
  "recommendations": [
    {
      "area": "Code Quality",
      "priority": "high",
      "current_score": 82.2,
      "target_score": 85.0,
      "gap": 2.8,
      "actions": [
        "Eliminate magic numbers by using named constants",
        "Break down methods over 50 lines into smaller functions",
        "Add more descriptive variable names"
      ],
      "estimated_impact": "High",
      "effort": "Medium"
    }
  ]
}
```

### 4. Get User Trends

**GET** `/api/analytics/user/<author_login>/trends?days=180`

Get quality trends for user over time.

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze (default: 180)

**Example:**
```bash
curl "http://localhost:5000/api/analytics/user/john-doe/trends?days=180"
```

**Response:**
```json
{
  "author_login": "john-doe",
  "analysis_period_days": 180,
  "trend_analysis": {
    "quality": {
      "direction": "improving",
      "change_percent": 8.5,
      "recent_avg": 85.0,
      "older_avg": 76.5,
      "confidence": "high"
    },
    "security": {
      "direction": "stable",
      "change_percent": 0.0,
      "recent_avg": 100.0,
      "older_avg": 100.0,
      "confidence": "high"
    },
    "coverage": {
      "direction": "improving",
      "change_percent": 12.3,
      "recent_avg": 78.5,
      "older_avg": 66.2,
      "confidence": "medium"
    }
  },
  "code_scores": {
    "overall_quality": 85.0,
    "security": 100.0,
    "maintainability": 78.5
  }
}
```

---

## PR Management APIs

### 1. List PRs by Email

**POST** `/api/prs/list`

Get list of PRs for a user by email and date range.

**Request Body:**
```json
{
  "email": "john@example.com",
  "start_date": "2024-01-01",  // optional
  "end_date": "2024-12-31",    // optional
  "limit": 100                 // optional
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/prs/list \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "start_date": "2024-06-01",
    "limit": 50
  }'
```

**Response:**
```json
{
  "success": true,
  "email": "john@example.com",
  "total_prs": 28,
  "date_range": {
    "start": "2024-06-01",
    "end": null
  },
  "prs": [
    {
      "pr_number": 123,
      "pr_title": "Add new feature",
      "pr_url": "https://github.com/owner/repo/pull/123",
      "repository": "owner/repo",
      "author_login": "john-doe",
      "author_name": "John Doe",
      "analyzed_at": "2024-12-20T10:30:00Z",
      "overall_quality_score": 85.5,
      "security_score": 100.0,
      "maintainability_score": 78.3,
      "total_issues": 10,
      "critical_issues": 0,
      "high_issues": 2,
      "medium_issues": 5,
      "low_issues": 3,
      "files_changed": 5,
      "lines_added": 150,
      "lines_deleted": 20,
      "estimated_coverage": 75.0
    }
  ]
}
```

### 2. Get PR Details

**POST** `/api/prs/details`

Get detailed information for a specific PR.

**Request Body:**
```json
{
  "pr_number": 123,
  "repository": "owner/repo"  // optional but recommended
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/prs/details \
  -H "Content-Type: application/json" \
  -d '{
    "pr_number": 123,
    "repository": "owner/repo"
  }'
```

**Response:**
```json
{
  "success": true,
  "pr": {
    "pr_number": 123,
    "pr_title": "Add new feature",
    "pr_description": "This PR adds...",
    "pr_url": "https://github.com/owner/repo/pull/123",
    "repository": "owner/repo",
    "author_login": "john-doe",
    "author_email": "john@example.com",
    "author_name": "John Doe",
    "base_branch": "main",
    "head_branch": "feature-branch",
    "analyzed_at": "2024-12-20T10:30:00Z",
    "pr_created_at": "2024-12-19T14:20:00Z",
    "pr_updated_at": "2024-12-20T09:15:00Z",
    "overall_quality_score": 85.5,
    "security_score": 100.0,
    "maintainability_score": 78.3,
    "total_issues": 10,
    "issues_by_severity": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 3
    },
    "issues_by_agent": {
      "static_analysis": 3,
      "security": 0,
      "code_quality": 5,
      "context": 1,
      "coverage": 1
    },
    "code_metrics": {
      "files_changed": 5,
      "lines_added": 150,
      "lines_deleted": 20,
      "complexity_score": 15.5,
      "estimated_coverage": 75.0,
      "test_to_code_ratio": 0.8
    }
  },
  "issues": [
    {
      "issue_type": "MAGIC_NUMBER",
      "severity": "medium",
      "category": "quality",
      "file_path": "src/main.py",
      "line_number": 42,
      "title": "Magic number used",
      "description": "Avoid using magic numbers directly in code",
      "recommendation": "Use named constants instead",
      "agent_name": "Code Quality Agent"
    }
  ],
  "total_issues": 10
}
```

### 3. Get User Analytics by Email

**POST** `/api/analytics/user`

Get analytics for a user by email and date range.

**Request Body:**
```json
{
  "email": "john@example.com",
  "start_date": "2024-01-01",  // optional
  "end_date": "2024-12-31"     // optional
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/analytics/user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "start_date": "2024-06-01"
  }'
```

**Response:** (Same as `/api/analytics/user/<author_login>/analyze`)

---

## Auto-Merge APIs

### 1. Evaluate PR for Auto-Merge

**POST** `/api/auto-merge/evaluate`

Evaluate if a PR should be auto-merged based on configured conditions.

**Request Body:**
```json
{
  "repository": "owner/repo",
  "pr_number": 123
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/auto-merge/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "owner/repo",
    "pr_number": 123
  }'
```

**Response:**
```json
{
  "success": true,
  "should_merge": true,
  "reason": "All quality gates passed",
  "evaluation": {
    "checks_passed": [
      "Quality score above threshold (85.5 >= 80.0)",
      "Security score acceptable (100.0 >= 90.0)",
      "No critical issues (0 < 1)",
      "Required approvals met (2 >= 2)",
      "All status checks passed"
    ],
    "checks_failed": []
  },
  "pr_details": {
    "repository": "owner/repo",
    "pr_number": 123,
    "title": "Add new feature",
    "author": "john-doe",
    "state": "open"
  },
  "analysis_summary": {
    "quality_score": 85.5,
    "security_score": 100.0,
    "total_issues": 10,
    "reviews_count": 3,
    "approvals": 2
  }
}
```

### 2. Execute Auto-Merge

**POST** `/api/auto-merge/execute`

Execute auto-merge for a PR if it passes all conditions.

**Request Body:**
```json
{
  "repository": "owner/repo",
  "pr_number": 123,
  "force": false  // optional: skip checks if true (use with caution!)
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/auto-merge/execute \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "owner/repo",
    "pr_number": 123
  }'
```

**Response:**
```json
{
  "success": true,
  "merged": true,
  "message": "PR #123 merged successfully",
  "merge_sha": "abc123def456...",
  "merge_method": "squash",
  "evaluation": {
    "checks_passed": [...],
    "checks_failed": []
  }
}
```

**Error Response (if conditions not met):**
```json
{
  "success": false,
  "merged": false,
  "message": "PR does not meet auto-merge conditions: Quality score below threshold",
  "evaluation": {
    "checks_passed": ["Security score acceptable", "No critical issues"],
    "checks_failed": ["Quality score below threshold (75.0 < 80.0)"]
  }
}
```

### 3. Get Auto-Merge Configuration

**GET** `/api/auto-merge/config`

Get current auto-merge configuration.

**Example:**
```bash
curl http://localhost:5000/api/auto-merge/config
```

**Response:**
```json
{
  "enabled": false,
  "mode": "conditional",
  "conditions": {
    "min_quality_score": 80.0,
    "min_security_score": 90.0,
    "max_critical_issues": 0,
    "max_high_issues": 2,
    "required_approvals": 2,
    "require_all_checks_pass": true
  },
  "merge_settings": {
    "merge_method": "squash",
    "delete_branch": true,
    "post_merge_comment": true
  },
  "allowed_repositories": ["owner/repo1", "owner/repo2"],
  "allowed_users": ["john-doe", "jane-smith"]
}
```

---

## Error Responses

All endpoints return standardized error responses:

```json
{
  "error": "Error message describing what went wrong"
}
```

### Common Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Rate Limiting

Currently, no rate limiting is enforced. For production use, consider implementing:
- Rate limiting per IP address
- Rate limiting per API key
- Token bucket algorithm

---

## Authentication

Currently, the API uses GitHub token authentication configured in environment variables. For production:
- Implement API key authentication
- Add user-specific tokens
- Use OAuth for third-party integrations

---

## Pagination

For endpoints returning lists, pagination parameters:
- `limit`: Number of items per page
- `offset`: Number of items to skip

Example:
```bash
curl "http://localhost:5000/api/dashboard/user/john-doe/prs?limit=20&offset=40"
```

---

## Next Steps

- [API Examples](API_EXAMPLES.md) - See real-world usage examples
- [Quick Start Guide](QUICK_START.md) - Get started quickly
- [Configuration Guide](CONFIGURATION.md) - Configure the system

# API Examples

Real-world examples of using the Multi-Agent PR Review System API.

## Table of Contents

1. [Basic PR Analysis](#basic-pr-analysis)
2. [User Analytics](#user-analytics)
3. [Team Dashboard](#team-dashboard)
4. [Auto-Merge Workflows](#auto-merge-workflows)
5. [Batch Operations](#batch-operations)
6. [Integration Examples](#integration-examples)

---

## Basic PR Analysis

### Example 1: Analyze a New PR

When a developer creates a PR, analyze it immediately:

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "mycompany/backend-api",
    "pr_number": 234
  }'
```

**Use Case**: CI/CD pipeline integration, manual PR review

### Example 2: Security-Focused Analysis

Analyze a PR specifically for security issues:

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "mycompany/backend-api",
    "pr_number": 234,
    "agent_type": "security"
  }'
```

**Use Case**: Security-sensitive repositories, compliance requirements

### Example 3: Check Analysis Results

After analysis, retrieve detailed results:

```bash
curl -X POST http://localhost:5000/api/prs/details \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "mycompany/backend-api",
    "pr_number": 234
  }' | jq '.issues[] | select(.severity=="critical")'
```

**Use Case**: Filter critical issues, generate reports

---

## User Analytics

### Example 4: Developer Performance Report

Generate a 90-day performance report for a developer:

```bash
curl "http://localhost:5000/api/analytics/user/john-doe/analyze?days=90&min_prs=5" \
  | jq '{
    developer: .author_login,
    quality_score: .code_scores.overall_quality.average,
    security_score: .code_scores.security.average,
    total_prs: .analysis_period.total_prs,
    top_issues: .bad_practices[0:3] | map(.title)
  }'
```

**Output:**
```json
{
  "developer": "john-doe",
  "quality_score": 82.5,
  "security_score": 100,
  "total_prs": 28,
  "top_issues": [
    "Magic Numbers",
    "Long Methods",
    "TODO Comments"
  ]
}
```

**Use Case**: Performance reviews, developer coaching

### Example 5: Track Developer Improvement

Compare recent vs older performance:

```bash
# Recent 30 days
curl "http://localhost:5000/api/analytics/user/john-doe/summary?days=30" \
  > recent.json

# Older 30-60 days ago
curl "http://localhost:5000/api/analytics/user/john-doe/analyze?start_date=2024-10-21&end_date=2024-11-20" \
  > older.json

# Compare
jq -s '{"recent": .[0].code_scores.overall_quality, "older": .[1].code_scores.overall_quality.average}' \
  recent.json older.json
```

**Use Case**: Track improvement over time, validate training effectiveness

### Example 6: Get Personalized Recommendations

Get actionable recommendations for a developer:

```bash
curl "http://localhost:5000/api/analytics/user/john-doe/recommendations?priority=high" \
  | jq '.recommendations[] | {
    area: .area,
    priority: .priority,
    actions: .actions
  }'
```

**Output:**
```json
{
  "area": "Code Quality",
  "priority": "high",
  "actions": [
    "Eliminate magic numbers by using named constants",
    "Break down methods over 50 lines into smaller functions"
  ]
}
```

**Use Case**: Developer coaching, sprint planning

---

## Team Dashboard

### Example 7: Repository Health Overview

Get overall health metrics for a repository:

```bash
curl http://localhost:5000/api/dashboard/repository/mycompany/backend-api/stats \
  | jq '{
    total_prs: .total_prs,
    avg_quality: .avg_quality_score,
    avg_security: .avg_security_score,
    top_contributors: .top_contributors[0:5] | map({login, prs, avg_score})
  }'
```

**Use Case**: Weekly team meetings, management reports

### Example 8: Team Leaderboard

Generate a team leaderboard based on code quality:

```bash
#!/bin/bash
# Get all team members
TEAM_MEMBERS=("john-doe" "jane-smith" "bob-jones" "alice-wong")

# Fetch stats for each member
for member in "${TEAM_MEMBERS[@]}"; do
  curl -s "http://localhost:5000/api/dashboard/user/$member/statistics" \
    | jq "{
        name: .author_login,
        quality: .avg_quality_score,
        security: .avg_security_score,
        prs: .total_prs
      }"
done | jq -s 'sort_by(.quality) | reverse'
```

**Use Case**: Team motivation, recognition programs

### Example 9: Identify Code Quality Trends

Track repository quality over time:

```bash
# Get PRs from last 30 days
curl -X POST http://localhost:5000/api/prs/list \
  -H "Content-Type: application/json" \
  -d '{
    "email": "team@company.com",
    "start_date": "2024-11-21",
    "limit": 100
  }' | jq '[.prs[] | {
    date: .analyzed_at[0:10],
    quality: .overall_quality_score
  }] | group_by(.date) | map({
    date: .[0].date,
    avg_quality: (map(.quality) | add / length)
  })'
```

**Use Case**: Sprint retrospectives, quality initiatives

---

## Auto-Merge Workflows

### Example 10: Automated PR Approval Pipeline

Create a script for automated PR evaluation and merging:

```bash
#!/bin/bash
REPO="mycompany/backend-api"
PR_NUMBER=$1

echo "Evaluating PR #$PR_NUMBER for auto-merge..."

# Step 1: Evaluate
EVAL_RESULT=$(curl -s -X POST http://localhost:5000/api/auto-merge/evaluate \
  -H "Content-Type: application/json" \
  -d "{\"repository\": \"$REPO\", \"pr_number\": $PR_NUMBER}")

SHOULD_MERGE=$(echo $EVAL_RESULT | jq -r '.should_merge')

if [ "$SHOULD_MERGE" = "true" ]; then
  echo "✓ PR meets all criteria. Proceeding with merge..."
  
  # Step 2: Execute merge
  MERGE_RESULT=$(curl -s -X POST http://localhost:5000/api/auto-merge/execute \
    -H "Content-Type: application/json" \
    -d "{\"repository\": \"$REPO\", \"pr_number\": $PR_NUMBER}")
  
  echo "Merge result:"
  echo $MERGE_RESULT | jq '{merged, message, merge_sha}'
else
  echo "✗ PR does not meet criteria:"
  echo $EVAL_RESULT | jq '.reason'
  echo ""
  echo "Failed checks:"
  echo $EVAL_RESULT | jq '.evaluation.checks_failed'
fi
```

**Usage:**
```bash
./auto_merge.sh 234
```

**Use Case**: Automated deployment pipelines, low-risk PR merging

### Example 11: Conditional Auto-Merge

Merge only if specific conditions are met:

```bash
curl -X POST http://localhost:5000/api/auto-merge/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "mycompany/backend-api",
    "pr_number": 234
  }' | jq 'if .should_merge and .analysis_summary.critical_issues == 0 then
    "SAFE_TO_MERGE"
  else
    "MANUAL_REVIEW_REQUIRED"
  end'
```

**Use Case**: Risk-based deployment strategies

---

## Batch Operations

### Example 12: Analyze Multiple PRs

Analyze all open PRs in a repository:

```bash
#!/bin/bash
REPO="mycompany/backend-api"

# Get list of open PRs (from GitHub API or your system)
PR_NUMBERS=(234 235 236 237 238)

for PR in "${PR_NUMBERS[@]}"; do
  echo "Analyzing PR #$PR..."
  curl -s -X POST http://localhost:5000/api/analyze \
    -H "Content-Type: application/json" \
    -d "{\"repository\": \"$REPO\", \"pr_number\": $PR}" \
    | jq '{pr: .pr_number, status: .status, issues: .issues_found}'
  
  sleep 2  # Rate limiting
done
```

**Use Case**: Repository-wide quality audit, backfill analysis

### Example 13: Bulk User Analytics

Generate analytics for entire team:

```bash
#!/bin/bash
TEAM_EMAILS=(
  "john@company.com"
  "jane@company.com"
  "bob@company.com"
  "alice@company.com"
)

for EMAIL in "${TEAM_EMAILS[@]}"; do
  echo "Generating report for $EMAIL..."
  curl -s -X POST http://localhost:5000/api/analytics/user \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"$EMAIL\",
      \"start_date\": \"2024-01-01\"
    }" > "reports/$(echo $EMAIL | cut -d@ -f1)_report.json"
done

echo "Reports generated in reports/ directory"
```

**Use Case**: Annual reviews, team-wide assessments

---

## Integration Examples

### Example 14: CI/CD Integration (GitHub Actions)

Add to `.github/workflows/pr-analysis.yml`:

```yaml
name: PR Analysis
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Analyze PR
        run: |
          RESULT=$(curl -X POST ${{ secrets.PR_REVIEW_API }}/api/analyze \
            -H "Content-Type: application/json" \
            -d "{
              \"repository\": \"${{ github.repository }}\",
              \"pr_number\": ${{ github.event.pull_request.number }}
            }")
          
          echo "$RESULT" | jq .
          
          # Fail if critical issues found
          CRITICAL=$(echo "$RESULT" | jq -r '.critical_issues')
          if [ "$CRITICAL" -gt "0" ]; then
            echo "::error::Found $CRITICAL critical issues"
            exit 1
          fi
```

**Use Case**: Automated PR quality gates

### Example 15: Slack Integration

Send daily team quality report to Slack:

```bash
#!/bin/bash
# daily_report.sh

# Generate team statistics
STATS=$(curl -s http://localhost:5000/api/dashboard/repository/mycompany/backend-api/stats)

QUALITY=$(echo $STATS | jq -r '.avg_quality_score')
SECURITY=$(echo $STATS | jq -r '.avg_security_score')
TOTAL_PRS=$(echo $STATS | jq -r '.total_prs')

# Format Slack message
MESSAGE=$(cat <<EOF
{
  "text": "Daily Code Quality Report",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📊 Daily Code Quality Report"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Average Quality Score:*\n$QUALITY/100"
        },
        {
          "type": "mrkdwn",
          "text": "*Security Score:*\n$SECURITY/100"
        },
        {
          "type": "mrkdwn",
          "text": "*Total PRs Analyzed:*\n$TOTAL_PRS"
        }
      ]
    }
  ]
}
EOF
)

# Send to Slack
curl -X POST $SLACK_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d "$MESSAGE"
```

**Schedule with cron:**
```bash
0 9 * * * /path/to/daily_report.sh
```

**Use Case**: Daily team standup information, visibility

### Example 16: Jira Integration

Create Jira tickets for high-severity issues:

```bash
#!/bin/bash
PR_NUMBER=$1

# Get PR analysis
ANALYSIS=$(curl -s -X POST http://localhost:5000/api/prs/details \
  -H "Content-Type: application/json" \
  -d "{\"pr_number\": $PR_NUMBER, \"repository\": \"mycompany/backend-api\"}")

# Extract high-severity issues
HIGH_ISSUES=$(echo $ANALYSIS | jq -r '.issues[] | select(.severity=="high" or .severity=="critical")')

# Create Jira tickets for each
echo "$HIGH_ISSUES" | jq -c '.' | while read issue; do
  TITLE=$(echo $issue | jq -r '.title')
  DESC=$(echo $issue | jq -r '.description')
  FILE=$(echo $issue | jq -r '.file_path')
  LINE=$(echo $issue | jq -r '.line_number')
  
  # Create Jira ticket
  curl -X POST "$JIRA_API_URL/rest/api/2/issue" \
    -u "$JIRA_USER:$JIRA_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"fields\": {
        \"project\": {\"key\": \"TECH\"},
        \"summary\": \"Code Issue: $TITLE in PR #$PR_NUMBER\",
        \"description\": \"$DESC\n\nFile: $FILE:$LINE\",
        \"issuetype\": {\"name\": \"Bug\"}
      }
    }"
done
```

**Use Case**: Issue tracking, technical debt management

### Example 17: Dashboard Data Export

Export data for external dashboard/BI tools:

```bash
#!/bin/bash
# export_metrics.sh

OUTPUT_DIR="exports/$(date +%Y-%m-%d)"
mkdir -p $OUTPUT_DIR

# Export repository stats
curl -s http://localhost:5000/api/dashboard/repository/mycompany/backend-api/stats \
  > "$OUTPUT_DIR/repo_stats.json"

# Export user statistics
USERS=("john-doe" "jane-smith" "bob-jones")
for USER in "${USERS[@]}"; do
  curl -s "http://localhost:5000/api/dashboard/user/$USER/statistics" \
    > "$OUTPUT_DIR/${USER}_stats.json"
done

# Convert to CSV for Excel/Tableau
jq -r '["login","total_prs","quality_score","security_score"] | @csv,
  (.[] | [.author_login, .total_prs, .avg_quality_score, .avg_security_score] | @csv)' \
  "$OUTPUT_DIR"/*_stats.json > "$OUTPUT_DIR/team_metrics.csv"

echo "Metrics exported to $OUTPUT_DIR"
```

**Use Case**: Executive dashboards, data analysis

### Example 18: Python Script Integration

Use Python for complex automation:

```python
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:5000"

def analyze_pr(repo, pr_number):
    """Analyze a PR and return results."""
    response = requests.post(
        f"{API_BASE}/api/analyze",
        json={"repository": repo, "pr_number": pr_number}
    )
    return response.json()

def get_user_analytics(email, days=90):
    """Get user analytics for specified period."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    response = requests.post(
        f"{API_BASE}/api/analytics/user",
        json={
            "email": email,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
    )
    return response.json()

def check_quality_threshold(repo, pr_number, threshold=80.0):
    """Check if PR meets quality threshold."""
    result = analyze_pr(repo, pr_number)
    
    if not result.get('success'):
        return False, "Analysis failed"
    
    quality_score = result.get('metrics', {}).get('overall_quality_score', 0)
    critical_issues = result.get('critical_issues', 0)
    
    if quality_score < threshold:
        return False, f"Quality score {quality_score} below threshold {threshold}"
    
    if critical_issues > 0:
        return False, f"Found {critical_issues} critical issues"
    
    return True, "All checks passed"

# Example usage
if __name__ == "__main__":
    repo = "mycompany/backend-api"
    pr_number = 234
    
    passed, message = check_quality_threshold(repo, pr_number)
    print(f"Quality Check: {'✓ PASSED' if passed else '✗ FAILED'}")
    print(f"Message: {message}")
```

**Use Case**: Complex automation workflows, custom tooling

---

## Advanced Queries

### Example 19: Complex Data Analysis

Find developers who need coaching:

```bash
#!/bin/bash
# identify_coaching_needs.sh

TEAM_MEMBERS=("john-doe" "jane-smith" "bob-jones" "alice-wong")

echo "Developers needing coaching:"
echo "=============================="

for MEMBER in "${TEAM_MEMBERS[@]}"; do
  STATS=$(curl -s "http://localhost:5000/api/dashboard/user/$MEMBER/statistics")
  
  QUALITY=$(echo $STATS | jq -r '.avg_quality_score // 0')
  CRITICAL=$(echo $STATS | jq -r '.severity_distribution.critical // 0')
  TREND=$(echo $STATS | jq -r '.trends.quality // "unknown"')
  
  # Flag if quality < 75 OR has critical issues OR declining trend
  if (( $(echo "$QUALITY < 75" | bc -l) )) || \
     [ "$CRITICAL" -gt "5" ] || \
     [ "$TREND" = "declining" ]; then
    echo ""
    echo "Developer: $MEMBER"
    echo "  Quality Score: $QUALITY"
    echo "  Critical Issues: $CRITICAL"
    echo "  Trend: $TREND"
    echo "  → Needs coaching on:"
    
    # Get recommendations
    curl -s "http://localhost:5000/api/analytics/user/$MEMBER/recommendations?priority=high" \
      | jq -r '.recommendations[0:2] | .[] | "     - \(.area): \(.actions[0])"'
  fi
done
```

**Use Case**: Proactive developer support, training programs

### Example 20: Quality Gate Enforcement

Implement strict quality gates for production deployments:

```bash
#!/bin/bash
# quality_gate.sh

REPO=$1
PR_NUMBER=$2
DEPLOYMENT_TIER=$3  # dev, staging, production

echo "Running quality gate for $DEPLOYMENT_TIER deployment..."

# Different thresholds for different tiers
case $DEPLOYMENT_TIER in
  "production")
    MIN_QUALITY=90
    MIN_SECURITY=95
    MAX_CRITICAL=0
    MAX_HIGH=0
    ;;
  "staging")
    MIN_QUALITY=80
    MIN_SECURITY=90
    MAX_CRITICAL=0
    MAX_HIGH=2
    ;;
  "dev")
    MIN_QUALITY=70
    MIN_SECURITY=80
    MAX_CRITICAL=1
    MAX_HIGH=5
    ;;
esac

# Get analysis
ANALYSIS=$(curl -s -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{\"repository\": \"$REPO\", \"pr_number\": $PR_NUMBER}")

QUALITY=$(echo $ANALYSIS | jq -r '.metrics.overall_quality_score // 0')
SECURITY=$(echo $ANALYSIS | jq -r '.metrics.security_score // 0')
CRITICAL=$(echo $ANALYSIS | jq -r '.critical_issues // 0')
HIGH=$(echo $ANALYSIS | jq -r '.high_issues // 0')

PASSED=true

# Check all gates
if (( $(echo "$QUALITY < $MIN_QUALITY" | bc -l) )); then
  echo "✗ Quality gate failed: $QUALITY < $MIN_QUALITY"
  PASSED=false
fi

if (( $(echo "$SECURITY < $MIN_SECURITY" | bc -l) )); then
  echo "✗ Security gate failed: $SECURITY < $MIN_SECURITY"
  PASSED=false
fi

if [ "$CRITICAL" -gt "$MAX_CRITICAL" ]; then
  echo "✗ Critical issues gate failed: $CRITICAL > $MAX_CRITICAL"
  PASSED=false
fi

if [ "$HIGH" -gt "$MAX_HIGH" ]; then
  echo "✗ High severity gate failed: $HIGH > $MAX_HIGH"
  PASSED=false
fi

if [ "$PASSED" = true ]; then
  echo "✓ All quality gates passed for $DEPLOYMENT_TIER"
  exit 0
else
  echo "✗ Quality gates failed for $DEPLOYMENT_TIER deployment"
  exit 1
fi
```

**Usage:**
```bash
./quality_gate.sh mycompany/backend-api 234 production
```

**Use Case**: Deployment pipelines, risk management

---

## Tips and Best Practices

1. **Use jq for JSON processing** - It's powerful and makes filtering easy
2. **Implement rate limiting** - Add delays between batch requests
3. **Store credentials securely** - Use environment variables or secret managers
4. **Cache results** - Store frequently accessed data to reduce API calls
5. **Monitor API health** - Regularly check `/health` endpoint
6. **Log API calls** - Track usage and troubleshoot issues
7. **Handle errors gracefully** - Always check response status codes
8. **Use webhooks when possible** - More efficient than polling

---

## Next Steps

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Architecture](ARCHITECTURE.md) - Understand the system design
- [Configuration](CONFIGURATION.md) - Customize for your needs

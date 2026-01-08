"""Data models for feedback outputs."""
from dataclasses import dataclass
from typing import List, Dict, Any
from models.analysis_result import AggregatedResult, Issue, Severity


@dataclass
class FeedbackMessage:
    """Formatted feedback message for output."""
    title: str
    body: str
    severity: Severity
    metadata: Dict[str, Any]
    
    
class FeedbackFormatter:
    """Formats analysis results for different output channels."""
    
    @staticmethod
    def to_github_comment(result: AggregatedResult) -> str:
        """Format results as GitHub PR comment."""
        lines = []
        lines.append("## 🤖 Multi-Agent PR Review Results\n")
        
        # Summary section
        FeedbackFormatter._add_summary_section(lines, result)
        
        # Agent results
        FeedbackFormatter._add_agent_results(lines, result)
        
        lines.append(f"\n⏱️ Analysis completed in {result.total_execution_time:.2f} seconds")
        
        return "\n".join(lines)
    
    @staticmethod
    def _add_summary_section(lines: List[str], result: AggregatedResult) -> None:
        """Add summary section to GitHub comment."""
        summary = result.summary
        lines.append("### 📊 Summary")
        lines.append(f"- **Total Issues**: {summary['total_issues']}")
        lines.append(f"- 🔴 Critical: {summary['critical']}")
        lines.append(f"- 🟠 High: {summary['high']}")
        lines.append(f"- 🟡 Medium: {summary['medium']}")
        lines.append(f"- 🟢 Low: {summary['low']}\n")
        
        if result.should_block:
            lines.append("⚠️ **This PR has critical issues that should be addressed before merging.**\n")
    
    @staticmethod
    def _add_agent_results(lines: List[str], result: AggregatedResult) -> None:
        """Add agent results section to GitHub comment."""
        for agent_result in result.agent_results:
            if agent_result.issues:
                lines.append(f"### {agent_result.agent_name}")
                lines.append(f"Found {len(agent_result.issues)} issue(s)\n")
                
                FeedbackFormatter._add_agent_issues(lines, agent_result.issues)
    
    @staticmethod
    def _add_agent_issues(lines: List[str], issues: List[Issue]) -> None:
        """Add issues for an agent to GitHub comment."""
        for issue in issues[:10]:  # Limit to top 10
            emoji = FeedbackFormatter._severity_emoji(issue.severity)
            location = f"{issue.file}:{issue.line}" if issue.line else issue.file
            lines.append(f"{emoji} **{location}**: {issue.message}")
            if issue.suggestion:
                lines.append(f"   💡 *Suggestion: {issue.suggestion}*")
            lines.append("")
        
        if len(issues) > 10:
            lines.append(f"*...and {len(issues) - 10} more issues*\n")
    
    @staticmethod
    def to_slack_message(result: AggregatedResult) -> Dict[str, Any]:
        """Format results as Slack message blocks."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🤖 PR Review Complete"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Repository:*\n{result.repository}"},
                    {"type": "mrkdwn", "text": f"*PR Number:*\n#{result.pr_number}"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total Issues:*\n{result.summary['total_issues']}"},
                    {"type": "mrkdwn", "text": f"*Critical:*\n{result.summary['critical']} 🔴"}
                ]
            }
        ]
        
        if result.should_block:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠️ *Critical issues found - review required before merging*"
                }
            })
        
        return {"blocks": blocks}
    
    @staticmethod
    def to_dashboard_payload(result: AggregatedResult) -> Dict[str, Any]:
        """Format results for dashboard API."""
        return {
            "pr_number": result.pr_number,
            "repository": result.repository,
            "timestamp": result.total_execution_time,
            "summary": result.summary,
            "recommendation": result.recommendation,
            "should_block": result.should_block,
            "agents": [
                {
                    "name": agent.agent_name,
                    "success": agent.success,
                    "execution_time": agent.execution_time,
                    "issues_count": agent.total_issues,
                    "metrics": agent.metrics
                }
                for agent in result.agent_results
            ]
        }
    
    @staticmethod
    def _severity_emoji(severity: Severity) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🟢",
            Severity.INFO: "ℹ️"
        }
        return emoji_map.get(severity, "•")

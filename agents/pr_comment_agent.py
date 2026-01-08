"""
PR Comment Agent - Posts analysis results as GitHub PR comments

This agent takes analysis results from all other agents and formats them
as helpful comments directly on the GitHub PR, including:
- Overall summary comment
- Inline comments on specific lines with issues
- Categorized findings (critical, warnings, suggestions)
- Tracks all posted comments in database for analytics
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone
from models.analysis_result import AgentResult, Issue, Severity, IssueType
from models.pr_event import PREvent
from services.github_service import GitHubService
from utils.logger import logger


class PRCommentAgent:
    """Agent responsible for posting analysis results as PR comments."""
    
    def __init__(self, github_service: GitHubService, db_service=None, config: Optional[dict] = None):
        """
        Initialize PR Comment Agent.
        
        Args:
            github_service: GitHub service for API interactions
            db_service: Database service for tracking comments (optional)
            config: Configuration dict with options:
                - enabled: bool (default True)
                - post_summary: bool (default True)
                - post_inline_comments: bool (default True)
                - max_inline_comments: int (default 50)
                - severity_threshold: str (default "LOW")
                - group_by_file: bool (default True)
                - include_rag_insights: bool (default True)
                - track_in_database: bool (default True)
        """
        self.github_service = github_service
        self.db_service = db_service
        self.config = config or {}
        self.logger = logger.bind(agent="pr_comment")
        
        # Configuration
        self.enabled = self.config.get('enabled', True)
        self.post_summary = self.config.get('post_summary', True)
        self.post_inline_comments = self.config.get('post_inline_comments', True)
        self.max_inline_comments = self.config.get('max_inline_comments', 50)
        self.severity_threshold = self.config.get('severity_threshold', 'LOW')
        self.group_by_file = self.config.get('group_by_file', True)
        self.include_rag_insights = self.config.get('include_rag_insights', True)
        self.track_in_database = self.config.get('track_in_database', True) and db_service is not None
        
        # Severity ordering for filtering
        self.severity_levels = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1,
            'INFO': 0
        }
        
        self.logger.info(
            "PR Comment Agent initialized",
            enabled=self.enabled,
            post_summary=self.post_summary,
            post_inline=self.post_inline_comments,
            track_in_database=self.track_in_database,
            db_service_provided=db_service is not None
        )
    
    def post_analysis_comments(
        self, 
        pr_event: PREvent, 
        agent_result: AgentResult,
        commit_sha: Optional[str] = None,
        pr_analysis_id: Optional[int] = None
    ) -> Dict[str, bool]:
        """
        Post analysis results as PR comments.
        
        Args:
            pr_event: The PR event
            agent_result: Aggregated results from all agents
            commit_sha: Specific commit SHA (uses PR head if not provided)
            pr_analysis_id: Database ID of PR analysis (for tracking)
            
        Returns:
            Dict with results: {
                'summary_posted': bool,
                'inline_comments_posted': int,
                'success': bool
            }
        """
        if not self.enabled:
            return self._create_disabled_response()
        
        try:
            existing_summary = self.github_service.find_summary_comment(
                pr_event.repository, 
                pr_event.pr_number
            )
            
            results = self._initialize_results()
            
            if not existing_summary:
                results = self._post_comments_to_github(pr_event, agent_result, commit_sha, results)
            else:
                results = self._create_skipped_response(existing_summary)
            
            if pr_analysis_id and self.track_in_database:
                self._handle_database_tracking(
                    pr_event, pr_analysis_id, agent_result, 
                    commit_sha, results, existing_summary
                )
            
            return results
            
        except Exception as e:
            return self._create_error_response(e, pr_event)
    
    def _create_disabled_response(self) -> Dict[str, bool]:
        """Create response when agent is disabled."""
        self.logger.info("PR Comment Agent disabled")
        return {
            'summary_posted': False,
            'inline_comments_posted': 0,
            'success': False,
            'message': 'Agent disabled'
        }
    
    def _initialize_results(self) -> Dict[str, bool]:
        """Initialize default results dictionary."""
        return {
            'summary_posted': False,
            'inline_comments_posted': 0,
            'success': True
        }
    
    def _create_skipped_response(self, existing_summary: dict) -> Dict[str, bool]:
        """Create response when comments already exist on GitHub."""
        self.logger.info(
            "Bot summary already exists on GitHub. Skipping duplicate posting.",
            comment_id=existing_summary.get('id')
        )
        return {
            'summary_posted': False,
            'inline_comments_posted': 0,
            'success': True,
            'message': 'Comment already exists, skipped posting'
        }
    
    def _create_error_response(self, error: Exception, pr_event: PREvent) -> Dict[str, bool]:
        """Create response when an error occurs."""
        self.logger.error(
            "Failed to post PR comments",
            pr_number=pr_event.pr_number,
            error=str(error),
            exc_info=True
        )
        return {
            'summary_posted': False,
            'inline_comments_posted': 0,
            'success': False,
            'error': str(error)
        }
    
    def _post_comments_to_github(
        self, 
        pr_event: PREvent, 
        agent_result: AgentResult, 
        commit_sha: Optional[str],
        results: Dict[str, bool]
    ) -> Dict[str, bool]:
        """Post comments to GitHub and update results."""
        self.logger.info("No existing summary found. Proceeding to post comments to GitHub.")
        
        summary_response = None
        review_response = None
        
        # 1. Post Inline Comments as Review (if enabled)
        if self.post_inline_comments:
            sha_to_use = self._determine_commit_sha(pr_event, commit_sha)
            if sha_to_use:
                review_response, inline_count, _ = self._post_inline_comments_as_review(
                    pr_event, agent_result, sha_to_use
                )
                results['inline_comments_posted'] = inline_count
            else:
                self.logger.warning("Cannot post inline comments: commit SHA not found")
        
        # 2. Post Summary Comment (if enabled)
        if self.post_summary:
            summary_response = self._post_summary(pr_event, agent_result)
            if summary_response:
                results['summary_posted'] = True
        
        # Store responses for later use
        results['_summary_response'] = summary_response
        results['_review_response'] = review_response
        
        return results
    
    def _determine_commit_sha(self, pr_event: PREvent, commit_sha: Optional[str]) -> Optional[str]:
        """Determine the commit SHA to use for inline comments."""
        sha_to_use = commit_sha or pr_event.head_sha
        if not sha_to_use and hasattr(pr_event, 'head'):
            sha_to_use = pr_event.head.get('sha')
        return sha_to_use
    
    def _handle_database_tracking(
        self,
        pr_event: PREvent,
        pr_analysis_id: int,
        agent_result: AgentResult,
        commit_sha: Optional[str],
        results: Dict[str, bool],
        existing_summary: Optional[dict]
    ):
        """Handle tracking comments in database."""
        tracked_inline = self._generate_inline_comments(agent_result)
        
        summary_response = results.get('_summary_response')
        review_response = results.get('_review_response')
        
        github_comment_id = self._get_comment_id(summary_response, existing_summary)
        github_review_id = str(review_response.get('id')) if review_response else None
        review_event = review_response.get('state') if review_response else None
        
        self._track_comments_in_database(
            pr_event=pr_event,
            pr_analysis_id=pr_analysis_id,
            agent_result=agent_result,
            summary_posted=True,
            inline_comments=tracked_inline,
            review_event=review_event,
            commit_sha=commit_sha,
            github_comment_id=github_comment_id,
            github_review_id=github_review_id
        )
        
        results['summary_posted'] = True
        if not results['inline_comments_posted']:
            results['inline_comments_posted'] = len(tracked_inline)
        
        # Clean up internal keys
        results.pop('_summary_response', None)
        results.pop('_review_response', None)
    
    def _get_comment_id(
        self, 
        summary_response: Optional[dict], 
        existing_summary: Optional[dict]
    ) -> Optional[str]:
        """Get GitHub comment ID from responses."""
        if summary_response:
            return str(summary_response.get('id'))
        if existing_summary:
            return str(existing_summary.get('id'))
        return None
    
    def _generate_inline_comments(self, agent_result: AgentResult) -> List[Dict]:
        """
        Generate inline comments from analysis results without posting to GitHub.
        Returns list of comment dictionaries.
        """
        inline_comments = self._build_inline_comments(agent_result)
        # No need to limit since we're not posting to GitHub
        return inline_comments
    
    def _post_summary(self, pr_event: PREvent, agent_result: AgentResult) -> Optional[dict]:
        """
        Post summary comment to PR.
        
        Returns:
            Dict with comment details if successful, None otherwise
        """
        summary = self._build_summary_comment(agent_result)
        comment_response = self.github_service.post_comment(
            pr_event.repository,
            pr_event.pr_number,
            summary
        )
        
        if comment_response:
            self.logger.info(
                "Posted summary comment",
                pr_number=pr_event.pr_number,
                repository=pr_event.repository,
                comment_id=comment_response.get('id')
            )
        return comment_response
    
    def _post_inline_comments_as_review(
        self, 
        pr_event: PREvent, 
        agent_result: AgentResult, 
        commit_sha: str
    ) -> tuple:
        """
        Post inline comments as a review.
        
        Returns:
            tuple: (review_response: Optional[dict], inline_count: int, inline_comments: List[Dict])
                   review_response contains review details with 'id' if successful
        """
        if not self.post_inline_comments:
            return (None, 0, [])
        
        inline_comments = self._build_inline_comments(agent_result)
        
        # Limit and prioritize comments
        inline_comments = self._limit_inline_comments(inline_comments, pr_event.pr_number)
        
        if inline_comments:
            review_event = self._determine_review_event()
            review_response, inline_count = self._try_post_review(
                pr_event, agent_result, commit_sha, inline_comments, review_event
            )
            return (review_response, inline_count, inline_comments)
        
        return (None, 0, [])
    
    def _limit_inline_comments(self, inline_comments: List[Dict], pr_number: int) -> List[Dict]:
        """Limit number of inline comments to maximum allowed."""
        if len(inline_comments) > self.max_inline_comments:
            self.logger.warning(
                "Too many inline comments, limiting to maximum",
                comment_count=len(inline_comments),
                max_allowed=self.max_inline_comments,
                pr_number=pr_number,
                agent="pr_comment"
            )
            inline_comments = self._prioritize_comments(inline_comments)[:self.max_inline_comments]
        return inline_comments
    
    def _try_post_review(
        self,
        pr_event: PREvent,
        agent_result: AgentResult,
        commit_sha: str,
        inline_comments: List[Dict],
        review_event: str
    ) -> tuple:
        """
        Try to post comments as a review, fall back to individual comments if failed.
        
        Returns:
            tuple: (review_response: Optional[dict], inline_count: int)
                   review_response contains review details with 'id' if successful
        """
        # Use full summary as review body unless we are going to post a separate summary comment
        if self.post_summary:
            review_body = "## 🤖 Automated Code Review: Findings Below\n\nSee the detailed summary at the bottom of this conversation."
        else:
            review_body = self._build_summary_comment(agent_result)
        
        review_response = self.github_service.post_review_with_comments(
            repository=pr_event.repository,
            pr_number=pr_event.pr_number,
            commit_sha=commit_sha,
            review_body=review_body,
            review_event=review_event,
            inline_comments=inline_comments
        )
        
        if review_response:
            self.logger.info(
                "Posted inline comments as review WITH summary",
                pr_number=pr_event.pr_number,
                count=len(inline_comments),
                review_id=review_response.get('id')
            )
            return (review_response, len(inline_comments))  # Review posted successfully with summary
        
        # Fall back to individual comments (without summary)
        posted_count = self._post_individual_comments(pr_event, commit_sha, inline_comments)
        return (None, posted_count)  # Review failed, posted individual comments
    
    def _post_individual_comments(
        self,
        pr_event: PREvent,
        commit_sha: str,
        inline_comments: List[Dict]
    ) -> int:
        """
        Post comments individually as fallback.
        Captures GitHub comment IDs and stores them in the inline_comments list.
        """
        self.logger.info(
            "Review failed, falling back to individual comments",
            pr_number=pr_event.pr_number
        )
        posted_count = 0
        failed_count = 0
        for comment in inline_comments:
            try:
                comment_response = self.github_service.post_inline_comment(
                    repository=pr_event.repository,
                    pr_number=pr_event.pr_number,
                    commit_sha=commit_sha,
                    file_path=comment['path'],
                    line_number=comment['line'],
                    comment_body=comment['body']
                )
                self.logger.info("POST_INLINE_COMMENT RETURNED", 
                               response_type=type(comment_response).__name__,
                               response_value=str(comment_response),
                               response_bool=bool(comment_response),
                               path=comment.get('path'),
                               line=comment.get('line'))
                if comment_response:
                    # Store the GitHub comment ID in the comment dict for later tracking
                    comment['github_comment_id'] = str(comment_response.get('id'))
                    self.logger.info("STORED ID IN COMMENT DICT", 
                                   path=comment.get('path'), 
                                   line=comment.get('line'),
                                   stored_id=comment['github_comment_id'])
                    posted_count += 1
                else:
                    # Comment failed to post (returned None from GitHub service)
                    failed_count += 1
                    self.logger.warning(
                        "Failed to post inline comment - line not in diff or invalid",
                        path=comment.get('path'),
                        line=comment.get('line'),
                        agent="pr_comment"
                    )
            except Exception as e:
                failed_count += 1
                self.logger.debug("Failed to post individual comment", 
                                error=str(e),
                                path=comment.get('path'),
                                line=comment.get('line'))
                continue
        
        self.logger.info(
            "Posted individual inline comments",
            pr_number=pr_event.pr_number,
            count=posted_count,
            failed=failed_count,
            attempted=len(inline_comments)
        )
        return posted_count
    
    def _count_issues_by_severity(self, issues: List) -> Dict[str, int]:
        """Count issues by severity level."""
        return {
            'critical': sum(1 for i in issues if str(i.severity.value).lower() == 'critical'),
            'high': sum(1 for i in issues if str(i.severity.value).lower() == 'high'),
            'medium': sum(1 for i in issues if str(i.severity.value).lower() == 'medium'),
            'low': sum(1 for i in issues if str(i.severity.value).lower() == 'low')
        }
    
    def _count_issues_by_type(self, issues: List) -> Dict[str, int]:
        """Count issues by type."""
        return {
            'security': sum(1 for i in issues if str(i.type.value).lower() == 'security'),
            'quality': sum(1 for i in issues if str(i.type.value).lower() == 'quality'),
            'complexity': sum(1 for i in issues if str(i.type.value).lower() == 'complexity')
        }
    
    def _separate_inline_and_contextual_issues(self, issues: List) -> tuple:
        """Separate issues into inline (file-specific) and contextual."""
        inline_issues = [i for i in issues if i.file and i.file != 'N/A' and (i.line or (i.metadata and i.metadata.get('line')))]
        contextual_issues = [i for i in issues if not i.file or i.file == 'N/A']
        return inline_issues, contextual_issues
    
    def _build_summary_header(self, agent_result: AgentResult, severity_counts: Dict[str, int], total_issues: int) -> List[str]:
        """Build the header section of the summary comment."""
        return [
            "## 🤖 Automated Code Review Results",
            "",
            f"**Analysis completed in {agent_result.execution_time:.2f}s**",
            "",
            "### 📊 Summary",
            "",
            f"- **Total Issues Found:** {total_issues}",
            f"  - 🔴 Critical: {severity_counts['critical']}",
            f"  - 🟠 High: {severity_counts['high']}",
            f"  - 🟡 Medium: {severity_counts['medium']}",
            f"  - 🔵 Low: {severity_counts['low']}",
            ""
        ]
    
    def _build_inline_comments_section(self, inline_count: int, inline_severity_counts: Dict[str, int]) -> List[str]:
        """Build the inline comments section."""
        lines = [
            "### 💬 Inline Code Comments",
            "",
            f"**{inline_count} issue(s)** posted as inline comments on code:",
        ]
        
        if inline_count > 0:
            lines.extend([
                f"  - 🔴 Critical: {inline_severity_counts['critical']}",
                f"  - 🟠 High: {inline_severity_counts['high']}",
                f"  - 🟡 Medium: {inline_severity_counts['medium']}",
                f"  - 🔵 Low: {inline_severity_counts['low']}",
                "",
                "*See inline comments below on specific code lines.*",
            ])
        else:
            lines.append("  - No issues found in the changed code.")
        
        lines.append("")
        return lines
    
    def _build_contextual_observations_section(self, contextual_issues: List) -> List[str]:
        """Build the contextual observations section."""
        if not contextual_issues:
            return []
        
        lines = [
            "### 🔍 Contextual Observations",
            "",
            f"**{len(contextual_issues)} observation(s)** about this PR:",
            ""
        ]
        
        severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}
        for issue in contextual_issues:
            emoji = severity_emoji.get(str(issue.severity.value).lower(), '⚪')
            lines.append(f"- {emoji} **{issue.message}**")
            if issue.suggestion:
                lines.append(f"  - 💡 {issue.suggestion}")
        lines.append("")
        return lines
    
    def _build_summary_comment(self, agent_result: AgentResult) -> str:
        """Build the main summary comment."""
        # Get issues from agent_result.issues (primary) or fallback to metadata
        issues = agent_result.issues if hasattr(agent_result, 'issues') and agent_result.issues else agent_result.metadata.get('all_issues', [])
        
        self.logger.info(
            "Building summary comment",
            issue_count=len(issues),
            has_issues=bool(issues),
            agent_name=agent_result.agent_name
        )
        
        # Count by severity and type
        severity_counts = self._count_issues_by_severity(issues)
        type_counts = self._count_issues_by_type(issues)
        
        self.logger.info("Issue counts by severity", **severity_counts)
        
        # Separate inline issues from contextual issues
        inline_issues, contextual_issues = self._separate_inline_and_contextual_issues(issues)
        inline_severity_counts = self._count_issues_by_severity(inline_issues)
        
        # Build comment sections
        lines = self._build_summary_header(agent_result, severity_counts, len(issues))
        lines.extend(self._build_inline_comments_section(len(inline_issues), inline_severity_counts))
        lines.extend(self._build_issue_breakdown_section(type_counts))
        lines.extend(self._build_contextual_observations_section(contextual_issues))
        lines.extend(self._build_rag_insights_section(agent_result))
        lines.extend(self._build_action_required_section(severity_counts))
        lines.extend([
            "---",
            "*This is an automated review. Please review the inline comments for specific details.*"
        ])
        
        return "\n".join(lines)
    
    def _build_issue_breakdown_section(self, type_counts: Dict[str, int]) -> List[str]:
        """Build the issue breakdown section."""
        return [
            "### 🔍 Issue Breakdown",
            "",
            f"- 🛡️ Security Issues: {type_counts['security']}",
            f"- 💎 Code Quality Issues: {type_counts['quality']}",
            f"- 🔧 Complexity Issues: {type_counts['complexity']}",
            ""
        ]
    
    def _build_rag_insights_section(self, agent_result: AgentResult) -> List[str]:
        """Build the RAG AI-powered insights section."""
        if not self.include_rag_insights:
            return []
        
        rag_metadata = agent_result.metadata.get('rag_insights', {})
        if not rag_metadata:
            return []
        
        lines = [
            "### 🧠 AI-Powered Insights",
            "",
            f"- **Novelty Score:** {rag_metadata.get('novelty_score', 0):.2f} (Higher = More unique)",
            f"- **Risk Score:** {rag_metadata.get('risk_score', 0):.2f} (Higher = More risky)",
            f"- **Similar PRs Found:** {rag_metadata.get('similar_prs_count', 0)}",
            ""
        ]
        
        # Add learned patterns if available
        learned_patterns = rag_metadata.get('learned_patterns', [])
        if learned_patterns:
            lines.append("**Learned Patterns:**")
            for pattern in learned_patterns:
                lines.append(f"- {pattern}")
            lines.append("")
        
        # Add RAG recommendations if available
        lines.extend(self._format_rag_recommendations(rag_metadata.get('recommendations', '')))
        
        return lines
    
    def _format_rag_recommendations(self, recommendations: str) -> List[str]:
        """Format RAG recommendations, removing duplicates."""
        if not recommendations:
            return []
        
        lines = ["**Key Recommendations:**"]
        
        # Split by newlines and filter out empty lines and duplicates
        rec_lines = [line.strip() for line in recommendations.split('\n') if line.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recs = []
        for rec in rec_lines:
            # Normalize the line (remove leading - or * if present)
            normalized = rec.lstrip('- *').strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_recs.append(rec if rec.startswith(('-', '*')) else f"- {rec}")
        
        # Add top 3 unique recommendations
        for rec in unique_recs[:3]:
            lines.append(rec)
        lines.append("")
        
        return lines
    
    def _build_action_required_section(self, severity_counts: Dict[str, int]) -> List[str]:
        """Build the action required / next steps section."""
        critical = severity_counts['critical']
        high = severity_counts['high']
        
        if critical > 0:
            return [
                "### ⚠️ Action Required",
                "",
                f"This PR has **{critical} critical issue(s)** that should be addressed before merging.",
                ""
            ]
        
        if high > 0:
            return [
                "### 💡 Recommendations",
                "",
                f"Consider addressing the **{high} high-priority issue(s)** for better code quality.",
                ""
            ]
        
        return [
            "### ✅ Looking Good!",
            "",
            "No critical or high-priority issues found. Review the inline comments for minor improvements.",
            ""
        ]

    
    def _build_inline_comments(self, agent_result: AgentResult) -> List[Dict]:
        """Build list of inline comments for specific lines."""
        # Get all issues from the agent_result
        issues = agent_result.issues if hasattr(agent_result, 'issues') else []
        
        # Also check metadata for all_issues (fallback)
        if not issues:
            issues = agent_result.metadata.get('all_issues', [])
        
        self.logger.info("Building inline comments from issues", issue_count=len(issues), agent="pr_comment")
        
        comments = []
        
        # Filter by severity threshold
        threshold = self.severity_levels.get(self.severity_threshold, 0)
        self.logger.info("Severity threshold", threshold_name=self.severity_threshold, threshold_value=threshold, agent="pr_comment")
        
        for issue in issues:
            # Check severity threshold
            issue_severity = self.severity_levels.get(issue.severity.name, 0)
            if issue_severity < threshold:
                self.logger.debug("Skipping issue due to severity", issue_severity=issue.severity.name, threshold=self.severity_threshold)
                continue
            
            # Only add issues with file and line information
            if not issue.file or issue.file == 'N/A':
                self.logger.debug("Skipping issue without file", file=issue.file)
                continue
            
            # Try to extract line number from issue
            line_number = self._extract_line_number(issue)
            if not line_number:
                self.logger.debug("Skipping issue without line number", file=issue.file)
                continue
            
            # Validate line number is reasonable (GitHub API limitation)
            if not self._is_valid_line_number(line_number):
                self.logger.warning(
                    "Skipping issue with invalid line number",
                    file=issue.file,
                    line=line_number,
                    agent="pr_comment"
                )
                continue
            
            # Build comment body
            comment_body = self._format_inline_comment(issue)
            
            comments.append({
                'path': issue.file,
                'line': line_number,
                'body': comment_body,
                'side': 'RIGHT',
                'severity': issue.severity.name,
                'type': issue.type.name
            })
        
        self.logger.info("Built inline comments", count=len(comments), agent="pr_comment")
        return comments
    
    def _is_valid_line_number(self, line_number: int) -> bool:
        """
        Validate if line number is reasonable.
        GitHub API only allows comments on lines that are part of the diff.
        This is a basic sanity check - actual validation happens when posting.
        """
        if line_number is None:
            return False
        if line_number < 1:
            return False
        # Reject obviously invalid line numbers (files rarely exceed 10000 lines in PRs)
        if line_number > 10000:
            return False
        return True
    
    def _extract_line_number(self, issue: Issue) -> Optional[int]:
        """Extract line number from issue metadata."""
        # Check metadata for line number
        if issue.metadata and 'line' in issue.metadata:
            return issue.metadata['line']
        
        # Check if line is mentioned in message
        if issue.line:
            return issue.line
        
        # Default to line 1 if no line specified
        return 1
    
    def _format_inline_comment(self, issue: Issue) -> str:
        """Format an individual inline comment."""
        # Emoji mapping
        severity_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🔵',
            'INFO': 'ℹ️'
        }
        
        type_emoji = {
            'SECURITY': '🛡️',
            'CODE_QUALITY': '💎',
            'COMPLEXITY': '🔄',
            'STYLE': '🎨',
            'CONTEXT': '📋',
            'COVERAGE': '📊'
        }
        
        lines = [
            f"## {severity_emoji.get(issue.severity.name, '⚠️')} {type_emoji.get(issue.type.name, '🔍')} {issue.type.name.replace('_', ' ').title()}",
            "",
            f"**Severity:** {issue.severity.name}",
            "",
            issue.message,
        ]
        
        if issue.suggestion:
            lines.extend([
                "",
                "**💡 Suggestion:**",
                issue.suggestion
            ])
        
        # Add metadata if useful
        if issue.metadata:
            useful_metadata = {k: v for k, v in issue.metadata.items() 
                             if k not in ['line', 'file'] and v is not None}
            if useful_metadata:
                lines.extend([
                    "",
                    "**Additional Info:**",
                ])
                for key, value in useful_metadata.items():
                    lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def _build_review_body(self, agent_result: AgentResult, comment_count: int) -> str:
        """Build the main review body text."""
        issues = agent_result.issues if hasattr(agent_result, 'issues') and agent_result.issues else []
        critical = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        high = sum(1 for i in issues if i.severity == Severity.HIGH)
        
        lines = [
            "## 🤖 Automated Code Review",
            "",
            f"I've analyzed this PR and found {len(issues)} issue(s).",
            f"Posted {comment_count} inline comment(s) on specific lines.",
            ""
        ]
        
        if critical > 0:
            lines.append(f"⚠️ **{critical} critical issue(s) require immediate attention.**")
        elif high > 0:
            lines.append(f"💡 **{high} high-priority issue(s) should be reviewed.**")
        else:
            lines.append("✅ No critical issues found. Review the comments for improvements.")
        
        return "\n".join(lines)
    
    def _determine_review_event(self) -> str:
        """
        Determine the review event type based on findings.
        
        Returns:
            'COMMENT' for all cases (REQUEST_CHANGES disabled to avoid blocking PRs)
        """
        # Always use COMMENT to avoid blocking PRs
        # In the future, could implement logic like:
        # if agent_result.critical_count > 0:
        #     return 'REQUEST_CHANGES'
        return 'COMMENT'
    
    def _prioritize_comments(self, comments: List[Dict]) -> List[Dict]:
        """Prioritize comments by severity."""
        severity_order = {
            'CRITICAL': 0,
            'HIGH': 1,
            'MEDIUM': 2,
            'LOW': 3,
            'INFO': 4
        }
        
        return sorted(
            comments,
            key=lambda c: severity_order.get(c.get('severity', 'INFO'), 5)
        )
    
    def _create_summary_comment_record(
        self,
        pr_event: PREvent,
        pr_analysis_id: int,
        agent_result: AgentResult,
        commit_sha: str,
        review_event: str,
        github_comment_id: Optional[str],
        github_review_id: Optional[str]
    ):
        """Create a PRComment record for summary comment."""
        from models.database import PRComment
        
        summary_text = self._build_summary_comment(agent_result)
        
        # Build GitHub URL for the comment
        github_url = None
        if github_comment_id:
            github_url = f"https://github.com/{pr_event.repository}/pull/{pr_event.pr_number}#issuecomment-{github_comment_id}"
        
        return PRComment(
            pr_analysis_id=pr_analysis_id,
            comment_type='summary',
            comment_body=summary_text,
            comment_preview=summary_text[:200] if summary_text else '',
            commit_sha=commit_sha,
            posted_successfully=True,
            review_event=review_event if github_review_id else None,
            github_comment_id=github_comment_id,
            github_review_id=github_review_id,
            github_url=github_url,
            agent_version='1.0.0',
            config_used=self.config,
            posted_at=datetime.now(timezone.utc)
        )
    
    def _create_inline_comment_record(
        self,
        pr_event: PREvent,
        pr_analysis_id: int,
        comment: Dict,
        commit_sha: str,
        review_event: str,
        github_review_id: Optional[str]
    ):
        """Create a PRComment record for inline comment."""
        from models.database import PRComment
        
        inline_github_comment_id = comment.get('github_comment_id')
        
        self.logger.info(
            "TRACKING INLINE - comment data",
            path=comment.get('path'),
            line=comment.get('line'),
            github_comment_id=inline_github_comment_id
        )
        
        # Build GitHub URL for inline comment
        github_url = None
        if inline_github_comment_id:
            github_url = f"https://github.com/{pr_event.repository}/pull/{pr_event.pr_number}#discussion_r{inline_github_comment_id}"
        
        return PRComment(
            pr_analysis_id=pr_analysis_id,
            comment_type='inline',
            file_path=comment.get('path'),
            line_number=comment.get('line'),
            comment_body=comment.get('body', ''),
            comment_preview=comment.get('body', '')[:200],
            commit_sha=commit_sha,
            issue_severity=comment.get('severity'),
            issue_type=comment.get('type'),
            posted_successfully=True,
            review_event=review_event,
            github_comment_id=inline_github_comment_id,
            github_review_id=github_review_id,
            github_url=github_url,
            agent_version='1.0.0',
            config_used=self.config,
            posted_at=datetime.now(timezone.utc)
        )
    
    def _track_comments_in_database(
        self,
        pr_event: PREvent,
        pr_analysis_id: int,
        agent_result: AgentResult,
        summary_posted: bool,
        inline_comments: List[Dict],
        review_event: str,
        commit_sha: str,
        github_comment_id: Optional[str] = None,
        github_review_id: Optional[str] = None
    ):
        """
        Track posted comments in database for analytics.
        
        Args:
            pr_event: The PR event (for repository and PR number)
            pr_analysis_id: Database ID of the PR analysis
            agent_result: Analysis results
            summary_posted: Whether summary was posted
            inline_comments: List of inline comments posted
            review_event: Review type (COMMENT, REQUEST_CHANGES)
            commit_sha: Commit SHA
            github_comment_id: GitHub comment ID (for summary comments)
            github_review_id: GitHub review ID (for review with inline comments)
        """
        self.logger.info(
            "TRACKING DEBUG - Entry",
            track_in_database=self.track_in_database,
            db_service_exists=self.db_service is not None,
            pr_analysis_id=pr_analysis_id,
            summary_posted=summary_posted,
            inline_count=len(inline_comments) if inline_comments else 0,
            github_comment_id=github_comment_id,
            github_review_id=github_review_id
        )
        
        if not self.track_in_database or not self.db_service:
            self.logger.warning(
                "TRACKING SKIPPED - Early return",
                track_in_database=self.track_in_database,
                db_service_exists=self.db_service is not None
            )
            return
        
        try:
            comments_to_track = []
            
            # Always track summary comment in database (even if not posted to GitHub)
            # This ensures we have a record of all analysis results
            summary_record = self._create_summary_comment_record(
                pr_event, pr_analysis_id, agent_result, commit_sha,
                review_event, github_comment_id if summary_posted else None, 
                github_review_id
            )
            comments_to_track.append(summary_record)
            
            # Always track inline comments in database (even if not posted to GitHub)
            for comment in inline_comments:
                inline_record = self._create_inline_comment_record(
                    pr_event, pr_analysis_id, comment, commit_sha,
                    review_event, github_review_id
                )
                comments_to_track.append(inline_record)
            
            # Save to database using UPSERT logic (update if exists, insert if new)
            if comments_to_track:
                self._upsert_comments_to_database(pr_analysis_id, comments_to_track)
                    
        except Exception as e:
            self.logger.error("Error tracking comments", error=str(e), exc_info=True)
    
    def _upsert_comments_to_database(self, pr_analysis_id: int, comments_to_track: list):
        """
        Insert or update comments in database.
        Updates existing comments instead of creating duplicates.
        Uniqueness based on: pr_analysis_id + comment_type + file_path + line_number
        """
        from models.database import PRComment
        from sqlalchemy import and_
        
        with self.db_service.get_session() as session:
            try:
                inserted_count = 0
                updated_count = 0
                
                for comment in comments_to_track:
                    # Build query to find existing comment
                    query = session.query(PRComment).filter(
                        and_(
                            PRComment.pr_analysis_id == comment.pr_analysis_id,
                            PRComment.comment_type == comment.comment_type
                        )
                    )
                    
                    # Add file/line filters for inline comments
                    if comment.comment_type == 'inline' and comment.file_path:
                        query = query.filter(
                            and_(
                                PRComment.file_path == comment.file_path,
                                PRComment.line_number == comment.line_number
                            )
                        )
                    
                    existing = query.first()
                    
                    if existing:
                        # Update existing comment
                        existing.comment_body = comment.comment_body
                        existing.comment_preview = comment.comment_preview
                        existing.commit_sha = comment.commit_sha
                        existing.issue_severity = comment.issue_severity
                        existing.issue_type = comment.issue_type
                        existing.github_comment_id = comment.github_comment_id
                        existing.github_review_id = comment.github_review_id
                        existing.posted_successfully = comment.posted_successfully
                        existing.last_checked_at = datetime.now(timezone.utc)
                        updated_count += 1
                        self.logger.debug(
                            "Updating existing comment",
                            pr_analysis_id=pr_analysis_id,
                            comment_type=comment.comment_type,
                            file_path=comment.file_path,
                            line=comment.line_number
                        )
                    else:
                        # Insert new comment
                        session.add(comment)
                        inserted_count += 1
                        self.logger.debug(
                            "Inserting new comment",
                            pr_analysis_id=pr_analysis_id,
                            comment_type=comment.comment_type,
                            file_path=comment.file_path,
                            line=comment.line_number
                        )
                
                session.commit()
                self.logger.info(
                    "Tracked comments in database",
                    pr_analysis_id=pr_analysis_id,
                    inserted=inserted_count,
                    updated=updated_count,
                    total=len(comments_to_track)
                )
            except Exception as e:
                session.rollback()
                self.logger.error("Failed to track comments in database", error=str(e))


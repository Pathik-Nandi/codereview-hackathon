"""Analytics service for generating insights and best practices recommendations."""
from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from models.database import PRAnalysis, PRIssue, PRMetrics, UserStatistics, BestPractice
from services.database_service import DatabaseService
from utils.logger import logger


class AnalyticsService:
    """Service for analyzing PR data and generating insights."""
    
    # Category constants
    CATEGORY_CODE_QUALITY = 'code_quality'
    CATEGORY_SECURITY = 'security'
    CATEGORY_MAINTAINABILITY = 'maintainability'
    
    def __init__(self, db_service: DatabaseService):
        """Initialize analytics service."""
        self.db_service = db_service
    
    def get_user_insights(self, author_login: str) -> Dict[str, Any]:
        """
        Generate comprehensive insights for a user based on their PR history.
        
        Returns:
            Dictionary with best practices, bad practices, quality scores, 
            improvement areas, and metrics.
        """
        with self.db_service.get_session() as session:
            # Get user statistics
            user_stats = session.query(UserStatistics).filter_by(
                author_login=author_login
            ).first()
            
            if not user_stats:
                return {
                    'error': 'No data found for user',
                    'author_login': author_login
                }
            
            # Get recent PRs
            recent_prs = session.query(PRAnalysis).filter_by(
                author_login=author_login
            ).order_by(desc(PRAnalysis.analyzed_at)).limit(50).all()
            
            if not recent_prs:
                return {
                    'error': 'No PRs found for user',
                    'author_login': author_login
                }
            
            # Analyze patterns
            insights = {
                'author_login': author_login,
                'author_email': user_stats.author_email,
                'summary': self._generate_summary(user_stats, recent_prs),
                'quality_scores': self._calculate_quality_scores(user_stats, recent_prs),
                'best_practices': self._identify_best_practices(recent_prs, session),
                'bad_practices': self._identify_bad_practices(recent_prs, session),
                'improvement_areas': self._identify_improvement_areas(recent_prs, session),
                'strengths': self._identify_strengths(recent_prs, session),
                'trends': self._calculate_trends(recent_prs),
                'metrics': self._calculate_metrics(recent_prs, session),
                'recommendations': self._generate_recommendations(recent_prs, session),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            return insights
    
    def _generate_summary(self, user_stats: UserStatistics, _recent_prs: List[PRAnalysis]) -> Dict[str, Any]:
        """Generate high-level summary.
        
        Args:
            user_stats: User statistics
            _recent_prs: Recent PRs (unused, reserved for future use)
        """
        return {
            'total_prs_analyzed': user_stats.total_prs,
            'total_issues_found': user_stats.total_issues_found,
            'average_issues_per_pr': round(user_stats.total_issues_found / user_stats.total_prs, 2) if user_stats.total_prs > 0 else 0,
            'date_range': {
                'first_pr': user_stats.first_pr_date.isoformat() if user_stats.first_pr_date else None,
                'last_pr': user_stats.last_pr_date.isoformat() if user_stats.last_pr_date else None
            },
            'overall_quality_rating': self._get_quality_rating(user_stats.avg_quality_score),
            'security_rating': self._get_quality_rating(user_stats.avg_security_score),
            'maintainability_rating': self._get_quality_rating(user_stats.avg_maintainability_score)
        }
    
    def _get_quality_rating(self, score: Optional[float]) -> str:
        """Convert numeric score to rating."""
        if score is None:
            return "Unknown"
        if score >= 90:
            return "Excellent"
        if score >= 80:
            return "Good"
        if score >= 70:
            return "Fair"
        if score >= 60:
            return "Poor"
        return "Critical"
    
    def _calculate_quality_scores(self, user_stats: UserStatistics, recent_prs: List[PRAnalysis]) -> Dict[str, Any]:
        """Calculate various quality scores."""
        return {
            'overall_quality_score': round(user_stats.avg_quality_score or 0, 2),
            'security_score': round(user_stats.avg_security_score or 0, 2),
            'maintainability_score': round(user_stats.avg_maintainability_score or 0, 2),
            'coverage_score': round(user_stats.avg_coverage or 0, 2),
            'complexity_score': round(user_stats.avg_complexity or 0, 2) if user_stats.avg_complexity else 0,
            'severity_distribution': {
                'critical': user_stats.critical_issues_total,
                'high': user_stats.high_issues_total,
                'medium': user_stats.medium_issues_total,
                'low': user_stats.low_issues_total
            },
            'best_pr_quality': max((pr.overall_quality_score or 0) for pr in recent_prs) if recent_prs else 0,
            'worst_pr_quality': min((pr.overall_quality_score or 0) for pr in recent_prs) if recent_prs else 0
        }
    
    def _identify_best_practices(self, recent_prs: List[PRAnalysis], _session: Session) -> List[Dict[str, Any]]:
        """Identify practices the user is doing well.
        
        Args:
            recent_prs: Recent PRs to analyze
            _session: Database session (unused, reserved for future use)
        """
        best_practices = []
        
        # Check security practices
        security_scores = [pr.security_score for pr in recent_prs if pr.security_score]
        if security_scores and sum(security_scores) / len(security_scores) >= 85:
            best_practices.append({
                'category': 'Security',
                'practice': 'Strong Security Practices',
                'description': 'You consistently avoid security vulnerabilities in your code.',
                'score': round(sum(security_scores) / len(security_scores), 2),
                'priority': 'high'
            })
        
        # Check code coverage
        coverage_scores = [pr.estimated_coverage for pr in recent_prs if pr.estimated_coverage]
        if coverage_scores and sum(coverage_scores) / len(coverage_scores) >= 80:
            best_practices.append({
                'category': 'Testing',
                'practice': 'Good Test Coverage',
                'description': 'You maintain high test coverage in your PRs.',
                'score': round(sum(coverage_scores) / len(coverage_scores), 2),
                'priority': 'high'
            })
        
        # Check for low critical/high severity issues
        critical_issues = sum(pr.critical_issues for pr in recent_prs)
        high_issues = sum(pr.high_issues for pr in recent_prs)
        
        if critical_issues == 0 and high_issues < len(recent_prs):
            best_practices.append({
                'category': self.CATEGORY_CODE_QUALITY,
                'practice': 'Low Critical Issues',
                'description': 'You avoid critical and high-severity code issues.',
                'score': 100,
                'priority': 'high'
            })
        
        # Check PR size (smaller is better)
        avg_files_changed = sum(pr.files_changed for pr in recent_prs) / len(recent_prs) if recent_prs else 0
        if avg_files_changed < 10:
            best_practices.append({
                'category': 'Process',
                'practice': 'Small, Focused PRs',
                'description': 'You create small, manageable pull requests that are easier to review.',
                'score': 100,
                'priority': 'medium'
            })
        
        return best_practices
    
    def _identify_bad_practices(self, recent_prs: List[PRAnalysis], session: Session) -> List[Dict[str, Any]]:
        """Identify practices the user should avoid."""
        bad_practices = []
        
        # Collect all issues across PRs
        all_issues = []
        for pr in recent_prs:
            issues = session.query(PRIssue).filter_by(pr_analysis_id=pr.id).all()
            all_issues.extend(issues)
        
        # Count issue types
        issue_type_counts = Counter(issue.issue_type for issue in all_issues)
        
        # Identify most common bad practices
        for issue_type, count in issue_type_counts.most_common(10):
            if count >= 5:  # Only report if appears 5+ times
                bad_practices.append({
                    'category': self._get_issue_category(issue_type),
                    'practice': self._format_issue_type(issue_type),
                    'description': self._get_issue_description(issue_type),
                    'occurrences': count,
                    'priority': self._get_issue_priority(issue_type, count),
                    'recommendation': self._get_issue_recommendation(issue_type)
                })
        
        return bad_practices
    
    def _identify_improvement_areas(self, recent_prs: List[PRAnalysis], _session: Session) -> List[Dict[str, Any]]:
        """Identify specific areas where user can improve.
        
        Args:
            recent_prs: Recent PRs to analyze
            _session: Database session (unused, reserved for future use)
        """
        improvement_areas = []
        
        # Check security score
        security_scores = [pr.security_score for pr in recent_prs if pr.security_score]
        if security_scores and sum(security_scores) / len(security_scores) < 80:
            improvement_areas.append({
                'area': 'Security',
                'current_score': round(sum(security_scores) / len(security_scores), 2),
                'target_score': 90,
                'priority': 'critical',
                'actions': [
                    'Review security best practices for input validation',
                    'Avoid hardcoding sensitive information',
                    'Use parameterized queries to prevent SQL injection',
                    'Implement proper authentication and authorization'
                ]
            })
        
        # Check code coverage
        coverage_scores = [pr.estimated_coverage for pr in recent_prs if pr.estimated_coverage]
        if coverage_scores and sum(coverage_scores) / len(coverage_scores) < 70:
            improvement_areas.append({
                'area': 'Test Coverage',
                'current_score': round(sum(coverage_scores) / len(coverage_scores), 2),
                'target_score': 80,
                'priority': 'high',
                'actions': [
                    'Write unit tests for new features',
                    'Add integration tests for critical paths',
                    'Cover edge cases and error handling',
                    'Aim for at least 80% code coverage'
                ]
            })
        
        # Check code quality
        quality_scores = [pr.overall_quality_score for pr in recent_prs if pr.overall_quality_score]
        if quality_scores and sum(quality_scores) / len(quality_scores) < 75:
            improvement_areas.append({
                'area': self.CATEGORY_CODE_QUALITY,
                'current_score': round(sum(quality_scores) / len(quality_scores), 2),
                'target_score': 85,
                'priority': 'high',
                'actions': [
                    'Reduce code complexity and nesting levels',
                    'Break down long methods into smaller functions',
                    'Eliminate magic numbers and use named constants',
                    'Follow language-specific style guides'
                ]
            })
        
        # Check for high complexity
        avg_complexity = sum(pr.complexity_score for pr in recent_prs if pr.complexity_score) / len(recent_prs) if recent_prs else 0
        if avg_complexity > 20:
            improvement_areas.append({
                'area': 'Code Complexity',
                'current_score': round(avg_complexity, 2),
                'target_score': 15,
                'priority': 'medium',
                'actions': [
                    'Simplify complex conditional logic',
                    'Extract methods to reduce cyclomatic complexity',
                    'Use early returns to reduce nesting',
                    'Consider design patterns for complex logic'
                ]
            })
        
        return improvement_areas
    
    def _identify_strengths(self, recent_prs: List[PRAnalysis], _session: Session) -> List[str]:
        """Identify user's strengths.
        
        Args:
            recent_prs: Recent PRs to analyze
            _session: Database session (unused, reserved for future use)
        """
        strengths = []
        
        # Analyze patterns
        security_scores = [pr.security_score for pr in recent_prs if pr.security_score]
        quality_scores = [pr.overall_quality_score for pr in recent_prs if pr.overall_quality_score]
        coverage_scores = [pr.estimated_coverage for pr in recent_prs if pr.estimated_coverage]
        
        if security_scores and sum(security_scores) / len(security_scores) >= 90:
            strengths.append("Excellent security awareness - consistently avoids vulnerabilities")
        
        if quality_scores and sum(quality_scores) / len(quality_scores) >= 85:
            strengths.append("High code quality standards - writes clean, maintainable code")
        
        if coverage_scores and sum(coverage_scores) / len(coverage_scores) >= 80:
            strengths.append("Strong testing practices - maintains good test coverage")
        
        # Check for consistent improvement
        if len(quality_scores) >= 10:
            recent_avg = sum(quality_scores[-5:]) / 5
            older_avg = sum(quality_scores[-10:-5]) / 5
            if recent_avg > older_avg + 5:
                strengths.append("Continuous improvement - quality scores trending upward")
        
        # Check for low critical issues
        total_critical = sum(pr.critical_issues for pr in recent_prs)
        if total_critical == 0:
            strengths.append("Zero critical issues - demonstrates careful code review before submission")
        
        return strengths if strengths else ["Keep analyzing more PRs to identify strengths"]
    
    def _calculate_trends(self, recent_prs: List[PRAnalysis]) -> Dict[str, Any]:
        """Calculate trends over time."""
        if len(recent_prs) < 5:
            return {'status': 'Insufficient data for trend analysis'}
        
        # Split into recent and older
        mid_point = len(recent_prs) // 2
        recent_half = recent_prs[:mid_point]
        older_half = recent_prs[mid_point:]
        
        # Calculate averages
        recent_quality = sum(pr.overall_quality_score or 0 for pr in recent_half) / len(recent_half)
        older_quality = sum(pr.overall_quality_score or 0 for pr in older_half) / len(older_half)
        
        recent_security = sum(pr.security_score or 0 for pr in recent_half) / len(recent_half)
        older_security = sum(pr.security_score or 0 for pr in older_half) / len(older_half)
        
        recent_coverage = sum(pr.estimated_coverage or 0 for pr in recent_half) / len(recent_half)
        older_coverage = sum(pr.estimated_coverage or 0 for pr in older_half) / len(older_half)
        
        return {
            'quality_trend': self._get_trend_direction(recent_quality, older_quality),
            'security_trend': self._get_trend_direction(recent_security, older_security),
            'coverage_trend': self._get_trend_direction(recent_coverage, older_coverage),
            'quality_change': round(recent_quality - older_quality, 2),
            'security_change': round(recent_security - older_security, 2),
            'coverage_change': round(recent_coverage - older_coverage, 2)
        }
    
    def _get_trend_direction(self, recent: float, older: float) -> str:
        """Determine trend direction."""
        diff = recent - older
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def _calculate_metrics(self, recent_prs: List[PRAnalysis], _session: Session) -> Dict[str, Any]:
        """Calculate detailed metrics.
        
        Args:
            recent_prs: Recent PRs to analyze
            _session: Database session (unused, reserved for future use)
        """
        return {
            'total_prs': len(recent_prs),
            'total_issues': sum(pr.total_issues for pr in recent_prs),
            'avg_issues_per_pr': round(sum(pr.total_issues for pr in recent_prs) / len(recent_prs), 2) if recent_prs else 0,
            'avg_files_changed': round(sum(pr.files_changed for pr in recent_prs) / len(recent_prs), 2) if recent_prs else 0,
            'avg_lines_changed': round(sum((pr.lines_added + pr.lines_deleted) for pr in recent_prs) / len(recent_prs), 2) if recent_prs else 0,
            'agent_breakdown': {
                'static_analysis': sum(pr.static_analysis_issues for pr in recent_prs),
                'security': sum(pr.security_issues for pr in recent_prs),
                'code_quality': sum(pr.code_quality_issues for pr in recent_prs),
                'context': sum(pr.context_issues for pr in recent_prs),
                'coverage': sum(pr.coverage_issues for pr in recent_prs)
            },
            'most_active_repository': self._get_most_active_repo(recent_prs)
        }
    
    def _get_most_active_repo(self, recent_prs: List[PRAnalysis]) -> Optional[str]:
        """Get repository with most PRs."""
        if not recent_prs:
            return None
        repo_counts = Counter(pr.repository for pr in recent_prs)
        return repo_counts.most_common(1)[0][0] if repo_counts else None
    
    def _generate_recommendations(self, recent_prs: List[PRAnalysis], session: Session) -> List[Dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Collect all issues
        all_issues = []
        for pr in recent_prs:
            issues = session.query(PRIssue).filter_by(pr_analysis_id=pr.id).all()
            all_issues.extend(issues)
        
        # Group by issue type
        issue_type_counts = Counter(issue.issue_type for issue in all_issues)
        
        # Generate recommendations for top issues
        for issue_type, count in issue_type_counts.most_common(5):
            recommendations.append({
                'issue_type': self._format_issue_type(issue_type),
                'occurrences': count,
                'priority': self._get_issue_priority(issue_type, count),
                'recommendation': self._get_issue_recommendation(issue_type),
                'resources': self._get_learning_resources(issue_type)
            })
        
        return recommendations
    
    def _get_issue_category(self, issue_type: str) -> str:
        """Get category for issue type."""
        security_types = ['hardcoded_secret', 'sql_injection', 'command_injection', 'weak_crypto', 'xxe']
        quality_types = ['magic_number', 'deep_nesting', 'long_method', 'complex_boolean']
        testing_types = ['low_coverage', 'missing_tests', 'no_test_methods']
        
        issue_lower = issue_type.lower()
        if any(s in issue_lower for s in security_types):
            return 'Security'
        elif any(q in issue_lower for q in quality_types):
            return self.CATEGORY_CODE_QUALITY
        elif any(t in issue_lower for t in testing_types):
            return 'Testing'
        else:
            return 'General'
    
    def _format_issue_type(self, issue_type: str) -> str:
        """Format issue type for display."""
        return issue_type.replace('_', ' ').title()
    
    def _get_issue_description(self, issue_type: str) -> str:
        """Get description for issue type."""
        descriptions = {
            'MAGIC_NUMBER': 'Using hardcoded numeric literals without named constants',
            'DEEP_NESTING': 'Excessive nesting levels making code hard to read',
            'LONG_METHOD': 'Methods that are too long and should be broken down',
            'HARDCODED_SECRET': 'Sensitive information hardcoded in source code',
            'SQL_INJECTION': 'Potential SQL injection vulnerabilities',
            'NO_SYSTEM_OUT': 'Using System.out.println instead of proper logging',
            'TODO_COMMENT': 'Unresolved TODO comments in code',
            'LOW_COVERAGE': 'Insufficient test coverage for code changes',
            'HIGH_COMPLEXITY': 'High cyclomatic complexity indicating complex logic'
        }
        return descriptions.get(issue_type, 'Code quality or security issue detected')
    
    def _get_issue_priority(self, issue_type: str, count: int) -> str:
        """Determine priority based on issue type and frequency."""
        security_types = ['hardcoded_secret', 'sql_injection', 'command_injection']
        
        if any(s in issue_type.lower() for s in security_types):
            return 'critical'
        elif count >= 20:
            return 'high'
        elif count >= 10:
            return 'medium'
        else:
            return 'low'
    
    def _get_issue_recommendation(self, issue_type: str) -> str:
        """Get recommendation for issue type."""
        recommendations = {
            'MAGIC_NUMBER': 'Define named constants for numeric values to improve code readability',
            'DEEP_NESTING': 'Refactor code to reduce nesting levels, use early returns and extract methods',
            'LONG_METHOD': 'Break down long methods into smaller, single-responsibility functions',
            'HARDCODED_SECRET': 'Use environment variables or secure vaults for sensitive information',
            'SQL_INJECTION': 'Use parameterized queries or ORM to prevent SQL injection',
            'NO_SYSTEM_OUT': 'Replace System.out.println with proper logging framework (SLF4J, Log4j)',
            'TODO_COMMENT': 'Create tickets for TODO items and resolve them before merging',
            'LOW_COVERAGE': 'Add unit tests to increase coverage to at least 80%',
            'HIGH_COMPLEXITY': 'Simplify complex logic by extracting methods and reducing conditionals'
        }
        return recommendations.get(issue_type, 'Review and refactor this code pattern')
    
    def _get_learning_resources(self, issue_type: str) -> List[str]:
        """Get learning resources for issue type."""
        resources = {
            'MAGIC_NUMBER': [
                'Clean Code by Robert Martin - Chapter on Meaningful Names',
                'Refactoring: Replace Magic Number with Symbolic Constant'
            ],
            'DEEP_NESTING': [
                'Refactoring: Replace Nested Conditional with Guard Clauses',
                'Clean Code: Functions Should Do One Thing'
            ],
            'HARDCODED_SECRET': [
                'OWASP: Sensitive Data Exposure',
                '12-Factor App: Store config in environment'
            ],
            'SQL_INJECTION': [
                'OWASP Top 10: Injection Flaws',
                'Parameterized Queries Tutorial'
            ]
        }
        return resources.get(issue_type, ['Search for best practices related to this issue'])
    
    def get_repository_insights(self, repository: str) -> Dict[str, Any]:
        """Generate insights for an entire repository."""
        with self.db_service.get_session() as session:
            prs = session.query(PRAnalysis).filter_by(repository=repository).all()
            
            if not prs:
                return {'error': 'No data found for repository', 'repository': repository}
            
            return {
                'repository': repository,
                'summary': {
                    'total_prs': len(prs),
                    'total_issues': sum(pr.total_issues for pr in prs),
                    'avg_quality_score': round(sum(pr.overall_quality_score or 0 for pr in prs) / len(prs), 2),
                    'unique_contributors': len({pr.author_login for pr in prs})
                },
                'top_contributors': self._get_top_contributors(prs),
                'common_issues': self._get_most_common_issues_for_repo(session, repository),
                'quality_trends': self._calculate_repo_trends(prs),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _get_top_contributors(self, prs: List[PRAnalysis]) -> List[Dict[str, Any]]:
        """Get top contributors by PR count."""
        contributor_counts = Counter(pr.author_login for pr in prs)
        
        top_contributors = []
        for login, count in contributor_counts.most_common(10):
            user_prs = [pr for pr in prs if pr.author_login == login]
            top_contributors.append({
                'author_login': login,
                'pr_count': count,
                'avg_quality_score': round(sum(pr.overall_quality_score or 0 for pr in user_prs) / len(user_prs), 2)
            })
        
        return top_contributors
    
    def _get_most_common_issues_for_repo(self, session: Session, repository: str) -> List[Dict[str, Any]]:
        """Get most common issues in a repository."""
        results = session.query(
            PRIssue.issue_type,
            func.count(PRIssue.id).label('count')
        ).join(PRAnalysis).filter(
            PRAnalysis.repository == repository
        ).group_by(PRIssue.issue_type).order_by(
            desc('count')
        ).limit(10).all()
        
        return [
            {
                'issue_type': self._format_issue_type(r[0]),
                'count': r[1],
                'recommendation': self._get_issue_recommendation(r[0])
            }
            for r in results
        ]
    
    def _calculate_repo_trends(self, prs: List[PRAnalysis]) -> Dict[str, Any]:
        """Calculate repository-wide trends."""
        if len(prs) < 10:
            return {'status': 'Insufficient data'}
        
        # Sort by date
        sorted_prs = sorted(prs, key=lambda pr: pr.analyzed_at)
        
        # Split into quarters
        mid = len(sorted_prs) // 2
        older = sorted_prs[:mid]
        recent = sorted_prs[mid:]
        
        older_avg = sum(pr.overall_quality_score or 0 for pr in older) / len(older)
        recent_avg = sum(pr.overall_quality_score or 0 for pr in recent) / len(recent)
        
        return {
            'quality_trend': self._get_trend_direction(recent_avg, older_avg),
            'improvement': round(recent_avg - older_avg, 2),
            'older_period_score': round(older_avg, 2),
            'recent_period_score': round(recent_avg, 2)
        }

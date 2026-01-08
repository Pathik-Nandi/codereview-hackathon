"""Analytics Processing Agent for generating insights from PR data."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from collections import Counter

from services.database_service import DatabaseService
from services.analytics_service import AnalyticsService
from utils.logger import logger


class AnalyticsProcessingAgent:
    """
    Agent responsible for processing and analyzing PR data over time.
    
    This agent:
    - Analyzes user performance over selected time ranges
    - Generates best practices and bad practices recommendations
    - Calculates quality scores and metrics
    - Provides actionable insights for dashboard display
    """
    
    # Category constants
    CATEGORY_CODE_QUALITY = 'code_quality'
    CATEGORY_SECURITY = 'security'
    CATEGORY_MAINTAINABILITY = 'maintainability'
    
    def __init__(self, db_service: DatabaseService, analytics_service: AnalyticsService):
        """Initialize analytics processing agent."""
        self.db_service = db_service
        self.analytics_service = analytics_service
        self.agent_name = "Analytics Processing Agent"
        logger.info("Analytics Processing Agent initialized")
    
    def process_user_analytics(
        self,
        author_login: str,
        author_email: Optional[str] = None,
        author_name: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Process analytics for a user with smart scheduling.
        Only runs if analytics haven't been generated recently (within last 4 hours).
        
        This maintains:
        - PR-level data: Each PR stored in pr_analysis (for historical queries)
        - User-level analytics: Aggregated snapshots in user_analytics (updated periodically)
        
        Args:
            author_login: GitHub username
            author_email: User's email address
            author_name: User's full name
            force: Force analytics generation even if recent snapshot exists
            
        Returns:
            Analytics result with success status
        """
        try:
            # Check if analytics already generated recently (within last 4 hours)
            if not force:
                from datetime import timedelta
                latest_analytics = self.db_service.get_latest_user_analytics(author_login)
                
                if latest_analytics:
                    # Ensure both datetimes are timezone-aware for comparison
                    analysis_date = latest_analytics.analysis_date
                    if analysis_date.tzinfo is None:
                        # If analysis_date is naive, assume it's UTC
                        analysis_date = analysis_date.replace(tzinfo=timezone.utc)
                    
                    time_since_last = datetime.now(timezone.utc) - analysis_date
                    if time_since_last < timedelta(hours=4):
                        logger.info(
                            "Skipping analytics - recent snapshot exists",
                            author=author_login,
                            last_run=latest_analytics.analysis_date.isoformat(),
                            hours_ago=round(time_since_last.total_seconds() / 3600, 1)
                        )
                        return {
                            'success': True,
                            'skipped': True,
                            'reason': 'Recent analytics exists',
                            'last_run': latest_analytics.analysis_date.isoformat(),
                            'analytics_id': latest_analytics.id,
                            'author_login': author_login
                        }
            
            # Analyze user over all time (no date range for now)
            analytics_result = self.analyze_user_over_time(
                author_login=author_login,
                start_date=None,
                end_date=None,
                min_prs=1  # Process even with 1 PR
            )
            
            if not analytics_result.get('success'):
                return analytics_result
            
            # Add email and name to analytics result
            analytics_result['author_email'] = author_email
            analytics_result['author_name'] = author_name
            
            # Save to database
            saved_analytics = self.db_service.save_user_analytics(analytics_result)
            
            if saved_analytics:
                analytics_result['analytics_id'] = saved_analytics.id
                logger.info(
                    "User analytics processed and saved",
                    author=author_login,
                    analytics_id=saved_analytics.id
                )
            else:
                logger.warning("Analytics generated but not saved to database", author=author_login)
            
            return analytics_result
            
        except Exception as e:
            logger.error(
                "Failed to process user analytics",
                author=author_login,
                error=str(e)
            )
            return {
                'success': False,
                'error': str(e),
                'author_login': author_login
            }
    
    def analyze_user_over_time(
        self,
        author_login: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_prs: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze user's PR history over a time range.
        
        Args:
            author_login: GitHub username
            start_date: Start of analysis period (None = all time)
            end_date: End of analysis period (None = now)
            min_prs: Minimum PRs required for analysis
            
        Returns:
            Comprehensive analysis with metrics, best practices, recommendations
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get user's PRs in date range
            prs = self._get_user_prs_in_range(author_login, start_date, end_date)
            
            if len(prs) < min_prs:
                return {
                    'success': False,
                    'error': f'Insufficient data: Only {len(prs)} PRs found (minimum {min_prs} required)',
                    'author_login': author_login,
                    'prs_analyzed': len(prs)
                }
            
            # Generate comprehensive analysis
            analysis = {
                'success': True,
                'author_login': author_login,
                'analysis_period': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else datetime.now(timezone.utc).isoformat(),
                    'total_prs': len(prs)
                },
                'quality_metrics': self._calculate_quality_metrics(prs),
                'code_scores': self._calculate_code_scores(prs),
                'rag_metrics': self._calculate_rag_metrics(prs),  # NEW: RAG insights
                'best_practices': self._identify_best_practices(prs),
                'bad_practices': self._identify_bad_practices(prs),
                'improvement_recommendations': self._generate_improvement_recommendations(prs),
                'trend_analysis': self._analyze_trends(prs),
                'issue_distribution': self._analyze_issue_distribution(prs),
                'agent_breakdown': self._analyze_agent_performance(prs),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            analysis['processing_time_ms'] = duration_ms
            
            logger.info(
                "User analysis completed",
                author=author_login,
                prs_count=len(prs),
                duration_ms=duration_ms
            )
            
            return analysis
            
        except Exception as e:
            logger.error(
                "Failed to analyze user over time",
                author=author_login,
                error=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'author_login': author_login
            }
    
    def _get_user_prs_in_range(
        self,
        author_login: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Any]:
        """Get user's PRs within date range."""
        with self.db_service.get_session() as session:
            from models.database import PRAnalysis
            
            query = session.query(PRAnalysis).filter_by(author_login=author_login)
            
            if start_date:
                query = query.filter(PRAnalysis.analyzed_at >= start_date)
            if end_date:
                query = query.filter(PRAnalysis.analyzed_at <= end_date)
            
            prs = query.order_by(PRAnalysis.analyzed_at.desc()).all()
            
            # Expunge all objects from session so they can be used outside
            for pr in prs:
                session.expunge(pr)
            
            return prs
    
    def _calculate_quality_metrics(self, prs: List[Any]) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics."""
        if not prs:
            return {}
        
        total_issues = sum(pr.total_issues for pr in prs)
        total_files = sum(pr.files_changed for pr in prs)
        total_lines_added = sum(pr.lines_added for pr in prs)
        total_lines_deleted = sum(pr.lines_deleted for pr in prs)
        
        return {
            'total_prs': len(prs),
            'total_issues': total_issues,
            'avg_issues_per_pr': round(total_issues / len(prs), 2),
            'total_files_changed': total_files,
            'avg_files_per_pr': round(total_files / len(prs), 2),
            'total_lines_added': total_lines_added,
            'total_lines_deleted': total_lines_deleted,
            'total_lines_changed': total_lines_added + total_lines_deleted,
            'avg_lines_per_pr': round((total_lines_added + total_lines_deleted) / len(prs), 2),
            'severity_distribution': {
                'critical': sum(pr.critical_issues for pr in prs),
                'high': sum(pr.high_issues for pr in prs),
                'medium': sum(pr.medium_issues for pr in prs),
                'low': sum(pr.low_issues for pr in prs)
            },
            'coverage_metrics': {
                'avg_coverage': round(sum(pr.estimated_coverage or 0 for pr in prs) / len(prs), 2),
                'avg_test_ratio': round(sum(pr.test_to_code_ratio or 0 for pr in prs) / len(prs), 3),
                'avg_complexity': round(sum(pr.complexity_score or 0 for pr in prs) / len(prs), 2)
            }
        }
    
    def _calculate_code_scores(self, prs: List[Any]) -> Dict[str, Any]:
        """Calculate aggregated code quality scores."""
        if not prs:
            return {}
        
        quality_scores = [pr.overall_quality_score for pr in prs if pr.overall_quality_score]
        security_scores = [pr.security_score for pr in prs if pr.security_score]
        maintainability_scores = [pr.maintainability_score for pr in prs if pr.maintainability_score]
        
        return {
            'overall_quality': {
                'average': round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0,
                'min': round(min(quality_scores), 2) if quality_scores else 0,
                'max': round(max(quality_scores), 2) if quality_scores else 0,
                'rating': self._get_score_rating(sum(quality_scores) / len(quality_scores) if quality_scores else 0)
            },
            'security': {
                'average': round(sum(security_scores) / len(security_scores), 2) if security_scores else 0,
                'min': round(min(security_scores), 2) if security_scores else 0,
                'max': round(max(security_scores), 2) if security_scores else 0,
                'rating': self._get_score_rating(sum(security_scores) / len(security_scores) if security_scores else 0)
            },
            'maintainability': {
                'average': round(sum(maintainability_scores) / len(maintainability_scores), 2) if maintainability_scores else 0,
                'min': round(min(maintainability_scores), 2) if maintainability_scores else 0,
                'max': round(max(maintainability_scores), 2) if maintainability_scores else 0,
                'rating': self._get_score_rating(sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 0)
            }
        }
    
    def _get_score_rating(self, score: float) -> str:
        """Convert numeric score to rating."""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 60:
            return "Poor"
        else:
            return "Critical"
    
    def _identify_best_practices(self, prs: List[Any]) -> List[Dict[str, Any]]:
        """Identify what user does well."""
        best_practices = []
        
        # Check security practices
        security_scores = [pr.security_score for pr in prs if pr.security_score]
        avg_security = sum(security_scores) / len(security_scores) if security_scores else 0
        
        if avg_security >= 90:
            best_practices.append({
                'category': 'Security',
                'title': 'Excellent Security Awareness',
                'description': 'You consistently avoid security vulnerabilities in your code',
                'score': round(avg_security, 2),
                'impact': 'high',
                'evidence': f'Average security score: {round(avg_security, 2)}/100 across {len(prs)} PRs'
            })
        
        # Check test coverage
        coverage_scores = [pr.estimated_coverage for pr in prs if pr.estimated_coverage]
        avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
        
        if avg_coverage >= 80:
            best_practices.append({
                'category': 'Testing',
                'title': 'Strong Test Coverage',
                'description': 'You maintain high test coverage in your pull requests',
                'score': round(avg_coverage, 2),
                'impact': 'high',
                'evidence': f'Average coverage: {round(avg_coverage, 2)}% across {len(prs)} PRs'
            })
        
        # Check PR size (smaller is better)
        avg_files = sum(pr.files_changed for pr in prs) / len(prs)
        if avg_files < 10:
            best_practices.append({
                'category': 'Process',
                'title': 'Small, Focused Pull Requests',
                'description': 'You create manageable PRs that are easier to review and merge',
                'score': 100,
                'impact': 'medium',
                'evidence': f'Average {round(avg_files, 1)} files changed per PR'
            })
        
        # Check critical issues
        total_critical = sum(pr.critical_issues for pr in prs)
        if total_critical == 0:
            best_practices.append({
                'category': self.CATEGORY_CODE_QUALITY,
                'title': 'Zero Critical Issues',
                'description': 'You avoid critical code quality and security issues',
                'score': 100,
                'impact': 'high',
                'evidence': f'No critical issues in {len(prs)} PRs analyzed'
            })
        
        # Check consistency
        quality_scores = [pr.overall_quality_score for pr in prs if pr.overall_quality_score]
        if quality_scores:
            std_dev = (sum((x - sum(quality_scores)/len(quality_scores))**2 for x in quality_scores) / len(quality_scores))**0.5
            if std_dev < 10:
                best_practices.append({
                    'category': 'Consistency',
                    'title': 'Consistent Code Quality',
                    'description': 'You maintain stable quality across all your pull requests',
                    'score': 95,
                    'impact': 'medium',
                    'evidence': f'Low variance in quality scores (std dev: {round(std_dev, 2)})'
                })
        
        return best_practices
    
    def _identify_bad_practices(self, prs: List[Any]) -> List[Dict[str, Any]]:
        """Identify practices user should improve."""
        bad_practices = []
        
        # Collect all issues across PRs
        with self.db_service.get_session() as session:
            from models.database import PRIssue
            
            all_issues = []
            for pr in prs:
                issues = session.query(PRIssue).filter_by(pr_analysis_id=pr.id).all()
                all_issues.extend(issues)
            
            # Count issue types
            issue_counts = Counter(issue.issue_type for issue in all_issues)
            
            # Identify top problematic patterns
            for issue_type, count in issue_counts.most_common(10):
                if count >= 5:  # Only report if frequent
                    bad_practices.append({
                        'category': self._get_issue_category(issue_type),
                        'title': self._format_issue_type(issue_type),
                        'description': self._get_issue_description(issue_type),
                        'occurrences': count,
                        'frequency': round(count / len(prs), 2),
                        'severity': self._get_pattern_severity(issue_type),
                        'recommendation': self._get_issue_recommendation(issue_type)
                    })
        
        # Check for high issue density
        avg_issues = sum(pr.total_issues for pr in prs) / len(prs)
        if avg_issues > 30:
            bad_practices.append({
                'category': self.CATEGORY_CODE_QUALITY,
                'title': 'High Issue Density',
                'description': 'Your PRs contain a high number of issues on average',
                'occurrences': int(sum(pr.total_issues for pr in prs)),
                'frequency': round(avg_issues, 2),
                'severity': 'high',
                'recommendation': 'Review code before committing, use IDE linters, run local analysis'
            })
        
        # Check for low test coverage
        coverage_scores = [pr.estimated_coverage for pr in prs if pr.estimated_coverage]
        avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
        
        if avg_coverage < 70:
            bad_practices.append({
                'category': 'Testing',
                'title': 'Insufficient Test Coverage',
                'description': 'Your test coverage is below recommended threshold',
                'occurrences': len([c for c in coverage_scores if c < 70]),
                'frequency': round(avg_coverage, 2),
                'severity': 'high',
                'recommendation': 'Aim for 80%+ coverage, write tests alongside new features'
            })
        
        return bad_practices
    
    def _generate_improvement_recommendations(self, prs: List[Any]) -> List[Dict[str, Any]]:
        """Generate actionable improvement recommendations."""
        recommendations = []
        
        # Analyze quality scores
        quality_scores = [pr.overall_quality_score for pr in prs if pr.overall_quality_score]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        if avg_quality < 85:
            gap = 85 - avg_quality
            recommendations.append({
                'area': 'Overall Code Quality',
                'priority': 'high' if gap > 15 else 'medium',
                'current_score': round(avg_quality, 2),
                'target_score': 85,
                'gap': round(gap, 2),
                'actions': [
                    'Review and refactor code with high complexity',
                    'Eliminate magic numbers and hardcoded values',
                    'Reduce nesting levels and method lengths',
                    'Follow language-specific coding standards'
                ],
                'estimated_effort': 'medium',
                'expected_impact': 'high'
            })
        
        # Analyze security
        security_scores = [pr.security_score for pr in prs if pr.security_score]
        avg_security = sum(security_scores) / len(security_scores) if security_scores else 0
        
        if avg_security < 90:
            recommendations.append({
                'area': 'Security Practices',
                'priority': 'critical' if avg_security < 70 else 'high',
                'current_score': round(avg_security, 2),
                'target_score': 95,
                'gap': round(95 - avg_security, 2),
                'actions': [
                    'Use environment variables for sensitive data',
                    'Implement parameterized queries to prevent SQL injection',
                    'Validate and sanitize all user inputs',
                    'Use strong cryptographic algorithms',
                    'Review OWASP Top 10 security risks'
                ],
                'estimated_effort': 'high',
                'expected_impact': 'critical'
            })
        
        # Analyze test coverage
        coverage_scores = [pr.estimated_coverage for pr in prs if pr.estimated_coverage]
        avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
        
        if avg_coverage < 80:
            recommendations.append({
                'area': 'Test Coverage',
                'priority': 'high',
                'current_score': round(avg_coverage, 2),
                'target_score': 80,
                'gap': round(80 - avg_coverage, 2),
                'actions': [
                    'Write unit tests for all public methods',
                    'Add integration tests for critical workflows',
                    'Test edge cases and error conditions',
                    'Achieve at least 80% line coverage'
                ],
                'estimated_effort': 'medium',
                'expected_impact': 'high'
            })
        
        # Analyze complexity
        complexity_scores = [pr.complexity_score for pr in prs if pr.complexity_score]
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        
        if avg_complexity > 20:
            recommendations.append({
                'area': 'Code Complexity',
                'priority': 'medium',
                'current_score': round(avg_complexity, 2),
                'target_score': 15,
                'gap': round(avg_complexity - 15, 2),
                'actions': [
                    'Break down complex methods into smaller functions',
                    'Reduce conditional branching',
                    'Use early returns to simplify logic',
                    'Apply design patterns to reduce complexity'
                ],
                'estimated_effort': 'medium',
                'expected_impact': 'medium'
            })
        
        return recommendations
    
    def _analyze_trends(self, prs: List[Any]) -> Dict[str, Any]:
        """Analyze quality trends over time."""
        if len(prs) < 10:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 10 PRs for trend analysis'
            }
        
        # Split into recent and older
        mid = len(prs) // 2
        recent_prs = prs[:mid]
        older_prs = prs[mid:]
        
        # Calculate averages
        recent_quality = sum(pr.overall_quality_score or 0 for pr in recent_prs) / len(recent_prs)
        older_quality = sum(pr.overall_quality_score or 0 for pr in older_prs) / len(older_prs)
        
        recent_security = sum(pr.security_score or 0 for pr in recent_prs) / len(recent_prs)
        older_security = sum(pr.security_score or 0 for pr in older_prs) / len(older_prs)
        
        recent_coverage = sum(pr.estimated_coverage or 0 for pr in recent_prs) / len(recent_prs)
        older_coverage = sum(pr.estimated_coverage or 0 for pr in older_prs) / len(older_prs)
        
        return {
            'status': 'analyzed',
            'quality': {
                'direction': self._get_trend_direction(recent_quality, older_quality),
                'change': round(recent_quality - older_quality, 2),
                'recent_avg': round(recent_quality, 2),
                'older_avg': round(older_quality, 2)
            },
            'security': {
                'direction': self._get_trend_direction(recent_security, older_security),
                'change': round(recent_security - older_security, 2),
                'recent_avg': round(recent_security, 2),
                'older_avg': round(older_security, 2)
            },
            'coverage': {
                'direction': self._get_trend_direction(recent_coverage, older_coverage),
                'change': round(recent_coverage - older_coverage, 2),
                'recent_avg': round(recent_coverage, 2),
                'older_avg': round(older_coverage, 2)
            }
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
    
    def _analyze_issue_distribution(self, prs: List[Any]) -> Dict[str, Any]:
        """Analyze distribution of issues across agents."""
        return {
            'by_agent': {
                'static_analysis': sum(pr.static_analysis_issues for pr in prs),
                'security': sum(pr.security_issues for pr in prs),
                'code_quality': sum(pr.code_quality_issues for pr in prs),
                'context': sum(pr.context_issues for pr in prs),
                'coverage': sum(pr.coverage_issues for pr in prs)
            },
            'by_severity': {
                'critical': sum(pr.critical_issues for pr in prs),
                'high': sum(pr.high_issues for pr in prs),
                'medium': sum(pr.medium_issues for pr in prs),
                'low': sum(pr.low_issues for pr in prs)
            }
        }
    
    def _analyze_agent_performance(self, prs: List[Any]) -> Dict[str, Any]:
        """Analyze which agents find most issues."""
        total_issues = sum(pr.total_issues for pr in prs)
        
        if total_issues == 0:
            return {}
        
        return {
            'static_analysis': {
                'total': sum(pr.static_analysis_issues for pr in prs),
                'percentage': round(sum(pr.static_analysis_issues for pr in prs) / total_issues * 100, 2)
            },
            'security': {
                'total': sum(pr.security_issues for pr in prs),
                'percentage': round(sum(pr.security_issues for pr in prs) / total_issues * 100, 2)
            },
            'code_quality': {
                'total': sum(pr.code_quality_issues for pr in prs),
                'percentage': round(sum(pr.code_quality_issues for pr in prs) / total_issues * 100, 2)
            },
            'context': {
                'total': sum(pr.context_issues for pr in prs),
                'percentage': round(sum(pr.context_issues for pr in prs) / total_issues * 100, 2)
            },
            'coverage': {
                'total': sum(pr.coverage_issues for pr in prs),
                'percentage': round(sum(pr.coverage_issues for pr in prs) / total_issues * 100, 2)
            }
        }
    
    def _get_issue_category(self, issue_type: str) -> str:
        """Get category for issue type."""
        security_types = ['hardcoded_secret', 'sql_injection', 'command_injection', 'weak_crypto']
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
            'LOW_COVERAGE': 'Insufficient test coverage for code changes'
        }
        return descriptions.get(issue_type, 'Code quality or security issue detected')
    
    def _get_pattern_severity(self, issue_type: str) -> str:
        """Get severity for issue pattern."""
        critical_types = ['hardcoded_secret', 'sql_injection', 'command_injection']
        high_types = ['weak_crypto', 'xxe', 'low_coverage']
        
        issue_lower = issue_type.lower()
        if any(c in issue_lower for c in critical_types):
            return 'critical'
        elif any(h in issue_lower for h in high_types):
            return 'high'
        else:
            return 'medium'
    
    def _get_issue_recommendation(self, issue_type: str) -> str:
        """Get recommendation for issue type."""
        recommendations = {
            'MAGIC_NUMBER': 'Define named constants for numeric values',
            'DEEP_NESTING': 'Use early returns and extract methods to reduce nesting',
            'LONG_METHOD': 'Break down long methods into smaller, focused functions',
            'HARDCODED_SECRET': 'Use environment variables or secure vaults',
            'SQL_INJECTION': 'Use parameterized queries or ORM',
            'NO_SYSTEM_OUT': 'Replace with proper logging framework',
            'LOW_COVERAGE': 'Add unit tests to increase coverage to 80%+'
        }
        return recommendations.get(issue_type, 'Review and refactor this code pattern')
    
    def _get_high_risk_prs(self, prs_with_rag: List) -> List[Dict]:
        """Identify high-risk PRs from RAG analysis."""
        high_risk_prs = []
        for pr in prs_with_rag:
            if (pr.rag_risk_score or 0) > 0.7:
                high_risk_prs.append({
                    'pr_number': pr.pr_number,
                    'title': pr.pr_title,
                    'risk_score': pr.rag_risk_score,
                    'analyzed_at': pr.analyzed_at.isoformat() if pr.analyzed_at else None
                })
        return high_risk_prs[:5]  # Top 5

    def _get_novel_contributions(self, prs_with_rag: List) -> List[Dict]:
        """Identify novel contributions from RAG analysis."""
        novel_contributions = []
        for pr in prs_with_rag:
            if (pr.rag_novelty_score or 0) > 0.8:
                novel_contributions.append({
                    'pr_number': pr.pr_number,
                    'title': pr.pr_title,
                    'novelty_score': pr.rag_novelty_score,
                    'analyzed_at': pr.analyzed_at.isoformat() if pr.analyzed_at else None
                })
        return novel_contributions[:5]  # Top 5

    def _aggregate_patterns(self, prs_with_rag: List) -> List[Dict]:
        """Aggregate and count patterns from RAG analysis."""
        all_patterns = []
        for pr in prs_with_rag:
            if pr.rag_patterns_identified:
                if isinstance(pr.rag_patterns_identified, list):
                    all_patterns.extend(pr.rag_patterns_identified)
                elif isinstance(pr.rag_patterns_identified, dict):
                    all_patterns.extend(pr.rag_patterns_identified.keys())
        
        patterns_learned = []
        if all_patterns:
            pattern_counts = Counter(all_patterns)
            for pattern, count in pattern_counts.most_common(10):
                patterns_learned.append({
                    'pattern': pattern,
                    'occurrences': count,
                    'frequency': count / len(prs_with_rag)
                })
        return patterns_learned

    def _calculate_basic_rag_stats(self, prs_with_rag: List) -> Dict:
        """Calculate basic RAG statistics (averages and totals)."""
        avg_risk = sum(pr.rag_risk_score or 0 for pr in prs_with_rag) / len(prs_with_rag)
        avg_novelty = sum(pr.rag_novelty_score or 0 for pr in prs_with_rag) / len(prs_with_rag)
        total_similar = sum(pr.rag_similar_prs_count or 0 for pr in prs_with_rag)
        total_recommendations = sum(pr.rag_recommendations_count or 0 for pr in prs_with_rag)
        
        return {
            'avg_risk': avg_risk,
            'avg_novelty': avg_novelty,
            'total_similar': total_similar,
            'total_recommendations': total_recommendations
        }

    def _calculate_rag_metrics(self, prs: List) -> Dict[str, Any]:
        """
        Calculate RAG-specific metrics from PRs.
        
        Args:
            prs: List of PRAnalysis objects
            
        Returns:
            Dictionary with RAG metrics and insights
        """
        prs_with_rag = [pr for pr in prs if getattr(pr, 'has_rag_insights', False)]
        
        if not prs_with_rag:
            return {
                'total_insights': 0,
                'avg_risk_score': None,
                'avg_novelty_score': None,
                'total_similar_prs': 0,
                'total_recommendations': 0,
                'high_risk_prs': [],
                'novel_contributions': [],
                'patterns_learned': [],
                'insights_summary': None,
                'risk_trend': None,
                'novelty_trend': None
            }
        
        # Calculate basic statistics
        basic_stats = self._calculate_basic_rag_stats(prs_with_rag)
        
        # Identify high-risk PRs and novel contributions
        high_risk_prs = self._get_high_risk_prs(prs_with_rag)
        novel_contributions = self._get_novel_contributions(prs_with_rag)
        
        # Aggregate patterns
        patterns_learned = self._aggregate_patterns(prs_with_rag)
        
        # Calculate trends
        risk_trend = self._calculate_rag_trend(prs_with_rag, 'rag_risk_score')
        novelty_trend = self._calculate_rag_trend(prs_with_rag, 'rag_novelty_score')
        
        # Create insights summary
        insights_summary = {
            'lessons_learned': self._extract_rag_lessons(prs_with_rag),
            'pitfalls_avoided': self._extract_rag_pitfalls(prs_with_rag),
            'best_practices': self._extract_rag_best_practices(prs_with_rag)
        }
        
        return {
            'total_insights': len(prs_with_rag),
            'avg_risk_score': round(basic_stats['avg_risk'], 3) if basic_stats['avg_risk'] else None,
            'avg_novelty_score': round(basic_stats['avg_novelty'], 3) if basic_stats['avg_novelty'] else None,
            'total_similar_prs': basic_stats['total_similar'],
            'total_recommendations': basic_stats['total_recommendations'],
            'high_risk_prs': high_risk_prs,
            'novel_contributions': novel_contributions,
            'patterns_learned': patterns_learned,
            'insights_summary': insights_summary,
            'risk_trend': risk_trend,
            'novelty_trend': novelty_trend
        }
    
    def _calculate_rag_trend(self, prs: List, metric_field: str) -> Dict[str, Any]:
        """Calculate trend for a RAG metric."""
        if len(prs) < 4:
            return {'direction': 'stable', 'change': 0}
        
        # Sort by date
        sorted_prs = sorted(prs, key=lambda p: p.analyzed_at or datetime.min.replace(tzinfo=timezone.utc))
        
        # Split into recent and older
        split_point = len(sorted_prs) // 2
        older_prs = sorted_prs[:split_point]
        recent_prs = sorted_prs[split_point:]
        
        # Calculate averages
        older_avg = sum(getattr(pr, metric_field) or 0 for pr in older_prs) / len(older_prs)
        recent_avg = sum(getattr(pr, metric_field) or 0 for pr in recent_prs) / len(recent_prs)
        
        change = recent_avg - older_avg
        
        # Determine direction (for risk, lower is better)
        if metric_field == 'rag_risk_score':
            if change < -0.05:
                direction = 'improving'
            elif change > 0.05:
                direction = 'declining'
            else:
                direction = 'stable'
        else:  # novelty
            if change > 0.05:
                direction = 'improving'
            elif change < -0.05:
                direction = 'declining'
            else:
                direction = 'stable'
        
        return {
            'direction': direction,
            'change': round(change, 3),
            'recent_avg': round(recent_avg, 3),
            'older_avg': round(older_avg, 3)
        }
    
    def _extract_rag_lessons(self, prs: List) -> List[str]:
        """Extract lessons learned from RAG insights."""
        # This is a simplified version - in production, you'd query rag_insights table
        lessons = set()
        for pr in prs[:10]:  # Sample recent PRs
            if pr.pr_title and 'fix' in pr.pr_title.lower():
                lessons.add(f"Fixed issue in PR #{pr.pr_number}")
        return list(lessons)[:5]
    
    def _extract_rag_pitfalls(self, prs: List) -> List[str]:
        """Extract pitfalls from RAG insights."""
        pitfalls = []
        high_risk_count = sum(1 for pr in prs if (pr.rag_risk_score or 0) > 0.7)
        if high_risk_count > 0:
            pitfalls.append(f"{high_risk_count} high-risk PRs identified in period")
        return pitfalls[:5]
    
    def _extract_rag_best_practices(self, prs: List) -> List[str]:
        """Extract best practices from RAG insights."""
        practices = []
        novel_count = sum(1 for pr in prs if (pr.rag_novelty_score or 0) > 0.8)
        if novel_count > 0:
            practices.append(f"{novel_count} novel contributions showing innovation")
        return practices[:5]

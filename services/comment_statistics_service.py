"""
Service for aggregating PR comment statistics.

This service queries the pr_comments table and generates aggregated statistics
for analytics dashboards and trend analysis.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session
from models.database import PRComment, PRCommentStatistics, PRAnalysis
from services.database_service import DatabaseService
from utils.logger import logger

# Constants
MSG_STATS_ALREADY_EXIST = 'Statistics already exist'
MSG_NO_COMMENTS = 'No comments for this'


class CommentStatisticsService:
    """Service for generating comment statistics."""
    
    def __init__(self, db_service: Optional[DatabaseService] = None):
        """Initialize the service."""
        self.db_service = db_service or DatabaseService()
    
    def generate_daily_statistics(self, target_date: Optional[datetime] = None) -> Dict:
        """
        Generate daily comment statistics.
        
        Args:
            target_date: Date to generate statistics for (defaults to yesterday)
            
        Returns:
            Dict with statistics generation results
        """
        if target_date is None:
            # Default to yesterday to ensure complete day
            target_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        # Set to start of day
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        logger.info(
            "Generating daily comment statistics",
            date=start_date.date(),
            period="daily"
        )
        
        with self.db_service.get_session() as session:
            # Check if statistics already exist for this date
            existing = session.query(PRCommentStatistics).filter(
                and_(
                    PRCommentStatistics.date == start_date,
                    PRCommentStatistics.period_type == 'daily'
                )
            ).first()
            
            if existing:
                logger.warning(
                    "Statistics already exist for this date",
                    date=start_date.date(),
                    existing_id=existing.id
                )
                return {
                    'success': False,
                    'message': MSG_STATS_ALREADY_EXIST,
                    'statistics_id': existing.id
                }
            
            # Query comments for the date range
            comments = session.query(PRComment).filter(
                and_(
                    PRComment.posted_at >= start_date,
                    PRComment.posted_at < end_date
                )
            ).all()
            
            if not comments:
                logger.info("No comments found for date", date=start_date.date())
                return {
                    'success': False,
                    'message': 'No comments for this date',
                    'date': start_date.date()
                }
            
            # Calculate statistics
            stats = self._calculate_statistics(comments, start_date, 'daily')
            
            # Save to database
            statistics = PRCommentStatistics(**stats)
            session.add(statistics)
            session.commit()
            
            logger.info(
                "Daily statistics generated",
                statistics_id=statistics.id,
                date=start_date.date(),
                total_comments=stats['total_comments_posted']
            )
            
            return {
                'success': True,
                'statistics_id': statistics.id,
                'date': start_date.date(),
                'total_comments': stats['total_comments_posted']
            }
    
    def generate_weekly_statistics(self, target_date: Optional[datetime] = None) -> Dict:
        """
        Generate weekly comment statistics.
        
        Args:
            target_date: Start date of week (defaults to last week Monday)
            
        Returns:
            Dict with statistics generation results
        """
        if target_date is None:
            # Default to last week's Monday
            today = datetime.now(timezone.utc)
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            target_date = last_monday
        
        # Set to start of day (Monday)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
        
        logger.info(
            "Generating weekly comment statistics",
            week_start=start_date.date(),
            week_end=end_date.date(),
            period="weekly"
        )
        
        with self.db_service.get_session() as session:
            # Check if statistics already exist
            existing = session.query(PRCommentStatistics).filter(
                and_(
                    PRCommentStatistics.date == start_date,
                    PRCommentStatistics.period_type == 'weekly'
                )
            ).first()
            
            if existing:
                logger.warning(
                    "Statistics already exist for this week",
                    week_start=start_date.date(),
                    existing_id=existing.id
                )
                return {
                    'success': False,
                    'message': MSG_STATS_ALREADY_EXIST,
                    'statistics_id': existing.id
                }
            
            # Query comments for the week
            comments = session.query(PRComment).filter(
                and_(
                    PRComment.posted_at >= start_date,
                    PRComment.posted_at < end_date
                )
            ).all()
            
            if not comments:
                logger.info("No comments found for week", week_start=start_date.date())
                return {
                    'success': False,
                    'message': 'No comments for this week',
                    'week_start': start_date.date()
                }
            
            # Calculate statistics
            stats = self._calculate_statistics(comments, start_date, 'weekly')
            
            # Save to database
            statistics = PRCommentStatistics(**stats)
            session.add(statistics)
            session.commit()
            
            logger.info(
                "Weekly statistics generated",
                statistics_id=statistics.id,
                week_start=start_date.date(),
                total_comments=stats['total_comments_posted']
            )
            
            return {
                'success': True,
                'statistics_id': statistics.id,
                'week_start': start_date.date(),
                'total_comments': stats['total_comments_posted']
            }
    
    def generate_monthly_statistics(self, year: Optional[int] = None, month: Optional[int] = None) -> Dict:
        """
        Generate monthly comment statistics.
        
        Args:
            year: Year (defaults to last month)
            month: Month (defaults to last month)
            
        Returns:
            Dict with statistics generation results
        """
        if year is None or month is None:
            # Default to last month
            today = datetime.now(timezone.utc)
            if today.month == 1:
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1
        
        # Start of month
        start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        # End of month (start of next month)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        else:
            end_date = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        logger.info(
            "Generating monthly comment statistics",
            year=year,
            month=month,
            period="monthly"
        )
        
        with self.db_service.get_session() as session:
            # Check if statistics already exist
            existing = session.query(PRCommentStatistics).filter(
                and_(
                    PRCommentStatistics.date == start_date,
                    PRCommentStatistics.period_type == 'monthly'
                )
            ).first()
            
            if existing:
                logger.warning(
                    "Statistics already exist for this month",
                    year=year,
                    month=month,
                    existing_id=existing.id
                )
                return {
                    'success': False,
                    'message': MSG_STATS_ALREADY_EXIST,
                    'statistics_id': existing.id
                }
            
            # Query comments for the month
            comments = session.query(PRComment).filter(
                and_(
                    PRComment.posted_at >= start_date,
                    PRComment.posted_at < end_date
                )
            ).all()
            
            if not comments:
                logger.info("No comments found for month", year=year, month=month)
                return {
                    'success': False,
                    'message': 'No comments for this month',
                    'year': year,
                    'month': month
                }
            
            # Calculate statistics
            stats = self._calculate_statistics(comments, start_date, 'monthly')
            
            # Save to database
            statistics = PRCommentStatistics(**stats)
            session.add(statistics)
            session.commit()
            
            logger.info(
                "Monthly statistics generated",
                statistics_id=statistics.id,
                year=year,
                month=month,
                total_comments=stats['total_comments_posted']
            )
            
            return {
                'success': True,
                'statistics_id': statistics.id,
                'year': year,
                'month': month,
                'total_comments': stats['total_comments_posted']
            }
    
    def _calculate_statistics(
        self, 
        comments: List[PRComment], 
        date: datetime, 
        period_type: str
    ) -> Dict:
        """
        Calculate statistics from a list of comments.
        
        Args:
            comments: List of PRComment objects
            date: Date for the statistics period
            period_type: 'daily', 'weekly', or 'monthly'
            
        Returns:
            Dict with calculated statistics
        """
        total_comments = len(comments)
        
        # Count by type
        summary_count = sum(1 for c in comments if c.comment_type == 'summary')
        inline_count = sum(1 for c in comments if c.comment_type == 'inline')
        review_count = sum(1 for c in comments if c.review_event in ['COMMENT', 'REQUEST_CHANGES', 'APPROVE'])
        
        # Success metrics
        successful = sum(1 for c in comments if c.posted_successfully)
        failed = total_comments - successful
        success_rate = (successful / total_comments * 100) if total_comments > 0 else 0
        
        # Count by severity
        severity_map = self._count_by_severity(comments)
        
        # Count by type
        type_map = self._count_by_issue_type(comments)
        
        # Review type distribution
        review_types = self._count_by_review_type(comments)
        
        return {
            'date': date,
            'period_type': period_type,
            'total_comments_posted': total_comments,
            'summary_comments': summary_count,
            'inline_comments': inline_count,
            'review_comments': review_count,
            'successful_posts': successful,
            'failed_posts': failed,
            'success_rate': round(success_rate, 2),
            'critical_comments': severity_map['critical'],
            'high_comments': severity_map['high'],
            'medium_comments': severity_map['medium'],
            'low_comments': severity_map['low'],
            'security_comments': type_map['security'],
            'quality_comments': type_map['quality'],
            'complexity_comments': type_map['complexity'],
            'coverage_comments': type_map['coverage'],
            'request_changes_count': review_types['REQUEST_CHANGES'],
            'comment_only_count': review_types['COMMENT'],
            'approve_count': review_types['APPROVE'],
            'created_at': datetime.now(timezone.utc)
        }
    
    def _count_by_severity(self, comments: List[PRComment]) -> Dict[str, int]:
        """Count comments by severity level."""
        severity_map = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for comment in comments:
            severity = comment.issue_severity
            if severity and severity.lower() in severity_map:
                severity_map[severity.lower()] += 1
        return severity_map
    
    def _count_by_issue_type(self, comments: List[PRComment]) -> Dict[str, int]:
        """Count comments by issue type category."""
        type_map = {'security': 0, 'quality': 0, 'complexity': 0, 'coverage': 0}
        for comment in comments:
            issue_type = comment.issue_type
            if issue_type:
                issue_type_lower = issue_type.lower()
                if 'security' in issue_type_lower:
                    type_map['security'] += 1
                elif 'quality' in issue_type_lower or 'style' in issue_type_lower:
                    type_map['quality'] += 1
                elif 'complexity' in issue_type_lower or 'cognitive' in issue_type_lower:
                    type_map['complexity'] += 1
                elif 'coverage' in issue_type_lower or 'test' in issue_type_lower:
                    type_map['coverage'] += 1
        return type_map
    
    def _count_by_review_type(self, comments: List[PRComment]) -> Dict[str, int]:
        """Count comments by review event type."""
        review_types = {'REQUEST_CHANGES': 0, 'COMMENT': 0, 'APPROVE': 0}
        for comment in comments:
            if comment.review_event and comment.review_event in review_types:
                review_types[comment.review_event] += 1
        return review_types
    
    def get_statistics(
        self, 
        period_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 30
    ) -> List[Dict]:
        """
        Retrieve comment statistics.
        
        Args:
            period_type: Filter by period type ('daily', 'weekly', 'monthly')
            start_date: Filter from this date
            end_date: Filter to this date
            limit: Maximum number of records to return
            
        Returns:
            List of statistics records
        """
        with self.db_service.get_session() as session:
            query = session.query(PRCommentStatistics)
            
            if period_type:
                query = query.filter(PRCommentStatistics.period_type == period_type)
            
            if start_date:
                query = query.filter(PRCommentStatistics.date >= start_date)
            
            if end_date:
                query = query.filter(PRCommentStatistics.date <= end_date)
            
            query = query.order_by(PRCommentStatistics.date.desc()).limit(limit)
            
            stats = query.all()
            
            return [
                {
                    'id': s.id,
                    'date': s.date.isoformat() if s.date else None,
                    'period_type': s.period_type,
                    'total_comments': s.total_comments_posted,
                    'summary_comments': s.summary_comments,
                    'inline_comments': s.inline_comments,
                    'success_rate': s.success_rate,
                    'critical_comments': s.critical_comments,
                    'high_comments': s.high_comments,
                    'medium_comments': s.medium_comments,
                    'low_comments': s.low_comments,
                    'security_comments': s.security_comments,
                    'quality_comments': s.quality_comments,
                    'complexity_comments': s.complexity_comments,
                    'coverage_comments': s.coverage_comments
                }
                for s in stats
            ]

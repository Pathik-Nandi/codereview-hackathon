"""
Celery configuration for asynchronous task processing.
"""
from celery import Celery
from utils.config import config
from utils.logger import logger

# Initialize Celery app
# Using memory transport for development (replace with Redis/RabbitMQ in production)
celery_app = Celery(
    'pr_analysis',
    broker='memory://',  # In-memory for now, use redis:// in production
    backend='cache+memory://'  # In-memory cache backend
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_ignore_result=False,
    task_track_started=True
)

logger.info("Celery configured with in-memory transport (development mode)")


@celery_app.task(name='tasks.process_user_analytics_async')
def process_user_analytics_async(author_login: str, author_email: str = None, author_name: str = None):
    """
    Async Celery task for processing user analytics.
    
    Args:
        author_login: GitHub username
        author_email: User's email address
        author_name: User's full name
        
    Returns:
        Analytics result dictionary
    """
    try:
        from services.database_service import DatabaseService
        from services.analytics_service import AnalyticsService
        from agents.analytics_processing_agent import AnalyticsProcessingAgent
        
        # Initialize services
        db_service = DatabaseService()
        analytics_service = AnalyticsService()
        analytics_agent = AnalyticsProcessingAgent(db_service, analytics_service)
        
        # Process analytics
        result = analytics_agent.process_user_analytics(
            author_login=author_login,
            author_email=author_email,
            author_name=author_name
        )
        
        logger.info(
            "Async analytics processing completed",
            author=author_login,
            success=result.get('success')
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Async analytics processing failed",
            author=author_login,
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e),
            'author_login': author_login
        }


@celery_app.task(name='tasks.generate_daily_comment_statistics')
def generate_daily_comment_statistics():
    """
    Celery task to generate daily comment statistics.
    Runs daily at midnight to process previous day's comments.
    
    Returns:
        Statistics generation result dictionary
    """
    try:
        from services.comment_statistics_service import CommentStatisticsService
        
        service = CommentStatisticsService()
        result = service.generate_daily_statistics()
        
        logger.info(
            "Daily comment statistics generated",
            success=result.get('success'),
            total_comments=result.get('total_comments', 0)
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to generate daily comment statistics", error=str(e))
        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task(name='tasks.generate_weekly_comment_statistics')
def generate_weekly_comment_statistics():
    """
    Celery task to generate weekly comment statistics.
    Runs weekly on Monday to process previous week's comments.
    
    Returns:
        Statistics generation result dictionary
    """
    try:
        from services.comment_statistics_service import CommentStatisticsService
        
        service = CommentStatisticsService()
        result = service.generate_weekly_statistics()
        
        logger.info(
            "Weekly comment statistics generated",
            success=result.get('success'),
            total_comments=result.get('total_comments', 0)
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to generate weekly comment statistics", error=str(e))
        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task(name='tasks.generate_monthly_comment_statistics')
def generate_monthly_comment_statistics():
    """
    Celery task to generate monthly comment statistics.
    Runs on the 1st of each month to process previous month's comments.
    
    Returns:
        Statistics generation result dictionary
    """
    try:
        from services.comment_statistics_service import CommentStatisticsService
        
        service = CommentStatisticsService()
        result = service.generate_monthly_statistics()
        
        logger.info(
            "Monthly comment statistics generated",
            success=result.get('success'),
            total_comments=result.get('total_comments', 0)
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to generate monthly comment statistics", error=str(e))
        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task(name='tasks.generate_user_analytics_daily')
def generate_user_analytics_daily():
    """
    Celery task to generate user analytics for all active users.
    Respects the 4-hour rule - only generates if last run was 4+ hours ago.
    
    Returns:
        Analytics generation result dictionary
    """
    try:
        from services.generate_user_analytics import UserAnalyticsGenerator
        
        generator = UserAnalyticsGenerator()
        result = generator.generate_for_all_users(force=False)  # Respect 4-hour rule
        
        logger.info(
            "Daily user analytics generation completed",
            success=result.get('success'),
            generated=result.get('generated', 0),
            skipped=result.get('skipped', 0),
            failed=result.get('failed', 0)
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to generate daily user analytics", error=str(e))
        return {
            'success': False,
            'error': str(e)
        }


@celery_app.task(name='tasks.generate_user_analytics_weekly')
def generate_user_analytics_weekly():
    """
    Celery task to generate user analytics for all active users (weekly).
    Forces regeneration regardless of last run time.
    
    Returns:
        Analytics generation result dictionary
    """
    try:
        from services.generate_user_analytics import UserAnalyticsGenerator
        
        generator = UserAnalyticsGenerator()
        result = generator.generate_for_all_users(force=True)  # Force weekly snapshot
        
        logger.info(
            "Weekly user analytics generation completed",
            success=result.get('success'),
            generated=result.get('generated', 0),
            skipped=result.get('skipped', 0),
            failed=result.get('failed', 0)
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to generate weekly user analytics", error=str(e))
        return {
            'success': False,
            'error': str(e)
        }


# Configure periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    # User Analytics
    'generate-user-analytics-daily': {
        'task': 'tasks.generate_user_analytics_daily',
        'schedule': 86400.0,  # Every day (for testing)
        # For production, use: 'schedule': crontab(hour=2, minute=0)  # Daily at 02:00
    },
    'generate-user-analytics-weekly': {
        'task': 'tasks.generate_user_analytics_weekly',
        'schedule': 604800.0,  # Every 7 days (for testing)
        # For production, use: 'schedule': crontab(day_of_week=1, hour=3, minute=0)  # Monday 03:00
    },
    # Comment Statistics
    'generate-daily-comment-stats': {
        'task': 'tasks.generate_daily_comment_statistics',
        'schedule': 3600.0,  # Every hour (for testing, change to crontab for daily)
        # For production, use: 'schedule': crontab(hour=0, minute=5)  # Daily at 00:05
    },
    'generate-weekly-comment-stats': {
        'task': 'tasks.generate_weekly_comment_statistics',
        'schedule': 86400.0,  # Every day (for testing, change to weekly)
        # For production, use: 'schedule': crontab(day_of_week=1, hour=1, minute=0)  # Monday 01:00
    },
    'generate-monthly-comment-stats': {
        'task': 'tasks.generate_monthly_comment_statistics',
        'schedule': 86400.0,  # Every day (for testing, change to monthly)
        # For production, use: 'schedule': crontab(day_of_month=1, hour=2, minute=0)  # 1st day 02:00
    },
}

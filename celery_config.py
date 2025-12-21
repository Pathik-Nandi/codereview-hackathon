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

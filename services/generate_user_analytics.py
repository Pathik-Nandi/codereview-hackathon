#!/usr/bin/env python3
"""
Generate User Analytics on Schedule

This script generates user analytics for all active users who have PRs.
Similar to generate_comment_statistics.py but for user analytics.

Usage:
    python3.10 generate_user_analytics.py --period daily
    python3.10 generate_user_analytics.py --period weekly
    python3.10 generate_user_analytics.py --force
    
Cron Examples:
    # Daily at 02:00
    0 2 * * * cd /path/to/codereview && python3.10 services/generate_user_analytics.py --period daily
    
    # Weekly on Monday at 03:00
    0 3 * * 1 cd /path/to/codereview && python3.10 services/generate_user_analytics.py --period weekly
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.database_service import DatabaseService
from services.analytics_service import AnalyticsService
from agents.analytics_processing_agent import AnalyticsProcessingAgent
from utils.logger import logger


class UserAnalyticsGenerator:
    """Service for generating scheduled user analytics."""
    
    def __init__(self):
        """Initialize the service."""
        self.db_service = DatabaseService()
        self.analytics_service = AnalyticsService(self.db_service)
        self.analytics_agent = AnalyticsProcessingAgent(self.db_service, self.analytics_service)
    
    def get_active_users(self, min_prs: int = 1) -> List[tuple]:
        """
        Get list of active users who have PRs.
        
        Args:
            min_prs: Minimum number of PRs required
            
        Returns:
            List of tuples (author_login, author_email, author_name, pr_count)
        """
        with self.db_service.get_session() as session:
            result = session.execute(text('''
                SELECT DISTINCT 
                    author_login, 
                    author_email, 
                    author_name,
                    COUNT(*) as pr_count
                FROM pr_analysis
                WHERE author_login IS NOT NULL
                GROUP BY author_login, author_email, author_name
                HAVING COUNT(*) >= :min_prs
                ORDER BY COUNT(*) DESC
            '''), {'min_prs': min_prs}).fetchall()
            
            return result
    
    def generate_for_user(
        self,
        author_login: str,
        author_email: str = None,
        author_name: str = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Generate analytics for a single user.
        
        Args:
            author_login: GitHub username
            author_email: User's email
            author_name: User's full name
            force: Force regeneration even if recent snapshot exists
            
        Returns:
            Result dictionary with success status
        """
        try:
            result = self.analytics_agent.process_user_analytics(
                author_login=author_login,
                author_email=author_email,
                author_name=author_name,
                force=force
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to generate analytics for user",
                author=author_login,
                error=str(e)
            )
            return {
                'success': False,
                'error': str(e),
                'author_login': author_login
            }
    
    def generate_for_all_users(self, force: bool = False) -> Dict[str, Any]:
        """
        Generate analytics for all active users.
        
        Args:
            force: Force regeneration for all users
            
        Returns:
            Summary of generation results
        """
        start_time = datetime.now(timezone.utc)
        
        logger.info("Starting user analytics generation for all users")
        
        # Get all active users
        users = self.get_active_users(min_prs=1)
        
        if not users:
            logger.warning("No active users found")
            return {
                'success': False,
                'message': 'No active users found',
                'users_processed': 0
            }
        
        logger.info(f"Found {len(users)} active users to process")
        
        results = {
            'success': True,
            'total_users': len(users),
            'generated': 0,
            'skipped': 0,
            'failed': 0,
            'details': []
        }
        
        for user in users:
            author_login, author_email, author_name, pr_count = user
            
            result = self.generate_for_user(
                author_login=author_login,
                author_email=author_email,
                author_name=author_name,
                force=force
            )
            
            user_result = {
                'author_login': author_login,
                'pr_count': pr_count,
                'success': result.get('success'),
                'skipped': result.get('skipped', False)
            }
            
            if result.get('success'):
                if result.get('skipped'):
                    results['skipped'] += 1
                    user_result['reason'] = result.get('reason')
                else:
                    results['generated'] += 1
                    user_result['analytics_id'] = result.get('analytics_id')
            else:
                results['failed'] += 1
                user_result['error'] = result.get('error')
            
            results['details'].append(user_result)
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        results['duration_seconds'] = round(duration, 2)
        
        logger.info(
            "User analytics generation completed",
            total=results['total_users'],
            generated=results['generated'],
            skipped=results['skipped'],
            failed=results['failed'],
            duration=results['duration_seconds']
        )
        
        return results


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate user analytics for all active users'
    )
    parser.add_argument(
        '--period',
        type=str,
        choices=['daily', 'weekly'],
        default='daily',
        help='Generation period (default: daily). Affects logging only.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration even if recent analytics exist (ignores 4-hour rule)'
    )
    parser.add_argument(
        '--min-prs',
        type=int,
        default=1,
        help='Minimum PRs required for a user to be processed (default: 1)'
    )
    return parser.parse_args()


def print_generation_header(args):
    """Print generation header with configuration."""
    print("=" * 80)
    print("User Analytics Generator")
    print("=" * 80)
    print(f"Period: {args.period}")
    print(f"Force: {args.force}")
    print(f"Min PRs: {args.min_prs}")
    print("=" * 80)
    print()


def format_detail_status(detail):
    """Format status for a detail entry."""
    if detail['success'] and not detail['skipped']:
        return '✅'
    elif detail['skipped']:
        return '⏭️'
    else:
        return '❌'


def format_detail_message(detail):
    """Format message for a detail entry."""
    status = format_detail_status(detail)
    msg = f"  {status} {detail['author_login']} ({detail['pr_count']} PRs)"
    
    if detail.get('analytics_id'):
        msg += f" - ID: {detail['analytics_id']}"
    elif detail.get('reason'):
        msg += f" - {detail['reason']}"
    elif detail.get('error'):
        msg += f" - Error: {detail['error'][:50]}"
    
    return msg


def print_generation_summary(results):
    """Print generation summary."""
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if not results.get('success'):
        print(f"⚠️  {results.get('message', 'Unknown error')}")
        return
    
    print(f"✅ Successfully generated: {results['generated']}/{results['total_users']}")
    print(f"⏭️  Skipped (recent): {results['skipped']}/{results['total_users']}")
    print(f"❌ Failed: {results['failed']}/{results['total_users']}")
    print(f"⏱️  Duration: {results['duration_seconds']}s")
    
    # Show details
    if results['details']:
        print("\nDetails:")
        for detail in results['details']:
            print(format_detail_message(detail))


def main():
    """Main entry point for user analytics generation."""
    args = parse_arguments()
    print_generation_header(args)
    
    try:
        generator = UserAnalyticsGenerator()
        
        # Override min_prs if provided
        if args.min_prs > 1:
            generator.get_active_users = lambda: generator.get_active_users(min_prs=args.min_prs)
        
        results = generator.generate_for_all_users(force=args.force)
        
        print_generation_summary(results)
        print("=" * 80)
        
        # Exit with appropriate code
        exit_code = 1 if results.get('failed', 0) > 0 else 0
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error("Failed to generate user analytics", error=str(e), exc_info=True)
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Generate PR Comment Statistics

This script aggregates comment data from the pr_comments table and generates
statistics records in the pr_comment_statistics table.

Usage:
    python3 generate_comment_statistics.py --period daily
    python3 generate_comment_statistics.py --period weekly
    python3 generate_comment_statistics.py --period monthly
    python3 generate_comment_statistics.py --period all
    
Cron Examples:
    # Daily at 00:05
    5 0 * * * cd /path/to/codereview && python3 generate_comment_statistics.py --period daily
    
    # Weekly on Monday at 01:00
    0 1 * * 1 cd /path/to/codereview && python3 generate_comment_statistics.py --period weekly
    
    # Monthly on 1st at 02:00
    0 2 1 * * cd /path/to/codereview && python3 generate_comment_statistics.py --period monthly
"""
import argparse
import sys
from datetime import datetime, timedelta
from services.comment_statistics_service import CommentStatisticsService
from utils.logger import logger


def main():
    """Main entry point for comment statistics generation."""
    parser = argparse.ArgumentParser(
        description='Generate PR comment statistics for analytics'
    )
    parser.add_argument(
        '--period',
        type=str,
        choices=['daily', 'weekly', 'monthly', 'all'],
        default='daily',
        help='Statistics period to generate (default: daily)'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Specific date to process (format: YYYY-MM-DD). Defaults to yesterday/last period.'
    )
    parser.add_argument(
        '--backfill',
        type=int,
        help='Backfill statistics for the last N days/weeks/months'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration even if statistics already exist'
    )
    
    args = parser.parse_args()
    
    service = CommentStatisticsService()
    
    print("=" * 80)
    print("PR Comment Statistics Generator")
    print("=" * 80)
    print(f"Period: {args.period}")
    print(f"Date: {args.date or 'auto (previous period)'}")
    print(f"Backfill: {args.backfill or 'no'}")
    print(f"Force: {args.force}")
    print("=" * 80)
    print()
    
    results = []
    
    try:
        if args.period == 'all':
            periods = ['daily', 'weekly', 'monthly']
        else:
            periods = [args.period]
        
        for period in periods:
            print(f"\n📊 Generating {period.upper()} statistics...")
            print("-" * 80)
            
            if args.backfill:
                # Backfill multiple periods
                results.extend(
                    _backfill_statistics(service, period, args.backfill, args.force)
                )
            else:
                # Generate single period
                result = _generate_single_period(service, period, args.date, args.force)
                results.append(result)
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        success_count = sum(1 for r in results if r.get('success'))
        total_comments = sum(r.get('total_comments', 0) for r in results if r.get('success'))
        
        print(f"✅ Successfully generated: {success_count}/{len(results)} statistics")
        print(f"📝 Total comments processed: {total_comments}")
        
        if success_count < len(results):
            print(f"⚠️  Failed: {len(results) - success_count}")
            print("\nFailed periods:")
            for r in results:
                if not r.get('success'):
                    print(f"  - {r.get('period', 'unknown')}: {r.get('message', 'unknown error')}")
        
        print("=" * 80)
        
        # Exit with error code if any failed
        sys.exit(0 if success_count == len(results) else 1)
        
    except Exception as e:
        logger.error("Failed to generate statistics", error=str(e), exc_info=True)
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


def _generate_single_period(
    service: CommentStatisticsService, 
    period: str, 
    date_str: str = None,
    force: bool = False
) -> dict:
    """Generate statistics for a single period."""
    target_date = None
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"❌ Invalid date format: {date_str} (expected YYYY-MM-DD)")
            return {'success': False, 'message': 'Invalid date format', 'period': period}
    
    if period == 'daily':
        result = service.generate_daily_statistics(target_date)
    elif period == 'weekly':
        result = service.generate_weekly_statistics(target_date)
    elif period == 'monthly':
        if target_date:
            result = service.generate_monthly_statistics(
                year=target_date.year,
                month=target_date.month
            )
        else:
            result = service.generate_monthly_statistics()
    else:
        result = {'success': False, 'message': f'Unknown period: {period}'}
    
    # Print result
    if result.get('success'):
        print(f"✅ Generated statistics (ID: {result.get('statistics_id')})")
        date_display = result.get('date') or result.get('week_start')
        if not date_display and result.get('year'):
            date_display = f"{result.get('year')}-{result.get('month'):02}"
        print(f"   Date: {date_display}")
        print(f"   Total comments: {result.get('total_comments', 0)}")
    else:
        message = result.get('message', 'Unknown error')
        if 'already exist' in message and not force:
            print(f"ℹ️  {message} (use --force to regenerate)")
        else:
            print(f"⚠️  {message}")
    
    result['period'] = period
    return result


def _backfill_statistics(
    service: CommentStatisticsService,
    period: str,
    count: int,
    force: bool = False
) -> list:
    """Backfill statistics for multiple periods."""
    results = []
    
    print(f"Backfilling last {count} {period} periods...")
    
    for i in range(count, 0, -1):
        if period == 'daily':
            target_date = datetime.now() - timedelta(days=i)
            date_str = target_date.strftime('%Y-%m-%d')
            print(f"\n  [{count - i + 1}/{count}] Processing {date_str}...")
            result = service.generate_daily_statistics(target_date)
            
        elif period == 'weekly':
            target_date = datetime.now() - timedelta(weeks=i)
            # Set to Monday
            target_date = target_date - timedelta(days=target_date.weekday())
            date_str = target_date.strftime('%Y-%m-%d')
            print(f"\n  [{count - i + 1}/{count}] Processing week starting {date_str}...")
            result = service.generate_weekly_statistics(target_date)
            
        elif period == 'monthly':
            current_date = datetime.now()
            # Go back i months
            year = current_date.year
            month = current_date.month - i
            while month <= 0:
                month += 12
                year -= 1
            
            print(f"\n  [{count - i + 1}/{count}] Processing {year}-{month:02d}...")
            result = service.generate_monthly_statistics(year, month)
        
        else:
            result = {'success': False, 'message': f'Unknown period: {period}'}
        
        # Print inline result
        if result.get('success'):
            print(f"     ✅ Success - {result.get('total_comments', 0)} comments")
        else:
            message = result.get('message', 'Unknown error')
            if 'already exist' in message and not force:
                print(f"     ⏭️  Skipped - {message}")
            else:
                print(f"     ⚠️  Failed - {message}")
        
        result['period'] = period
        results.append(result)
    
    return results


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Script to delete comments from GitHub Pull Requests.
Can delete:
1. Review comments (inline comments on code)
2. Issue comments (general PR comments)
3. All comments by a specific user (e.g., bot)
"""

import os
import sys
from github import Github, GithubException
import structlog

logger = structlog.get_logger(__name__)


class PRCommentDeleter:
    """Delete comments from GitHub Pull Requests."""
    
    def __init__(self, token: str = None):
        """Initialize with GitHub token."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token not found. Set GITHUB_TOKEN environment variable.")
        
        self.github = Github(self.token)
        self.user = self.github.get_user()
        logger.info(f"Authenticated as: {self.user.login}")
    
    def delete_pr_comments(
        self, 
        repository: str, 
        pr_number: int, 
        comment_type: str = "all",
        dry_run: bool = True
    ):
        """
        Delete comments from a specific PR.
        
        Args:
            repository: Repository in format 'owner/repo'
            pr_number: PR number
            comment_type: Type of comments to delete
                - "all": Delete all comments
                - "review": Delete only review comments (inline)
                - "issue": Delete only issue comments (general PR comments)
                - "bot": Delete only comments by the authenticated bot user
            dry_run: If True, only show what would be deleted without actually deleting
        
        Returns:
            dict with deletion results
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            results = {
                'review_comments_deleted': 0,
                'issue_comments_deleted': 0,
                'errors': []
            }
            
            logger.info(f"Processing PR #{pr_number} in {repository}")
            logger.info(f"Mode: {'DRY RUN' if dry_run else 'DELETE'}")
            logger.info(f"Filter: {comment_type}")
            
            # Delete review comments (inline comments)
            if comment_type in ["all", "review", "bot"]:
                review_comments = pr.get_review_comments()
                for comment in review_comments:
                    should_delete = self._should_delete_comment(comment, comment_type)
                    if should_delete:
                        # Get position info safely
                        position = getattr(comment, 'position', None) or getattr(comment, 'original_position', 'N/A')
                        logger.info(
                            f"  Review comment by {comment.user.login} on {comment.path}:{position}"
                        )
                        logger.info(f"    Preview: {comment.body[:100]}...")
                        
                        if not dry_run:
                            try:
                                comment.delete()
                                results['review_comments_deleted'] += 1
                                logger.info("    ✓ Deleted")
                            except GithubException as e:
                                error_msg = f"Failed to delete review comment {comment.id}: {e}"
                                logger.error(error_msg)
                                results['errors'].append(error_msg)
                        else:
                            logger.info("    [DRY RUN] Would delete")
                            results['review_comments_deleted'] += 1
            
            # Delete issue comments (general PR comments)
            if comment_type in ["all", "issue", "bot"]:
                issue_comments = pr.get_issue_comments()
                for comment in issue_comments:
                    should_delete = self._should_delete_comment(comment, comment_type)
                    if should_delete:
                        logger.info(f"  Issue comment by {comment.user.login}")
                        logger.info(f"    Preview: {comment.body[:100]}...")
                        
                        if not dry_run:
                            try:
                                comment.delete()
                                results['issue_comments_deleted'] += 1
                                logger.info("    ✓ Deleted")
                            except GithubException as e:
                                error_msg = f"Failed to delete issue comment {comment.id}: {e}"
                                logger.error(error_msg)
                                results['errors'].append(error_msg)
                        else:
                            logger.info("    [DRY RUN] Would delete")
                            results['issue_comments_deleted'] += 1
            
            # Summary
            total = results['review_comments_deleted'] + results['issue_comments_deleted']
            logger.info(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
            logger.info(f"  Review comments: {results['review_comments_deleted']}")
            logger.info(f"  Issue comments: {results['issue_comments_deleted']}")
            logger.info(f"  Total: {total}")
            logger.info(f"  Errors: {len(results['errors'])}")
            
            return results
            
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting comments: {e}", exc_info=True)
            raise
    
    def delete_all_bot_comments(
        self, 
        repository: str, 
        start_pr: int = 1, 
        end_pr: int = None,
        dry_run: bool = True
    ):
        """
        Delete all bot comments from multiple PRs.
        
        Args:
            repository: Repository in format 'owner/repo'
            start_pr: Starting PR number
            end_pr: Ending PR number (if None, process only start_pr)
            dry_run: If True, only show what would be deleted
        
        Returns:
            dict with aggregate results
        """
        if end_pr is None:
            end_pr = start_pr
        
        aggregate_results = {
            'prs_processed': 0,
            'total_review_comments_deleted': 0,
            'total_issue_comments_deleted': 0,
            'errors': []
        }
        
        logger.info(f"Processing PRs #{start_pr} to #{end_pr}")
        
        for pr_num in range(start_pr, end_pr + 1):
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"PR #{pr_num}")
                logger.info('='*60)
                
                results = self.delete_pr_comments(
                    repository=repository,
                    pr_number=pr_num,
                    comment_type="bot",
                    dry_run=dry_run
                )
                
                aggregate_results['prs_processed'] += 1
                aggregate_results['total_review_comments_deleted'] += results['review_comments_deleted']
                aggregate_results['total_issue_comments_deleted'] += results['issue_comments_deleted']
                aggregate_results['errors'].extend(results['errors'])
                
            except GithubException as e:
                if e.status == 404:
                    logger.warning(f"PR #{pr_num} not found, skipping...")
                else:
                    error_msg = f"Error processing PR #{pr_num}: {e}"
                    logger.error(error_msg)
                    aggregate_results['errors'].append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error with PR #{pr_num}: {e}"
                logger.error(error_msg, exc_info=True)
                aggregate_results['errors'].append(error_msg)
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"FINAL SUMMARY {'(DRY RUN)' if dry_run else ''}")
        logger.info('='*60)
        logger.info(f"PRs processed: {aggregate_results['prs_processed']}")
        logger.info(f"Total review comments: {aggregate_results['total_review_comments_deleted']}")
        logger.info(f"Total issue comments: {aggregate_results['total_issue_comments_deleted']}")
        logger.info(f"Total errors: {len(aggregate_results['errors'])}")
        
        return aggregate_results
    
    def _should_delete_comment(self, comment, comment_type: str) -> bool:
        """Determine if a comment should be deleted based on type filter."""
        if comment_type == "all":
            return True
        elif comment_type == "bot":
            # Delete only if comment is by the authenticated user (bot)
            return comment.user.login == self.user.login
        else:
            # For "review" and "issue" types, handled by filtering in main logic
            return True


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Delete comments from GitHub Pull Requests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - see what would be deleted from PR #1
  python delete_pr_comments.py -r owner/repo -p 1 --dry-run
  
  # Delete all bot comments from PR #1
  python delete_pr_comments.py -r owner/repo -p 1 --type bot
  
  # Delete all comments from PR #1 (requires confirmation)
  python delete_pr_comments.py -r owner/repo -p 1 --type all
  
  # Delete bot comments from PRs #1-5
  python delete_pr_comments.py -r owner/repo --start 1 --end 5 --type bot
  
  # Delete only review comments (inline) from PR #1
  python delete_pr_comments.py -r owner/repo -p 1 --type review
  
  # Delete only issue comments (general) from PR #1
  python delete_pr_comments.py -r owner/repo -p 1 --type issue
        """
    )
    
    parser.add_argument(
        '-r', '--repository',
        required=True,
        help='Repository in format owner/repo'
    )
    
    parser.add_argument(
        '-p', '--pr',
        type=int,
        help='Single PR number to process'
    )
    
    parser.add_argument(
        '--start',
        type=int,
        help='Starting PR number for batch processing'
    )
    
    parser.add_argument(
        '--end',
        type=int,
        help='Ending PR number for batch processing'
    )
    
    parser.add_argument(
        '--type',
        choices=['all', 'review', 'issue', 'bot'],
        default='bot',
        help='Type of comments to delete (default: bot)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    parser.add_argument(
        '--token',
        help='GitHub token (or use GITHUB_TOKEN env var)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.pr and not (args.start and args.end):
        parser.error("Either --pr or both --start and --end must be specified")
    
    if args.pr and (args.start or args.end):
        parser.error("Cannot use --pr with --start/--end")
    
    # Confirm if not dry run and deleting all comments
    if not args.dry_run and args.type in ['all']:
        confirm = input(
            f"⚠️  WARNING: This will delete ALL {args.type} comments from the specified PR(s)!\n"
            "Type 'DELETE' to confirm: "
        )
        if confirm != "DELETE":
            print("Aborted.")
            sys.exit(0)
    
    try:
        deleter = PRCommentDeleter(token=args.token)
        
        if args.pr:
            # Single PR
            deleter.delete_pr_comments(
                repository=args.repository,
                pr_number=args.pr,
                comment_type=args.type,
                dry_run=args.dry_run
            )
        else:
            # Multiple PRs
            deleter.delete_all_bot_comments(
                repository=args.repository,
                start_pr=args.start,
                end_pr=args.end,
                dry_run=args.dry_run
            )
        
        if args.dry_run:
            print("\n✓ Dry run complete. Use without --dry-run to actually delete comments.")
        else:
            print("\n✓ Comments deleted successfully!")
        
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

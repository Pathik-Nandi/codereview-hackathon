#!/usr/bin/env python3
"""Script to delete all comments from specified PRs."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github import Github, GithubException
from utils.config import config


def delete_pr_comments(repository: str, pr_numbers: list):
    """
    Delete all comments from specified PRs.
    
    Args:
        repository: Repository full name (owner/repo)
        pr_numbers: List of PR numbers to delete comments from
    """
    github = Github(config.github_token)
    repo = github.get_repo(repository)
    
    for pr_number in pr_numbers:
        print(f"\n{'='*50}")
        print(f"Processing PR #{pr_number}")
        print('='*50)
        
        try:
            pr = repo.get_pull(pr_number)
            
            # Delete issue comments (regular comments)
            print(f"\nDeleting issue comments from PR #{pr_number}...")
            issue = repo.get_issue(pr_number)
            issue_comments = list(issue.get_comments())
            issue_comment_count = 0
            for comment in issue_comments:
                try:
                    comment.delete()
                    issue_comment_count += 1
                    print(f"  Deleted issue comment {comment.id}")
                except GithubException as e:
                    print(f"  Failed to delete issue comment {comment.id}: {e}")
            print(f"  Total issue comments deleted: {issue_comment_count}")
            
            # Delete review comments (inline comments)
            print(f"\nDeleting review comments from PR #{pr_number}...")
            review_comments = list(pr.get_review_comments())
            review_comment_count = 0
            for comment in review_comments:
                try:
                    comment.delete()
                    review_comment_count += 1
                    print(f"  Deleted review comment {comment.id}")
                except GithubException as e:
                    print(f"  Failed to delete review comment {comment.id}: {e}")
            print(f"  Total review comments deleted: {review_comment_count}")
            
            print(f"\n✅ PR #{pr_number}: Deleted {issue_comment_count} issue comments and {review_comment_count} review comments")
            
        except GithubException as e:
            print(f"❌ Failed to process PR #{pr_number}: {e}")


if __name__ == "__main__":
    repository = "tarentomaheshvakkund/testdata-hackathon"
    pr_numbers = [6, 7, 8, 9]
    
    print(f"Deleting comments from PRs {pr_numbers} in {repository}")
    delete_pr_comments(repository, pr_numbers)
    print("\n" + "="*50)
    print("Done!")

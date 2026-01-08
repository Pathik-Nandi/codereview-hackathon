"""GitHub service for interacting with GitHub API."""
import hmac
import hashlib
from typing import Optional
from github import Github, GithubException
from models.pr_event import PREvent, PRFile
from utils.logger import logger
from utils.config import config


class GitHubService:
    """Service for GitHub API interactions."""
    
    def __init__(self):
        """Initialize GitHub service."""
        self.logger = logger.bind(service="github")
        self.github = Github(config.github_token)
        self.webhook_secret = config.github_webhook_secret
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify GitHub webhook signature.
        
        Args:
            payload: The webhook payload
            signature: The signature from GitHub
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            self.logger.warning("Webhook secret not configured")
            return True
        
        expected_signature = 'sha256=' + hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def _is_valid_commit_email(self, email: str) -> bool:
        """Check if email is valid (not a noreply address)."""
        return email and 'noreply.github.com' not in email
    
    def _extract_email_from_commit(self, commit, pr_author_login: str) -> Optional[str]:
        """Extract email from a single commit if author matches PR author."""
        try:
            # Check if we have commit author data
            if not (commit.commit and commit.commit.author and commit.commit.author.email):
                return None

            email = commit.commit.author.email

            # Only validate email format, don't check GitHub user match
            # (email may not be associated with any GitHub account)
            return email if self._is_valid_commit_email(email) else None

        except Exception as commit_error:
            self.logger.debug("Error checking commit for email", error=str(commit_error))
            return None
    
    def get_author_email_from_commits(self, repository: str, pr_number: int) -> Optional[str]:
        """
        Try to get author email from PR commits.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            commits = pr.get_commits()
            
            # Try to get email from commits by the PR author
            for commit in commits:
                email = self._extract_email_from_commit(commit, pr.user.login)
                if email:
                    self.logger.info(
                        "Found author email from commits",
                        repository=repository,
                        pr_number=pr_number,
                        email=email
                    )
                    return email
            
            self.logger.debug(
                "No valid email found in commits",
                repository=repository,
                pr_number=pr_number
            )
            return None
            
        except Exception as e:
            self.logger.error(
                "Failed to get author email from commits",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return None
    
    def get_pr_details(self, repository: str, pr_number: int) -> Optional[dict]:
        """
        Get PR details from GitHub.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            Dictionary with PR details or None if not found
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            # Try to get email from user object first
            author_email = getattr(pr.user, 'email', None)
            
            # If not available, try to get from commits
            if not author_email or 'noreply.github.com' in author_email:
                commit_email = self.get_author_email_from_commits(repository, pr_number)
                if commit_email:
                    author_email = commit_email
            
            details = {
                'title': pr.title,
                'body': pr.body or '',
                'state': pr.state,
                'draft': pr.draft if hasattr(pr, 'draft') else False,
                'user': {
                    'login': pr.user.login,
                    'id': pr.user.id,
                    'email': author_email,
                    'name': getattr(pr.user, 'name', None)
                },
                'head': {
                    'ref': pr.head.ref,
                    'sha': pr.head.sha  # Required for inline comments
                },
                'base': {
                    'ref': pr.base.ref,
                    'sha': pr.base.sha
                },
                'created_at': pr.created_at.isoformat() if pr.created_at else None,
                'updated_at': pr.updated_at.isoformat() if pr.updated_at else None
            }
            
            self.logger.info(
                "Retrieved PR details",
                repository=repository,
                pr_number=pr_number,
                title=pr.title,
                author_email=author_email
            )
            
            return details
            
        except GithubException as e:
            self.logger.error(
                "Failed to get PR details",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return None
    
    def get_pr_files(self, repository: str, pr_number: int) -> list:
        """
        Get files changed in a PR.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            List of PRFile objects
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            files = []
            for file in pr.get_files():
                files.append(PRFile(
                    filename=file.filename,
                    status=file.status,
                    additions=file.additions,
                    deletions=file.deletions,
                    changes=file.changes,
                    patch=file.patch
                ))
            
            self.logger.info(
                "Retrieved PR files",
                repository=repository,
                pr_number=pr_number,
                file_count=len(files)
            )
            
            return files
            
        except GithubException as e:
            self.logger.error(
                "Failed to get PR files",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            raise
    
    def has_existing_comments_or_reviews(self, repository: str, pr_number: int) -> bool:
        """
        Check if a PR already has any comments or reviews.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            True if PR has existing comments or reviews, False otherwise
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            # Check for issue comments
            issue_comments_count = pr.get_issue_comments().totalCount
            if issue_comments_count > 0:
                self.logger.info(
                    "PR has existing issue comments",
                    repository=repository,
                    pr_number=pr_number,
                    count=issue_comments_count
                )
                return True
            
            # Check for review comments
            review_comments_count = pr.get_review_comments().totalCount
            if review_comments_count > 0:
                self.logger.info(
                    "PR has existing review comments",
                    repository=repository,
                    pr_number=pr_number,
                    count=review_comments_count
                )
                return True
            
            # Check for PR reviews
            reviews_count = pr.get_reviews().totalCount
            if reviews_count > 0:
                self.logger.info(
                    "PR has existing reviews",
                    repository=repository,
                    pr_number=pr_number,
                    count=reviews_count
                )
                return True
            
            self.logger.info(
                "PR has no existing comments or reviews",
                repository=repository,
                pr_number=pr_number
            )
            return False
            
        except GithubException as e:
            self.logger.error(
                "Failed to check for existing comments/reviews",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            # In case of error, return False to allow processing
            return False
    
    def find_summary_comment(self, repository: str, pr_number: int, signature: str = "## 🤖 Automated Code Review Results") -> Optional[dict]:
        """
        Search for an existing summary comment by the bot on a PR.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            signature: The unique string to identify the bot's summary
            
        Returns:
            Dict with comment details if found, None otherwise
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            for comment in pr.get_issue_comments():
                if signature in comment.body:
                    self.logger.info(
                        "Found existing bot summary comment",
                        repository=repository,
                        pr_number=pr_number,
                        comment_id=comment.id
                    )
                    return {
                        'id': comment.id,
                        'body': comment.body,
                        'html_url': comment.html_url
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(
                "Failed to search for existing summary comment",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return None

    def post_comment(self, repository: str, pr_number: int, comment: str) -> Optional[dict]:
        """
        Post a comment on a PR.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            comment: Comment text
            
        Returns:
            Dict with comment details if successful, None otherwise
            Dict contains: {'id': int, 'body': str, 'html_url': str, 'created_at': str}
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            comment_obj = pr.create_issue_comment(comment)
            
            self.logger.info(
                "Posted PR comment",
                repository=repository,
                pr_number=pr_number,
                comment_id=comment_obj.id
            )
            
            return {
                'id': comment_obj.id,
                'body': comment_obj.body,
                'html_url': comment_obj.html_url,
                'created_at': comment_obj.created_at.isoformat() if comment_obj.created_at else None
            }
            
        except GithubException as e:
            self.logger.error(
                "Failed to post comment",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return None
    
    def create_review(
        self, 
        repository: str, 
        pr_number: int, 
        event: str,
        body: Optional[str] = None
    ) -> bool:
        """
        Create a PR review.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            event: Review event (APPROVE, REQUEST_CHANGES, COMMENT)
            body: Review body text
            
        Returns:
            True if successful
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            pr.create_review(body=body, event=event)
            
            self.logger.info(
                "Created PR review",
                repository=repository,
                pr_number=pr_number,
                event=event
            )
            
            return True
            
        except GithubException as e:
            self.logger.error(
                "Failed to create review",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return False
    
    def request_changes(self, repository: str, pr_number: int, body: str) -> bool:
        """Request changes on a PR."""
        return self.create_review(repository, pr_number, "REQUEST_CHANGES", body)
    
    def approve_pr(self, repository: str, pr_number: int, body: str) -> bool:
        """Approve a PR."""
        return self.create_review(repository, pr_number, "APPROVE", body)
    
    def merge_pr(
        self, 
        repository: str, 
        pr_number: int, 
        merge_method: str = "squash",
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        delete_branch: bool = True
    ) -> dict:
        """
        Merge a pull request.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            merge_method: Merge method (merge, squash, rebase)
            commit_title: Custom commit title
            commit_message: Custom commit message
            delete_branch: Whether to delete the branch after merge
            
        Returns:
            Dictionary with merge result containing:
            - success: bool
            - sha: str (commit SHA if successful)
            - message: str (status message)
            - merged: bool
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            # Check if PR is already merged
            if pr.merged:
                self.logger.info(
                    "PR already merged",
                    repository=repository,
                    pr_number=pr_number
                )
                return {
                    'success': False,
                    'merged': True,
                    'message': 'PR is already merged',
                    'sha': pr.merge_commit_sha
                }
            
            # Check if PR is mergeable
            if pr.mergeable is False:
                self.logger.warning(
                    "PR is not mergeable",
                    repository=repository,
                    pr_number=pr_number,
                    mergeable_state=pr.mergeable_state
                )
                return {
                    'success': False,
                    'merged': False,
                    'message': f'PR is not mergeable (state: {pr.mergeable_state})',
                    'mergeable_state': pr.mergeable_state
                }
            
            # Perform the merge
            result = pr.merge(
                commit_title=commit_title,
                commit_message=commit_message,
                merge_method=merge_method
            )
            
            self.logger.info(
                "PR merged successfully",
                repository=repository,
                pr_number=pr_number,
                merge_method=merge_method,
                sha=result.sha
            )
            
            # Delete branch if requested
            if delete_branch and result.merged:
                try:
                    ref = repo.get_git_ref(f"heads/{pr.head.ref}")
                    ref.delete()
                    self.logger.info(
                        "Branch deleted after merge",
                        repository=repository,
                        branch=pr.head.ref
                    )
                except GithubException as e:
                    self.logger.warning(
                        "Failed to delete branch after merge",
                        repository=repository,
                        branch=pr.head.ref,
                        error=str(e)
                    )
            
            return {
                'success': True,
                'merged': result.merged,
                'sha': result.sha,
                'message': result.message
            }
            
        except GithubException as e:
            self.logger.error(
                "Failed to merge PR",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return {
                'success': False,
                'merged': False,
                'message': f'Merge failed: {str(e)}'
            }
    
    def get_pr_reviews(self, repository: str, pr_number: int) -> list:
        """
        Get all reviews for a PR.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            List of review objects with state and user info
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            reviews = pr.get_reviews()
            
            review_list = []
            for review in reviews:
                review_list.append({
                    'user': review.user.login,
                    'state': review.state,  # APPROVED, CHANGES_REQUESTED, COMMENTED
                    'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None
                })
            
            self.logger.info(
                "Retrieved PR reviews",
                repository=repository,
                pr_number=pr_number,
                review_count=len(review_list)
            )
            
            return review_list
            
        except GithubException as e:
            self.logger.error(
                "Failed to get PR reviews",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return []
    
    def check_pr_status_checks(self, repository: str, pr_number: int) -> dict:
        """
        Check the status of all CI/CD checks on a PR.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            Dictionary with status check results
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            commit = repo.get_commit(pr.head.sha)
            
            # Get combined status
            status = commit.get_combined_status()
            
            result = {
                'state': status.state,  # success, pending, failure
                'total_count': status.total_count,
                'statuses': []
            }
            
            for s in status.statuses:
                result['statuses'].append({
                    'context': s.context,
                    'state': s.state,
                    'description': s.description
                })
            
            self.logger.info(
                "Retrieved PR status checks",
                repository=repository,
                pr_number=pr_number,
                state=status.state,
                check_count=status.total_count
            )
            
            return result
            
        except GithubException as e:
            self.logger.error(
                "Failed to get PR status checks",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return {
                'state': 'unknown',
                'total_count': 0,
                'statuses': []
            }
    
    def post_inline_comment(
        self, 
        repository: str, 
        pr_number: int, 
        commit_sha: str,
        file_path: str,
        line_number: int,
        comment_body: str,
        side: str = "RIGHT"
    ) -> Optional[dict]:
        """
        Post an inline comment on a specific line of a PR file.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            commit_sha: Commit SHA to comment on
            file_path: Path to the file
            line_number: Line number to comment on
            comment_body: Comment text
            side: Which side of diff (RIGHT for new, LEFT for old)
            
        Returns:
            Dict with comment details if successful, None otherwise
            Dict contains: {'id': int, 'body': str, 'path': str, 'line': int}
            
        Note:
            GitHub API only allows comments on lines that are part of the PR's diff.
            If the line is not in the diff, a 422 error will be returned and this
            method will return None.
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            # Create review comment on specific line
            comment_obj = pr.create_review_comment(
                body=comment_body,
                commit=repo.get_commit(commit_sha),
                path=file_path,
                line=line_number,
                side=side
            )
            
            self.logger.info(
                "Posted inline PR comment",
                repository=repository,
                pr_number=pr_number,
                file=file_path,
                line=line_number,
                comment_id=comment_obj.id
            )
            
            try:
                return {
                    'id': comment_obj.id,
                    'body': comment_obj.body,
                    'path': comment_obj.path,
                    'line': comment_obj.line
                }
            except Exception as e:
                # If accessing properties fails, just return the ID
                self.logger.warning(
                    "Could not access all comment properties, returning ID only",
                    comment_id=comment_obj.id,
                    error=str(e)
                )
                return {
                    'id': comment_obj.id,
                    'body': comment_body,
                    'path': file_path,
                    'line': line_number
                }
            
        except GithubException as e:
            error_str = str(e)
            # Log different messages based on error type
            if "422" in error_str and "could not be resolved" in error_str.lower():
                self.logger.warning(
                    "Line not in PR diff - cannot post comment",
                    repository=repository,
                    pr_number=pr_number,
                    file=file_path,
                    line=line_number,
                    hint="Line may not be part of the PR changes or may be invalid"
                )
            else:
                self.logger.error(
                    "Failed to post inline comment",
                    repository=repository,
                    pr_number=pr_number,
                    file=file_path,
                    line=line_number,
                    error=error_str
                )
            return None
    
    def post_review_with_comments(
        self, 
        repository: str, 
        pr_number: int,
        commit_sha: str,
        review_body: str,
        review_event: str = "COMMENT",
        inline_comments: Optional[list] = None
    ) -> Optional[dict]:
        """
        Post a review with multiple inline comments at once.
        
        Args:
            repository: Repository full name (owner/repo)
            pr_number: PR number
            commit_sha: Commit SHA to review
            review_body: Main review body text
            review_event: APPROVE, REQUEST_CHANGES, or COMMENT
            inline_comments: List of dicts with keys:
                - path: str (file path)
                - line: int (line number)
                - body: str (comment text)
                - side: str (optional, defaults to "RIGHT")
            
        Returns:
            Dict with review data (id, html_url) if successful, None otherwise
        """
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            commit = repo.get_commit(commit_sha)
            
            # Build comments list for review
            comments = []
            if inline_comments:
                for comment in inline_comments:
                    comments.append({
                        'path': comment['path'],
                        'line': comment['line'],
                        'body': comment['body'],
                        'side': comment.get('side', 'RIGHT')
                    })
            
            # Create review with all comments
            review = pr.create_review(
                body=review_body,
                event=review_event,
                commit=commit,
                comments=comments if comments else None
            )
            
            self.logger.info(
                "Posted PR review with inline comments",
                repository=repository,
                pr_number=pr_number,
                review_event_type=review_event,
                comment_count=len(comments),
                review_id=review.id
            )
            
            # Return review data including GitHub IDs
            return {
                'id': review.id,
                'html_url': review.html_url,
                'state': review.state,
                'body': review.body
            }
            
        except GithubException as e:
            self.logger.error(
                "Failed to post review with comments",
                repository=repository,
                pr_number=pr_number,
                error=str(e)
            )
            return None
    
    def get_file_content_at_commit(
        self,
        repository: str,
        file_path: str,
        commit_sha: str
    ) -> Optional[dict]:
        """
        Get entire file content at a specific commit (for caching).
        
        Args:
            repository: Repository full name (owner/repo)
            file_path: Path to file in repository
            commit_sha: Commit SHA to get content from
            
        Returns:
            Dictionary with file lines or None if not found
        """
        try:
            repo = self.github.get_repo(repository)
            
            # Get file content at specific commit
            file_content = repo.get_contents(file_path, ref=commit_sha)
            
            if file_content.type != "file":
                return None
            
            # Decode content
            content = file_content.decoded_content.decode('utf-8')
            lines = content.split('\n')
            
            return {
                'file_path': file_path,
                'lines': lines,
                'total_lines': len(lines)
            }
            
        except GithubException as e:
            self.logger.error(
                "Failed to get file content at commit",
                repository=repository,
                file_path=file_path,
                commit_sha=commit_sha,
                error=str(e)
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error getting file content",
                repository=repository,
                file_path=file_path,
                error=str(e)
            )
            return None

    def get_file_content_at_line(
        self, 
        repository: str, 
        file_path: str, 
        line_number: int, 
        commit_sha: str,
        context_lines: int = 3
    ) -> Optional[dict]:
        """
        Get file content around a specific line.
        
        Args:
            repository: Repository full name (owner/repo)
            file_path: Path to file in repository
            line_number: Line number to get context for
            commit_sha: Commit SHA to get content from
            context_lines: Number of lines to include before and after
            
        Returns:
            Dictionary with code lines or None if not found
        """
        try:
            repo = self.github.get_repo(repository)
            
            # Get file content at specific commit
            file_content = repo.get_contents(file_path, ref=commit_sha)
            
            if file_content.type != "file":
                return None
            
            # Decode content
            content = file_content.decoded_content.decode('utf-8')
            lines = content.split('\n')
            
            # Calculate line range
            start_line = max(1, line_number - context_lines)
            end_line = min(len(lines), line_number + context_lines)
            
            # Extract lines with numbers
            code_lines = []
            for i in range(start_line - 1, end_line):
                code_lines.append({
                    'line_number': i + 1,
                    'content': lines[i] if i < len(lines) else '',
                    'is_target': (i + 1) == line_number
                })
            
            return {
                'file_path': file_path,
                'target_line': line_number,
                'start_line': start_line,
                'end_line': end_line,
                'lines': code_lines,
                'total_lines': len(lines)
            }
            
        except GithubException as e:
            self.logger.error(
                "Failed to get file content",
                repository=repository,
                file_path=file_path,
                line_number=line_number,
                commit_sha=commit_sha,
                error=str(e)
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error getting file content",
                repository=repository,
                file_path=file_path,
                error=str(e)
            )
            return None


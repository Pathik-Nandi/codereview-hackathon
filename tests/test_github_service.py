"""
Unit tests for GitHubService.

Tests the GitHub service's ability to:
- Fetch PR details from GitHub API
- Get PR files
- Post comments
- Verify webhook signatures
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime
import hmac
import hashlib


class TestGitHubService:
    """Tests for the GitHubService class."""
    
    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        mock = Mock()
        return mock
    
    @pytest.fixture
    def github_service(self, mock_github_client):
        """Create a GitHubService with mocked GitHub client."""
        with patch('services.github_service.Github', return_value=mock_github_client):
            with patch('services.github_service.config') as mock_config:
                mock_config.github_token = "test-token"
                mock_config.get.return_value = None
                from services.github_service import GitHubService
                return GitHubService()
    
    @pytest.mark.unit
    def test_github_service_initialization(self, github_service):
        """Test that GitHubService initializes correctly."""
        assert github_service.github is not None
        assert github_service.logger is not None
    
    @pytest.mark.unit
    def test_get_pr_details_success(self):
        """Test successful PR details fetch."""
        # Create mock datetime objects
        mock_created_at = datetime(2025, 12, 1, 10, 0, 0)
        mock_updated_at = datetime(2025, 12, 1, 12, 0, 0)
        
        mock_pr = Mock()
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.number = 42
        mock_pr.id = 1001
        mock_pr.draft = False
        mock_pr.user.login = "test-user"
        mock_pr.user.id = 12345
        mock_pr.user.email = None
        mock_pr.user.name = None
        mock_pr.base.ref = "main"
        mock_pr.head.ref = "feature/test"
        mock_pr.head.sha = "abc123"
        mock_pr.created_at = mock_created_at
        mock_pr.updated_at = mock_updated_at
        mock_pr.raw_data = {}
        
        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        
        mock_github = Mock()
        mock_github.get_repo.return_value = mock_repo
        
        with patch('services.github_service.Github', return_value=mock_github):
            with patch('services.github_service.config') as mock_config:
                mock_config.github_token = "test-token"
                from services.github_service import GitHubService
                service = GitHubService()
                
                result = service.get_pr_details("test-org/test-repo", 42)
                
                assert result is not None
                assert result['title'] == "Test PR"
                mock_repo.get_pull.assert_called_once_with(42)
    
    @pytest.mark.unit
    def test_get_pr_details_not_found(self):
        """Test handling of PR not found."""
        from github import GithubException
        
        mock_repo = Mock()
        mock_repo.get_pull.side_effect = GithubException(404, {"message": "Not Found"}, None)
        
        mock_github = Mock()
        mock_github.get_repo.return_value = mock_repo
        
        with patch('services.github_service.Github', return_value=mock_github):
            with patch('services.github_service.config') as mock_config:
                mock_config.github_token = "test-token"
                from services.github_service import GitHubService
                service = GitHubService()
                
                result = service.get_pr_details("test-org/test-repo", 999)
                
                assert result is None
    
    @pytest.mark.unit
    def test_get_pr_files(self):
        """Test fetching PR files."""
        mock_file1 = Mock()
        mock_file1.filename = "src/main.py"
        mock_file1.status = "modified"
        mock_file1.additions = 10
        mock_file1.deletions = 5
        mock_file1.changes = 15
        mock_file1.patch = "@@ -1,5 +1,10 @@\n+added line"
        
        mock_file2 = Mock()
        mock_file2.filename = "src/utils.py"
        mock_file2.status = "added"
        mock_file2.additions = 50
        mock_file2.deletions = 0
        mock_file2.changes = 50
        mock_file2.patch = None
        
        mock_pr = Mock()
        mock_pr.get_files.return_value = [mock_file1, mock_file2]
        
        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        
        mock_github = Mock()
        mock_github.get_repo.return_value = mock_repo
        
        with patch('services.github_service.Github', return_value=mock_github):
            with patch('services.github_service.config') as mock_config:
                mock_config.github_token = "test-token"
                from services.github_service import GitHubService
                service = GitHubService()
                
                files = service.get_pr_files("test-org/test-repo", 42)
                
                assert len(files) == 2
                assert files[0].filename == "src/main.py"
                assert files[1].filename == "src/utils.py"
    
    @pytest.mark.unit
    def test_post_comment_success(self):
        """Test successful comment posting."""
        mock_comment = Mock()
        mock_comment.id = 12345
        
        mock_pr = Mock()
        mock_pr.create_issue_comment.return_value = mock_comment
        
        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        
        mock_github = Mock()
        mock_github.get_repo.return_value = mock_repo
        
        with patch('services.github_service.Github', return_value=mock_github):
            with patch('services.github_service.config') as mock_config:
                mock_config.github_token = "test-token"
                from services.github_service import GitHubService
                service = GitHubService()
                
                result = service.post_comment("test-org/test-repo", 42, "Test comment")
                
                assert result is True
                mock_pr.create_issue_comment.assert_called_once_with("Test comment")
    
    @pytest.mark.unit
    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification."""
        with patch('services.github_service.Github'):
            with patch('services.github_service.config') as mock_config:
                mock_config.github_token = "test-token"
                # Use a property mock to properly set the webhook secret
                type(mock_config).github_webhook_secret = PropertyMock(return_value="webhook-secret")
                mock_config.get.return_value = "webhook-secret"
                
                from services.github_service import GitHubService
                service = GitHubService()
                # Set the webhook_secret directly on the service
                service.webhook_secret = "webhook-secret"
                
                payload = b'{"action": "opened"}'
                secret = "webhook-secret"
                expected_sig = hmac.new(
                    secret.encode('utf-8'),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                signature = f"sha256={expected_sig}"
                
                result = service.verify_webhook_signature(payload, signature)
                
                assert result is True
    
    @pytest.mark.unit
    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature verification."""
        with patch('services.github_service.Github'):
            with patch('services.github_service.config') as mock_config:
                mock_config.github_token = "test-token"
                type(mock_config).github_webhook_secret = PropertyMock(return_value="webhook-secret")
                mock_config.get.return_value = "webhook-secret"
                
                from services.github_service import GitHubService
                service = GitHubService()
                # Set the webhook_secret directly on the service
                service.webhook_secret = "webhook-secret"
                
                payload = b'{"action": "opened"}'
                signature = "sha256=invalid_signature"
                
                result = service.verify_webhook_signature(payload, signature)
                
                assert result is False
    
    @pytest.mark.unit
    def test_create_review_success(self):
        """Test successful review creation."""
        mock_review = Mock()
        mock_review.id = 9999
        
        mock_pr = Mock()
        mock_pr.create_review.return_value = mock_review
        
        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        
        mock_github = Mock()
        mock_github.get_repo.return_value = mock_repo
        
        with patch('services.github_service.Github', return_value=mock_github):
            with patch('services.github_service.config') as mock_config:
                with patch('services.github_service.logger') as mock_logger:
                    mock_config.github_token = "test-token"
                    mock_logger.bind.return_value = Mock()
                    
                    from services.github_service import GitHubService
                    service = GitHubService()
                    # Mock the logger on the service instance
                    service.logger = Mock()
                    
                    result = service.create_review(
                        "test-org/test-repo",
                        42,
                        "COMMENT",
                        "Review body"
                    )
                    
                    assert result is True
                    mock_pr.create_review.assert_called_once()

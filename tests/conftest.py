"""
Pytest fixtures for PR Review System tests.

This module contains shared fixtures used across all test modules.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List


# ============================================================================
# PR Event Fixtures
# ============================================================================

@pytest.fixture
def sample_pr_author():
    """Create a sample PR author."""
    from models.pr_event import PRAuthor
    return PRAuthor(
        login="test-user",
        id=12345,
        avatar_url="https://github.com/avatars/test-user"
    )


@pytest.fixture
def sample_pr_file():
    """Create a sample PR file."""
    from models.pr_event import PRFile
    return PRFile(
        filename="src/main.py",
        status="modified",
        additions=10,
        deletions=5,
        changes=15,
        patch="@@ -1,5 +1,10 @@\n+def new_function():\n+    pass"
    )


@pytest.fixture
def sample_pr_files():
    """Create a list of sample PR files."""
    from models.pr_event import PRFile
    return [
        PRFile(
            filename="src/main.py",
            status="modified",
            additions=10,
            deletions=5,
            changes=15,
            patch="@@ -1,5 +1,10 @@\n+def new_function():\n+    pass"
        ),
        PRFile(
            filename="src/utils.py",
            status="added",
            additions=50,
            deletions=0,
            changes=50,
            patch="@@ -0,0 +1,50 @@\n+# New file content"
        ),
        PRFile(
            filename="tests/test_main.py",
            status="modified",
            additions=20,
            deletions=10,
            changes=30,
            patch="@@ -1,10 +1,20 @@\n+def test_new():\n+    assert True"
        )
    ]


@pytest.fixture
def sample_pr_event(sample_pr_author, sample_pr_files):
    """Create a sample PR event."""
    from models.pr_event import PREvent
    return PREvent(
        action="opened",
        id=1001,
        pr_number=42,
        pr_title="Add new feature",
        pr_description="This PR adds a new feature for testing.",
        pr_url="https://github.com/test-org/test-repo/pull/42",
        repository="test-org/test-repo",
        repository_url="https://github.com/test-org/test-repo",
        author=sample_pr_author,
        base_branch="main",
        head_branch="feature/new-feature",
        files=sample_pr_files,
        created_at=datetime(2025, 12, 1, 10, 0, 0),
        updated_at=datetime(2025, 12, 1, 12, 0, 0),
        is_draft=False
    )


# ============================================================================
# Analysis Result Fixtures
# ============================================================================

@pytest.fixture
def sample_issue():
    """Create a sample issue."""
    from models.analysis_result import Issue, IssueType, Severity
    return Issue(
        file="src/main.py",
        line=10,
        column=5,
        type=IssueType.CODE_SMELL,
        severity=Severity.MEDIUM,
        code="complexity",
        message="Function is too complex",
        suggestion="Consider refactoring into smaller functions",
        metadata={"complexity_score": 15}
    )


@pytest.fixture
def sample_issues():
    """Create a list of sample issues."""
    from models.analysis_result import Issue, IssueType, Severity
    return [
        Issue(
            file="src/main.py",
            line=10,
            column=5,
            type=IssueType.CODE_SMELL,
            severity=Severity.MEDIUM,
            code="complexity",
            message="Function is too complex",
            suggestion="Consider refactoring",
            metadata={}
        ),
        Issue(
            file="src/utils.py",
            line=25,
            column=1,
            type=IssueType.SECURITY,
            severity=Severity.HIGH,
            code="sql-injection",
            message="Possible SQL injection vulnerability",
            suggestion="Use parameterized queries",
            metadata={}
        ),
        Issue(
            file="src/main.py",
            line=50,
            column=10,
            type=IssueType.BUG,
            severity=Severity.CRITICAL,
            code="null-pointer",
            message="Potential null pointer dereference",
            suggestion="Add null check",
            metadata={}
        )
    ]


@pytest.fixture
def sample_agent_result(sample_issues):
    """Create a sample agent result."""
    from models.analysis_result import AgentResult
    return AgentResult(
        agent_name="Main Orchestrator Agent",
        success=True,
        issues=sample_issues,
        metrics={
            "complexity_score": 75,
            "maintainability_index": 80,
            "security_score": 65
        },
        execution_time=2.5,
        error=None,
        metadata={
            "files_analyzed": 3,
            "lines_analyzed": 150
        }
    )


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_github_service():
    """Create a mock GitHub service."""
    mock = Mock()
    mock.get_pr_details.return_value = {
        'id': 1001,
        'number': 42,
        'title': 'Test PR',
        'body': 'Test description',
        'user': {'login': 'test-user', 'id': 12345},
        'base': {'ref': 'main'},
        'head': {'ref': 'feature/test', 'sha': 'abc123'},
        'draft': False,
        'created_at': '2025-12-01T10:00:00Z',
        'updated_at': '2025-12-01T12:00:00Z'
    }
    mock.get_pr_files.return_value = []
    mock.post_comment.return_value = True
    mock.verify_webhook_signature.return_value = True
    return mock


@pytest.fixture
def mock_database_service():
    """Create a mock database service."""
    mock = Mock()
    mock.save_pr_analysis.return_value = Mock(id=1)
    mock.get_pr_analysis.return_value = None
    mock.get_user_statistics.return_value = None
    return mock


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        'database': {'enabled': True},
        'github': {'token': 'test-token'},
        'agents': {
            'static_analysis': {'enabled': True},
            'security': {'enabled': True},
            'code_quality': {'enabled': True}
        },
        'pr_comments': {'enabled': False}
    }


# ============================================================================
# Flask App Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Create a Flask test application."""
    # Import here to avoid circular imports
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Set environment to disable database for testing
    with patch.dict(os.environ, {
        'DATABASE_ENABLED': 'false',
        'GITHUB_TOKEN': 'test-token'
    }):
        # Import and configure the app
        from main import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


# ============================================================================
# Database Fixtures (for integration tests)
# ============================================================================

@pytest.fixture
def test_db_url():
    """Return a test database URL (SQLite in-memory)."""
    return "sqlite:///:memory:"


# ============================================================================
# Utility Functions
# ============================================================================

def create_mock_pr_event_dict(pr_number: int = 42, repository: str = "test-org/test-repo") -> Dict[str, Any]:
    """Create a PR event dictionary for testing."""
    return {
        'pr_number': pr_number,
        'repository': repository,
        'title': 'Test PR',
        'description': 'Test description',
        'author': {'login': 'test-user'},
        'base_branch': 'main',
        'head_branch': 'feature/test'
    }

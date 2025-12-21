"""Data models for GitHub PR events."""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class PRFile:
    """Represents a file changed in the PR."""
    filename: str
    status: str  # added, modified, removed
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None


@dataclass
class PRAuthor:
    """Represents the PR author."""
    login: str
    id: int
    avatar_url: str


@dataclass
class PREvent:
    """Represents a GitHub PR event."""
    action: str  # opened, synchronize, reopened
    id: int  # GitHub's unique PR ID (globally unique)
    pr_number: int  # PR number within repository
    pr_title: str
    pr_description: Optional[str]
    pr_url: str
    repository: str
    repository_url: str
    author: PRAuthor
    base_branch: str
    head_branch: str
    files: List[PRFile]
    created_at: datetime
    updated_at: datetime
    is_draft: bool
    
    @classmethod
    def from_webhook(cls, payload: dict) -> 'PREvent':
        """Create PREvent from GitHub webhook payload."""
        pr = payload['pull_request']
        
        return cls(
            action=payload['action'],
            id=pr['id'],  # GitHub's unique PR ID
            pr_number=pr['number'],
            pr_title=pr['title'],
            pr_description=pr.get('body'),
            pr_url=pr['html_url'],
            repository=payload['repository']['full_name'],
            repository_url=payload['repository']['html_url'],
            author=PRAuthor(
                login=pr['user']['login'],
                id=pr['user']['id'],
                avatar_url=pr['user']['avatar_url']
            ),
            base_branch=pr['base']['ref'],
            head_branch=pr['head']['ref'],
            files=[],  # Will be populated separately
            created_at=datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00')),
            is_draft=pr.get('draft', False)
        )

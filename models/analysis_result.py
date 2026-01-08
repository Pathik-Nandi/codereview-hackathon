"""Data models for analysis results."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    """Types of issues that can be detected."""
    SECURITY = "security"
    QUALITY = "quality"
    STYLE = "style"
    COMPLEXITY = "complexity"
    VULNERABILITY = "vulnerability"
    BUG = "bug"
    CONTEXT = "context"


@dataclass
class Issue:
    """Represents a single issue found during analysis."""
    type: IssueType
    severity: Severity
    message: str
    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from a single agent's analysis."""
    agent_name: str
    success: bool
    execution_time: float
    issues: List[Issue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def critical_count(self) -> int:
        """Count of critical issues."""
        return sum(1 for issue in self.issues if issue.severity == Severity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        """Count of high severity issues."""
        return sum(1 for issue in self.issues if issue.severity == Severity.HIGH)
    
    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return len(self.issues)


@dataclass
class AggregatedResult:
    """Aggregated results from all agents."""
    pr_number: int
    repository: str
    total_execution_time: float
    agent_results: List[AgentResult]
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    should_block: bool = False
    
    def __post_init__(self):
        """Calculate summary statistics."""
        all_issues = []
        for result in self.agent_results:
            all_issues.extend(result.issues)
        
        self.summary = {
            'total_issues': len(all_issues),
            'critical': sum(1 for i in all_issues if i.severity == Severity.CRITICAL),
            'high': sum(1 for i in all_issues if i.severity == Severity.HIGH),
            'medium': sum(1 for i in all_issues if i.severity == Severity.MEDIUM),
            'low': sum(1 for i in all_issues if i.severity == Severity.LOW),
            'by_type': self._count_by_type(all_issues)
        }
        
        # Determine if PR should be blocked
        self.should_block = self.summary['critical'] > 0
        
    def _count_by_type(self, issues: List[Issue]) -> Dict[str, int]:
        """Count issues by type."""
        counts = {}
        for issue in issues:
            type_name = issue.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

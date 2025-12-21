"""Base agent class for all specialized agents."""
from abc import ABC, abstractmethod
from typing import List
import time
from models.analysis_result import AgentResult, Issue
from models.pr_event import PREvent
from utils.logger import logger


class BaseAgent(ABC):
    """Base class for all analysis agents."""
    
    def __init__(self, name: str, config: dict):
        """Initialize the agent."""
        self.name = name
        self.config = config
        self.logger = logger.bind(agent=name)
    
    def analyze(self, pr_event: PREvent) -> AgentResult:
        """
        Run analysis on the PR.
        
        Args:
            pr_event: The PR event to analyze
            
        Returns:
            AgentResult with findings
        """
        start_time = time.time()
        self.logger.info("Starting analysis", pr_number=pr_event.pr_number)
        
        try:
            issues = self._analyze_impl(pr_event)
            execution_time = time.time() - start_time
            
            result = AgentResult(
                agent_name=self.name,
                success=True,
                execution_time=execution_time,
                issues=issues,
                metrics=self._collect_metrics(pr_event, issues)
            )
            
            self.logger.info(
                "Analysis complete",
                pr_number=pr_event.pr_number,
                issues_found=len(issues),
                execution_time=execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                "Analysis failed",
                pr_number=pr_event.pr_number,
                error=str(e),
                exc_info=True
            )
            
            return AgentResult(
                agent_name=self.name,
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    @abstractmethod
    def _analyze_impl(self, pr_event: PREvent) -> List[Issue]:
        """
        Implement the actual analysis logic.
        
        Args:
            pr_event: The PR event to analyze
            
        Returns:
            List of issues found
        """
        pass
    
    def _collect_metrics(self, pr_event: PREvent, issues: List[Issue]) -> dict:
        """
        Collect metrics about the analysis.
        
        Args:
            pr_event: The PR event
            issues: Issues found
            
        Returns:
            Dictionary of metrics
        """
        return {
            'files_analyzed': len(pr_event.files),
            'issues_found': len(issues),
            'lines_changed': sum(f.changes for f in pr_event.files)
        }

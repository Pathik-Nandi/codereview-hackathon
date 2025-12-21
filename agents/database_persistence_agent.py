"""Database Persistence Agent for PR Analysis Results."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from services.database_service import DatabaseService
from utils.logger import logger


class DatabasePersistenceAgent:
    """
    Agent responsible for persisting PR analysis results to PostgreSQL database.
    
    This agent:
    - Saves PR analysis results to database
    - Updates user statistics
    - Stores individual issues and metrics
    - Handles database transactions
    """
    
    def __init__(self, db_service: DatabaseService):
        """Initialize database persistence agent."""
        self.db_service = db_service
        self.agent_name = "Database Persistence Agent"
        logger.info("Database Persistence Agent initialized")
    
    def persist_analysis(
        self,
        pr_data: Dict[str, Any],
        analysis_result: Dict[str, Any],
        author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Persist PR analysis results to database.
        
        Args:
            pr_data: PR metadata (repository, pr_number, author, etc.)
            analysis_result: Analysis result from main agent
            author_email: Optional email address of PR author
            
        Returns:
            Dictionary with persistence status and database IDs
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Convert AnalysisResult to dictionary format
            analysis_dict = self._convert_analysis_result(analysis_result)
            
            # Enhance with PR metadata
            analysis_dict['repository'] = pr_data.get('repository')
            analysis_dict['pr_number'] = pr_data.get('pr_number')
            
            # Save to database
            pr_analysis = self.db_service.save_pr_analysis(
                pr_data=pr_data,
                analysis_result=analysis_dict,
                author_email=author_email
            )
            
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
            logger.info(
                "PR analysis persisted successfully",
                pr_analysis_id=pr_analysis.id,
                repository=pr_data.get('repository'),
                pr_number=pr_data.get('pr_number'),
                duration_ms=duration_ms
            )
            
            return {
                'success': True,
                'pr_analysis_id': pr_analysis.id,
                'author_login': pr_analysis.author_login,
                'total_issues': pr_analysis.total_issues,
                'quality_score': pr_analysis.overall_quality_score,
                'security_score': pr_analysis.security_score,
                'duration_ms': duration_ms
            }
            
        except Exception as e:
            logger.error(
                "Failed to persist PR analysis",
                error=str(e),
                repository=pr_data.get('repository'),
                pr_number=pr_data.get('pr_number')
            )
            
            return {
                'success': False,
                'error': str(e),
                'duration_ms': int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            }
    
    def _convert_analysis_result(self, analysis_result: Any) -> Dict[str, Any]:
        """Convert AnalysisResult object or dict to dictionary format."""
        
        # Handle AgentResult object directly (from dispatcher)
        if hasattr(analysis_result, 'issues') and hasattr(analysis_result, 'metadata'):
            return self._convert_agent_result_object(analysis_result)
        
        # Handle dict input (legacy path)
        if isinstance(analysis_result, dict):
            return self._convert_dict_result(analysis_result)
        
        # Fallback
        return self._get_empty_result()
    
    def _convert_agent_result_object(self, analysis_result: Any) -> Dict[str, Any]:
        """Convert AgentResult object to dictionary."""
        # Extract agent breakdown from metadata
        agent_breakdown = analysis_result.metadata.get('agent_breakdown', {}) if analysis_result.metadata else {}
        
        # Count issues by severity
        severity_counts = self._count_issues_by_severity(analysis_result.issues)
        
        return {
            'issues_found': len(analysis_result.issues),
            'critical_issues': severity_counts['critical'],
            'high_issues': severity_counts['high'],
            'medium_issues': severity_counts['medium'],
            'low_issues': severity_counts['low'],
            'agent_breakdown': agent_breakdown,
            'analysis_time_ms': int(analysis_result.execution_time * 1000) if hasattr(analysis_result, 'execution_time') and analysis_result.execution_time else 0,
            'version': '1.0.0'
        }
    
    def _count_issues_by_severity(self, issues: List[Any]) -> Dict[str, int]:
        """Count issues by severity level."""
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for issue in issues:
            severity = issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity)
            severity = severity.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def _convert_dict_result(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert dictionary result to standard format."""
        # If it already has the right structure, return it
        if 'issues_found' in analysis_result:
            return analysis_result
        
        # Otherwise, try to extract from nested structure
        return {
            'issues_found': analysis_result.get('issues_found', 0),
            'critical_issues': analysis_result.get('critical_issues', 0),
            'high_issues': analysis_result.get('high_issues', 0),
            'medium_issues': analysis_result.get('medium_issues', 0),
            'low_issues': analysis_result.get('low_issues', 0),
            'agent_breakdown': analysis_result.get('agent_breakdown', {}),
            'analysis_time_ms': analysis_result.get('analysis_time_ms', 0),
            'version': '1.0.0'
        }
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Get empty result structure."""
        return {
            'issues_found': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'agent_breakdown': {},
            'analysis_time_ms': 0,
            'version': '1.0.0'
        }
    
    def persist_batch_analysis(
        self,
        batch_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Persist multiple PR analysis results in batch.
        
        Args:
            batch_results: List of PR analysis results with metadata
            
        Returns:
            Summary of batch persistence operation
        """
        start_time = datetime.now(timezone.utc)
        successful = 0
        failed = 0
        errors = []
        
        for item in batch_results:
            try:
                result = self.persist_analysis(
                    pr_data=item.get('pr_data', {}),
                    analysis_result=item.get('analysis_result'),
                    author_email=item.get('author_email')
                )
                
                if result.get('success'):
                    successful += 1
                else:
                    failed += 1
                    errors.append({
                        'pr_number': item.get('pr_data', {}).get('pr_number'),
                        'error': result.get('error')
                    })
                    
            except Exception as e:
                failed += 1
                errors.append({
                    'pr_number': item.get('pr_data', {}).get('pr_number'),
                    'error': str(e)
                })
        
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        logger.info(
            "Batch persistence completed",
            total=len(batch_results),
            successful=successful,
            failed=failed,
            duration_ms=duration_ms
        )
        
        return {
            'success': failed == 0,
            'total': len(batch_results),
            'successful': successful,
            'failed': failed,
            'errors': errors if errors else None,
            'duration_ms': duration_ms
        }
    
    def get_persistence_status(self, repository: str, pr_number: int) -> Dict[str, Any]:
        """
        Check if PR analysis exists in database.
        
        Args:
            repository: Repository name (owner/repo)
            pr_number: PR number
            
        Returns:
            Status information
        """
        try:
            pr_analysis = self.db_service.get_pr_analysis(repository, pr_number)
            
            if pr_analysis:
                return {
                    'exists': True,
                    'pr_analysis_id': pr_analysis.id,
                    'analyzed_at': pr_analysis.analyzed_at.isoformat(),
                    'total_issues': pr_analysis.total_issues,
                    'quality_score': pr_analysis.overall_quality_score
                }
            else:
                return {
                    'exists': False
                }
                
        except Exception as e:
            logger.error("Failed to check persistence status", error=str(e))
            return {
                'exists': False,
                'error': str(e)
            }

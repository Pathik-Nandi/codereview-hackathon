"""Dashboard service for sending analysis data."""
import requests
from typing import Dict, Any
from utils.logger import logger
from utils.config import config


class DashboardService:
    """Service for dashboard API interactions."""
    
    def __init__(self):
        """Initialize dashboard service."""
        self.logger = logger.bind(service="dashboard")
        self.api_url = config.dashboard_api_url
        self.api_key = config.dashboard_api_key
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def submit_analysis(self, data: Dict[str, Any]) -> bool:
        """
        Submit analysis results to dashboard.
        
        Args:
            data: Analysis data payload
            
        Returns:
            True if successful
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/analysis",
                json=data,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            self.logger.info(
                "Submitted analysis to dashboard",
                pr_number=data.get('pr_number'),
                status_code=response.status_code
            )
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Failed to submit to dashboard",
                error=str(e),
                pr_number=data.get('pr_number')
            )
            return False
    
    def update_status(
        self, 
        pr_number: int, 
        repository: str, 
        status: str
    ) -> bool:
        """
        Update PR analysis status.
        
        Args:
            pr_number: PR number
            repository: Repository name
            status: Status (pending, in_progress, completed, failed)
            
        Returns:
            True if successful
        """
        try:
            payload = {
                'pr_number': pr_number,
                'repository': repository,
                'status': status
            }
            
            response = requests.put(
                f"{self.api_url}/api/v1/status",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            response.raise_for_status()
            
            self.logger.info(
                "Updated status on dashboard",
                pr_number=pr_number,
                status=status
            )
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Failed to update status",
                error=str(e),
                pr_number=pr_number
            )
            return False
    
    def get_history(self, repository: str, limit: int = 10) -> list:
        """
        Get analysis history for a repository.
        
        Args:
            repository: Repository name
            limit: Number of records to fetch
            
        Returns:
            List of analysis records
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/history/{repository}",
                params={'limit': limit},
                headers=self.headers,
                timeout=10
            )
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Failed to get history",
                error=str(e),
                repository=repository
            )
            return []

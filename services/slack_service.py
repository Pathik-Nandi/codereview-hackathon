"""Slack service for sending notifications."""
from typing import Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.logger import logger
from utils.config import config


class SlackService:
    """Service for Slack notifications."""
    
    def __init__(self):
        """Initialize Slack service."""
        self.logger = logger.bind(service="slack")
        self.client = WebClient(token=config.slack_bot_token)
        self.channel_id = config.slack_channel_id
    
    def send_message(self, text: str, blocks: list = None) -> bool:
        """
        Send a message to Slack channel.
        
        Args:
            text: Plain text message (fallback)
            blocks: Slack block kit blocks
            
        Returns:
            True if successful
        """
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=text,
                blocks=blocks
            )
            
            self.logger.info(
                "Sent Slack message",
                channel=self.channel_id,
                timestamp=response.get('ts')
            )
            
            return True
            
        except SlackApiError as e:
            self.logger.error(
                "Failed to send Slack message",
                error=str(e),
                response=e.response
            )
            return False
    
    def send_pr_notification(self, pr_data: Dict[str, Any]) -> bool:
        """
        Send PR review notification.
        
        Args:
            pr_data: PR and analysis data
            
        Returns:
            True if successful
        """
        text = (
            f"PR Review Complete: {pr_data.get('repository')} "
            f"#{pr_data.get('pr_number')}"
        )
        
        blocks = pr_data.get('blocks', [])
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View PR"},
                    "url": pr_data.get('pr_url'),
                    "style": "primary"
                }
            ]
        })
        
        return self.send_message(text, blocks)
    
    def send_critical_alert(
        self, 
        repository: str, 
        pr_number: int, 
        pr_url: str,
        critical_count: int
    ) -> bool:
        """
        Send critical issue alert with mentions.
        
        Args:
            repository: Repository name
            pr_number: PR number
            pr_url: PR URL
            critical_count: Number of critical issues
            
        Returns:
            True if successful
        """
        text = f"🚨 Critical Issues Found: {repository} #{pr_number}"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Critical Security Issues Detected"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Repository:*\n{repository}"},
                    {"type": "mrkdwn", "text": f"*PR:*\n#{pr_number}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{critical_count}* critical issue(s) found. Immediate attention required! <!channel>"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Review Now"},
                        "url": pr_url,
                        "style": "danger"
                    }
                ]
            }
        ]
        
        return self.send_message(text, blocks)

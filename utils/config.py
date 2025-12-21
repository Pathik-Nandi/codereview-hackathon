"""Configuration management utilities."""
import os
import yaml
from typing import Any, Dict
from dotenv import load_dotenv
from pathlib import Path


class Config:
    """Application configuration manager."""
    
    def __init__(self):
        """Initialize configuration."""
        # Load environment variables
        load_dotenv()
        
        # Load YAML configuration
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Environment variables
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
        self.slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_channel_id = os.getenv('SLACK_CHANNEL_ID')
        self.dashboard_api_url = os.getenv('DASHBOARD_API_URL')
        self.dashboard_api_key = os.getenv('DASHBOARD_API_KEY')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.flask_port = int(os.getenv('FLASK_PORT', 5000))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def is_agent_enabled(self, agent_name: str) -> bool:
        """Check if an agent is enabled."""
        return self.get(f'agents.{agent_name}.enabled', False)
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        return self.get(f'agents.{agent_name}', {})


# Global configuration instance
config = Config()

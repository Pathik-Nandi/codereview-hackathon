"""Agent dispatcher - dispatches PRs to main orchestrator agent."""
from typing import Optional
from models.pr_event import PREvent
from models.analysis_result import AgentResult
from agents.main_agent import MainAgent
from utils.logger import logger
from utils.config import config


class AgentDispatcher:
    """
    Dispatches PR analysis to the main agent which internally runs all agents.
    """
    
    def __init__(self, db_service=None):
        """Initialize the agent dispatcher with main agent."""
        self.logger = logger.bind(component="agent_dispatcher")
        
        # Initialize the main orchestrator agent
        # It will internally manage all specialized agents
        # Pass db_service for RAG agent
        self.main_agent = MainAgent(config.get('agents', {}), db_service=db_service)
        
        self.logger.info(
            "Agent dispatcher initialized with Main Orchestrator Agent"
        )
    
    def dispatch(self, pr_event: PREvent, _agent_type: Optional[str] = None) -> AgentResult:
        """
        Dispatch PR to the main agent which runs all specialized agents internally.
        
        Args:
            pr_event: The PR event to analyze
            _agent_type: Ignored - main agent always runs all agents (underscore prefix indicates unused)
            
        Returns:
            AgentResult with aggregated results from all agents
        """
        self.logger.info(
            "Dispatching PR to Main Orchestrator Agent",
            pr_number=pr_event.pr_number,
            repository=pr_event.repository,
            file_count=len(pr_event.files)
        )
        
        # Run main agent (which internally calls all other agents)
        result = self.main_agent.analyze(pr_event)
        
        # Get breakdown by agent and convert Issue objects to dicts for JSON serialization
        agent_breakdown = self.main_agent.get_agent_breakdown()
        
        # Convert Issue objects in agent_breakdown to serializable dictionaries
        serializable_breakdown = {}
        for agent_name, agent_data in agent_breakdown.items():
            serializable_breakdown[agent_name] = {
                'issues_count': agent_data.get('issues_count', 0),
                'issues': [
                    {
                        'file': issue.file,
                        'line': issue.line,
                        'column': issue.column,
                        'type': issue.type.value if hasattr(issue.type, 'value') else str(issue.type),
                        'severity': issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                        'code': issue.code,
                        'message': issue.message,
                        'suggestion': issue.suggestion,
                        'metadata': issue.metadata
                    }
                    for issue in agent_data.get('issues', [])
                ],
                'metadata': {**agent_data.get('metadata', {}), **agent_data.get('metrics', {})}  # Include agent metrics/metadata for database
            }
        
        self.logger.info(
            "Main Agent analysis complete",
            pr_number=pr_event.pr_number,
            total_issues=len(result.issues),
            success=result.success,
            agents_run=len(agent_breakdown)
        )
        
        # Add serializable agent breakdown to result metadata
        result.metadata = result.metadata or {}
        result.metadata['agent_breakdown'] = serializable_breakdown
        
        # Extract RAG insights and add to main metadata for PR comment agent
        for agent_name, agent_data in agent_breakdown.items():
            if 'RAG' in agent_name or 'rag' in agent_name.lower():
                rag_metadata = agent_data.get('metadata', {})
                if rag_metadata:
                    # Get nested rag_insights dictionary
                    rag_insights_dict = rag_metadata.get('rag_insights', {})
                    
                    # Extract RAG-specific data for PR comment agent
                    result.metadata['rag_insights'] = {
                        'novelty_score': rag_metadata.get('novelty_score', 0),
                        'risk_score': rag_metadata.get('risk_score', 0),
                        'similar_prs_count': rag_metadata.get('similar_prs_found', 0),
                        'recommendations': rag_insights_dict.get('recommendations', ''),
                        'lessons_learned': rag_insights_dict.get('lessons_learned', ''),
                        'potential_pitfalls': rag_insights_dict.get('potential_pitfalls', ''),
                        'best_practices': rag_insights_dict.get('best_practices', ''),
                        'learned_patterns': rag_metadata.get('patterns_identified', []),
                        'similar_prs': rag_metadata.get('similar_prs', []),
                        'full_text': rag_insights_dict.get('full_text', '')
                    }
                    self.logger.info(
                        "RAG insights added to result metadata",
                        similar_prs=rag_metadata.get('similar_prs_found', 0),
                        has_recommendations=bool(rag_insights_dict.get('recommendations', '').strip()),
                        patterns=len(rag_metadata.get('patterns_identified', []))
                    )
        
        return result
    
    def get_available_agents(self) -> list:
        """Get list of sub-agents run by main agent."""
        return [
            'Main Orchestrator Agent (includes: Static Analysis, Security, Code Quality, Context)'
        ]


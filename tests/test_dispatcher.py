"""
Unit tests for AgentDispatcher.

Tests the dispatcher's ability to:
- Initialize with the main orchestrator agent
- Dispatch PR events to the main agent
- Return aggregated analysis results
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestAgentDispatcher:
    """Tests for the AgentDispatcher class."""
    
    @pytest.fixture
    def mock_main_agent(self):
        """Create a mock MainAgent."""
        mock = Mock()
        mock.analyze.return_value = Mock(
            agent_name="Main Orchestrator Agent",
            success=True,
            issues=[],
            metrics={},
            execution_time=1.0,
            error=None,
            metadata={}
        )
        mock.get_agent_breakdown.return_value = {}
        return mock
    
    @pytest.fixture
    def dispatcher_with_mock(self, mock_main_agent):
        """Create an AgentDispatcher with mocked dependencies."""
        with patch('agents.dispatcher.MainAgent', return_value=mock_main_agent):
            with patch('agents.dispatcher.config') as mock_config:
                mock_config.get.return_value = {}
                from agents.dispatcher import AgentDispatcher
                return AgentDispatcher(db_service=None)
    
    @pytest.mark.unit
    def test_dispatcher_initialization(self, dispatcher_with_mock):
        """Test that dispatcher initializes correctly."""
        dispatcher = dispatcher_with_mock
        assert dispatcher.main_agent is not None
        assert dispatcher.logger is not None
    
    @pytest.mark.unit
    def test_dispatch_returns_agent_result(self, dispatcher_with_mock, sample_pr_event):
        """Test that dispatch returns an AgentResult."""
        dispatcher = dispatcher_with_mock
        
        result = dispatcher.dispatch(sample_pr_event)
        
        # Verify the main agent was called
        dispatcher.main_agent.analyze.assert_called_once_with(sample_pr_event)
        
        # Verify result structure
        assert result.success is True
        assert result.agent_name == "Main Orchestrator Agent"
    
    @pytest.mark.unit
    def test_dispatch_adds_agent_breakdown_to_metadata(self, sample_pr_event):
        """Test that dispatch adds agent breakdown to result metadata."""
        # Create a mock issue for the breakdown
        mock_issue = Mock()
        mock_issue.file = "test.py"
        mock_issue.line = 10
        mock_issue.column = 5
        mock_issue.type = Mock(value="code_smell")
        mock_issue.severity = Mock(value="medium")
        mock_issue.code = "test-code"
        mock_issue.message = "Test message"
        mock_issue.suggestion = "Test suggestion"
        mock_issue.metadata = {}
        
        mock_result = Mock(
            agent_name="Main Orchestrator Agent",
            success=True,
            issues=[],
            metrics={},
            execution_time=1.0,
            error=None,
            metadata=None
        )
        
        mock_main_agent = Mock()
        mock_main_agent.analyze.return_value = mock_result
        mock_main_agent.get_agent_breakdown.return_value = {
            "static_analysis": {
                "issues_count": 1,
                "issues": [mock_issue],
                "metadata": {}
            }
        }
        
        with patch('agents.dispatcher.MainAgent', return_value=mock_main_agent):
            with patch('agents.dispatcher.config') as mock_config:
                mock_config.get.return_value = {}
                from agents.dispatcher import AgentDispatcher
                dispatcher = AgentDispatcher(db_service=None)
                
                result = dispatcher.dispatch(sample_pr_event)
                
                # Verify agent breakdown is in metadata
                assert result.metadata is not None
                assert 'agent_breakdown' in result.metadata
    
    @pytest.mark.unit
    def test_get_available_agents(self, dispatcher_with_mock):
        """Test that available agents list is returned."""
        dispatcher = dispatcher_with_mock
        
        agents = dispatcher.get_available_agents()
        
        assert isinstance(agents, list)
        assert len(agents) > 0
        assert "Main Orchestrator Agent" in agents[0]
    
    @pytest.mark.unit
    def test_dispatch_handles_failed_analysis(self, sample_pr_event):
        """Test that dispatch handles analysis failures gracefully."""
        mock_result = Mock(
            agent_name="Main Orchestrator Agent",
            success=False,
            issues=[],
            metrics={},
            execution_time=0.5,
            error="Analysis failed due to parsing error",
            metadata=None
        )
        
        mock_main_agent = Mock()
        mock_main_agent.analyze.return_value = mock_result
        mock_main_agent.get_agent_breakdown.return_value = {}
        
        with patch('agents.dispatcher.MainAgent', return_value=mock_main_agent):
            with patch('agents.dispatcher.config') as mock_config:
                mock_config.get.return_value = {}
                from agents.dispatcher import AgentDispatcher
                dispatcher = AgentDispatcher(db_service=None)
                
                result = dispatcher.dispatch(sample_pr_event)
                
                assert result.success is False
                assert result.error == "Analysis failed due to parsing error"
    
    @pytest.mark.unit
    def test_dispatch_with_db_service(self, sample_pr_event, mock_database_service):
        """Test that dispatcher accepts and uses db_service."""
        mock_main_agent = Mock()
        mock_main_agent.analyze.return_value = Mock(
            agent_name="Main Orchestrator Agent",
            success=True,
            issues=[],
            metrics={},
            execution_time=1.0,
            error=None,
            metadata=None
        )
        mock_main_agent.get_agent_breakdown.return_value = {}
        
        with patch('agents.dispatcher.MainAgent', return_value=mock_main_agent) as mock_main:
            with patch('agents.dispatcher.config') as mock_config:
                mock_config.get.return_value = {}
                from agents.dispatcher import AgentDispatcher
                dispatcher = AgentDispatcher(db_service=mock_database_service)
                
                # Verify MainAgent was initialized with db_service
                mock_main.assert_called_once()
                call_kwargs = mock_main.call_args
                assert call_kwargs[1].get('db_service') == mock_database_service

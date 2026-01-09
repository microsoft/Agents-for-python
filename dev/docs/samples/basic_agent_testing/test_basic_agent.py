import pytest
from microsoft_agents.testing import Integration, AgentClient, ResponseClient


class TestBasicAgent(Integration):
    """Basic agent integration tests"""
    
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    @pytest.mark.asyncio
    async def test_greeting(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test agent responds to greeting"""
        
        # Arrange
        greeting = "Hello"
        
        # Act
        await agent_client.send_activity(greeting)
        responses = await response_client.pop()
        
        # Assert
        assert len(responses) > 0, "Agent should respond to greeting"
        assert responses[0].text is not None, "Response should have text"
        print(f"Agent responded: {responses[0].text}")
    
    @pytest.mark.asyncio
    async def test_question(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test agent responds to questions"""
        
        # Act
        await agent_client.send_activity("How are you?")
        responses = await response_client.pop()
        
        # Assert
        assert len(responses) > 0, "Agent should respond to question"
        assert isinstance(responses[0].text, str), "Response should be text"
    
    @pytest.mark.asyncio
    async def test_empty_message(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test agent handles empty messages gracefully"""
        
        # Act
        await agent_client.send_activity("")
        responses = await response_client.pop()
        
        # Assert - agent should still respond
        assert len(responses) > 0, "Agent should respond to empty message"
    
    @pytest.mark.asyncio
    async def test_multiple_messages(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test conversation flow with multiple messages"""
        
        # First message
        await agent_client.send_activity("Hi there!")
        responses1 = await response_client.pop()
        assert len(responses1) > 0
        
        # Second message
        await agent_client.send_activity("How can you help?")
        responses2 = await response_client.pop()
        assert len(responses2) > 0
        
        # Both should have responses
        assert len(responses1) + len(responses2) >= 2

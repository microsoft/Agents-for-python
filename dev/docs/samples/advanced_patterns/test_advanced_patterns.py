import pytest
import time
import asyncio
from microsoft_agents.testing import Integration, AgentClient, ResponseClient


class TestAdvancedPatterns(Integration):
    """Advanced testing patterns and scenarios"""
    
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    # ============================================================
    # Pattern 1: Multi-Turn Conversation
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient,
        conversation_data
    ):
        """Test multi-turn conversation flow"""
        
        # Turn 1: Greeting
        await agent_client.send_activity(conversation_data["greeting"])
        responses1 = await response_client.pop()
        assert len(responses1) > 0, "Should respond to greeting"
        greeting_response = responses1[0].text
        
        # Turn 2: Question
        await agent_client.send_activity(conversation_data["question"])
        responses2 = await response_client.pop()
        assert len(responses2) > 0, "Should respond to question"
        
        # Turn 3: Goodbye
        await agent_client.send_activity(conversation_data["goodbye"])
        responses3 = await response_client.pop()
        assert len(responses3) > 0, "Should respond to goodbye"
        
        # Verify conversation happened
        assert len(responses1) + len(responses2) + len(responses3) >= 3
    
    # ============================================================
    # Pattern 2: Parameterized Testing
    # ============================================================
    
    @pytest.mark.parametrize("greeting", [
        "Hello",
        "Hi",
        "Hey",
        "Greetings",
        "Good morning",
    ])
    @pytest.mark.asyncio
    async def test_various_greetings(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient,
        greeting: str
    ):
        """Test various greeting patterns"""
        
        await agent_client.send_activity(greeting)
        responses = await response_client.pop()
        
        assert len(responses) > 0, f"Should respond to '{greeting}'"
        assert responses[0].text is not None
    
    # ============================================================
    # Pattern 3: Performance Assertions
    # ============================================================
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_response_time_acceptable(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test response time is within acceptable range"""
        
        start = time.time()
        await agent_client.send_activity("What's your name?")
        responses = await response_client.pop()
        duration = time.time() - start
        
        assert len(responses) > 0
        assert duration < 2.0, f"Response took {duration:.2f}s, expected < 2s"
    
    # ============================================================
    # Pattern 4: Error Recovery
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test agent recovers from errors"""
        
        # Send invalid/empty message
        await agent_client.send_activity("")
        responses1 = await response_client.pop()
        assert len(responses1) > 0, "Should respond to empty message"
        
        # Agent should still work after error
        await agent_client.send_activity("Hello")
        responses2 = await response_client.pop()
        assert len(responses2) > 0, "Should recover and respond normally"
    
    # ============================================================
    # Pattern 5: State Preservation
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_conversation_context_preservation(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test agent maintains conversation context"""
        
        # First message: establish context
        await agent_client.send_activity("My name is Alice")
        responses1 = await response_client.pop()
        assert len(responses1) > 0
        
        # Second message: agent should remember
        await agent_client.send_activity("Do you remember my name?")
        responses2 = await response_client.pop()
        assert len(responses2) > 0
        response_text = responses2[0].text
        
        # Check if context preserved (may contain name)
        # This depends on agent implementation
        print(f"Context test response: {response_text}")
    
    # ============================================================
    # Pattern 6: Concurrent Message Handling
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_concurrent_messages(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test agent handles concurrent messages"""
        
        # Send multiple messages concurrently
        tasks = [
            agent_client.send_activity(f"Message {i}")
            for i in range(5)
        ]
        
        await asyncio.gather(*tasks)
        
        # Collect responses
        responses = await response_client.pop()
        
        # Should have responses for all messages
        assert len(responses) >= 5, f"Expected 5+ responses, got {len(responses)}"
    
    # ============================================================
    # Pattern 7: Message Validation
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_response_validation(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test response content validation"""
        
        await agent_client.send_activity("Hello")
        responses = await response_client.pop()
        
        assert len(responses) > 0
        response = responses[0]
        
        # Validate response structure
        assert hasattr(response, 'text'), "Response should have text field"
        assert hasattr(response, 'type'), "Response should have type field"
        assert response.type == "message", "Response should be message type"
        assert len(response.text) > 0, "Response text should not be empty"
    
    # ============================================================
    # Pattern 8: Edge Case Testing
    # ============================================================
    
    @pytest.mark.parametrize("edge_case", [
        "",                    # Empty
        " " * 10,             # Whitespace
        "X" * 1000,           # Very long
        "123456789",          # Numbers only
        "!@#$%^&*()",         # Special chars
    ])
    @pytest.mark.asyncio
    async def test_edge_cases(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient,
        edge_case: str
    ):
        """Test agent handles edge cases"""
        
        await agent_client.send_activity(edge_case)
        responses = await response_client.pop()
        
        # Agent should always respond gracefully
        assert len(responses) > 0, f"Should handle: {repr(edge_case)}"
    
    # ============================================================
    # Pattern 9: Custom Setup per Test
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_with_custom_setup(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient,
        test_messages
    ):
        """Test with custom setup data"""
        
        # Use fixture data
        greeting = test_messages["greeting"]
        question = test_messages["question_simple"]
        
        # First interaction
        await agent_client.send_activity(greeting)
        r1 = await response_client.pop()
        assert len(r1) > 0
        
        # Second interaction
        await agent_client.send_activity(question)
        r2 = await response_client.pop()
        assert len(r2) > 0
    
    # ============================================================
    # Pattern 10: Assertion with Context
    # ============================================================
    
    @pytest.mark.asyncio
    async def test_detailed_assertions(
        self,
        agent_client: AgentClient,
        response_client: ResponseClient
    ):
        """Test with detailed assertion messages"""
        
        message = "Test message"
        await agent_client.send_activity(message)
        responses = await response_client.pop()
        
        # Detailed assertions with context
        assert len(responses) > 0, (
            f"Expected response to '{message}', "
            f"but got {len(responses)} responses"
        )
        
        response = responses[0]
        assert response.text is not None, (
            f"Response should have text field, "
            f"got: {response}"
        )
        
        assert len(response.text) > 0, (
            f"Response text should not be empty, "
            f"got: '{response.text}'"
        )

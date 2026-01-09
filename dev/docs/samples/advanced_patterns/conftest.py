# tests/conftest.py - Shared fixtures and configuration

import pytest
from microsoft_agents.testing import SDKConfig, AgentClient, ResponseClient


@pytest.fixture(scope="session")
def sdk_config():
    """Load SDK configuration once per session"""
    return SDKConfig(env_path=".env")


@pytest.fixture
def agent_url(sdk_config):
    """Get agent URL from config"""
    return sdk_config.config.get("AGENT_URL", "http://localhost:3978/")


@pytest.fixture
def service_url(sdk_config):
    """Get service URL from config"""
    return sdk_config.config.get("SERVICE_URL", "http://localhost:8001/")


@pytest.fixture
def conversation_data():
    """Provide test conversation data"""
    return {
        "greeting": "Hello",
        "question": "How are you?",
        "name": "Alice",
        "goodbye": "Goodbye",
    }


@pytest.fixture
def test_messages():
    """Provide test messages"""
    return {
        "greeting": "Hi there!",
        "greeting_formal": "Good morning",
        "question_simple": "What time is it?",
        "question_complex": "Can you explain quantum computing?",
        "empty": "",
        "long": "X" * 1000,
        "special": "!@#$%^&*()",
    }


@pytest.fixture
def mock_responses():
    """Provide mock response data for assertions"""
    return {
        "greeting": "Hello! How can I help?",
        "question": "Based on your question, here's what I can tell you...",
        "error": "I didn't quite understand that.",
        "help": "Here are the things I can help you with:",
    }


@pytest.fixture
async def test_setup(agent_url, service_url):
    """Fixture for test setup"""
    return {
        "agent_url": agent_url,
        "service_url": service_url,
        "conversation_id": "test_conv_123",
        "user_id": "test_user_123",
    }


@pytest.fixture
def execution_times():
    """Track execution times for performance tests"""
    times = {}
    
    def record(name, duration):
        if name not in times:
            times[name] = []
        times[name].append(duration)
    
    return record

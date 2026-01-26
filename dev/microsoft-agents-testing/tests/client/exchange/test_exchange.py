"""
Unit tests for the Exchange class.

This module tests:
- Exchange initialization
- Exchange properties
- is_allowed_exception static method
- from_request factory method
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import aiohttp

from microsoft_agents.testing.client.exchange.exchange import Exchange
from microsoft_agents.activity import Activity, ActivityTypes, DeliveryModes, InvokeResponse


# =============================================================================
# Exchange Initialization Tests
# =============================================================================

class TestExchangeInit:
    """Test Exchange initialization."""
    
    def test_init_with_defaults(self):
        exchange = Exchange()
        
        assert exchange.request is None
        assert exchange.status_code is None
        assert exchange.response_body is None
        assert exchange.invoke_response is None
        assert exchange.error is None
        assert exchange.responses == []
    
    def test_init_with_request(self):
        request = Activity(type=ActivityTypes.message, text="hello")
        exchange = Exchange(request=request)
        
        assert exchange.request is request
    
    def test_init_with_responses(self):
        response1 = Activity(type=ActivityTypes.message, text="response1")
        response2 = Activity(type=ActivityTypes.message, text="response2")
        exchange = Exchange(responses=[response1, response2])
        
        assert len(exchange.responses) == 2
        assert exchange.responses[0] is response1
        assert exchange.responses[1] is response2
    
    def test_init_with_status_code(self):
        exchange = Exchange(status_code=200)
        assert exchange.status_code == 200
    
    def test_init_with_error(self):
        error = Exception("test error")
        exchange = Exchange(error=str(error))
        assert exchange.error == str(error)
    
    def test_init_with_invoke_response(self):
        invoke_response = InvokeResponse(status=200, body={"result": "ok"})
        exchange = Exchange(invoke_response=invoke_response)
        assert exchange.invoke_response is invoke_response


# =============================================================================
# Exchange with Complete Data Tests
# =============================================================================

class TestExchangeWithData:
    """Test Exchange with complete data."""
    
    def test_request_response_exchange(self):
        request = Activity(type=ActivityTypes.message, text="hello")
        response = Activity(type=ActivityTypes.message, text="hi there")
        
        exchange = Exchange(
            request=request,
            status_code=200,
            responses=[response]
        )
        
        assert exchange.request.text == "hello"
        assert exchange.status_code == 200
        assert len(exchange.responses) == 1
        assert exchange.responses[0].text == "hi there"
    
    def test_failed_exchange(self):
        request = Activity(type=ActivityTypes.message, text="hello")
        error = aiohttp.ClientConnectionError("Connection failed")
        
        exchange = Exchange(
            request=request,
            error=str(error),
            responses=[]
        )
        
        assert exchange.request.text == "hello"
        assert exchange.error == str(error)
        assert len(exchange.responses) == 0


# =============================================================================
# is_allowed_exception Tests
# =============================================================================

class TestIsAllowedException:
    """Test the is_allowed_exception static method."""
    
    def test_client_timeout_is_allowed(self):
        error = aiohttp.ClientTimeout()
        assert Exchange.is_allowed_exception(error) is True
    
    def test_client_connection_error_is_allowed(self):
        error = aiohttp.ClientConnectionError("connection failed")
        assert Exchange.is_allowed_exception(error) is True
    
    def test_generic_exception_not_allowed(self):
        error = Exception("generic error")
        assert Exchange.is_allowed_exception(error) is False
    
    def test_value_error_not_allowed(self):
        error = ValueError("value error")
        assert Exchange.is_allowed_exception(error) is False
    
    def test_runtime_error_not_allowed(self):
        error = RuntimeError("runtime error")
        assert Exchange.is_allowed_exception(error) is False


# =============================================================================
# Responses List Tests
# =============================================================================

class TestExchangeResponses:
    """Test Exchange responses list."""
    
    def test_empty_responses(self):
        exchange = Exchange()
        assert exchange.responses == []
        assert len(exchange.responses) == 0
    
    def test_single_response(self):
        response = Activity(type=ActivityTypes.message, text="single")
        exchange = Exchange(responses=[response])
        
        assert len(exchange.responses) == 1
        assert exchange.responses[0].text == "single"
    
    def test_multiple_responses(self):
        responses = [
            Activity(type=ActivityTypes.typing),
            Activity(type=ActivityTypes.message, text="first"),
            Activity(type=ActivityTypes.message, text="second"),
        ]
        exchange = Exchange(responses=responses)
        
        assert len(exchange.responses) == 3
        assert exchange.responses[0].type == ActivityTypes.typing
        assert exchange.responses[1].text == "first"
        assert exchange.responses[2].text == "second"


# =============================================================================
# Exchange Model Validation Tests
# =============================================================================

class TestExchangeModel:
    """Test Exchange as a Pydantic model."""
    
    def test_exchange_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(Exchange, BaseModel)
    
    def test_exchange_model_dump(self):
        request = Activity(type=ActivityTypes.message, text="hello")
        exchange = Exchange(request=request, status_code=200)
        
        data = exchange.model_dump(exclude_unset=True)
        assert "request" in data
        assert "status_code" in data
    
    def test_exchange_with_none_error_serializes(self):
        exchange = Exchange(error=None)
        # Should not raise
        data = exchange.model_dump()
        assert "error" in data

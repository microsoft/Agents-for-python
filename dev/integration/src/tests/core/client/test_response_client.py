from re import A
import pytest
from aioresponses import aioresponses

from src.core import ResponseClient

class TestResponseClient:

    @pytest.fixture
    def response_client(self):
        return ResponseClient(base_url="")
    
    @pytest.fixture
    def service_url(self):
        with aioresponses() as mocked:
            mocked.get("https://example.com/service-url", payload={"serviceUrl": "https://service.example.com"})
            client = ResponseClient(base_url="https://example.com")
            service_url = client.get_service_url()
            yield service_url
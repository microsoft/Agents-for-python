import os
from dotenv import load_dotenv

load_dotenv()

class BenchmarkConfig:
    """Configuration class for benchmark settings."""
    
    TENANT_ID: str = ""
    APP_ID: str = ""
    APP_SECRET: str = ""
    AGENT_API_URL: str = ""

    @classmethod
    def load_from_env(cls) -> None:
        """Loads configuration values from environment variables."""
        cls.TENANT_ID = os.environ.get("TENANT_ID", "")
        cls.APP_ID = os.environ.get("APP_ID", "")
        cls.APP_SECRET = os.environ.get("APP_SECRET", "")
        cls.AGENT_URL = os.environ.get("AGENT_API_URL", "http://localhost:3978/api/messages")

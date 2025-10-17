import requests
from .config import BenchmarkConfig

# URL = "https://directline.botframework.com/v3/directline/tokens/generate"
URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


def generate_token(app_id: str, app_secret: str) -> str:
    """Generate a Direct Line token using the provided app credentials."""

    url = URL.format(tenant_id=BenchmarkConfig.TENANT_ID)

    res = requests.post(
        url,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "client_id": app_id,
            "client_secret": app_secret,
            "scope": f"{app_id}/.default",
        },
        timeout=10,
    )
    return res.json().get("access_token")


def generate_token_from_env() -> str:
    """Generates a Direct Line token using environment variables."""
    app_id = BenchmarkConfig.APP_ID
    app_secret = BenchmarkConfig.APP_SECRET
    if not app_id or not app_secret:
        raise ValueError("APP_ID and APP_SECRET must be set in the BenchmarkConfig.")
    return generate_token(app_id, app_secret)

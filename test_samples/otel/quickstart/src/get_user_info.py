import aiohttp

async def get_user_info(token):
    """
    Get information about the current user from Microsoft Graph API.
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        async with session.get(
            "https://graph.microsoft.com/v1.0/me", headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            error_text = await response.text()
            raise Exception(f"Error from Graph API: {response.status} - {error_text}")

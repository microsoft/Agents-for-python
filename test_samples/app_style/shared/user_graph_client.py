import aiohttp


class GraphClient:
    """
    A simple Microsoft Graph client using aiohttp.
    """

    @staticmethod
    async def get_me(token: str):
        """
        Get information about the current user.
        """
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            async with session.get(
                f"https://graph.microsoft.com/v1.0/me", headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Error from Graph API: {response.status} - {error_text}"
                    )

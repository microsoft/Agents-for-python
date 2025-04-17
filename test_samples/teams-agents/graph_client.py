import aiohttp


class GraphClient:
    """
    A simple Microsoft Graph client using aiohttp.
    """

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://graph.microsoft.com/v1.0"

    async def get_me(self):
        """
        Get information about the current user.
        """
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            async with session.get(f"{self.base_url}/me", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Error from Graph API: {response.status} - {error_text}"
                    )

    async def get_user_photo(self):
        """
        Get the current user's photo.
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with session.get(
                f"{self.base_url}/me/photo/$value", headers=headers
            ) as response:
                if response.status == 200:
                    return await response.read()
                elif response.status == 404:
                    return None  # No photo available
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Error from Graph API: {response.status} - {error_text}"
                    )

    async def get_calendar_events(self, start_datetime=None, end_datetime=None):
        """
        Get the current user's calendar events.
        """
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            url = f"{self.base_url}/me/events"
            params = {}

            if start_datetime and end_datetime:
                filter_query = f"start/dateTime ge '{start_datetime}' and end/dateTime le '{end_datetime}'"
                params["$filter"] = filter_query

            params["$select"] = "subject,organizer,start,end,location"
            params["$orderby"] = "start/dateTime"
            params["$top"] = "10"

            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Error from Graph API: {response.status} - {error_text}"
                    )

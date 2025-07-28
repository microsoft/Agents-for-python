# from microsoft.graph.client import AuthenticationProvider, Client
# from microsoft.graph.types import User

# class CachedAuthProvider(AuthenticationProvider):
#     def __init__(self, token: str):
#         self.__token = token

#     async def get_access_token(self):
#         return self.__token

# async def get_user_info(token: str):
#     client = Client(CachedAuthProvider(token))
#     me_response = await client.api("/me").get()
#     image_uri: str = "data:image/png;base64{$defaultImage}"
#     try:
#         photo_res = await client.api("/me/photo/$value").get()
#         image_buffer = await photo_res.array_buffer()
#         image_uri = f"data:image/png;base64,{image_buffer.content.decode()}"
#     except Exception as e:
#         print(f"Error fetching user photo: {e}")

#     return {
#         "root":
#         {
#             "display_name": me_response.display_name,
#             "mail": me_response.mail,
#             "job_title": me_response.job_title,
#             "given_name": me_response.given_name,
#             "surname": me_response.surname,
#             "image_uri": image_uri,
#         }
#     }

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

    # async def get_user_info(token: str):


#     client = Client(CachedAuthProvider(token))
#     me_response = await client.api("/me").get()
#     image_uri: str = "data:image/png;base64{$defaultImage}"
#     try:
#         photo_res = await client.api("/me/photo/$value").get()
#         image_buffer = await photo_res.array_buffer()
#         image_uri = f"data:image/png;base64,{image_buffer.content.decode()}"
#     except Exception as e:
#         print(f"Error fetching user photo: {e}")

#     return {
#         "root":
#         {
#             "display_name": me_response.display_name,
#             "mail": me_response.mail,
#             "job_title": me_response.job_title,
#             "given_name": me_response.given_name,
#             "surname": me_response.surname,
#             "image_uri": image_uri,
#         }
#     }

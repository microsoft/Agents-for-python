# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License.

# import pydantic

# from microsoft_agents.activity import (
#     Activity,
#     AdaptiveCardSearchInvokeValue,
#     AdaptiveCardInvokeResponse,
#     Channels,
#     SearchInvokeTypes,
# )

# from . import factory

# def try_validate_search_invoke_value(
#     activity: Activity,
# ) -> tuple[AdaptiveCardSearchInvokeValue, AdaptiveCardInvokeResponse]:

#     search_invoke_value: AdaptiveCardSearchInvokeValue
#     try:
#         search_invoke_value = AdaptiveCardSearchInvokeValue.model_validate(activity.value)
#     except pydantic.ValidationError:
#         return None, factory.bad_request("Invalid search Activity.value property for search")

#     missing_field: str | None = None

#     if not search_invoke_value.kind:
#         if activity.channel_id and activity.channel_id.channel == Channels.ms_teams.value:
#             search_invoke_value.kind = SearchInvokeTypes.SEARCH
#         else:
#             missing_field = "kind"

#     if not search_invoke_value.query_text:
#         missing_field = "query_text" if not missing_field else f"{missing_field}, query_text"

#     if missing_field:
#         return None, factory.bad_request(
#             f"Missing required field(s) in search Activity.value property: {missing_field}"
#         )

#     error_response = None

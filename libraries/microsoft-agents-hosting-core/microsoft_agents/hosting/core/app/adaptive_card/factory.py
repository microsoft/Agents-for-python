# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from http import HTTPStatus

from microsoft_agents.activity import (
    AdaptiveCardInvokeResponse,
    ContentTypes,
    OAuthCard,
)


def adaptive_card(adaptive_card_json: str) -> AdaptiveCardInvokeResponse:
    return AdaptiveCardInvokeResponse(
        status_code=HTTPStatus.OK,
        type=ContentTypes.adaptive_card,
        value=adaptive_card_json,
    )


def search_response(result: dict | str) -> AdaptiveCardInvokeResponse:
    return AdaptiveCardInvokeResponse(
        status_code=HTTPStatus.OK,
        type=ContentTypes.search_response,
        value=result,
    )


def message(msg: str) -> AdaptiveCardInvokeResponse:
    return AdaptiveCardInvokeResponse(
        status_code=HTTPStatus.OK,
        type=ContentTypes.message,
        value=msg,
    )


def login(card: OAuthCard) -> AdaptiveCardInvokeResponse:
    return AdaptiveCardInvokeResponse(
        status_code=HTTPStatus.UNAUTHORIZED,
        type=ContentTypes.login_request,
        value=card,
    )


def incorrect_auth_code() -> AdaptiveCardInvokeResponse:
    return AdaptiveCardInvokeResponse(
        status_code=HTTPStatus.UNAUTHORIZED,
        type=ContentTypes.incorrect_auth_code,
    )


def precondition_failed(
    message: str, code: str | None = None
) -> AdaptiveCardInvokeResponse:
    return AdaptiveCardInvokeResponse(
        status_code=HTTPStatus.PRECONDITION_FAILED,
        type=ContentTypes.precondition_failed,
        value={
            "message": message,
            "code": code or str(HTTPStatus.PRECONDITION_FAILED),
        },
    )


def error(
    status_code: int, message: str, code: str | None = None
) -> AdaptiveCardInvokeResponse:
    return AdaptiveCardInvokeResponse(
        status_code=status_code,
        type=ContentTypes.error,
        value={
            "code": code or str(status_code),
            "message": message,
        },
    )


def bad_request(message: str) -> AdaptiveCardInvokeResponse:
    return error(
        HTTPStatus.BAD_REQUEST,
        message,
        "BadRequest",
    )


def not_supported(message: str) -> AdaptiveCardInvokeResponse:
    return error(
        HTTPStatus.NOT_IMPLEMENTED,
        message,
        "NotSupported",
    )


def internal_error(message: str) -> AdaptiveCardInvokeResponse:
    return error(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        message,
        "InternalError",
    )

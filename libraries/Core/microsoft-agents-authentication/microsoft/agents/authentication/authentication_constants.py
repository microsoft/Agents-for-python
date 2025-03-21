# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC


class AuthenticationConstants(ABC):
    # Agents SDK OAuth scope to request.
    AGENTS_SDK_SCOPE = "https://api.botframework.com"

    # Token issuer for ABS tokens.
    AGENTS_SDK_TOKEN_ISSUER = "https://api.botframework.com"

    # Default OAuth Url used to get a token from IUserTokenClient.
    AGENTS_SDK_OAUTH_URL = "https://api.botframework.com"

    # Public ABS OpenId Metadata URL.
    PUBLIC_ABS_OPENID_METADATA_URL = (
        "https://login.botframework.com/v1/.well-known/openidconfiguration"
    )

    # Public OpenId Metadata URL.
    PUBLIC_OPENID_METADATA_URL = (
        "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
    )

    # Enterprise Channel OpenId Metadata URL format.
    ENTERPRISE_CHANNEL_OPENID_METADATA_URL_FORMAT = "https://{0}.enterprisechannel.botframework.com/v1/.well-known/openidconfiguration"

    # Gov ABS OpenId Metadata URL.
    GOV_ABS_OPENID_METADATA_URL = (
        "https://login.botframework.azure.us/v1/.well-known/openidconfiguration"
    )

    # Gov OpenId Metadata URL.
    GOV_OPENID_METADATA_URL = "https://login.microsoftonline.us/cab8a31a-1906-4287-a0d8-4eef66b95f6e/v2.0/.well-known/openid-configuration"

    # The V1 Azure AD token issuer URL template that will contain the tenant id where
    # the token was issued from.
    VALID_TOKEN_ISSUER_URL_TEMPLATE_V1 = "https://sts.windows.net/{0}/"

    # The V2 Azure AD token issuer URL template that will contain the tenant id where
    # the token was issued from.
    VALID_TOKEN_ISSUER_URL_TEMPLATE_V2 = "https://login.microsoftonline.com/{0}/v2.0"

    # "azp" Claim.
    # Authorized party - the party to which the ID Token was issued.
    # This claim follows the general format set forth in the OpenID Spec.
    #     http://openid.net/specs/openid-connect-core-1_0.html#IDToken
    AUTHORIZED_PARTY = "azp"

    """
    Audience Claim. From RFC 7519.
        https://tools.ietf.org/html/rfc7519#section-4.1.3
    The "aud" (audience) claim identifies the recipients that the JWT is
    intended for.  Each principal intended to process the JWT MUST
    identify itself with a value in the audience claim.If the principal
    processing the claim does not identify itself with a value in the
    "aud" claim when this claim is present, then the JWT MUST be
    rejected.In the general case, the "aud" value is an array of case-
    sensitive strings, each containing a StringOrURI value.In the
    special case when the JWT has one audience, the "aud" value MAY be a
    single case-sensitive string containing a StringOrURI value.The
    interpretation of audience values is generally application specific.
    Use of this claim is OPTIONAL.
    """
    AUDIENCE_CLAIM = "aud"

    """
    Issuer Claim. From RFC 7519.
        https://tools.ietf.org/html/rfc7519#section-4.1.1
    The "iss" (issuer) claim identifies the principal that issued the
    JWT.  The processing of this claim is generally application specific.
    The "iss" value is a case-sensitive string containing a StringOrURI
    value.  Use of this claim is OPTIONAL.
    """
    ISSUER_CLAIM = "iss"

    """
    From RFC 7515
        https://tools.ietf.org/html/rfc7515#section-4.1.4
    The "kid" (key ID) Header Parameter is a hint indicating which key
    was used to secure the JWS. This parameter allows originators to
    explicitly signal a change of key to recipients. The structure of
    the "kid" value is unspecified. Its value MUST be a case-sensitive
    string. Use of this Header Parameter is OPTIONAL.
    When used with a JWK, the "kid" value is used to match a JWK "kid"
    parameter value.
    """
    KEY_ID_HEADER = "kid"

    # Token version claim name. As used in Microsoft AAD tokens.
    VERSION_CLAIM = "ver"

    # App ID claim name. As used in Microsoft AAD 1.0 tokens.
    APP_ID_CLAIM = "appid"

    # Service URL claim name.
    SERVICE_URL_CLAIM = "serviceurl"

    # Tenant Id claim name. As used in Microsoft AAD tokens.
    TENANT_ID_CLAIM = "tid"

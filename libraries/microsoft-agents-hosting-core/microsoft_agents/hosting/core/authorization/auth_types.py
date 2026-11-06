# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class AuthTypes(StrEnum):
    certificate = "certificate"
    certificate_subject_name = "CertificateSubjectName"
    client_secret = "ClientSecret"
    user_managed_identity = "UserManagedIdentity"
    system_managed_identity = "SystemManagedIdentity"
    federated_credentials = "FederatedCredentials"
    identity_proxy_manager = "IdentityProxyManager"
    entra_auth_sidecar = "EntraAuthSideCar"
    workload_identity = "WorkloadIdentity"

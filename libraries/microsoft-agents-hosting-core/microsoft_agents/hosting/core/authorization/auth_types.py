# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class AuthTypes(str, Enum):
    certificate = "certificate"
    certificate_subject_name = "CertificateSubjectName"
    client_secret = "ClientSecret"
    user_managed_identity = "UserManagedIdentity"
    system_managed_identity = "SystemManagedIdentity"

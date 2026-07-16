# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Well-known Microsoft Teams service endpoint URLs for proactive messaging.

These constants identify the Teams service endpoint for each cloud environment.
Use them only when the incoming request's ``serviceUrl`` is unavailable; once a
``serviceUrl`` has been returned from a prior conversation, cache and reuse that
value instead.
"""

# Service endpoint for the public global Teams environment.
PUBLIC_GLOBAL = "https://smba.trafficmanager.net/teams/"

# Service endpoint for the GCC (Government Community Cloud) Teams environment.
GCC = "https://smba.infra.gcc.teams.microsoft.com/teams"

# Service endpoint for the GCC High Teams environment.
GCC_HIGH = "https://smba.infra.gov.teams.microsoft.us/teams"

# Service endpoint for the DoD (Department of Defense) Teams environment.
DOD = "https://smba.infra.dod.teams.microsoft.us/teams"

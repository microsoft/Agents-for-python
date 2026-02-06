# Microsoft 365 Agents SDK for Python - Release Notes v0.8.0

**Release Date:** February 6, 2026
**Previous Version:** 0.7.0 (Released January 21, 2026)

## Major Features & Enhancements

### Microsoft Copilot Studio Connector Support
A significant enhancement enabling seamless integration with Microsoft Copilot Studio connectors, with comprehensive OAuth and authorization infrastructure updates.

**New Capabilities:**
- Added `ConnectorUserAuthorization` handler with On-Behalf-Of (OBO) token exchange support for Copilot Studio connector requests
- New `connector_user` role type in `RoleTypes` enum for connector user identification
- New `copilot_studio` channel in `Channels` enum for channel-specific handling
- Added `MCSConnectorClient` for direct Copilot Studio connector interactions
- Enhanced `ClaimsIdentity` to store original security tokens for improved token management

**Configuration Improvements:**
- Support for `auto_sign_in` configuration in authorization flow
- Improved handler instantiation from config with better connector scenario support
- JWT authorization middleware automatically assigns anonymous claims when no auth config is present

**Pull Request:** [#295 - MCS Connector (Updated)](https://github.com/microsoft/Agents-for-python/pull/295)

### Enhanced Multi-Tenant Authentication
Comprehensive improvements to MSAL authentication enabling robust multi-tenant and multi-instance support for agentic applications.

**Dynamic MSAL Client Management:**
- Refactored `MsalAuth` class to manage multiple `ConfidentialClientApplication` and `ManagedIdentityClient` instances using a map keyed by tenant and instance
- Added helper methods for dynamic authority and tenant ID resolution
- Improved authority resolution to handle both `/common` and tenant GUIDs in authority URLs
- Updated MSAL dependency to `>=1.34.0` for latest features and bug fixes

**Token Acquisition Enhancements:**
- Token acquisition methods now accept `tenant_id` as an explicit parameter for correct token scoping
- Introduced shared `TokenCache` for MSAL clients to enable token reuse and reduce redundant authentication requests
- Improved scope resolution to handle empty or missing scopes gracefully
- Added `get_agentic_tenant_id` method to activity context for easier tenant information retrieval

**Connection Manager Robustness:**
- Refactored `MsalConnectionManager` to maintain explicit configuration map for connections
- Enforces presence of default service connection with clear error messages when connections are missing
- Cross-referenced agent authentication configurations for JWT patching

**Pull Requests:** 
- [#301 - Dynamic MSAL client resolution and robust authority/tenant handling](https://github.com/microsoft/Agents-for-python/pull/301)
- [#307 - Enhance MsalAuth for multi-tenant support, update MSAL version, and add JWT decoding functionality](https://github.com/microsoft/Agents-for-python/pull/307)

## Bug Fixes

### FastAPI JWT Middleware Async/Await Fix
Fixed a critical runtime error in FastAPI JWT middleware where `get_anonymous_claims()` was incorrectly being awaited despite being a synchronous method.

**Changes:**
- Removed incorrect `await` from synchronous `get_anonymous_claims()` call in `jwt_authorization_middleware.py`
- Aligned FastAPI middleware implementation with aiohttp middleware which correctly calls the method synchronously
- Resolves runtime errors when using Agents Playground in Anonymous mode

**Pull Request:** [#299 - Fix: Remove await from synchronous get_anonymous_claims() in FastAPI JWT middleware](https://github.com/microsoft/Agents-for-python/pull/299)

## Developer Experience Enhancements

### JWT Token Decode Demo
Added a comprehensive Adaptive Card-based JWT token decode demonstration in the agentic-test sample.

**New Features:**
- `JWTDecodeCard.json` Adaptive Card template for displaying JWT token information
- `jwtcard.py` supporting code for decoding and presenting token details
- Updated sample agent to decode agentic tokens and display them in user-friendly format

**Pull Request:** [#307](https://github.com/microsoft/Agents-for-python/pull/307)

---

# Microsoft 365 Agents SDK for Python - Release Notes v0.7.0

**Release Date:** January 21, 2026
**Previous Version:** 0.6.1 (Released December 2, 2025)

## Enhancements

- **Authentication & Token Management**: Centralized token scope handling with new `get_token_scope` method in `ClaimsIdentity` for consistent scope determination across ChannelServiceAdapter and RestChannelServiceClientFactory (#290)
- **Storage Backend Improvements**: AsyncTokenCredential support for CosmosDB and Blob Storage configurations, with enhanced async resource cleanup and improved error handling (#283)
- **Copilot Studio Integration**: Configurable `aiohttp.ClientSession` creation through `ConnectionSettings.client_session_kwargs` parameter for custom HTTP client behavior (#278)
- **Configuration & Logging**: Log configuration support via `.env` file with new `configure_logging` function (#230)

## Documentation

- Installation instructions simplified by removing test PyPI references (#284)

---

# Microsoft 365 Agents SDK for Python - Release Notes v0.6.1

**Release Date:** December 2, 2025
**Previous Version:** 0.6.0 (Released November 18, 2025)

## Changes Documented

- **Build & Packaging**: Version file support via `VERSION.txt` with `MANIFEST.in` inclusion (#261, #263)
- **Bug Fix**: OAuth `_SignInState` serialization refactored to use Pydantic `BaseModel` (#264)

---

# Microsoft 365 Agents SDK for Python - Release Notes v0.6.0

**Release Date:** November 18, 2025  
**Previous Version:** 0.5.0 (Released October 22, 2025)

## Major Features

- **FastAPI Integration Package** (#176) - New `microsoft-agents-hosting-fastapi` hosting option
- **Distributed Error Resources** (#223, #237, #240) - Standardized error codes (-60000 to -66999 ranges) with help URLs across all packages
- **TypingIndicator Simplification** (#212) - Explicit `start()`/`stop()` API, removed async locking complexity

## Bug Fixes

- ChannelServiceAdapter.create_conversation flow (#233)
- Streaming disabled for agentic requests on Teams (#243)
- HTTP client error handling with precise status code checks (#202)
- M365Copilot channel detection (#208, #210)
- Copilot Studio client conversation ID persistence (#195)
- Default max conversation ID length reduced to 150 (#196)

## Documentation

- Contributing guidelines for internal/external developers (#234)
- Type hints and docstring improvements (#207, #214)
- CODEOWNERS unified to agents-sdk team (#199)

---

# Microsoft 365 Agents SDK for Python - Release Notes v0.5.0

**Release Date:** October 22, 2025  
**Previous Version:** 0.4.0 (Released October 7, 2025)

## 🎉 What's New in 0.5.0

This release represents a significant step forward in the Microsoft 365 Agents SDK for Python, focusing on enhanced Python version support, improved developer experience, and robust new features for building enterprise-grade conversational agents.

---

## 🔄 Breaking Changes

### Python Version Requirements
- **Dropped Support:** Python 3.9 is no longer supported
- **New Minimum:** Python 3.10 is now the minimum required version
- **Migration:** Update your Python environment to 3.10 or later before upgrading

### Import Structure (from previous releases)
If you haven't already migrated from earlier versions, note the import structure change:

```python
# Old (no longer supported)
from microsoft.agents.activity import Activity

# New (current)
from microsoft_agents.activity import Activity
```
---


## 🚀 Major Features & Enhancements

### Expanded Python Version Support
The SDK now officially supports Python versions 3.10 through 3.14, providing developers with flexibility to use the latest Python features and improvements. This aligns with the currently [supported versions of Python](https://devguide.python.org/versions/). 

**Key Changes:**
- Added support for Python 3.12, 3.13, and 3.14
- Updated minimum Python requirement to 3.10 (dropped Python 3.9 support)
- Updated CI/CD pipelines to test against all supported Python versions
- Enhanced compatibility testing across the Python ecosystem

**Pull Requests:**
- [#177 - Add support for Python versions 3.12, 3.13, and 3.14](https://github.com/microsoft/Agents-for-python/pull/177)
- [#172 - Update Python version requirements to 3.10](https://github.com/microsoft/Agents-for-python/pull/172)

### Sub-Channel Identification Support
A powerful new feature that enables agents to handle complex channel routing and identification scenarios.

**New Capabilities:**
- Enhanced Activity model with sub-channel identification
- New `ChannelId` class for managing channel routing
- Support for channel-specific entity handling
- Improved conversation routing and context management

**Technical Details:**
- Added `_channel_id_field_mixin.py` for channel ID management
- Enhanced Activity serialization with channel identification
- New entity types for product information and geo-coordinates
- Comprehensive test coverage for sub-channel scenarios

**Pull Request:**
- [#150 - Support sub channel identification from Activities](https://github.com/microsoft/Agents-for-python/pull/150)

---

## 📚 Documentation & Developer Experience

### Comprehensive Library Documentation
Each package now includes detailed README files with examples, installation instructions, and usage guidance.

**New Documentation:**
- Individual README files for all 8 core libraries
- PyPI-friendly descriptions for better package discovery
- Comprehensive SDK overview and getting started guides
- Sample code and best practices for each component

**Libraries with New Documentation:**
- `microsoft-agents-activity` - Core activity handling and models
- `microsoft-agents-authentication-msal` - MSAL authentication integration
- `microsoft-agents-copilotstudio-client` - Copilot Studio connectivity
- `microsoft-agents-hosting-aiohttp` - AIOHTTP-based hosting
- `microsoft-agents-hosting-core` - Core hosting functionality
- `microsoft-agents-hosting-teams` - Microsoft Teams integration
- `microsoft-agents-storage-blob` - Azure Blob Storage support
- `microsoft-agents-storage-cosmos` - Azure Cosmos DB storage

**Pull Request:**
- [#157 - Author README files for each library and integrate into PyPI descriptions](https://github.com/microsoft/Agents-for-python/pull/157)

### Enhanced Type Annotations
Improved code clarity and IDE support through comprehensive type annotations across the SDK.

**Improvements:**
- Enhanced type hints for better IntelliSense support
- Improved static analysis capabilities
- Better error detection during development
- Consistent typing patterns across all modules

**Pull Request:**
- [#162 - Enhance type annotations in various modules](https://github.com/microsoft/Agents-for-python/pull/162)

---

## 🔧 Developer Tools & Quality Improvements

### PyTest Warning Cleanup
Eliminated test warnings to provide a cleaner development experience and stricter quality enforcement.

**Quality Improvements:**
- Cleaned up test classes to eliminate PyTest warnings
- Enhanced test reliability and consistency
- Improved CI/CD pipeline stability
- Better error reporting and debugging

**Pull Request:**
- [#168 - Cleanup test classes to eliminate warnings from PyTest](https://github.com/microsoft/Agents-for-python/pull/168)
- [#164 - Refactor testing functions to use create_ prefix](https://github.com/microsoft/Agents-for-python/pull/164)
- [#166 - Refactor timestamp handling in FileTranscriptStore](https://github.com/microsoft/Agents-for-python/pull/166)

---
## 🔐 Authentication & Security Enhancements

### OAuth Flow Consolidation
Simplified OAuth authentication flows for better security and ease of use.

**Improvements:**
- Consolidated OAuth flow `begin_flow` calls into single API
- New `getTokenOrSignInResource` API for streamlined authentication
- Reduced complexity in authentication setup
- Improved security patterns and best practices

**Pull Request:**
- [#146 - Consolidating OAuthFlow begin_flow calls](https://github.com/microsoft/Agents-for-python/pull/146)

### License Information
Added comprehensive license information to all package configurations for better compliance and transparency.

**Changes:**
- Modernize license tagging in all `pyproject.toml` files
- Improved package metadata for PyPI
- Enhanced compliance with open source standards
- Better legal clarity for enterprise adoption

**Pull Request:**
- [#161 - Add license information to pyproject.toml files](https://github.com/microsoft/Agents-for-python/pull/161)

---

## 🐛 Bug Fixes & Maintenance

### Activity Model Improvements
Removed deprecated "delay" activity type to simplify the activity model and improve clarity.

**Changes:**
- Removed "delay" activity as an implied activity type
- Simplified activity handling logic
- Improved activity model consistency

**Pull Request:**
- [#149 - Remove "delay" activity as an implied activity](https://github.com/microsoft/Agents-for-python/pull/149)

### Documentation Fixes
Multiple rounds of documentation improvements for better clarity and accuracy.

**Improvements:**
- Fixed documentation comments across multiple modules
- Improved code examples and usage patterns
- Enhanced API documentation
- Better consistency in documentation style

**Pull Requests:**
- [#155 - Yet another round of doc fixes](https://github.com/microsoft/Agents-for-python/pull/155)
- [#154 - Additional doc comment fixes](https://github.com/microsoft/Agents-for-python/pull/154)

---

## 📦 Package Information

### Included Libraries

This release includes the following 8 core libraries:

1. **microsoft-agents-activity** - Core activity models and handling
2. **microsoft-agents-authentication-msal** - MSAL authentication integration
3. **microsoft-agents-copilotstudio-client** - Copilot Studio client connectivity
4. **microsoft-agents-hosting-aiohttp** - AIOHTTP-based agent hosting
5. **microsoft-agents-hosting-core** - Core hosting functionality and abstractions
6. **microsoft-agents-hosting-teams** - Microsoft Teams-specific hosting
7. **microsoft-agents-storage-blob** - Azure Blob Storage integration
8. **microsoft-agents-storage-cosmos** - Azure Cosmos DB storage integration

### Python Version Support

- **Supported Versions:** Python 3.10, 3.11, 3.12, 3.13, 3.14
- **Minimum Required:** Python 3.10
- **Recommended:** Python 3.11 or later for optimal performance

---

## 🚀 Getting Started

### Installation

Install individual packages as needed:

```bash
pip install microsoft-agents-activity
pip install microsoft-agents-hosting-core
pip install microsoft-agents-hosting-aiohttp
# ... other packages as needed
```

### Quick Start

```python
from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.aiohttp import start_agent_process

# Your agent implementation here
```

### Sample Applications

Explore comprehensive samples and documentation at:
- [Microsoft 365 Agents SDK Samples](https://github.com/microsoft/Agents)
- [Python-specific examples](https://github.com/microsoft/Agents-for-python/tree/main/test_samples)

---

## 🙏 Acknowledgments

Special thanks to all contributors who made this release possible, including the Microsoft 365 Agents team and the open source community for their valuable feedback and contributions.

---

## 📞 Support & Resources

- **Documentation:** [Microsoft 365 Agents SDK](https://aka.ms/agents)
- **Issues:** [GitHub Issues](https://github.com/microsoft/Agents-for-python/issues)
- **Samples:** [Agent Samples Repository](https://github.com/microsoft/Agents)
- **Community:** Join our developer community discussions

For technical support and questions, please use the GitHub Issues page or refer to our comprehensive documentation and samples.

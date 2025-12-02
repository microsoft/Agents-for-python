# Microsoft 365 Agents SDK for Python - Release Notes v0.6.0

**Release Date:** November 18, 2025  
**Previous Version:** 0.5.0 (Released October 22, 2025)

## 🎉 What's New in 0.6.0

This release focuses on expanding hosting options with FastAPI integration, introducing a comprehensive integration testing framework, enhancing error handling with distributed error resources and standardized error codes, and improving the developer experience with numerous bug fixes and quality improvements.

---

## 🚀 Major Features & Enhancements

### FastAPI Integration Package
A new hosting option for building Microsoft Agents using the FastAPI framework, providing an alternative to the existing AIOHTTP hosting.

**New Capabilities:**
- FastAPI-based hosting for Microsoft Agents
- Streaming response functionality with chunked and interactive message delivery
- Citation handling utilities for conversational AI scenarios
- Support for Teams and Direct Line channels

**Package:** `microsoft-agents-hosting-fastapi`

**Pull Request:**
- [#176 - FastAPI integration package](https://github.com/microsoft/Agents-for-python/pull/176)

### Integration Testing Framework
A comprehensive testing framework for agent integration testing, enabling automated testing of agent behaviors and conversations.

**New Capabilities:**
- Agent integration testing utilities
- Authentication helpers and environment setup tools
- Agent client classes for simulating conversations
- Data-driven testing support
- Benchmarking improvements with verbose output mode

**Package:** `microsoft-agents-testing`

**Pull Request:**
- [#228 - Integration Testing Framework](https://github.com/microsoft/Agents-for-python/pull/228)

### Distributed Error Resources with Error Codes
Refactored error handling across the SDK to use distributed package-specific error resources with standardized error codes and help URLs.

**Key Changes:**
- Created `ErrorMessage` class for consistent error formatting
- Distributed error resources across 8 packages with dedicated error code ranges
- Each error includes: message template, error code, and help URL
- Error codes use negative numbers aligned with C# SDK patterns

**Error Code Ranges:**
| Range | Package | Category |
|-------|---------|----------|
| -60000 to -60999 | microsoft-agents-authentication-msal | Authentication |
| -61000 to -61999 | microsoft-agents-storage-cosmos | Storage (Cosmos) |
| -61100 to -61199 | microsoft-agents-storage-blob | Storage (Blob) |
| -62000 to -62999 | microsoft-agents-hosting-teams | Teams |
| -63000 to -63999 | microsoft-agents-hosting-core | Hosting |
| -64000 to -64999 | microsoft-agents-activity | Activity |
| -65000 to -65999 | microsoft-agents-copilotstudio-client | Copilot Studio |
| -66000 to -66999 | microsoft-agents-hosting-core | General/Validation |

**Example Error Output:**
```
Failed to acquire token. {'error': 'invalid_grant'}

Error Code: -60012
Help URL: https://aka.ms/M365AgentsErrorCodes/#-60012
```

**Pull Requests:**
- [#223 - Distribute error resources across packages with error codes and help URLs](https://github.com/microsoft/Agents-for-python/pull/223)
- [#237 - Replace help_url_anchor with error_code in error message URLs](https://github.com/microsoft/Agents-for-python/pull/237)
- [#240 - Move ErrorMessage to microsoft-agents-activity to resolve circular dependency](https://github.com/microsoft/Agents-for-python/pull/240)

### TypingIndicator Simplification
Refactored the `TypingIndicator` class for simpler usage and improved reliability.

**Improvements:**
- Simplified API with explicit `start()` and `stop()` methods
- Removed asynchronous locking complexity
- Typing indicator now scoped to a single conversation turn
- Improved async task management with proper cancellation handling

**Pull Request:**
- [#212 - TypingIndicator simplification](https://github.com/microsoft/Agents-for-python/pull/212)

### Proactive Messaging Sample
New end-to-end sample demonstrating proactive messaging in Microsoft Teams.

**Features:**
- New agent implementation for proactive messaging
- HTTP endpoints for creating conversations and sending proactive messages
- Comprehensive documentation and setup instructions

**Pull Requests:**
- [#213 - Proactive sample](https://github.com/microsoft/Agents-for-python/pull/213)
- [#217 - Fix for proactive experimental sample in WC](https://github.com/microsoft/Agents-for-python/pull/217)
- [#218 - Fix for proactive experimental sample in WC](https://github.com/microsoft/Agents-for-python/pull/218)

---

## 🐛 Bug Fixes & Improvements

### ChannelServiceAdapter.create_conversation Fix
Fixed the connector client creation flow to properly initialize before the turn context, ensuring correct setup for conversation creation scenarios.

**Changes:**
- Refactored `create_connector_client` to accept optional `context` parameter
- Updated error handling for claims identity validation
- Added comprehensive unit tests for connector client factory logic

**Pull Request:**
- [#233 - Fix ChannelServiceAdapter.create_conversation implementation](https://github.com/microsoft/Agents-for-python/pull/233)

### Streaming Response Improvements for Agentic Requests
Disabled streaming when receiving agentic requests for the MS Teams channel to ensure compatibility.

**Pull Request:**
- [#243 - Disabling streaming when receiving agentic request for msteams channel](https://github.com/microsoft/Agents-for-python/pull/243)

### Improved HTTP Client Error Handling
Enhanced error handling and logging in `UserTokenClient` and `ConnectorClient` for more precise status code checking and consistent logging patterns.

**Improvements:**
- Updated status code checks to use precise ranges
- Switched to parameterized logging for better performance
- Improved handling for specific HTTP status codes (e.g., 404 responses)

**Pull Request:**
- [#202 - Improved UserTokenClient and ConnectorClient status code error handling](https://github.com/microsoft/Agents-for-python/pull/202)

### Channel Detection for M365Copilot
Updated streaming channel detection logic to support M365Copilot channel scenarios.

**Pull Requests:**
- [#208 - Channel check changes needed for M365Copilot](https://github.com/microsoft/Agents-for-python/pull/208)
- [#210 - Cherry-pick 0.5 fixes for streaming and typing indicator](https://github.com/microsoft/Agents-for-python/pull/210)

### Copilot Studio Client Improvements
Updated the Copilot Studio client to properly capture and persist conversation IDs from HTTP response headers.

**Pull Request:**
- [#195 - Update conversation ID in copilot studio client when start_conversation is called](https://github.com/microsoft/Agents-for-python/pull/195)

### Conversation ID Length Adjustment
Reduced the default maximum conversation ID length from 200 to 150 characters to align with system constraints.

**Pull Request:**
- [#196 - Adjusting default max conversation id length](https://github.com/microsoft/Agents-for-python/pull/196)

### Internal Logging Utility
Added `_DeferredString` utility class for deferred string evaluation, improving logging efficiency for expensive string operations.

**Pull Request:**
- [#205 - Internal logging utility: _DeferredString](https://github.com/microsoft/Agents-for-python/pull/205)

### Typing Indicator Error Handling
Improved error handling in the typing indicator loop with cleaner cancellation handling.

**Pull Request:**
- [#209 - Temporal fix for typing indicator](https://github.com/microsoft/Agents-for-python/pull/209)

---

## 📚 Documentation & Developer Experience

### Updated Contributing Guidelines
Added clarified contribution instructions in README.md, including specific steps for Microsoft internal developers.

**Pull Request:**
- [#234 - Update contributing guidelines in README.md](https://github.com/microsoft/Agents-for-python/pull/234)

### Type Hints and Documentation Improvements
Enhanced type annotations and documentation across multiple files for improved clarity and consistency.

**Improvements:**
- Updated optional type hints for model fields
- Improved docstring formatting and references
- Added precise return type annotations for async methods

**Pull Requests:**
- [#207 - Update parameter type hints and documentation across multiple files](https://github.com/microsoft/Agents-for-python/pull/207)
- [#214 - Type annotation and documentation improvements](https://github.com/microsoft/Agents-for-python/pull/214)

### CODEOWNERS Update
Updated team ownership to use the unified agents-sdk team for streamlined code reviews.

**Pull Request:**
- [#199 - Update CODEOWNERS for unified team ownership](https://github.com/microsoft/Agents-for-python/pull/199)

---

## 📦 Package Information

### Included Libraries

This release includes the following 9 core libraries (FastAPI integration package added in 0.6.0):

1. **microsoft-agents-activity** - Core activity models and handling
2. **microsoft-agents-authentication-msal** - MSAL authentication integration
3. **microsoft-agents-copilotstudio-client** - Copilot Studio client connectivity
4. **microsoft-agents-hosting-aiohttp** - AIOHTTP-based agent hosting
5. **microsoft-agents-hosting-core** - Core hosting functionality and abstractions
6. **microsoft-agents-hosting-fastapi** - FastAPI-based agent hosting *(New in 0.6.0)*
7. **microsoft-agents-hosting-teams** - Microsoft Teams-specific hosting
8. **microsoft-agents-storage-blob** - Azure Blob Storage integration
9. **microsoft-agents-storage-cosmos** - Azure Cosmos DB storage integration

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
pip install microsoft-agents-hosting-fastapi  # New in 0.6.0
# ... other packages as needed
```

### Quick Start with FastAPI

```python
from microsoft_agents.hosting.fastapi import start_agent_process
from microsoft_agents.hosting.core import TurnContext

# Your FastAPI agent implementation here
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

---
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
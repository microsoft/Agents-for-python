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
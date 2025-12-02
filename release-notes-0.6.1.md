# Microsoft 365 Agents SDK for Python - Release Notes v0.6.1

**Release Date:** December 1, 2025  
**Previous Version:** 0.6.0 (Released November 18, 2025)

## Overview

This is a patch release that includes important bug fixes and build process improvements. Version 0.6.1 ensures reliable package versioning and fixes a serialization issue in the OAuth flow.

---

## 🔧 Build & Packaging Improvements

### Package Version File Support

Updated the versioning mechanism for all Python library packages to ensure consistent and reliable version management.

**Changes:**
- Build process now writes package version to a `VERSION.txt` file in each library directory
- All `setup.py` files updated to read version from `VERSION.txt` (falls back to environment variable)
- Added `MANIFEST.in` files to include `VERSION.txt` in built packages

**Affected Libraries:**
- `microsoft-agents-activity`
- `microsoft-agents-authentication-msal`
- `microsoft-agents-copilotstudio-client`
- `microsoft-agents-hosting-aiohttp`
- `microsoft-agents-hosting-core`
- `microsoft-agents-hosting-fastapi`
- `microsoft-agents-hosting-teams`
- `microsoft-agents-storage-blob`
- `microsoft-agents-storage-cosmos`

**Pull Requests:**
- [#261 - Getting package version from file when building packages](https://github.com/microsoft/Agents-for-python/pull/261)
- [#263 - Adding MANIFEST.in file to include package version files in builds](https://github.com/microsoft/Agents-for-python/pull/263)

---

## 🐛 Bug Fixes

### OAuth SignInState Serialization Fix

Fixed serialization and deserialization issues with the `_SignInState` class in the OAuth flow.

**Changes:**
- Refactored `_SignInState` class to use Pydantic's `BaseModel` for data modeling and validation
- Updated serialization methods to use Pydantic's `model_dump` and `model_validate` utilities
- Improved maintainability and code clarity

**Pull Request:**
- [#264 - Fixing _sign_in_state serialization/deserialization](https://github.com/microsoft/Agents-for-python/pull/264)

---

## 📦 Package Information

### Included Libraries

All 9 core libraries are included in this release:

1. **microsoft-agents-activity** - Core activity models and handling
2. **microsoft-agents-authentication-msal** - MSAL authentication integration
3. **microsoft-agents-copilotstudio-client** - Copilot Studio client connectivity
4. **microsoft-agents-hosting-aiohttp** - AIOHTTP-based agent hosting
5. **microsoft-agents-hosting-core** - Core hosting functionality and abstractions
6. **microsoft-agents-hosting-fastapi** - FastAPI-based agent hosting
7. **microsoft-agents-hosting-teams** - Microsoft Teams-specific hosting
8. **microsoft-agents-storage-blob** - Azure Blob Storage integration
9. **microsoft-agents-storage-cosmos** - Azure Cosmos DB storage integration

### Python Version Support

- **Supported Versions:** Python 3.10, 3.11, 3.12, 3.13, 3.14
- **Minimum Required:** Python 3.10

---

## 🚀 Upgrading

To upgrade to version 0.6.1, update your packages using pip:

```bash
pip install --upgrade microsoft-agents-activity==0.6.1
pip install --upgrade microsoft-agents-hosting-core==0.6.1
# ... other packages as needed
```

---

## 📞 Support & Resources

- **Documentation:** [Microsoft 365 Agents SDK](https://aka.ms/agents)
- **Issues:** [GitHub Issues](https://github.com/microsoft/Agents-for-python/issues)
- **Samples:** [Agent Samples Repository](https://github.com/microsoft/Agents)

For technical support and questions, please use the GitHub Issues page or refer to our comprehensive documentation and samples.

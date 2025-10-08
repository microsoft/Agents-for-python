# Microsoft Agents Storage - Blob

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-storage-blob)](https://pypi.org/project/microsoft-agents-storage-blob/)

Azure Blob Storage integration for Microsoft 365 Agents SDK. This library provides persistent storage for conversation state, user data, and custom agent information using Azure Blob Storage.

## What is this?

This library implements the storage interface for the Microsoft 365 Agents SDK using Azure Blob Storage as the backend. It enables your agents to persist conversation state, user preferences, and custom data across sessions. Perfect for production deployments where you need reliable, scalable cloud storage.

## Installation

```bash
pip install microsoft-agents-storage-blob
```

## Quick Start

### Basic Configuration with Connection String

```python
from microsoft_agents.storage.blob import BlobStorage, BlobStorageConfig

# Configure using connection string
config = BlobStorageConfig(
    container_name="agent-storage",
    connection_string="DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=..."
)

# Create storage instance
storage = BlobStorage(config)

# Initialize the container (creates if doesn't exist)
await storage.initialize()
```

### Using with AgentApplication

```python
from microsoft_agents.hosting.core import AgentApplication, TurnState
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.storage.blob import BlobStorage, BlobStorageConfig

# Configure blob storage
blob_config = BlobStorageConfig(
    container_name="my-agent-data",
    connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)
storage = BlobStorage(blob_config)
await storage.initialize()

# Create agent with blob storage
app = AgentApplication[TurnState](
    storage=storage,
    adapter=adapter,
    authorization=authorization
)
```

## Configuration Options

### Connection String Authentication

The simplest way to connect - uses a storage account connection string:

```python
config = BlobStorageConfig(
    container_name="agent-storage",
    connection_string="DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=mykey;EndpointSuffix=core.windows.net"
)
```

**Get your connection string:**
- Azure Portal → Storage Account → Access Keys → Connection String

### Token-Based Authentication (Recommended for Production)

Uses Azure Active Directory credentials for secure, keyless authentication:

```python
from azure.identity import DefaultAzureCredential

config = BlobStorageConfig(
    container_name="agent-storage",
    url="https://myaccount.blob.core.windows.net",
    credential=DefaultAzureCredential()
)
```

**Benefits:**
- ✅ No secrets in code
- ✅ Managed Identity support
- ✅ Automatic token renewal
- ✅ Fine-grained access control via Azure RBAC

### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `container_name` | `str` | Yes | Name of the blob container to use |
| `connection_string` | `str` | No* | Storage account connection string |
| `url` | `str` | No* | Blob service URL (e.g., `https://account.blob.core.windows.net`) |
| `credential` | `TokenCredential` | No** | Azure credential for authentication |

*Either `connection_string` OR (`url` + `credential`) must be provided  
**Required when using `url`

## Core Operations

### Read Data

```python
from microsoft_agents.hosting.core.storage import StoreItem

# Define your data model
class UserPreferences(StoreItem):
    def __init__(self, user_id: str, theme: str = "light", language: str = "en"):
        self.id = user_id
        self.theme = theme
        self.language = language

# Read single item
result = await storage.read(["user123"], target_cls=UserPreferences)
if "user123" in result:
    prefs = result["user123"]
    print(f"Theme: {prefs.theme}, Language: {prefs.language}")

# Read multiple items
results = await storage.read(
    ["user123", "user456", "user789"], 
    target_cls=UserPreferences
)
```

### Write Data

```python
# Create or update items
user_prefs = UserPreferences("user123", theme="dark", language="es")

await storage.write({
    "user123": user_prefs
})

# Write multiple items at once
await storage.write({
    "user123": UserPreferences("user123", theme="dark"),
    "user456": UserPreferences("user456", theme="light"),
    "user789": UserPreferences("user789", language="fr")
})
```

### Delete Data

```python
# Delete single item
await storage.delete(["user123"])

# Delete multiple items
await storage.delete(["user123", "user456", "user789"])
```

## Common Patterns

### Conversation State Storage

```python
from microsoft_agents.hosting.core import ConversationState, TurnContext

class MyAgent(ActivityHandler):
    def __init__(self, storage: BlobStorage):
        self.conversation_state = ConversationState(storage)
    
    async def on_message_activity(self, turn_context: TurnContext):
        # Access conversation state
        state_accessor = self.conversation_state.create_property("conversation_data")
        conv_data = await state_accessor.get(turn_context, {})
        
        # Update message count
        conv_data["message_count"] = conv_data.get("message_count", 0) + 1
        
        await turn_context.send_activity(
            f"Message #{conv_data['message_count']} in this conversation"
        )
        
        # Save changes
        await self.conversation_state.save_changes(turn_context)
```

### User State Storage

```python
from microsoft_agents.hosting.core import UserState

class MyAgent(ActivityHandler):
    def __init__(self, storage: BlobStorage):
        self.user_state = UserState(storage)
    
    async def on_message_activity(self, turn_context: TurnContext):
        # Access user state
        user_accessor = self.user_state.create_property("user_profile")
        profile = await user_accessor.get(turn_context, {})
        
        # Track user preferences
        if not profile.get("name"):
            profile["name"] = turn_context.activity.from_property.name
            profile["first_interaction"] = turn_context.activity.timestamp
        
        profile["last_interaction"] = turn_context.activity.timestamp
        profile["total_messages"] = profile.get("total_messages", 0) + 1
        
        # Save changes
        await self.user_state.save_changes(turn_context)
```

### Custom Data Models

```python
from microsoft_agents.hosting.core.storage import StoreItem
from datetime import datetime

class TaskItem(StoreItem):
    def __init__(self, task_id: str, title: str, status: str = "pending"):
        self.id = task_id
        self.title = title
        self.status = status
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

class TaskManager:
    def __init__(self, storage: BlobStorage):
        self.storage = storage
    
    async def create_task(self, task_id: str, title: str):
        task = TaskItem(task_id, title)
        await self.storage.write({task_id: task})
        return task
    
    async def get_task(self, task_id: str):
        result = await self.storage.read([task_id], target_cls=TaskItem)
        return result.get(task_id)
    
    async def update_task_status(self, task_id: str, status: str):
        task = await self.get_task(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.utcnow().isoformat()
            await self.storage.write({task_id: task})
        return task
    
    async def delete_task(self, task_id: str):
        await self.storage.delete([task_id])
```

## Environment Setup

### Local Development with Azurite

Use the Azure Storage Emulator for local testing:

```bash
# Install Azurite
npm install -g azurite

# Start the emulator
azurite --silent --location c:\azurite --debug c:\azurite\debug.log
```

```python
# Use emulator connection string
config = BlobStorageConfig(
    container_name="local-test",
    connection_string=(
        "AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "DefaultEndpointsProtocol=http;"
        "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1"
    )
)
```

### Production Configuration

```python
import os
from azure.identity import DefaultAzureCredential

# Using environment variables
config = BlobStorageConfig(
    container_name=os.getenv("STORAGE_CONTAINER_NAME", "agent-production"),
    url=os.getenv("AZURE_STORAGE_URL"),
    credential=DefaultAzureCredential()
)

storage = BlobStorage(config)
await storage.initialize()
```

**Environment Variables:**
```bash
AZURE_STORAGE_URL=https://myaccount.blob.core.windows.net
STORAGE_CONTAINER_NAME=agent-production
```

### Azure Managed Identity

When running in Azure (App Service, Functions, Container Apps), use Managed Identity:

```python
from azure.identity import ManagedIdentityCredential

config = BlobStorageConfig(
    container_name="agent-storage",
    url="https://myaccount.blob.core.windows.net",
    credential=ManagedIdentityCredential()
)
```

**Azure RBAC Roles Required:**
- `Storage Blob Data Contributor` - For read/write access
- `Storage Blob Data Reader` - For read-only access

## Advanced Usage

### Batch Operations

```python
# Efficient batch reads
user_ids = [f"user{i}" for i in range(100)]
results = await storage.read(user_ids, target_cls=UserPreferences)

# Batch writes
batch_data = {
    f"user{i}": UserPreferences(f"user{i}", theme="dark")
    for i in range(100)
}
await storage.write(batch_data)

# Batch deletes
await storage.delete([f"user{i}" for i in range(100)])
```

### Error Handling

```python
from azure.core.exceptions import ResourceNotFoundError

async def safe_read_user(storage: BlobStorage, user_id: str):
    try:
        result = await storage.read([user_id], target_cls=UserPreferences)
        return result.get(user_id)
    except ResourceNotFoundError:
        # Container doesn't exist
        await storage.initialize()
        return None
    except Exception as e:
        # Log error and return default
        print(f"Error reading user data: {e}")
        return UserPreferences(user_id)
```

### Container Management

```python
# Initialize ensures container exists
await storage.initialize()

# Safe to call multiple times (idempotent)
await storage.initialize()
await storage.initialize()  # No-op if already initialized

# Manual container operations (if needed)
container_client = storage._container_client
exists = await container_client.exists()
if not exists:
    await container_client.create_container()
```

### Performance Optimization

```python
# Use async context manager for cleanup
async with BlobServiceClient.from_connection_string(conn_str) as client:
    container = client.get_container_client("agent-storage")
    # Operations here
    pass

# Reuse storage instance (singleton pattern)
class StorageManager:
    _instance = None
    
    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            config = BlobStorageConfig(...)
            cls._instance = BlobStorage(config)
            await cls._instance.initialize()
        return cls._instance
```

## Testing

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_storage():
    storage = AsyncMock(spec=BlobStorage)
    storage.read.return_value = {}
    storage.write.return_value = None
    storage.delete.return_value = None
    return storage

@pytest.mark.asyncio
async def test_agent_with_storage(mock_storage):
    agent = MyAgent(mock_storage)
    # Test agent logic
    await agent.process_message(...)
    
    # Verify storage was called
    mock_storage.write.assert_called_once()
```

### Integration Testing with Azurite

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_storage_integration():
    config = BlobStorageConfig(
        container_name="test-container",
        connection_string="UseDevelopmentStorage=true"
    )
    storage = BlobStorage(config)
    await storage.initialize()
    
    # Test real operations
    await storage.write({"key": TestItem("key", "value")})
    result = await storage.read(["key"], target_cls=TestItem)
    assert result["key"].value == "value"
    
    # Cleanup
    await storage.delete(["key"])
```

## Migration from MemoryStorage

Switching from `MemoryStorage` to `BlobStorage` is straightforward:

```python
# Before (development)
from microsoft_agents.hosting.core import MemoryStorage
storage = MemoryStorage()

# After (production)
from microsoft_agents.storage.blob import BlobStorage, BlobStorageConfig
config = BlobStorageConfig(
    container_name="agent-storage",
    connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)
storage = BlobStorage(config)
await storage.initialize()
```

**Benefits of switching to BlobStorage:**
- ✅ Data persists across restarts
- ✅ Scalable to millions of items
- ✅ Multi-instance support (load balancing)
- ✅ Automatic backups and geo-replication
- ✅ Built-in monitoring and diagnostics

## Troubleshooting

### Common Issues

**Container not found error:**
```python
# Solution: Initialize the storage
await storage.initialize()
```

**Authentication failures:**
```python
# Verify credential works
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
token = credential.get_token("https://storage.azure.com/.default")
print(f"Token acquired: {token.token[:20]}...")
```

**Connection string issues:**
```python
# Verify connection string format
from azure.storage.blob import BlobServiceClient
try:
    client = BlobServiceClient.from_connection_string(connection_string)
    print("Connection string valid")
except Exception as e:
    print(f"Invalid connection string: {e}")
```

## Best Practices

1. **Use Token Authentication in Production** - Avoid storing connection strings; use Managed Identity or DefaultAzureCredential
2. **Initialize Once** - Call `storage.initialize()` during app startup, not on every request
3. **Implement Retry Logic** - Handle transient failures with exponential backoff
4. **Monitor Performance** - Use Azure Monitor to track storage operations
5. **Set Lifecycle Policies** - Configure automatic cleanup of old data in Azure Portal
6. **Use Consistent Naming** - Establish key naming conventions (e.g., `user:{id}`, `conversation:{id}`)
7. **Batch Operations** - Read/write multiple items together when possible

## Key Classes Reference

- **`BlobStorage`** - Main storage implementation using Azure Blob Storage
- **`BlobStorageConfig`** - Configuration settings for connection and authentication
- **`StoreItem`** - Base class for data models (inherit to create custom types)

## Need Help?

- 📖 [Azure Blob Storage Documentation](https://docs.microsoft.com/azure/storage/blobs/)
- 🔐 [Azure Identity Documentation](https://docs.microsoft.com/python/api/azure-identity/)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)
- 💡 [Sample Applications](https://github.com/microsoft/Agents-for-python/tree/main/test_samples)

Part of the [Microsoft 365 Agents SDK](https://github.com/microsoft/Agents-for-python) family.

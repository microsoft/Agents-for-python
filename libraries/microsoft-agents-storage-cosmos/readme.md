# Microsoft Agents Storage - Cosmos DB

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/)

Azure Cosmos DB storage integration for Microsoft 365 Agents SDK. This library provides enterprise-grade persistent storage for conversation state, user data, and custom agent information using Azure Cosmos DB's globally distributed, multi-model database service.

## What is this?

This library implements the storage interface for the Microsoft 365 Agents SDK using Azure Cosmos DB as the backend. It provides automatic partitioning, global distribution, and low-latency access to your agent data. Perfect for production deployments requiring high availability, scalability, and multi-region support.

**Why Cosmos DB?**
- 🌍 Global distribution with multi-region writes
- ⚡ Single-digit millisecond latency
- 📈 Automatic and instant scalability
- 🔄 Multiple consistency models
- 💪 99.999% availability SLA

## Installation

```bash
pip install microsoft-agents-storage-cosmos
```

## Quick Start

### Basic Configuration with Auth Key

```python
from microsoft_agents.storage.cosmos import CosmosDBStorage, CosmosDBStorageConfig

# Configure using endpoint and auth key
config = CosmosDBStorageConfig(
    cosmos_db_endpoint="https://myaccount.documents.azure.com:443/",
    auth_key="your-auth-key-here",
    database_id="agent-database",
    container_id="agent-storage"
)

# Create storage instance
storage = CosmosDBStorage(config)

# Initialize (creates database and container if needed)
await storage.initialize()
```

### Using with AgentApplication

```python
from microsoft_agents.hosting.core import AgentApplication, TurnState
from microsoft_agents.storage.cosmos import CosmosDBStorage, CosmosDBStorageConfig
import os

# Configure Cosmos DB storage
cosmos_config = CosmosDBStorageConfig(
    cosmos_db_endpoint=os.getenv("COSMOS_DB_ENDPOINT"),
    auth_key=os.getenv("COSMOS_DB_AUTH_KEY"),
    database_id="agents",
    container_id="conversations"
)

storage = CosmosDBStorage(cosmos_config)
await storage.initialize()

# Create agent with Cosmos DB storage
app = AgentApplication[TurnState](
    storage=storage,
    adapter=adapter,
    authorization=authorization
)
```

## Configuration Options

### Auth Key Authentication (Simple)

```python
config = CosmosDBStorageConfig(
    cosmos_db_endpoint="https://myaccount.documents.azure.com:443/",
    auth_key="your-primary-or-secondary-key",
    database_id="agent-db",
    container_id="bot-storage"
)
```

**Get your endpoint and key:**
- Azure Portal → Cosmos DB Account → Keys → URI and Primary Key

### Token-Based Authentication (Recommended)

Uses Azure Active Directory credentials for secure, keyless authentication:

```python
from azure.identity import DefaultAzureCredential

config = CosmosDBStorageConfig(
    url="https://myaccount.documents.azure.com:443/",
    credential=DefaultAzureCredential(),
    database_id="agent-db",
    container_id="bot-storage"
)
```

**Note:** When using `url` with `credential`, do not provide `cosmos_db_endpoint` or `auth_key`.

### Configuration from JSON File

```python
# Create config.json
{
    "cosmos_db_endpoint": "https://myaccount.documents.azure.com:443/",
    "auth_key": "your-key",
    "database_id": "agent-db",
    "container_id": "bot-storage",
    "container_throughput": 800,
    "compatibility_mode": false
}

# Load from file
config = CosmosDBStorageConfig(filename="config.json")
```

### All Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cosmos_db_endpoint` | `str` | Yes* | `""` | Cosmos DB account endpoint URL |
| `auth_key` | `str` | Yes* | `""` | Primary or secondary authentication key |
| `database_id` | `str` | Yes | `""` | Database identifier |
| `container_id` | `str` | Yes | `""` | Container identifier |
| `url` | `str` | No** | `""` | Alternative to `cosmos_db_endpoint` for token auth |
| `credential` | `TokenCredential` | No** | `None` | Azure credential for token-based auth |
| `container_throughput` | `int` | No | `400` | RU/s when creating container (400-unlimited) |
| `cosmos_client_options` | `dict` | No | `{}` | Additional client options (connection_policy, consistency_level) |
| `key_suffix` | `str` | No | `""` | Suffix added to all keys for multi-tenancy |
| `compatibility_mode` | `bool` | No | `False` | Truncate keys to 255 chars for legacy support |

*Either (`cosmos_db_endpoint` + `auth_key`) OR (`url` + `credential`) required  
**Required when using `url`

## Core Operations

### Read Data

```python
from microsoft_agents.hosting.core.storage import StoreItem

# Define your data model
class ConversationData(StoreItem):
    def __init__(self, conv_id: str, topic: str = "", message_count: int = 0):
        self.id = conv_id
        self.topic = topic
        self.message_count = message_count

# Read single item
result = await storage.read(["conv123"], target_cls=ConversationData)
if "conv123" in result:
    conv = result["conv123"]
    print(f"Topic: {conv.topic}, Messages: {conv.message_count}")

# Read multiple items
results = await storage.read(
    ["conv123", "conv456", "conv789"],
    target_cls=ConversationData
)

# Handle missing items
for key in ["conv123", "conv456"]:
    if key in results:
        print(f"Found: {results[key].topic}")
    else:
        print(f"Not found: {key}")
```

### Write Data

```python
# Create or update items
conv_data = ConversationData("conv123", topic="Weather", message_count=5)

await storage.write({
    "conv123": conv_data
})

# Batch writes (more efficient)
await storage.write({
    "conv123": ConversationData("conv123", topic="Weather", message_count=5),
    "conv456": ConversationData("conv456", topic="Sports", message_count=12),
    "conv789": ConversationData("conv789", topic="News", message_count=3)
})
```

### Delete Data

```python
# Delete single item
await storage.delete(["conv123"])

# Delete multiple items
await storage.delete(["conv123", "conv456", "conv789"])

# Delete is idempotent (no error if item doesn't exist)
await storage.delete(["nonexistent-key"])  # No error
```

## Common Patterns

### Conversation State Storage

```python
from microsoft_agents.hosting.core import ConversationState, ActivityHandler, TurnContext

class MyAgent(ActivityHandler):
    def __init__(self, storage: CosmosDBStorage):
        self.conversation_state = ConversationState(storage)
    
    async def on_message_activity(self, turn_context: TurnContext):
        # Access conversation-scoped state
        state_accessor = self.conversation_state.create_property("conversation_data")
        conv_data = await state_accessor.get(turn_context, {})
        
        # Track conversation metadata
        if not conv_data.get("started_at"):
            conv_data["started_at"] = turn_context.activity.timestamp
            conv_data["topic"] = "general"
        
        conv_data["message_count"] = conv_data.get("message_count", 0) + 1
        conv_data["last_activity"] = turn_context.activity.timestamp
        
        # Save changes
        await self.conversation_state.save_changes(turn_context)
```

### User State Storage

```python
from microsoft_agents.hosting.core import UserState

class MyAgent(ActivityHandler):
    def __init__(self, storage: CosmosDBStorage):
        self.user_state = UserState(storage)
    
    async def on_message_activity(self, turn_context: TurnContext):
        # Access user-scoped state (persists across conversations)
        user_accessor = self.user_state.create_property("user_profile")
        profile = await user_accessor.get(turn_context, {})
        
        # Track user preferences and history
        if not profile.get("user_id"):
            profile["user_id"] = turn_context.activity.from_property.id
            profile["name"] = turn_context.activity.from_property.name
            profile["first_seen"] = turn_context.activity.timestamp
            profile["preferences"] = {"language": "en", "timezone": "UTC"}
        
        profile["last_seen"] = turn_context.activity.timestamp
        profile["total_interactions"] = profile.get("total_interactions", 0) + 1
        
        # Save changes
        await self.user_state.save_changes(turn_context)
```

### Custom Data Models

```python
from microsoft_agents.hosting.core.storage import StoreItem
from datetime import datetime
from typing import List

class OrderItem(StoreItem):
    def __init__(self, order_id: str, customer_id: str, items: List[dict], status: str = "pending"):
        self.id = order_id
        self.customer_id = customer_id
        self.items = items
        self.status = status
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.total_amount = sum(item.get("price", 0) for item in items)

class OrderManager:
    def __init__(self, storage: CosmosDBStorage):
        self.storage = storage
    
    async def create_order(self, order_id: str, customer_id: str, items: List[dict]):
        order = OrderItem(order_id, customer_id, items)
        await self.storage.write({order_id: order})
        return order
    
    async def get_order(self, order_id: str):
        result = await self.storage.read([order_id], target_cls=OrderItem)
        return result.get(order_id)
    
    async def update_order_status(self, order_id: str, new_status: str):
        order = await self.get_order(order_id)
        if order:
            order.status = new_status
            order.updated_at = datetime.utcnow().isoformat()
            await self.storage.write({order_id: order})
        return order
    
    async def cancel_order(self, order_id: str):
        await self.storage.delete([order_id])
```

## Advanced Features

### Key Suffix for Multi-Tenancy

Use key suffixes to isolate data for different tenants or environments:

```python
# Production environment
prod_config = CosmosDBStorageConfig(
    cosmos_db_endpoint="https://myaccount.documents.azure.com:443/",
    auth_key="your-key",
    database_id="shared-db",
    container_id="shared-container",
    key_suffix="_prod"
)

# Development environment (same database/container)
dev_config = CosmosDBStorageConfig(
    cosmos_db_endpoint="https://myaccount.documents.azure.com:443/",
    auth_key="your-key",
    database_id="shared-db",
    container_id="shared-container",
    key_suffix="_dev"
)

# Keys are automatically suffixed
# "user123" becomes "user123_prod" or "user123_dev"
```

### Compatibility Mode

Enable compatibility mode for legacy containers with 255-character key limits:

```python
config = CosmosDBStorageConfig(
    cosmos_db_endpoint="https://myaccount.documents.azure.com:443/",
    auth_key="your-key",
    database_id="legacy-db",
    container_id="old-container",
    compatibility_mode=True
)

# Long keys are automatically truncated with SHA-256 hash appended
# to prevent collisions
```

**Note:** Cannot use `key_suffix` with `compatibility_mode=True`.

### Custom Throughput Settings

```python
# Standard throughput (400 RU/s)
config = CosmosDBStorageConfig(
    cosmos_db_endpoint="...",
    auth_key="...",
    database_id="agent-db",
    container_id="storage",
    container_throughput=400  # Default
)

# High-performance throughput
config = CosmosDBStorageConfig(
    cosmos_db_endpoint="...",
    auth_key="...",
    database_id="agent-db",
    container_id="storage",
    container_throughput=1000  # Higher RU/s for more traffic
)

# Auto-scale throughput (specify in Azure Portal)
# Set to 0 to use existing container throughput
config = CosmosDBStorageConfig(
    cosmos_db_endpoint="...",
    auth_key="...",
    database_id="agent-db",
    container_id="existing-container",
    container_throughput=0  # Don't override existing
)
```

### Custom Client Options

```python
from azure.cosmos import documents

# Configure connection policy and consistency
connection_policy = documents.ConnectionPolicy()
connection_policy.RequestTimeout = 30000  # 30 seconds
connection_policy.PreferredLocations = ["West US", "East US"]

config = CosmosDBStorageConfig(
    cosmos_db_endpoint="...",
    auth_key="...",
    database_id="agent-db",
    container_id="storage",
    cosmos_client_options={
        "connection_policy": connection_policy,
        "consistency_level": "Session"  # Session, Eventual, Strong, etc.
    }
)
```

## Environment Setup

### Local Development with Cosmos DB Emulator

Install and run the Azure Cosmos DB Emulator for local testing:

**Download:** [Azure Cosmos DB Emulator](https://docs.microsoft.com/azure/cosmos-db/local-emulator)

```python
# Use emulator connection details
config = CosmosDBStorageConfig(
    cosmos_db_endpoint="https://localhost:8081",
    auth_key="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    database_id="local-test-db",
    container_id="bot-storage"
)

storage = CosmosDBStorage(config)
await storage.initialize()
```

**Note:** The auth key above is the well-known emulator key (safe to use locally).

### Production Configuration

```python
import os
from azure.identity import DefaultAzureCredential

# Using environment variables
config = CosmosDBStorageConfig(
    cosmos_db_endpoint=os.getenv("COSMOS_DB_ENDPOINT"),
    auth_key=os.getenv("COSMOS_DB_AUTH_KEY"),
    database_id=os.getenv("COSMOS_DATABASE_ID", "agents"),
    container_id=os.getenv("COSMOS_CONTAINER_ID", "production"),
    container_throughput=int(os.getenv("COSMOS_THROUGHPUT", "400"))
)

# Or use Managed Identity (recommended)
config = CosmosDBStorageConfig(
    url=os.getenv("COSMOS_DB_ENDPOINT"),
    credential=DefaultAzureCredential(),
    database_id="agents",
    container_id="production"
)

storage = CosmosDBStorage(config)
await storage.initialize()
```

**Environment Variables:**
```bash
COSMOS_DB_ENDPOINT=https://myaccount.documents.azure.com:443/
COSMOS_DB_AUTH_KEY=your-primary-key-here
COSMOS_DATABASE_ID=agents
COSMOS_CONTAINER_ID=production
COSMOS_THROUGHPUT=800
```

### Azure Managed Identity

When running in Azure (App Service, Functions, Container Apps):

```python
from azure.identity import ManagedIdentityCredential

config = CosmosDBStorageConfig(
    url="https://myaccount.documents.azure.com:443/",
    credential=ManagedIdentityCredential(),
    database_id="agents",
    container_id="production"
)
```

**Azure RBAC Roles Required:**
- `Cosmos DB Built-in Data Contributor` - For read/write access
- `Cosmos DB Built-in Data Reader` - For read-only access

## Key Sanitization

Cosmos DB has restrictions on certain characters in keys. The library automatically sanitizes keys:

```python
# Forbidden characters: \ ? / # \t \n \r *
# These are replaced with *{unicode-code-point}

# Example:
original_key = "user/123?test"
# Becomes: "user*47123*63test"

# Special handling for keys with forbidden characters
await storage.write({
    "user/123": user_data,  # Automatically sanitized
    "conversation?active": conv_data  # Automatically sanitized
})

# Read using original keys (sanitization is automatic)
result = await storage.read(["user/123", "conversation?active"], target_cls=UserData)
```

**Internal behavior:**
- Keys are sanitized before storage operations
- Original keys are preserved in the document as `realId`
- Reads return data mapped to original keys

## Error Handling

```python
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError

async def safe_storage_operation(storage: CosmosDBStorage, key: str):
    try:
        # Initialize if needed
        await storage.initialize()
        
        # Perform operation
        result = await storage.read([key], target_cls=UserData)
        return result.get(key)
        
    except CosmosResourceNotFoundError as e:
        # Container or database doesn't exist
        print(f"Resource not found: {e}")
        await storage.initialize()
        return None
        
    except CosmosHttpResponseError as e:
        # Network issues, throttling, etc.
        if e.status_code == 429:  # Too Many Requests
            print("Rate limited, implement retry with backoff")
        elif e.status_code == 503:  # Service Unavailable
            print("Service temporarily unavailable")
        else:
            print(f"Cosmos error: {e.status_code} - {e.message}")
        raise
        
    except ValueError as e:
        # Configuration or validation errors
        print(f"Configuration error: {e}")
        raise
```

## Performance Optimization

### Batch Operations

```python
# Efficient: Single request with multiple keys
user_ids = [f"user{i}" for i in range(100)]
results = await storage.read(user_ids, target_cls=UserData)

# Efficient: Batch write
batch_data = {
    f"user{i}": UserData(f"user{i}", name=f"User {i}")
    for i in range(100)
}
await storage.write(batch_data)
```

### Singleton Pattern

```python
# Reuse storage instance across requests
class StorageManager:
    _instance: CosmosDBStorage = None
    
    @classmethod
    async def get_instance(cls) -> CosmosDBStorage:
        if cls._instance is None:
            config = CosmosDBStorageConfig(
                cosmos_db_endpoint=os.getenv("COSMOS_DB_ENDPOINT"),
                auth_key=os.getenv("COSMOS_DB_AUTH_KEY"),
                database_id="agents",
                container_id="production"
            )
            cls._instance = CosmosDBStorage(config)
            await cls._instance.initialize()
        return cls._instance

# Use in your agent
storage = await StorageManager.get_instance()
```

### Indexing Strategy

Configure indexing in Azure Portal for better query performance:

```json
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        {
            "path": "/document/user_id/*"
        },
        {
            "path": "/document/timestamp/*"
        }
    ],
    "excludedPaths": [
        {
            "path": "/document/large_text/*"
        }
    ]
}
```

## Testing

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_storage():
    storage = AsyncMock(spec=CosmosDBStorage)
    storage.read.return_value = {}
    storage.write.return_value = None
    storage.delete.return_value = None
    storage.initialize.return_value = None
    return storage

@pytest.mark.asyncio
async def test_agent_with_storage(mock_storage):
    agent = MyAgent(mock_storage)
    
    # Test agent logic
    await agent.process_message(...)
    
    # Verify storage interactions
    mock_storage.initialize.assert_called_once()
    mock_storage.write.assert_called()
```

### Integration Testing with Emulator

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_cosmos_storage_integration():
    config = CosmosDBStorageConfig(
        cosmos_db_endpoint="https://localhost:8081",
        auth_key="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
        database_id="test-db",
        container_id="test-container"
    )
    
    storage = CosmosDBStorage(config)
    await storage.initialize()
    
    # Test CRUD operations
    test_item = TestData("key1", "value1")
    await storage.write({"key1": test_item})
    
    result = await storage.read(["key1"], target_cls=TestData)
    assert result["key1"].value == "value1"
    
    await storage.delete(["key1"])
    result = await storage.read(["key1"], target_cls=TestData)
    assert "key1" not in result
```

## Migration Guide

### From MemoryStorage

```python
# Before (development)
from microsoft_agents.hosting.core import MemoryStorage
storage = MemoryStorage()

# After (production)
from microsoft_agents.storage.cosmos import CosmosDBStorage, CosmosDBStorageConfig
import os

config = CosmosDBStorageConfig(
    cosmos_db_endpoint=os.getenv("COSMOS_DB_ENDPOINT"),
    auth_key=os.getenv("COSMOS_DB_AUTH_KEY"),
    database_id="agents",
    container_id="production"
)
storage = CosmosDBStorage(config)
await storage.initialize()
```

### From BlobStorage

Both storage implementations use the same interface:

```python
# BlobStorage
from microsoft_agents.storage.blob import BlobStorage, BlobStorageConfig

# CosmosDBStorage (drop-in replacement)
from microsoft_agents.storage.cosmos import CosmosDBStorage, CosmosDBStorageConfig

# Same usage pattern
storage = CosmosDBStorage(config)
await storage.initialize()
```

**Key Differences:**
- Cosmos DB: Better for high-throughput, low-latency scenarios
- Blob Storage: Better for large objects, archival, cost-sensitive scenarios

## Troubleshooting

### Common Issues

**"Database/Container not found"**
```python
# Solution: Initialize storage to create resources
await storage.initialize()
```

**"Invalid key characters"**
```python
# Solution: Keys are automatically sanitized
# Avoid using \ ? / # \t \n \r * if possible
# Library handles sanitization transparently
```

**"Request rate too large (429)"**
```python
# Solution: Increase container throughput or implement retry logic
config = CosmosDBStorageConfig(
    # ... other settings ...
    container_throughput=1000  # Increase RU/s
)
```

**Authentication failures**
```python
# Verify credentials work
from azure.cosmos.aio import CosmosClient

client = CosmosClient(endpoint, auth_key)
database_list = await client.list_databases()
print(f"Connected! Databases: {len(list(database_list))}")
```

## Best Practices

1. **Use Managed Identity in Production** - Avoid storing auth keys in code or environment variables
2. **Initialize Once** - Call `storage.initialize()` during app startup, not per request
3. **Batch Operations** - Read/write multiple items together when possible
4. **Monitor RU Consumption** - Use Azure Monitor to track Request Units usage
5. **Set Appropriate Throughput** - Start with 400 RU/s, scale up based on metrics
6. **Use Session Consistency** - Default consistency level for most scenarios
7. **Implement Retry Logic** - Handle transient failures with exponential backoff
8. **Partition Wisely** - Current implementation uses `/id` partitioning (automatic)
9. **Enable Diagnostics** - Configure Azure diagnostic logs for troubleshooting
10. **Test with Emulator** - Use local emulator for development and testing

## Key Classes Reference

- **`CosmosDBStorage`** - Main storage implementation using Azure Cosmos DB
- **`CosmosDBStorageConfig`** - Configuration settings for connection and behavior
- **`StoreItem`** - Base class for data models (inherit to create custom types)

## Need Help?

- 📖 [Azure Cosmos DB Documentation](https://docs.microsoft.com/azure/cosmos-db/)
- 🔐 [Azure Identity Documentation](https://docs.microsoft.com/python/api/azure-identity/)
- ⚡ [Cosmos DB Best Practices](https://docs.microsoft.com/azure/cosmos-db/performance-tips)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)
- 💡 [Sample Applications](https://github.com/microsoft/Agents-for-python/tree/main/test_samples)

Part of the [Microsoft 365 Agents SDK](https://github.com/microsoft/Agents-for-python) family.

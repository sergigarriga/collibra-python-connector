# Collibra Python Connector

[![PyPI version](https://badge.fury.io/py/collibra-connector.svg)](https://badge.fury.io/py/collibra-connector)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Typing: typed](https://img.shields.io/badge/typing-typed-green.svg)](https://www.python.org/dev/peps/pep-0561/)

An **UNOFFICIAL** comprehensive Python connector for the Collibra Data Governance Center API.

## Features

- **Complete API Coverage**: Asset, Community, Domain, User, Responsibility, Workflow, Metadata, Comment, Relation, and Output Module management
- **Automatic Retry Logic**: Built-in retry mechanism with exponential backoff for transient errors
- **Context Manager Support**: Use `with` statement for automatic session management and connection pooling
- **Pagination Helpers**: Easy iteration over large datasets without memory issues
- **Batch Processing**: Process bulk operations efficiently with rate limiting
- **Metadata Caching**: Thread-safe cache for frequently accessed metadata (UUIDs, types, statuses)
- **Input Validation**: Comprehensive parameter validation with clear error messages
- **Type Hints**: Full type annotations for better IDE support and static analysis
- **Custom Exceptions**: Structured exception hierarchy for precise error handling

## Installation

```bash
pip install collibra-connector
```

For development with testing tools:

```bash
pip install collibra-connector[dev]
```

## Quick Start

### Basic Usage

```python
from collibra_connector import CollibraConnector

# Initialize the connector
connector = CollibraConnector(
    api="https://your-collibra-instance.com",
    username="your-username",
    password="your-password",
    timeout=30,           # Request timeout in seconds
    max_retries=3,        # Number of retry attempts
    retry_delay=1.0       # Base delay between retries
)

# Test connection
if connector.test_connection():
    print("Connected successfully!")

# Find communities
communities = connector.community.find_communities(limit=10)
for community in communities.get("results", []):
    print(f"Community: {community['name']}")
```

### Using Context Manager (Recommended)

The context manager provides automatic session management and connection pooling:

```python
from collibra_connector import CollibraConnector

with CollibraConnector(
    api="https://your-collibra-instance.com",
    username="your-username",
    password="your-password"
) as connector:
    # Session is automatically managed
    communities = connector.community.find_communities()
    assets = connector.asset.find_assets(limit=100)

# Session is automatically closed
```

### Environment Variables Pattern

```python
import os
from collibra_connector import CollibraConnector

connector = CollibraConnector(
    api=os.environ["COLLIBRA_URL"],
    username=os.environ["COLLIBRA_USERNAME"],
    password=os.environ["COLLIBRA_PASSWORD"]
)
```

## API Reference

### Assets

```python
# Get an asset by ID
asset = connector.asset.get_asset("asset-uuid")

# Create an asset
new_asset = connector.asset.add_asset(
    name="My New Asset",
    domain_id="domain-uuid",
    display_name="My Asset Display Name",
    type_id="asset-type-uuid",
    status_id="status-uuid"  # Optional
)

# Update an asset
updated = connector.asset.change_asset(
    asset_id="asset-uuid",
    name="Updated Name",
    display_name="Updated Display Name"
)

# Find assets with filters
assets = connector.asset.find_assets(
    community_id="community-uuid",
    domain_id="domain-uuid",
    asset_type_ids=["type-uuid-1", "type-uuid-2"],
    limit=1000
)

# Set asset attributes
connector.asset.set_asset_attributes(
    asset_id="asset-uuid",
    type_id="attribute-type-uuid",
    values=["value1", "value2"]
)

# Set asset relations
connector.asset.set_asset_relations(
    asset_id="asset-uuid",
    related_asset_ids=["related-uuid-1", "related-uuid-2"],
    relation_direction="TO_TARGET",
    type_id="relation-type-uuid"
)

# Remove an asset
connector.asset.remove_asset("asset-uuid")
```

### Communities

```python
# Get a community
community = connector.community.get_community("community-uuid")

# Find communities with filters
communities = connector.community.find_communities(
    name="Search Term",
    name_match_mode="ANYWHERE",  # START, END, ANYWHERE, EXACT
    parent_id="parent-community-uuid",
    sort_field="NAME",
    sort_order="ASC",
    limit=100
)

# Create a community
new_community = connector.community.add_community(
    name="My New Community",
    description="Community description",
    parent_id="parent-community-uuid"  # Optional
)

# Update a community
connector.community.change_community(
    community_id="community-uuid",
    name="Updated Name",
    description="Updated description"
)

# Remove a community
connector.community.remove_community("community-uuid")
```

### Domains

```python
# Get a domain
domain = connector.domain.get_domain("domain-uuid")

# Find domains
domains = connector.domain.find_domains(
    community_id="community-uuid",
    name="Search Term",
    type_id="domain-type-uuid",
    include_sub_communities=True,
    limit=100
)

# Create a domain
new_domain = connector.domain.add_domain(
    name="My New Domain",
    community_id="community-uuid",
    type_id="domain-type-uuid",
    description="Domain description"
)

# Update a domain
connector.domain.change_domain(
    domain_id="domain-uuid",
    name="Updated Name"
)

# Remove a domain
connector.domain.remove_domain("domain-uuid")
```

### Users

```python
# Get user by ID
user = connector.user.get_user("user-uuid")

# Get user by username (convenience method)
user_id = connector.user.get_user_by_username("john.doe")

# Find users
users = connector.user.find_users(
    name="John",
    name_search_fields=["USERNAME", "FIRSTNAME", "LASTNAME"],
    include_disabled=False,
    sort_field="USERNAME",
    limit=50
)

# Create a user
new_user = connector.user.create_user(
    username="newuser",
    email_address="newuser@example.com"
)
```

### Workflows

```python
# Start a workflow
workflow = connector.workflow.start_workflow(
    workflow_definition_id="workflow-def-uuid",
    asset_ids=["asset-uuid-1", "asset-uuid-2"]
)
```

## Helper Utilities

### Pagination

Efficiently iterate over large datasets:

```python
from collibra_connector import CollibraConnector, Paginator

connector = CollibraConnector(...)

# Iterate over all assets (memory-efficient)
paginator = Paginator(
    connector.asset.find_assets,
    limit=100,          # Items per page
    max_items=10000     # Optional: stop after N items
)

# Iterate item by item
for asset in paginator.items():
    print(asset['name'])

# Or iterate page by page
for page in paginator.pages():
    print(f"Processing {len(page)} assets")
    for asset in page:
        process(asset)

# Collect all items (loads into memory)
all_assets = paginator.collect()
```

### Batch Processing

Process bulk operations with rate limiting:

```python
from collibra_connector import CollibraConnector, BatchProcessor

connector = CollibraConnector(...)

# Prepare data
assets_to_create = [
    {"name": "Asset 1", "domain_id": "domain-uuid"},
    {"name": "Asset 2", "domain_id": "domain-uuid"},
    # ... more assets
]

# Process in batches
processor = BatchProcessor(
    batch_size=50,      # Items per batch
    delay=0.1,          # Delay between batches (seconds)
    on_error="continue" # "continue", "stop", or "collect"
)

result = processor.process(
    items=assets_to_create,
    operation=connector.asset.add_asset,
    item_mapper=lambda a: {"name": a["name"], "domain_id": a["domain_id"]},
    progress_callback=lambda done, total: print(f"Progress: {done}/{total}")
)

print(f"Success: {result.success_count}, Errors: {result.error_count}")
print(f"Success rate: {result.success_rate:.1f}%")
```

### Metadata Caching

Cache frequently accessed metadata to reduce API calls:

```python
from collibra_connector import CollibraConnector, CachedMetadata

connector = CollibraConnector(...)

# Create cache with 1-hour TTL
cache = CachedMetadata(connector, ttl=3600)

# Get UUIDs by name (cached after first call)
asset_type_id = cache.get_asset_type_id("Business Term")
status_id = cache.get_status_id("Approved")
attribute_type_id = cache.get_attribute_type_id("Description")
domain_type_id = cache.get_domain_type_id("Physical Data Dictionary")
role_id = cache.get_role_id("Owner")

# Force refresh if needed
cache.refresh_all()

# Clear cache
cache.clear()
```

### Data Transformation

Utilities for transforming API responses:

```python
from collibra_connector import DataTransformer

# Extract IDs from results
assets = connector.asset.find_assets()
asset_ids = DataTransformer.extract_ids(assets["results"])

# Create name->ID mapping
communities = connector.community.find_communities()
name_to_id = DataTransformer.to_name_id_map(communities["results"])
community_id = name_to_id.get("My Community")

# Group items by a field
grouped = DataTransformer.group_by(assets["results"], "type.name")
for type_name, items in grouped.items():
    print(f"{type_name}: {len(items)} assets")

# Flatten nested asset structure
flat_asset = DataTransformer.flatten_asset(asset)
print(flat_asset["type.name"])  # Access nested values with dot notation
```

## Error Handling

The library provides a custom exception hierarchy:

```python
from collibra_connector import (
    CollibraConnector,
    CollibraAPIError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError
)

connector = CollibraConnector(...)

try:
    asset = connector.asset.get_asset("invalid-uuid")
except UnauthorizedError:
    print("Invalid credentials")
except ForbiddenError:
    print("Insufficient permissions")
except NotFoundError:
    print("Asset not found")
except ServerError:
    print("Server error - try again later")
except CollibraAPIError as e:
    print(f"API error: {e}")
```

## Retry Logic

The connector automatically retries on transient failures:

- **Connection errors**: Network issues, DNS failures
- **Timeouts**: Request timeouts
- **Server errors**: 500, 502, 503, 504 status codes
- **Rate limiting**: 429 status code

Configure retry behavior:

```python
connector = CollibraConnector(
    api="https://your-instance.com",
    username="user",
    password="pass",
    max_retries=5,      # Number of retry attempts
    retry_delay=2.0     # Base delay (uses exponential backoff)
)
```

## Configuration

### Timeouts

```python
# Set custom timeout (seconds)
connector = CollibraConnector(
    api="...",
    username="...",
    password="...",
    timeout=60  # 60 seconds
)
```

### Auto-load UUIDs

Load all metadata UUIDs on initialization:

```python
connector = CollibraConnector(
    api="...",
    username="...",
    password="...",
    uuids=True  # Fetch all UUIDs on init
)

# Access cached UUIDs
asset_type_id = connector.uuids["AssetType"]["Business Term"]
status_id = connector.uuids["Status"]["Approved"]
```

## Requirements

- Python 3.8+
- requests >= 2.20.0

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests/ -v
```

Run type checking:

```bash
mypy collibra_connector/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This is an **UNOFFICIAL** connector and is not affiliated with, endorsed by, or supported by Collibra. Use at your own risk.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

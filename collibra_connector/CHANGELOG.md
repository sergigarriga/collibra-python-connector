# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-12

### Added
- **Full Async Parity**: Added missing `User`, `Comment`, and `Workflow` modules to `AsyncCollibraConnector`.
- **Enhanced Search API**: Added `search()` alias and ensured typed returns for all search methods.
- **Robust Model Parsing**: Improved `ResourceReference` to automatically resolve display names from `userName`, `firstName`, or `lastName`.
- **Improved Error Handling**: Added specific handling for HTTP 400 (Bad Request) and fail-fast local UUID validation.

### Changed
- **Type Safety**: Synchronous API methods now consistently return Pydantic models instead of dictionaries (Breaking Change).
- **Naming Standardization**: Normalized all "hyperlink" parameters to `excluded_from_auto_hyperlinking`.

### Fixed
- **UserModel Parsing**: Fixed validation errors when the `name` field is missing from user responses.
- **LineageBuilder**: Fixed compatibility issues with the new Pydantic return types.
- **Helper Methods**: Fixed attribute and relation convenience methods to work with typed models.

## [1.1.0] - 2026-01-02

### Added

#### Full Pydantic Integration (Type Safety)
- All API methods now return typed Pydantic models instead of raw dictionaries
- Full IDE autocompletion support: `asset.status.name`, `asset.type.id`, etc.
- Comprehensive models for all Collibra resources:
  - `AssetModel`, `DomainModel`, `CommunityModel`, `UserModel`
  - `AttributeModel`, `RelationModel`, `ResponsibilityModel`
  - `WorkflowDefinitionModel`, `WorkflowInstanceModel`, `WorkflowTaskModel`
  - `SearchResultModel`, `AssetProfileModel`
- Generic `PaginatedResponseModel[T]` with iteration and pagination helpers
- Factory functions: `parse_asset()`, `parse_assets()`, etc.
- Convenience properties: `asset.effective_name`, `asset.type_name`, `user.full_name`

#### Async Support (AsyncCollibraConnector)
- New `AsyncCollibraConnector` using httpx for high-performance async operations
- Parallel batch operations: `get_assets_batch()`, `add_assets_batch()`
- 10-50x performance improvement for bulk operations
- Configurable concurrency limits
- Full async context manager support

#### Lineage Builder
- Declarative API for building data lineage graphs
- Fluent builder pattern: `builder.source(a).through(etl).to(b)`
- Convenience methods: `fan_in()`, `fan_out()`, `chain()`
- Factory methods: `LineageNode.table()`, `LineageNode.pipeline()`
- Automatic asset and relation creation on commit
- Export/import lineage graphs as dictionaries
- ASCII visualization of lineage

#### OpenTelemetry Integration (Observability)
- Native OpenTelemetry support for distributed tracing
- Automatic metrics collection (request count, duration, errors)
- OTLP exporter support for Grafana, Jaeger, etc.
- `@traced` and `@traced_async` decorators
- `TracedCollibraConnector` wrapper for automatic instrumentation
- Console export for debugging

#### CLI Tool (collibra-sdk)
- Command-line interface installed with `pip install collibra-connector[cli]`
- Commands:
  - `collibra-sdk search "query"` - Search for assets
  - `collibra-sdk get-asset --id "uuid"` - Get asset details
  - `collibra-sdk list-assets` - List assets with filters
  - `collibra-sdk export-domain --id "uuid" -o report.csv` - Export to CSV/JSON
  - `collibra-sdk list-communities` - List communities
  - `collibra-sdk list-domains` - List domains
  - `collibra-sdk bulk-update-status` - Bulk status updates
- Multiple output formats: JSON, table, CSV
- Environment variable configuration

#### Mocking Engine (Testing)
- `MockCollibraConnector` for unit testing without API calls
- `@mock_collibra` decorator for test functions
- `mock_collibra_context()` context manager
- `CollibraTestCase` base class for test suites
- In-memory data store with add/find operations
- All mock methods return proper Pydantic models

### Changed

- Version bumped to 1.1.0
- Updated pyproject.toml with optional dependencies:
  - `[async]` - httpx for async support
  - `[cli]` - click and pandas for CLI
  - `[telemetry]` - OpenTelemetry packages
  - `[pandas]` - DataFrame export
  - `[all]` - All optional dependencies
- Improved type hints throughout the codebase
- Better error messages with context
- Python 3.13 support added

### Fixed

- Improved handling of optional fields in API responses
- Better timestamp handling with datetime conversion properties

---

## [1.0.20] - 2025-01-01

### Fixed
- **Critical Bug Fix**: Fixed `add_asset()` method where `id` (Python built-in function) was incorrectly used instead of `_id` (the parameter) in the request body. This caused assets to be created without the specified ID.

### Added

#### Core Features
- **Retry Logic**: Added automatic retry mechanism with exponential backoff for transient errors (connection errors, timeouts, server errors 5xx, and rate limiting 429).
- **Context Manager Support**: `CollibraConnector` now supports the `with` statement for automatic session management and connection pooling.
- **Type Hints**: Added comprehensive type annotations throughout the codebase with `py.typed` marker for mypy support.
- **Input Validation**: Added validation for empty/whitespace API URL, username, and password in connector initialization.

#### Helper Utilities
- **Paginator**: Memory-efficient iteration over large paginated datasets.
  - `pages()`: Iterate page by page
  - `items()`: Iterate item by item
  - `collect()`: Collect all items into a list
  - Support for both offset and cursor-based pagination
  - `max_items` parameter to limit total items fetched

- **BatchProcessor**: Process bulk operations with rate limiting.
  - Configurable batch size and delay between batches
  - Error handling strategies: "continue", "stop", or "collect"
  - Progress callback support for monitoring

- **BatchResult**: Dataclass for batch operation results.
  - Track successes and errors separately
  - Calculate success rate percentage

- **CachedMetadata**: Thread-safe cache for frequently accessed metadata.
  - Cache asset types, statuses, attribute types, domain types, roles
  - Configurable TTL (time-to-live)
  - Methods: `get_asset_type_id()`, `get_status_id()`, `get_attribute_type_id()`, etc.
  - `clear()` and `refresh_all()` methods

- **DataTransformer**: Utilities for transforming API responses.
  - `flatten_asset()`: Flatten nested structures to dot-notation keys
  - `extract_ids()`: Extract specific field from list of items
  - `group_by()`: Group items by a field value
  - `to_name_id_map()`: Convert items to name->ID mapping

- **timed_cache**: Decorator for caching function results with TTL.
  - Automatic cache expiration
  - `clear_cache()` method on decorated functions

- **Search API**: Full support for Collibra Search API via `connector.search`.
  - `find()`: Generic search with advanced filtering, sorting, and highlighting.
  - `find_assets()`: Helper method specifically for searching assets.

- **Data Models**: Added Pydantic models for type-safe data handling in `collibra_connector.models`.
  - Includes `AssetModel`, `DomainModel`, `CommunityModel`, `UserModel`, etc.

- **Asset Management**: New methods in `Asset` API:
  - `add_tags()`: Add tags to assets.
  - `remove_tags()`: Remove tags from assets.
  - `add_attachment()`: Upload files as attachments.
  - `get_attachments()`: Retrieve asset attachments.
  - `get_full_profile()`: Get complete asset profile with attributes, relations, responsibilities.

- **Configuration**: Support for environment variables for credentials:
  - `COLLIBRA_URL`
  - `COLLIBRA_USERNAME`
  - `COLLIBRA_PASSWORD`

### Changed
- **Logging**: Removed global `logging.basicConfig` configuration to prevent interference with host applications.
- **Dependencies**: Added `pydantic>=2.0.0` as a required dependency.

## [1.0.19] - Previous Release

- Initial stable release on PyPI
- Basic API coverage for Assets, Communities, Domains, Users, etc.

---

## Migration Guide

### Upgrading from 1.0.x to 1.1.0

The main change is that API methods now return Pydantic models instead of dictionaries.
For backward compatibility, you can convert models to dicts:

```python
# Old way (still works with model conversion)
asset = conn.asset.get_asset("uuid")
asset_dict = asset.to_dict()  # or asset.model_dump()

# New way (recommended)
asset = conn.asset.get_asset("uuid")
print(asset.name)           # Direct attribute access
print(asset.status.name)    # Nested access
print(asset.type_name)      # Convenience property
```

### Using Async Connector

```python
import asyncio
from collibra_connector import AsyncCollibraConnector

async def main():
    async with AsyncCollibraConnector(
        api="https://your-instance.collibra.com",
        username="user",
        password="pass"
    ) as conn:
        # Parallel fetch - 50x faster than sequential
        assets = await conn.asset.get_assets_batch(asset_ids)

asyncio.run(main())
```

### Using Lineage Builder

```python
from collibra_connector.lineage import LineageBuilder, LineageNode

builder = LineageBuilder(conn)

# Define nodes
source = LineageNode.table("raw.customers", database="s3")
etl = LineageNode.pipeline("transform_customers")
target = LineageNode.table("customers", schema="warehouse")

# Build lineage
builder.chain(source, etl, target)

# Commit to Collibra
result = builder.commit(domain_id="lineage-domain-uuid")
```

### Using Mock for Tests

```python
from collibra_connector.testing import MockCollibraConnector, mock_collibra

@mock_collibra
def test_my_function():
    conn = CollibraConnector(api="mock://", username="x", password="y")
    asset = conn.asset.get_asset("any-id")
    assert asset.name is not None
```

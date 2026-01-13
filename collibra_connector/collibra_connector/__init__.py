#
#
#                           ███
#                     ██    ███   ███
#                    ████         ███
#              ███   ████   ██    ███   ████
#              ███   ████   ███   ███   ████
#                           ███   ███
#                           ███   ███
#          ██████████████   ███   ███   ████████
#           ███████████      █    ███    ██████
#
#         ███  █████████████   ████████████   ███
#         ███  █████████████   ████████████   ███
#
#           ██████           █     █████████████
#          ███████   ████   ███   ██████████████
#                    ████   ███
#                    ████   ███
#              ███   ████   ███   ███   ████
#               ██   ████   ██    ███    ██
#                    ████         ███
#                     ██    ███   ███
#                            █
#
#
"""
Collibra Connector Library
~~~~~~~~~~~~~~~~~~~~~~~~~~

A professional Python SDK for the Collibra Data Governance Center API.

Features:
    - Full type safety with Pydantic models
    - Async support for high-performance batch operations
    - Declarative lineage builder
    - OpenTelemetry integration for observability
    - CLI tool for terminal operations
    - Mock engine for testing

Basic Usage:
    >>> from collibra_connector import CollibraConnector
    >>>
    >>> conn = CollibraConnector(
    ...     api="https://your-instance.collibra.com",
    ...     username="user",
    ...     password="pass"
    ... )
    >>>
    >>> # All methods return typed Pydantic models
    >>> asset = conn.asset.get_asset("uuid")
    >>> print(asset.name)  # Full IDE autocompletion
    >>> print(asset.status.name)

Async Usage:
    >>> from collibra_connector import AsyncCollibraConnector
    >>> import asyncio
    >>>
    >>> async def main():
    ...     async with AsyncCollibraConnector(...) as conn:
    ...         # Fetch 100 assets in parallel
    ...         assets = await conn.asset.get_assets_batch(ids)
    >>>
    >>> asyncio.run(main())

Lineage Builder:
    >>> from collibra_connector.lineage import LineageBuilder, LineageNode
    >>>
    >>> builder = LineageBuilder(conn)
    >>> source = LineageNode.table("raw.orders")
    >>> target = LineageNode.table("warehouse.orders")
    >>> builder.add_edge(source, target, "is source for")
    >>> builder.commit(domain_id="lineage-domain-uuid")

Testing:
    >>> from collibra_connector.testing import MockCollibraConnector
    >>>
    >>> mock = MockCollibraConnector()
    >>> mock.asset.add_mock_asset({"name": "Test"})
    >>> asset = mock.asset.get_asset("any-id")
"""

from .connector import CollibraConnector
from .api.Exceptions import (
    CollibraAPIError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError,
)
from .helpers import (
    Paginator,
    PaginatedResponse,
    BatchProcessor,
    BatchResult,
    CachedMetadata,
    DataTransformer,
    DataFrameExporter,
    timed_cache,
)
from .models import (
    # Base classes
    BaseCollibraModel,
    ResourceReference,
    NamedResource,
    TimestampMixin,
    # Core models
    AssetModel,
    DomainModel,
    CommunityModel,
    UserModel,
    StatusModel,
    # Type models
    AssetTypeModel,
    DomainTypeModel,
    AttributeTypeModel,
    RelationTypeModel,
    RoleModel,
    # Data models
    AttributeModel,
    RelationModel,
    ResponsibilityModel,
    CommentModel,
    # Workflow models
    WorkflowDefinitionModel,
    WorkflowInstanceModel,
    WorkflowTaskModel,
    # Profile models
    AssetProfileModel,
    RelationsGrouped,
    RelationSummary,
    ResponsibilitySummary,
    # Paginated responses
    PaginatedResponseModel,
    AssetList,
    DomainList,
    CommunityList,
    UserList,
    AttributeList,
    RelationList,
    ResponsibilityList,
    CommentList,
    WorkflowDefinitionList,
    WorkflowInstanceList,
    WorkflowTaskList,
    SearchResults,
    # Factory functions
    parse_asset,
    parse_assets,
    parse_domain,
    parse_domains,
    parse_community,
    parse_communities,
    parse_user,
    parse_users,
    parse_attribute,
    parse_attributes,
    parse_relation,
    parse_relations,
    parse_responsibility,
    parse_responsibilities,
    parse_comment,
    parse_comments,
    parse_workflow_definition,
    parse_workflow_definitions,
    parse_workflow_instance,
    parse_workflow_instances,
    parse_workflow_task,
    parse_workflow_tasks,
    parse_search_results,
)

# Async connector (optional - requires httpx)
try:
    from .async_connector import AsyncCollibraConnector
except ImportError:
    AsyncCollibraConnector = None  # type: ignore

# Lineage builder
from .lineage import (
    LineageBuilder,
    LineageNode,
    LineageEdge,
    LineageCommitResult,
    LineageDirection,
    LineageRelationType,
)

# Telemetry (optional - requires opentelemetry)
try:
    from .telemetry import (
        enable_telemetry,
        disable_telemetry,
        is_telemetry_available,
        is_telemetry_enabled,
        traced,
        traced_async,
        span,
        TracedCollibraConnector,
        get_current_trace_id,
        get_current_span_id,
        add_span_attributes,
        record_exception,
    )
except ImportError:
    enable_telemetry = None  # type: ignore
    disable_telemetry = None  # type: ignore
    is_telemetry_available = lambda: False  # type: ignore
    is_telemetry_enabled = lambda: False  # type: ignore
    traced = None  # type: ignore
    traced_async = None  # type: ignore
    span = None  # type: ignore
    TracedCollibraConnector = None  # type: ignore
    get_current_trace_id = None  # type: ignore
    get_current_span_id = None  # type: ignore
    add_span_attributes = None  # type: ignore
    record_exception = None  # type: ignore

# Testing utilities
from .testing import (
    MockCollibraConnector,
    mock_collibra,
    mock_collibra_context,
    CollibraTestCase,
    MockDataStore,
)

__version__ = "1.2.0"
__all__ = [
    # Main connector
    "CollibraConnector",
    "AsyncCollibraConnector",
    # Exceptions
    "CollibraAPIError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ServerError",
    # Helpers
    "Paginator",
    "PaginatedResponse",
    "BatchProcessor",
    "BatchResult",
    "CachedMetadata",
    "DataTransformer",
    "DataFrameExporter",
    "timed_cache",
    # Base models
    "BaseCollibraModel",
    "ResourceReference",
    "NamedResource",
    "TimestampMixin",
    # Core models
    "AssetModel",
    "DomainModel",
    "CommunityModel",
    "UserModel",
    "StatusModel",
    # Type models
    "AssetTypeModel",
    "DomainTypeModel",
    "AttributeTypeModel",
    "RelationTypeModel",
    "RoleModel",
    # Data models
    "AttributeModel",
    "RelationModel",
    "ResponsibilityModel",
    "CommentModel",
    # Search models
    "SearchResultModel",
    "SearchResource",
    # Workflow models
    "WorkflowDefinitionModel",
    "WorkflowInstanceModel",
    "WorkflowTaskModel",
    # Profile models
    "AssetProfileModel",
    "RelationsGrouped",
    "RelationSummary",
    "ResponsibilitySummary",
    # Paginated responses
    "PaginatedResponseModel",
    "AssetList",
    "DomainList",
    "CommunityList",
    "UserList",
    "AttributeList",
    "RelationList",
    "ResponsibilityList",
    "CommentList",
    "WorkflowDefinitionList",
    "WorkflowInstanceList",
    "WorkflowTaskList",
    "SearchResults",
    # Factory functions
    "parse_asset",
    "parse_assets",
    "parse_domain",
    "parse_domains",
    "parse_community",
    "parse_communities",
    "parse_user",
    "parse_users",
    "parse_attribute",
    "parse_attributes",
    "parse_relation",
    "parse_relations",
    "parse_responsibility",
    "parse_responsibilities",
    "parse_comment",
    "parse_comments",
    "parse_workflow_definition",
    "parse_workflow_definitions",
    "parse_workflow_instance",
    "parse_workflow_instances",
    "parse_workflow_task",
    "parse_workflow_tasks",
    "parse_search_results",
    # Lineage
    "LineageBuilder",
    "LineageNode",
    "LineageEdge",
    "LineageCommitResult",
    "LineageDirection",
    "LineageRelationType",
    # Telemetry
    "enable_telemetry",
    "disable_telemetry",
    "is_telemetry_available",
    "is_telemetry_enabled",
    "traced",
    "traced_async",
    "span",
    "TracedCollibraConnector",
    "get_current_trace_id",
    "get_current_span_id",
    "add_span_attributes",
    "record_exception",
    # Testing
    "MockCollibraConnector",
    "mock_collibra",
    "mock_collibra_context",
    "CollibraTestCase",
    "MockDataStore",
]

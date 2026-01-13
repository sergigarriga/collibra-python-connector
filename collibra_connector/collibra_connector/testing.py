"""
Mocking Engine for Collibra Connector Testing.

This module provides utilities for testing code that uses the Collibra Connector
without making actual API calls. Perfect for unit tests and CI/CD pipelines.

Example:
    >>> from collibra_connector.testing import mock_collibra, MockCollibraConnector
    >>>
    >>> @mock_collibra
    ... def test_my_function():
    ...     conn = CollibraConnector(api="mock://", username="test", password="test")
    ...     asset = conn.asset.get_asset("any-uuid")
    ...     assert asset["name"] == "Mock Asset"

Or with custom responses:
    >>> from collibra_connector.testing import MockCollibraConnector
    >>>
    >>> def test_with_custom_data():
    ...     mock = MockCollibraConnector()
    ...     mock.asset.add_mock_asset({
    ...         "id": "custom-id",
    ...         "name": "Custom Asset",
    ...         "type": {"id": "type-1", "name": "Business Term"}
    ...     })
    ...
    ...     asset = mock.asset.get_asset("custom-id")
    ...     assert asset.name == "Custom Asset"
"""
from __future__ import annotations

import functools
import re
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar, Union
from unittest.mock import MagicMock, patch

from .models import (
    AssetModel,
    AssetList,
    DomainModel,
    DomainList,
    CommunityModel,
    CommunityList,
    UserModel,
    AttributeModel,
    AttributeList,
    RelationModel,
    RelationList,
    SearchResultModel,
    SearchResults,
    AssetProfileModel,
    ResourceReference,
    RelationsGrouped,
    RelationSummary,
    ResponsibilitySummary,
    PaginatedResponseModel,
    parse_asset,
    parse_assets,
)


T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def generate_timestamp() -> int:
    """Generate current timestamp in milliseconds."""
    return int(datetime.now().timestamp() * 1000)


@dataclass
class MockResponse:
    """Mock HTTP response."""
    status_code: int = 200
    data: Dict[str, Any] = field(default_factory=dict)

    def json(self) -> Dict[str, Any]:
        return self.data

    @property
    def text(self) -> str:
        import json
        return json.dumps(self.data)


@dataclass
class MockDataStore:
    """In-memory data store for mock data."""
    assets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    domains: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    communities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    users: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    attributes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    asset_types: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    statuses: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def clear(self) -> None:
        """Clear all data."""
        self.assets.clear()
        self.domains.clear()
        self.communities.clear()
        self.users.clear()
        self.attributes.clear()
        self.relations.clear()
        self.asset_types.clear()
        self.statuses.clear()


# Global mock data store
_mock_store = MockDataStore()


def _create_default_asset(
    asset_id: Optional[str] = None,
    name: str = "Mock Asset",
    **kwargs: Any
) -> Dict[str, Any]:
    """Create a default mock asset."""
    aid = asset_id or generate_uuid()
    return {
        "id": aid,
        "resourceType": "Asset",
        "name": name,
        "displayName": kwargs.get("display_name", name),
        "description": kwargs.get("description"),
        "type": kwargs.get("type", {
            "id": generate_uuid(),
            "resourceType": "AssetType",
            "name": "Business Term"
        }),
        "status": kwargs.get("status", {
            "id": generate_uuid(),
            "resourceType": "Status",
            "name": "Approved"
        }),
        "domain": kwargs.get("domain", {
            "id": generate_uuid(),
            "resourceType": "Domain",
            "name": "Mock Domain"
        }),
        "avgRating": kwargs.get("avg_rating", 0.0),
        "ratingsCount": kwargs.get("ratings_count", 0),
        "createdOn": kwargs.get("created_on", generate_timestamp()),
        "lastModifiedOn": kwargs.get("last_modified_on", generate_timestamp()),
        "excludedFromAutoHyperlinking": kwargs.get("excluded_from_auto_hyperlinking", False)
    }


def _create_default_domain(
    domain_id: Optional[str] = None,
    name: str = "Mock Domain",
    **kwargs: Any
) -> Dict[str, Any]:
    """Create a default mock domain."""
    did = domain_id or generate_uuid()
    return {
        "id": did,
        "resourceType": "Domain",
        "name": name,
        "description": kwargs.get("description"),
        "type": kwargs.get("type", {
            "id": generate_uuid(),
            "resourceType": "DomainType",
            "name": "Business Glossary"
        }),
        "community": kwargs.get("community", {
            "id": generate_uuid(),
            "resourceType": "Community",
            "name": "Mock Community"
        }),
        "createdOn": generate_timestamp(),
        "lastModifiedOn": generate_timestamp()
    }


def _create_default_community(
    community_id: Optional[str] = None,
    name: str = "Mock Community",
    **kwargs: Any
) -> Dict[str, Any]:
    """Create a default mock community."""
    cid = community_id or generate_uuid()
    return {
        "id": cid,
        "resourceType": "Community",
        "name": name,
        "description": kwargs.get("description"),
        "parent": kwargs.get("parent"),
        "createdOn": generate_timestamp(),
        "lastModifiedOn": generate_timestamp()
    }


class MockAssetAPI:
    """Mock Asset API with typed returns."""

    def __init__(self, store: MockDataStore) -> None:
        self._store = store

    def add_mock_asset(self, data: Dict[str, Any]) -> str:
        """Add a mock asset to the store."""
        asset_id = data.get("id", generate_uuid())
        self._store.assets[asset_id] = {**_create_default_asset(asset_id), **data}
        return asset_id

    def get_asset(self, asset_id: str) -> AssetModel:
        """Get an asset by ID."""
        if asset_id in self._store.assets:
            return parse_asset(self._store.assets[asset_id])

        # Return default mock asset
        return parse_asset(_create_default_asset(asset_id))

    def find_assets(
        self,
        community_id: Optional[str] = None,
        domain_id: Optional[str] = None,
        asset_type_ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any
    ) -> AssetList:
        """Find assets with filters."""
        results = list(self._store.assets.values())

        # Apply filters
        if domain_id:
            results = [a for a in results if a.get("domain", {}).get("id") == domain_id]
        if community_id:
            results = [a for a in results if a.get("community", {}).get("id") == community_id]
        if asset_type_ids:
            results = [a for a in results if a.get("type", {}).get("id") in asset_type_ids]

        # If no assets in store, return mock data
        if not results:
            results = [_create_default_asset() for _ in range(min(3, limit))]

        # Apply pagination
        total = len(results)
        results = results[offset:offset + limit]

        return parse_assets({
            "results": results,
            "total": total,
            "offset": offset,
            "limit": limit
        })

    def add_asset(
        self,
        name: str,
        domain_id: str,
        type_id: Optional[str] = None,
        status_id: Optional[str] = None,
        display_name: Optional[str] = None,
        **kwargs: Any
    ) -> AssetModel:
        """Create a new mock asset."""
        asset_id = generate_uuid()
        asset = _create_default_asset(
            asset_id=asset_id,
            name=name,
            display_name=display_name or name
        )
        if type_id:
            asset["type"]["id"] = type_id
        if status_id:
            asset["status"]["id"] = status_id
        asset["domain"]["id"] = domain_id

        self._store.assets[asset_id] = asset
        return parse_asset(asset)

    def change_asset(
        self,
        asset_id: str,
        **kwargs: Any
    ) -> AssetModel:
        """Update a mock asset."""
        if asset_id in self._store.assets:
            asset = self._store.assets[asset_id]
            if "name" in kwargs and kwargs["name"]:
                asset["name"] = kwargs["name"]
            if "display_name" in kwargs and kwargs["display_name"]:
                asset["displayName"] = kwargs["display_name"]
            if "status_id" in kwargs and kwargs["status_id"]:
                asset["status"]["id"] = kwargs["status_id"]
            return parse_asset(asset)

        return parse_asset(_create_default_asset(asset_id))

    def remove_asset(self, asset_id: str) -> None:
        """Remove a mock asset."""
        self._store.assets.pop(asset_id, None)

    def get_full_profile(
        self,
        asset_id: str,
        include_attributes: bool = True,
        include_relations: bool = True,
        include_responsibilities: bool = True,
        **kwargs: Any
    ) -> AssetProfileModel:
        """Get full profile for an asset."""
        asset = self.get_asset(asset_id)

        return AssetProfileModel(
            asset=asset,
            attributes={"Description": "Mock description", "Definition": "Mock definition"},
            relations=RelationsGrouped(
                outgoing={"contains": [RelationSummary(id=generate_uuid(), target_id=generate_uuid(), target_name="Related Asset")]},
                incoming={},
                outgoing_count=1,
                incoming_count=0
            ),
            responsibilities=[ResponsibilitySummary(role="Data Steward", owner="Mock User", owner_id=generate_uuid())]
        )


class MockAttributeAPI:
    """Mock Attribute API."""

    def __init__(self, store: MockDataStore) -> None:
        self._store = store

    def get_attributes(
        self,
        asset_id: str,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any
    ) -> AttributeList:
        """Get attributes for an asset."""
        # Return mock attributes
        attrs = [
            {
                "id": generate_uuid(),
                "resourceType": "Attribute",
                "type": {"id": generate_uuid(), "name": "Description"},
                "value": "Mock description",
                "asset": {"id": asset_id}
            },
            {
                "id": generate_uuid(),
                "resourceType": "Attribute",
                "type": {"id": generate_uuid(), "name": "Definition"},
                "value": "Mock definition",
                "asset": {"id": asset_id}
            }
        ]
        return PaginatedResponseModel[AttributeModel](
            results=[AttributeModel.model_validate(a) for a in attrs],
            total=len(attrs),
            offset=offset,
            limit=limit
        )

    def get_attributes_as_dict(self, asset_id: str) -> Dict[str, Any]:
        """Get attributes as dict."""
        return {
            "Description": "Mock description",
            "Definition": "Mock definition"
        }

    def add_attribute(
        self,
        asset_id: str,
        type_id: str,
        value: Any
    ) -> AttributeModel:
        """Add an attribute."""
        attr = {
            "id": generate_uuid(),
            "resourceType": "Attribute",
            "type": {"id": type_id, "name": "Custom"},
            "value": value,
            "asset": {"id": asset_id}
        }
        return AttributeModel.model_validate(attr)


class MockDomainAPI:
    """Mock Domain API."""

    def __init__(self, store: MockDataStore) -> None:
        self._store = store

    def add_mock_domain(self, data: Dict[str, Any]) -> str:
        """Add a mock domain to the store."""
        domain_id = data.get("id", generate_uuid())
        self._store.domains[domain_id] = {**_create_default_domain(domain_id), **data}
        return domain_id

    def get_domain(self, domain_id: str) -> DomainModel:
        """Get a domain by ID."""
        if domain_id in self._store.domains:
            return DomainModel.model_validate(self._store.domains[domain_id])
        return DomainModel.model_validate(_create_default_domain(domain_id))

    def find_domains(
        self,
        community_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any
    ) -> DomainList:
        """Find domains."""
        results = list(self._store.domains.values())
        if community_id:
            results = [d for d in results if d.get("community", {}).get("id") == community_id]

        if not results:
            results = [_create_default_domain() for _ in range(min(2, limit))]

        return PaginatedResponseModel[DomainModel](
            results=[DomainModel.model_validate(d) for d in results[offset:offset + limit]],
            total=len(results),
            offset=offset,
            limit=limit
        )


class MockCommunityAPI:
    """Mock Community API."""

    def __init__(self, store: MockDataStore) -> None:
        self._store = store

    def get_community(self, community_id: str) -> CommunityModel:
        """Get a community by ID."""
        if community_id in self._store.communities:
            return CommunityModel.model_validate(self._store.communities[community_id])
        return CommunityModel.model_validate(_create_default_community(community_id))

    def find_communities(
        self,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any
    ) -> CommunityList:
        """Find communities."""
        results = list(self._store.communities.values())
        if not results:
            results = [_create_default_community() for _ in range(min(2, limit))]

        return PaginatedResponseModel[CommunityModel](
            results=[CommunityModel.model_validate(c) for c in results[offset:offset + limit]],
            total=len(results),
            offset=offset,
            limit=limit
        )


class MockRelationAPI:
    """Mock Relation API."""

    def __init__(self, store: MockDataStore) -> None:
        self._store = store

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        type_id: str,
        **kwargs: Any
    ) -> RelationModel:
        """Create a relation."""
        rel = {
            "id": generate_uuid(),
            "resourceType": "Relation",
            "type": {"id": type_id, "name": "is source for"},
            "source": {"id": source_id, "name": "Source Asset"},
            "target": {"id": target_id, "name": "Target Asset"}
        }
        self._store.relations[rel["id"]] = rel
        return RelationModel.model_validate(rel)

    def find_relations(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any
    ) -> RelationList:
        """Find relations."""
        results = list(self._store.relations.values())
        if source_id:
            results = [r for r in results if r.get("source", {}).get("id") == source_id]
        if target_id:
            results = [r for r in results if r.get("target", {}).get("id") == target_id]

        return PaginatedResponseModel[RelationModel](
            results=[RelationModel.model_validate(r) for r in results[offset:offset + limit]],
            total=len(results),
            offset=offset,
            limit=limit
        )

    def get_asset_relations(
        self,
        asset_id: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Get relations for an asset."""
        return {
            "outgoing": {},
            "incoming": {},
            "outgoing_count": 0,
            "incoming_count": 0
        }


class MockSearchAPI:
    """Mock Search API."""

    def __init__(self, store: MockDataStore) -> None:
        self._store = store

    def find(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        **kwargs: Any
    ) -> SearchResults:
        """Search for assets."""
        # Simple matching on asset names
        results = []
        pattern = query.replace("*", ".*")

        for asset in self._store.assets.values():
            if re.search(pattern, asset.get("name", ""), re.IGNORECASE):
                results.append({
                    "resource": {
                        "id": asset["id"],
                        "resourceType": "Asset",
                        "name": asset["name"],
                        "displayName": asset.get("displayName")
                    },
                    "score": 1.0
                })

        # Add default results if empty
        if not results:
            results = [{
                "resource": {
                    "id": generate_uuid(),
                    "resourceType": "Asset",
                    "name": f"Result for: {query}",
                    "displayName": f"Result for: {query}"
                },
                "score": 0.9
            }]

        return PaginatedResponseModel[SearchResultModel](
            results=[SearchResultModel.model_validate(r) for r in results[offset:offset + limit]],
            total=len(results),
            offset=offset,
            limit=limit
        )

    def find_assets(self, query: str, **kwargs: Any) -> SearchResults:
        """Search specifically for assets."""
        return self.find(query, **kwargs)


class MockMetadataAPI:
    """Mock Metadata API."""

    def __init__(self, store: MockDataStore) -> None:
        self._store = store

    def get_asset_types(self, name: Optional[str] = None, limit: int = 100, **kwargs: Any) -> Dict[str, Any]:
        """Get asset types."""
        types = [
            {"id": generate_uuid(), "name": "Business Term", "publicId": "BusinessTerm"},
            {"id": generate_uuid(), "name": "Table", "publicId": "Table"},
            {"id": generate_uuid(), "name": "Column", "publicId": "Column"},
            {"id": generate_uuid(), "name": "Data Pipeline", "publicId": "DataPipeline"}
        ]
        if name:
            types = [t for t in types if name.lower() in t["name"].lower()]
        return {"results": types[:limit], "total": len(types)}

    def get_statuses(self, limit: int = 100, **kwargs: Any) -> Dict[str, Any]:
        """Get statuses."""
        statuses = [
            {"id": generate_uuid(), "name": "Approved"},
            {"id": generate_uuid(), "name": "Pending"},
            {"id": generate_uuid(), "name": "Rejected"},
            {"id": generate_uuid(), "name": "Draft"}
        ]
        return {"results": statuses[:limit], "total": len(statuses)}

    def get_relation_types(self, role: Optional[str] = None, limit: int = 100, **kwargs: Any) -> Dict[str, Any]:
        """Get relation types."""
        types = [
            {"id": generate_uuid(), "name": "contains", "role": "contains", "coRole": "is part of"},
            {"id": generate_uuid(), "name": "is source for", "role": "is source for", "coRole": "is target for"}
        ]
        if role:
            types = [t for t in types if role.lower() in (t.get("role") or "").lower()]
        return {"results": types[:limit], "total": len(types)}


class MockResponsibilityAPI:
    """Mock Responsibility API."""

    def __init__(self, store: MockDataStore) -> None:
        self._store = store

    def get_asset_responsibilities(self, asset_id: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get responsibilities for an asset."""
        return [
            {"role": "Data Steward", "owner": "Mock User", "owner_id": generate_uuid()},
            {"role": "Technical Owner", "owner": "Tech User", "owner_id": generate_uuid()}
        ]


class MockCollibraConnector:
    """
    Mock Collibra Connector for testing.

    This class provides the same interface as CollibraConnector
    but returns mock data instead of making API calls.

    Example:
        >>> mock = MockCollibraConnector()
        >>>
        >>> # Add custom test data
        >>> mock.asset.add_mock_asset({
        ...     "id": "test-id",
        ...     "name": "Test Asset",
        ...     "type": {"id": "type-1", "name": "Business Term"}
        ... })
        >>>
        >>> # Use like regular connector
        >>> asset = mock.asset.get_asset("test-id")
        >>> assert asset.name == "Test Asset"
        >>>
        >>> # Find assets
        >>> results = mock.asset.find_assets(limit=10)
        >>> for asset in results:
        ...     print(asset.name)
    """

    def __init__(
        self,
        api: str = "mock://collibra.test",
        username: str = "test",
        password: str = "test",
        **kwargs: Any
    ) -> None:
        """Initialize mock connector."""
        self._api = api
        self._base_url = api
        self._store = MockDataStore()

        # Initialize mock APIs
        self.asset = MockAssetAPI(self._store)
        self.attribute = MockAttributeAPI(self._store)
        self.domain = MockDomainAPI(self._store)
        self.community = MockCommunityAPI(self._store)
        self.relation = MockRelationAPI(self._store)
        self.search = MockSearchAPI(self._store)
        self.metadata = MockMetadataAPI(self._store)
        self.responsibility = MockResponsibilityAPI(self._store)

    @property
    def api(self) -> str:
        return self._api

    @property
    def base_url(self) -> str:
        return self._base_url

    def test_connection(self) -> bool:
        """Always returns True for mock."""
        return True

    def get_version(self) -> str:
        """Get mock version."""
        return "1.2.0-mock"

    def clear_all_data(self) -> None:
        """Clear all mock data."""
        self._store.clear()

    def __enter__(self) -> "MockCollibraConnector":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


@contextmanager
def mock_collibra_context(
    custom_data: Optional[Dict[str, Any]] = None
) -> Generator[MockCollibraConnector, None, None]:
    """
    Context manager for mocking Collibra in tests.

    Args:
        custom_data: Optional dict with custom mock data.

    Yields:
        MockCollibraConnector instance.

    Example:
        >>> with mock_collibra_context() as mock_conn:
        ...     mock_conn.asset.add_mock_asset({"name": "Test"})
        ...     result = mock_conn.asset.find_assets()
        ...     assert len(result) > 0
    """
    mock = MockCollibraConnector()

    if custom_data:
        for asset in custom_data.get("assets", []):
            mock.asset.add_mock_asset(asset)
        for domain in custom_data.get("domains", []):
            mock.domain.add_mock_domain(domain)

    yield mock


def mock_collibra(func: Optional[F] = None, **kwargs: Any) -> Union[F, Callable[[F], F]]:
    """
    Decorator for mocking Collibra in tests.

    Can be used with or without arguments.

    Examples:
        >>> @mock_collibra
        ... def test_something():
        ...     conn = CollibraConnector(api="mock://", username="x", password="y")
        ...     # This will use mock data
        ...     asset = conn.asset.get_asset("any-id")
        >>>
        >>> @mock_collibra(custom_assets=[{"name": "Custom"}])
        ... def test_with_data():
        ...     pass
    """
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def wrapper(*args: Any, **kw: Any) -> Any:
            # Patch CollibraConnector to return MockCollibraConnector
            with patch('collibra_connector.CollibraConnector', MockCollibraConnector):
                with patch('collibra_connector.connector.CollibraConnector', MockCollibraConnector):
                    return f(*args, **kw)
        return wrapper  # type: ignore

    if func is not None:
        return decorator(func)
    return decorator


class CollibraTestCase:
    """
    Base test case class for Collibra tests.

    Provides setUp/tearDown with automatic mocking.

    Example:
        >>> class TestMyFeature(CollibraTestCase):
        ...     def test_asset_creation(self):
        ...         asset = self.connector.asset.add_asset(
        ...             name="Test",
        ...             domain_id="domain-uuid"
        ...         )
        ...         assert asset.name == "Test"
    """

    def setUp(self) -> None:
        """Set up mock connector."""
        self.connector = MockCollibraConnector()

    def tearDown(self) -> None:
        """Clean up mock data."""
        self.connector.clear_all_data()

    def add_test_asset(self, **kwargs: Any) -> str:
        """Helper to add a test asset."""
        data = {
            "name": kwargs.get("name", "Test Asset"),
            **kwargs
        }
        return self.connector.asset.add_mock_asset(data)

    def add_test_domain(self, **kwargs: Any) -> str:
        """Helper to add a test domain."""
        data = {
            "name": kwargs.get("name", "Test Domain"),
            **kwargs
        }
        return self.connector.domain.add_mock_domain(data)

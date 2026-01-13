"""
Async Collibra Connector - Asynchronous API client using httpx.

This module provides an asynchronous version of CollibraConnector,
enabling parallel requests for massive performance improvements
in batch operations and migrations.

Example:
    >>> import asyncio
    >>> from collibra_connector import AsyncCollibraConnector
    >>>
    >>> async def main():
    ...     async with AsyncCollibraConnector(
    ...         api="https://your-instance.collibra.com",
    ...         username="user",
    ...         password="pass"
    ...     ) as conn:
    ...         # Fetch 100 assets in parallel
    ...         asset_ids = ["uuid1", "uuid2", ..., "uuid100"]
    ...         assets = await conn.asset.get_assets_batch(asset_ids)
    ...         print(f"Fetched {len(assets)} assets")
    >>>
    >>> asyncio.run(main())
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, TypeVar, Union, TYPE_CHECKING

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .models import (
    AssetModel,
    AssetList,
    DomainModel,
    DomainList,
    CommunityModel,
    CommunityList,
    UserModel,
    UserList,
    AttributeModel,
    AttributeList,
    RelationModel,
    RelationList,
    ResponsibilityModel,
    ResponsibilityList,
    CommentModel,
    CommentList,
    WorkflowDefinitionModel,
    WorkflowDefinitionList,
    WorkflowInstanceModel,
    WorkflowInstanceList,
    WorkflowTaskModel,
    WorkflowTaskList,
    SearchResults,
    SearchResultModel,
    AssetProfileModel,
    RelationsGrouped,
    RelationSummary,
    ResponsibilitySummary,
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
from .api.Exceptions import (
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError,
)


T = TypeVar('T')


class AsyncBaseAPI:
    """Base class for async API modules."""

    def __init__(self, connector: "AsyncCollibraConnector") -> None:
        self._connector = connector
        self._base_url = connector.api

    async def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make async GET request."""
        return await self._connector._request("GET", endpoint, params=params)

    async def _post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make async POST request."""
        return await self._connector._request("POST", endpoint, json=data, params=params)

    async def _put(
        self,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make async PUT request."""
        return await self._connector._request("PUT", endpoint, json=data)

    async def _patch(
        self,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make async PATCH request."""
        return await self._connector._request("PATCH", endpoint, json=data)

    async def _delete(self, endpoint: str) -> Dict[str, Any]:
        """Make async DELETE request."""
        return await self._connector._request("DELETE", endpoint)


class AsyncAssetAPI(AsyncBaseAPI):
    """Async Asset API with typed returns."""

    async def get_asset(self, asset_id: str) -> AssetModel:
        """
        Get an asset by ID.

        Args:
            asset_id: The UUID of the asset.

        Returns:
            AssetModel with full type information.

        Example:
            >>> asset = await conn.asset.get_asset("uuid")
            >>> print(asset.name)
            >>> print(asset.status.name)
        """
        data = await self._get(f"/assets/{asset_id}")
        return parse_asset(data)

    async def find_assets(
        self,
        community_id: Optional[str] = None,
        domain_id: Optional[str] = None,
        asset_type_ids: Optional[List[str]] = None,
        status_ids: Optional[List[str]] = None,
        name: Optional[str] = None,
        name_match_mode: str = "ANYWHERE",
        limit: int = 100,
        offset: int = 0
    ) -> AssetList:
        """
        Find assets with filters.

        Args:
            community_id: Filter by community.
            domain_id: Filter by domain.
            asset_type_ids: Filter by asset type IDs.
            status_ids: Filter by status IDs.
            name: Filter by name.
            name_match_mode: How to match name (ANYWHERE, START, END, EXACT).
            limit: Max results per page.
            offset: Offset for pagination.

        Returns:
            AssetList with paginated results.
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if community_id:
            params["communityId"] = community_id
        if domain_id:
            params["domainId"] = domain_id
        if asset_type_ids:
            params["typeIds"] = asset_type_ids
        if status_ids:
            params["statusIds"] = status_ids
        if name:
            params["name"] = name
            params["nameMatchMode"] = name_match_mode

        data = await self._get("/assets", params=params)
        return parse_assets(data)

    async def get_assets_batch(
        self,
        asset_ids: List[str],
        max_concurrent: int = 50
    ) -> List[AssetModel]:
        """
        Fetch multiple assets in parallel.

        This is the key advantage of async - fetch 100 assets
        in the time it would take to fetch 2-3 sequentially.

        Args:
            asset_ids: List of asset UUIDs to fetch.
            max_concurrent: Maximum concurrent requests.

        Returns:
            List of AssetModel objects.

        Example:
            >>> assets = await conn.asset.get_assets_batch(["id1", "id2", ...])
            >>> for asset in assets:
            ...     print(f"{asset.name}: {asset.status.name}")
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_one(asset_id: str) -> Optional[AssetModel]:
            async with semaphore:
                try:
                    return await self.get_asset(asset_id)
                except Exception:
                    return None

        results = await asyncio.gather(*[fetch_one(aid) for aid in asset_ids])
        return [r for r in results if r is not None]

    async def add_asset(
        self,
        name: str,
        domain_id: str,
        type_id: Optional[str] = None,
        status_id: Optional[str] = None,
        display_name: Optional[str] = None,
        excluded_from_auto_hyperlinking: bool = False
    ) -> AssetModel:
        """Create a new asset."""
        data: Dict[str, Any] = {
            "name": name,
            "domainId": domain_id,
            "excludedFromAutoHyperlinking": excluded_from_auto_hyperlinking
        }
        if type_id:
            data["typeId"] = type_id
        if status_id:
            data["statusId"] = status_id
        if display_name:
            data["displayName"] = display_name

        result = await self._post("/assets", data)
        return parse_asset(result)

    async def add_assets_batch(
        self,
        assets: List[Dict[str, Any]],
        max_concurrent: int = 20
    ) -> List[AssetModel]:
        """
        Create multiple assets in parallel.

        Args:
            assets: List of asset data dicts with keys:
                   name, domain_id, type_id, status_id, display_name
            max_concurrent: Maximum concurrent requests.

        Returns:
            List of created AssetModel objects.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def create_one(asset_data: Dict[str, Any]) -> Optional[AssetModel]:
            async with semaphore:
                try:
                    return await self.add_asset(**asset_data)
                except Exception:
                    return None

        results = await asyncio.gather(*[create_one(a) for a in assets])
        return [r for r in results if r is not None]

    async def change_asset(
        self,
        asset_id: str,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        status_id: Optional[str] = None,
        domain_id: Optional[str] = None
    ) -> AssetModel:
        """Update an asset."""
        data: Dict[str, Any] = {"id": asset_id}
        if name:
            data["name"] = name
        if display_name:
            data["displayName"] = display_name
        if status_id:
            data["statusId"] = status_id
        if domain_id:
            data["domainId"] = domain_id

        result = await self._patch(f"/assets/{asset_id}", data)
        return parse_asset(result)

    async def remove_asset(self, asset_id: str) -> None:
        """Delete an asset."""
        await self._delete(f"/assets/{asset_id}")

    async def get_full_profile(
        self,
        asset_id: str,
        include_attributes: bool = True,
        include_relations: bool = True,
        include_responsibilities: bool = True
    ) -> AssetProfileModel:
        """
        Get complete asset profile with all related data in parallel.

        This method fetches asset, attributes, relations, and responsibilities
        all in parallel, providing maximum performance.

        Args:
            asset_id: The UUID of the asset.
            include_attributes: Include attributes.
            include_relations: Include relations.
            include_responsibilities: Include responsibilities.

        Returns:
            AssetProfileModel with all data.
        """
        # Prepare tasks
        tasks = {
            "asset": self.get_asset(asset_id)
        }

        if include_attributes:
            tasks["attributes"] = self._connector.attribute.get_attributes_as_dict(asset_id)

        if include_relations:
            tasks["relations"] = self._connector.relation.get_asset_relations(asset_id)

        if include_responsibilities:
            tasks["responsibilities"] = self._connector.responsibility.get_asset_responsibilities(asset_id)

        # Execute all in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        result_dict = dict(zip(tasks.keys(), results))

        # Build profile
        asset = result_dict.get("asset")
        if isinstance(asset, Exception):
            raise asset

        attributes = result_dict.get("attributes", {})
        if isinstance(attributes, Exception):
            attributes = {}

        relations = result_dict.get("relations", {})
        if isinstance(relations, Exception):
            relations = {"outgoing": {}, "incoming": {}, "outgoing_count": 0, "incoming_count": 0}

        responsibilities = result_dict.get("responsibilities")
        
        # Build relations model
        relations_grouped = RelationsGrouped(
            outgoing={k: [RelationSummary(**r) for r in v] for k, v in relations.get("outgoing", {}).items()},
            incoming={k: [RelationSummary(**r) for r in v] for k, v in relations.get("incoming", {}).items()},
            outgoing_count=relations.get("outgoing_count", 0),
            incoming_count=relations.get("incoming_count", 0)
        )

        # Build responsibilities
        resp_summaries = []
        if responsibilities and not isinstance(responsibilities, Exception):
            for resp in responsibilities:
                resp_summaries.append(ResponsibilitySummary(
                    role=resp.role.name or "Unknown",
                    owner=resp.owner.name or "Unknown",
                    owner_id=resp.owner.id
                ))

        return AssetProfileModel(
            asset=asset,
            attributes=attributes,
            relations=relations_grouped,
            responsibilities=resp_summaries
        )


class AsyncAttributeAPI(AsyncBaseAPI):
    """Async Attribute API."""

    async def get_attributes(
        self,
        asset_id: str,
        type_ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> AttributeList:
        """Get attributes for an asset."""
        params: Dict[str, Any] = {
            "assetId": asset_id,
            "limit": limit,
            "offset": offset
        }
        if type_ids:
            params["typeIds"] = type_ids

        data = await self._get("/attributes", params=params)
        return parse_attributes(data)

    async def find_attributes(self, *args, **kwargs):
        """Alias for get_attributes."""
        return await self.get_attributes(*args, **kwargs)

    async def get_attributes_as_dict(self, asset_id: str) -> Dict[str, Any]:
        """Get attributes as a simple name->value dict."""
        result = await self.get_attributes(asset_id, limit=500)
        return {
            attr.type.name or "Unknown": attr.value
            for attr in result
        }

    async def add_attribute(
        self,
        asset_id: str,
        type_id: str,
        value: Any
    ) -> AttributeModel:
        """Add an attribute to an asset."""
        data = {
            "assetId": asset_id,
            "typeId": type_id,
            "value": value
        }
        result = await self._post("/attributes", data)
        return parse_attribute(result)

    async def add_attributes_batch(
        self,
        attributes: List[Dict[str, Any]],
        max_concurrent: int = 30
    ) -> List[AttributeModel]:
        """Add multiple attributes in parallel."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def add_one(attr: Dict[str, Any]) -> Optional[AttributeModel]:
            async with semaphore:
                try:
                    return await self.add_attribute(**attr)
                except Exception:
                    return None

        results = await asyncio.gather(*[add_one(a) for a in attributes])
        return [r for r in results if r is not None]


class AsyncDomainAPI(AsyncBaseAPI):
    """Async Domain API."""

    async def get_domain(self, domain_id: str) -> DomainModel:
        """Get a domain by ID."""
        data = await self._get(f"/domains/{domain_id}")
        return parse_domain(data)

    async def find_domains(
        self,
        community_id: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> DomainList:
        """Find domains with filters."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if community_id:
            params["communityId"] = community_id
        if name:
            params["name"] = name

        data = await self._get("/domains", params=params)
        return parse_domains(data)


class AsyncCommunityAPI(AsyncBaseAPI):
    """Async Community API."""

    async def get_community(self, community_id: str) -> CommunityModel:
        """Get a community by ID."""
        data = await self._get(f"/communities/{community_id}")
        return parse_community(data)

    async def find_communities(
        self,
        name: Optional[str] = None,
        parent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> CommunityList:
        """Find communities with filters."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if name:
            params["name"] = name
        if parent_id:
            params["parentId"] = parent_id

        data = await self._get("/communities", params=params)
        return parse_communities(data)


class AsyncRelationAPI(AsyncBaseAPI):
    """Async Relation API."""

    async def get_relation(self, relation_id: str) -> RelationModel:
        """Get a relation by ID."""
        data = await self._get(f"/relations/{relation_id}")
        return parse_relation(data)

    async def find_relations(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        type_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> RelationList:
        """Find relations with filters."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if source_id:
            params["sourceId"] = source_id
        if target_id:
            params["targetId"] = target_id
        if type_id:
            params["typeId"] = type_id

        data = await self._get("/relations", params=params)
        return parse_relations(data)

    async def add_relation(
        self,
        source_id: str,
        target_id: str,
        type_id: str
    ) -> RelationModel:
        """Create a new relation."""
        data = {
            "sourceId": source_id,
            "targetId": target_id,
            "typeId": type_id
        }
        result = await self._post("/relations", data)
        return parse_relation(result)

    async def add_relations_batch(
        self,
        relations: List[Dict[str, str]],
        max_concurrent: int = 30
    ) -> List[RelationModel]:
        """Create multiple relations in parallel."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def add_one(rel: Dict[str, str]) -> Optional[RelationModel]:
            async with semaphore:
                try:
                    return await self.add_relation(**rel)
                except Exception:
                    return None

        results = await asyncio.gather(*[add_one(r) for r in relations])
        return [r for r in results if r is not None]

    async def get_asset_relations(
        self,
        asset_id: str,
        direction: str = "BOTH",
        limit: int = 500
    ) -> Dict[str, Any]:
        """Get all relations for an asset, grouped by direction and type."""
        result: Dict[str, Any] = {
            "outgoing": {},
            "incoming": {},
            "outgoing_count": 0,
            "incoming_count": 0
        }

        tasks = []
        if direction in ("BOTH", "OUTGOING"):
            tasks.append(("outgoing", self.find_relations(source_id=asset_id, limit=limit)))
        if direction in ("BOTH", "INCOMING"):
            tasks.append(("incoming", self.find_relations(target_id=asset_id, limit=limit)))

        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        for (direction_key, _), rel_result in zip(tasks, results):
            if isinstance(rel_result, Exception):
                continue

            result[f"{direction_key}_count"] = rel_result.total

            for rel in rel_result.results:
                type_name = rel.type_name
                if type_name not in result[direction_key]:
                    result[direction_key][type_name] = []

                if direction_key == "outgoing":
                    result[direction_key][type_name].append({
                        "id": rel.id,
                        "target_id": rel.target.id,
                        "target_name": rel.target.name,
                        "target_type": rel.target.resource_type, # Simplified for now as we don't have full type cache here yet
                        "target_status": "N/A" # Status is not easily available without extra calls
                    })
                else:
                    result[direction_key][type_name].append({
                        "id": rel.id,
                        "source_id": rel.source.id,
                        "source_name": rel.source.name,
                        "source_type": rel.source.resource_type,
                        "source_status": "N/A"
                    })

        return result


class AsyncResponsibilityAPI(AsyncBaseAPI):
    """Async Responsibility API."""

    async def get_asset_responsibilities(
        self,
        asset_id: str,
        limit: int = 50
    ) -> ResponsibilityList:
        """Get responsibilities for an asset."""
        params = {"resourceIds": asset_id, "limit": limit}
        data = await self._get("/responsibilities", params=params)
        return parse_responsibilities(data)


class AsyncUserAPI(AsyncBaseAPI):
    """Async User API."""

    async def get_user(self, user_id: str) -> UserModel:
        """Get user by ID."""
        data = await self._get(f"/users/{user_id}")
        return parse_user(data)

    async def find_users(
        self,
        name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> UserList:
        """Find users with filters."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if name:
            params["name"] = name

        data = await self._get("/users", params=params)
        return parse_users(data)


class AsyncCommentAPI(AsyncBaseAPI):
    """Async Comment API."""

    async def add_comment(self, asset_id: str, content: str) -> CommentModel:
        """Add a comment to an asset."""
        data = {
            "content": content,
            "baseResource": {"id": asset_id, "resourceType": "Asset"}
        }
        result = await self._post("/comments", data)
        return parse_comment(result)

    async def find_comments(self, **kwargs) -> CommentList:
        """Find comments with filters."""
        result = await self._get("/comments", params=kwargs)
        return parse_comments(result)


class AsyncWorkflowAPI(AsyncBaseAPI):
    """Async Workflow API."""

    async def find_tasks(self, **kwargs) -> WorkflowTaskList:
        """Find workflow tasks."""
        result = await self._get("/workflowTasks", params=kwargs)
        return parse_workflow_tasks(result)

    async def get_task_form_data(self, task_id: str) -> Dict[str, Any]:
        """Get form data for a task."""
        return await self._get(f"/workflowTasks/{task_id}/taskFormData")


class AsyncSearchAPI(AsyncBaseAPI):
    """Async Search API."""

    async def find(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        category: Optional[str] = None,
        type_ids: Optional[List[str]] = None,
        domain_ids: Optional[List[str]] = None,
        community_ids: Optional[List[str]] = None
    ) -> SearchResults:
        """
        Perform a search query.

        Args:
            query: Search keywords (supports wildcards).
            limit: Max results.
            offset: Pagination offset.
            category: Filter by category (ASSET, DOMAIN, etc.).
            type_ids: Filter by type IDs.
            domain_ids: Filter by domain IDs.
            community_ids: Filter by community IDs.

        Returns:
            SearchResults with typed results.
        """
        data: Dict[str, Any] = {
            "keywords": query,
            "limit": limit,
            "offset": offset
        }

        if category:
            data["category"] = category
        if type_ids:
            data["typeIds"] = type_ids
        if domain_ids:
            data["domainIds"] = domain_ids
        if community_ids:
            data["communityIds"] = community_ids

        result = await self._post("/search", data)
        return parse_search_results(result)

    async def search(self, *args, **kwargs):
        """Alias for find()."""
        return await self.find(*args, **kwargs)

    async def find_assets(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        type_ids: Optional[List[str]] = None,
        domain_ids: Optional[List[str]] = None
    ) -> SearchResults:
        """Search specifically for assets."""
        return await self.find(
            query=query,
            limit=limit,
            offset=offset,
            category="ASSET",
            type_ids=type_ids,
            domain_ids=domain_ids
        )


class AsyncCollibraConnector:
    """
    Asynchronous Collibra Connector using httpx.

    Provides massive performance improvements for batch operations
    by executing requests in parallel.

    Example:
        >>> async with AsyncCollibraConnector(
        ...     api="https://your-instance.collibra.com",
        ...     username="user",
        ...     password="pass"
        ... ) as conn:
        ...     # Fetch 100 assets in parallel (10-50x faster than sync)
        ...     assets = await conn.asset.get_assets_batch(asset_ids)
        ...
        ...     # Create 50 relations in parallel
        ...     relations = await conn.relation.add_relations_batch(relation_data)
    """

    DEFAULT_TIMEOUT: float = 30.0
    DEFAULT_MAX_RETRIES: int = 3
    DEFAULT_RETRY_DELAY: float = 1.0
    RETRYABLE_STATUS_CODES: tuple = (429, 500, 502, 503, 504)

    def __init__(
        self,
        api: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        max_connections: int = 100
    ) -> None:
        """
        Initialize the async connector.

        Args:
            api: Base URL for Collibra (or COLLIBRA_URL env var).
            username: Username (or COLLIBRA_USERNAME env var).
            password: Password (or COLLIBRA_PASSWORD env var).
            timeout: Request timeout in seconds.
            max_retries: Max retry attempts.
            retry_delay: Base delay between retries.
            max_connections: Maximum concurrent connections.
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for async operations. "
                "Install it with: pip install httpx"
            )

        # Load from env vars if not provided
        api = api or os.environ.get("COLLIBRA_URL")
        username = username or os.environ.get("COLLIBRA_USERNAME")
        password = password or os.environ.get("COLLIBRA_PASSWORD")

        if not api:
            raise ValueError("API URL required (arg or COLLIBRA_URL env var)")
        if not username:
            raise ValueError("Username required (arg or COLLIBRA_USERNAME env var)")
        if not password:
            raise ValueError("Password required (arg or COLLIBRA_PASSWORD env var)")

        self._api = api.rstrip("/") + "/rest/2.0"
        self._base_url = api.rstrip("/")
        self._auth = (username, password)
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._max_connections = max_connections

        self._client: Optional[httpx.AsyncClient] = None
        self.logger = logging.getLogger(__name__)

        # Initialize API modules
        self.asset = AsyncAssetAPI(self)
        self.attribute = AsyncAttributeAPI(self)
        self.domain = AsyncDomainAPI(self)
        self.community = AsyncCommunityAPI(self)
        self.user = AsyncUserAPI(self)
        self.relation = AsyncRelationAPI(self)
        self.responsibility = AsyncResponsibilityAPI(self)
        self.comment = AsyncCommentAPI(self)
        self.workflow = AsyncWorkflowAPI(self)
        self.search = AsyncSearchAPI(self)

    @property
    def api(self) -> str:
        """Get the full API URL."""
        return self._api

    async def __aenter__(self) -> "AsyncCollibraConnector":
        """Enter async context manager."""
        limits = httpx.Limits(
            max_connections=self._max_connections,
            max_keepalive_connections=self._max_connections // 2
        )
        self._client = httpx.AsyncClient(
            auth=self._auth,
            timeout=self._timeout,
            limits=limits,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with automatic retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            endpoint: API endpoint (e.g., "/assets/{id}").
            **kwargs: Additional httpx request arguments.

        Returns:
            Response JSON as dictionary.

        Raises:
            Various exceptions based on response status.
        """
        if not self._client:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

        url = f"{self._api}{endpoint}"
        last_exception: Optional[Exception] = None

        for attempt in range(self._max_retries):
            try:
                response = await self._client.request(method, url, **kwargs)

                # Handle response based on status code
                if response.status_code in (200, 201):
                    if response.text.strip():
                        return response.json()
                    return {}
                elif response.status_code == 204:
                    return {}
                elif response.status_code == 401:
                    raise UnauthorizedError(f"Unauthorized: {response.text}")
                elif response.status_code == 403:
                    raise ForbiddenError(f"Forbidden: {response.text}")
                elif response.status_code == 404:
                    raise NotFoundError(f"Not found: {response.text}")
                elif response.status_code >= 500:
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (2 ** attempt)
                        self.logger.warning(
                            f"Server error {response.status_code}, "
                            f"retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise ServerError(f"Server error: {response.text}")
                elif response.status_code == 429:
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (2 ** attempt)
                        self.logger.warning(
                            f"Rate limited, retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise Exception(f"Rate limited: {response.text}")
                else:
                    raise Exception(
                        f"Unexpected status {response.status_code}: {response.text}"
                    )

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"{type(e).__name__}, retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise

        if last_exception:
            raise last_exception
        raise Exception("Request failed after all retries")

    async def test_connection(self) -> bool:
        """Test the connection to Collibra."""
        try:
            await self._request("GET", "/auth/sessions/current")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    async def gather_with_concurrency(
        self,
        coros: List[Any],
        max_concurrent: int = 50
    ) -> List[Any]:
        """
        Execute coroutines with limited concurrency.

        Useful for rate-limiting bulk operations.

        Args:
            coros: List of coroutines to execute.
            max_concurrent: Maximum concurrent executions.

        Returns:
            List of results.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited(coro: Any) -> Any:
            async with semaphore:
                return await coro

        return await asyncio.gather(*[limited(c) for c in coros])

    def get_version(self) -> str:
        """Get library version."""
        from . import __version__
        return __version__

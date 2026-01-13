"""
Helper utilities for the Collibra Connector.

This module provides utility classes and functions for:
- Pagination handling
- Batch operations
- Data transformations
- Caching
"""
from __future__ import annotations

import time
import functools
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
    TYPE_CHECKING,
)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock

if TYPE_CHECKING:
    from .connector import CollibraConnector


T = TypeVar('T')


@dataclass
class PaginatedResponse:
    """
    Represents a paginated API response.

    Attributes:
        results: List of items in the current page.
        total: Total number of items available.
        offset: Current offset in the result set.
        limit: Number of items per page.
        next_cursor: Cursor for the next page (if using cursor pagination).
    """
    results: List[Dict[str, Any]]
    total: int
    offset: int = 0
    limit: int = 0
    next_cursor: Optional[str] = None

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> "PaginatedResponse":
        """Create a PaginatedResponse from an API response dict."""
        return cls(
            results=response.get("results", []),
            total=response.get("total", 0),
            offset=response.get("offset", 0),
            limit=response.get("limit", 0),
            next_cursor=response.get("nextCursor"),
        )

    def has_more(self) -> bool:
        """Check if there are more pages available."""
        if self.next_cursor:
            return True
        return self.offset + len(self.results) < self.total

    def __len__(self) -> int:
        """Return the number of results in this page."""
        return len(self.results)

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over results in this page."""
        return iter(self.results)


class Paginator:
    """
    Helper class for iterating over paginated API results.

    Provides both page-by-page and item-by-item iteration over
    large result sets without loading everything into memory.

    Example:
        >>> paginator = Paginator(connector.asset.find_assets, limit=100)
        >>> for asset in paginator.items():
        ...     print(asset['name'])

        >>> # Or iterate by pages
        >>> for page in paginator.pages():
        ...     print(f"Processing {len(page)} items")
    """

    def __init__(
        self,
        fetch_func: Callable[..., Dict[str, Any]],
        limit: int = 100,
        max_items: Optional[int] = None,
        use_cursor: bool = False,
        **kwargs: Any
    ) -> None:
        """
        Initialize the paginator.

        Args:
            fetch_func: The API method to call for fetching results.
            limit: Number of items to fetch per page.
            max_items: Maximum total items to fetch (None for all).
            use_cursor: Whether to use cursor-based pagination.
            **kwargs: Additional arguments to pass to fetch_func.
        """
        self.fetch_func = fetch_func
        self.limit = limit
        self.max_items = max_items
        self.use_cursor = use_cursor
        self.kwargs = kwargs
        self._total_fetched = 0

    def pages(self) -> Generator[PaginatedResponse, None, None]:
        """
        Iterate over pages of results.

        Yields:
            PaginatedResponse objects for each page.
        """
        offset = 0
        cursor: Optional[str] = "" if self.use_cursor else None

        while True:
            # Check if we've reached max_items
            if self.max_items and self._total_fetched >= self.max_items:
                break

            # Calculate limit for this request
            current_limit = self.limit
            if self.max_items:
                remaining = self.max_items - self._total_fetched
                current_limit = min(self.limit, remaining)

            # Build request parameters
            params = {**self.kwargs, "limit": current_limit}

            if self.use_cursor and cursor is not None:
                params["cursor"] = cursor
            else:
                params["offset"] = offset

            # Fetch the page
            response = self.fetch_func(**params)
            page = PaginatedResponse.from_response(response)

            if not page.results:
                break

            self._total_fetched += len(page.results)
            yield page

            # Prepare for next iteration
            if self.use_cursor:
                cursor = page.next_cursor
                if not cursor:
                    break
            else:
                offset += len(page.results)
                if not page.has_more():
                    break

    def items(self) -> Generator[Dict[str, Any], None, None]:
        """
        Iterate over individual items across all pages.

        Yields:
            Individual result dictionaries.
        """
        for page in self.pages():
            yield from page.results

    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect all items into a list.

        Warning: This loads all results into memory. Use items()
        for memory-efficient iteration over large datasets.

        Returns:
            List of all result dictionaries.
        """
        return list(self.items())

    @property
    def total_fetched(self) -> int:
        """Get the total number of items fetched so far."""
        return self._total_fetched


class BatchProcessor:
    """
    Helper class for processing items in batches.

    Useful for bulk operations like creating or updating multiple
    assets, while respecting API rate limits.

    Example:
        >>> processor = BatchProcessor(batch_size=50, delay=0.5)
        >>> results = processor.process(
        ...     items=assets_to_create,
        ...     operation=connector.asset.add_asset,
        ...     item_mapper=lambda a: {'name': a['name'], 'domain_id': a['domain']}
        ... )
    """

    def __init__(
        self,
        batch_size: int = 50,
        delay: float = 0.1,
        on_error: str = "continue"
    ) -> None:
        """
        Initialize the batch processor.

        Args:
            batch_size: Number of items to process per batch.
            delay: Delay in seconds between batches.
            on_error: Error handling strategy: "continue", "stop", or "collect".
        """
        self.batch_size = batch_size
        self.delay = delay
        self.on_error = on_error

    def process(
        self,
        items: List[T],
        operation: Callable[..., Any],
        item_mapper: Optional[Callable[[T], Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> "BatchResult":
        """
        Process items in batches.

        Args:
            items: List of items to process.
            operation: The API operation to call for each item.
            item_mapper: Optional function to transform items into operation kwargs.
            progress_callback: Optional callback(processed, total) for progress updates.

        Returns:
            BatchResult with success/failure information.
        """
        result = BatchResult()
        total = len(items)

        for i, item in enumerate(items):
            try:
                # Transform item if mapper provided
                kwargs = item_mapper(item) if item_mapper else item

                # Execute operation
                response = operation(**kwargs) if isinstance(kwargs, dict) else operation(kwargs)
                result.add_success(item, response)

            except Exception as e:
                result.add_error(item, e)

                if self.on_error == "stop":
                    break

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total)

            # Delay between batches
            if (i + 1) % self.batch_size == 0 and i + 1 < total:
                time.sleep(self.delay)

        return result


@dataclass
class BatchResult:
    """
    Result of a batch processing operation.

    Attributes:
        successes: List of (item, response) tuples for successful operations.
        errors: List of (item, exception) tuples for failed operations.
    """
    successes: List[tuple] = field(default_factory=list)
    errors: List[tuple] = field(default_factory=list)

    def add_success(self, item: Any, response: Any) -> None:
        """Add a successful result."""
        self.successes.append((item, response))

    def add_error(self, item: Any, error: Exception) -> None:
        """Add an error result."""
        self.errors.append((item, error))

    @property
    def success_count(self) -> int:
        """Get the number of successful operations."""
        return len(self.successes)

    @property
    def error_count(self) -> int:
        """Get the number of failed operations."""
        return len(self.errors)

    @property
    def total_count(self) -> int:
        """Get the total number of operations."""
        return self.success_count + self.error_count

    @property
    def success_rate(self) -> float:
        """Get the success rate as a percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100

    def __repr__(self) -> str:
        return f"BatchResult(successes={self.success_count}, errors={self.error_count})"


class CachedMetadata:
    """
    Thread-safe cache for Collibra metadata like UUIDs.

    Caches metadata to avoid repeated API calls for frequently
    accessed data like asset types, statuses, and attributes.

    Example:
        >>> cache = CachedMetadata(connector, ttl=3600)
        >>> asset_type_id = cache.get_asset_type_id("Business Term")
        >>> status_id = cache.get_status_id("Approved")
    """

    def __init__(
        self,
        connector: "CollibraConnector",
        ttl: int = 3600
    ) -> None:
        """
        Initialize the metadata cache.

        Args:
            connector: The CollibraConnector instance.
            ttl: Time-to-live in seconds for cached data.
        """
        self.connector = connector
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = Lock()

    def _is_expired(self, key: str) -> bool:
        """Check if a cache entry has expired."""
        if key not in self._timestamps:
            return True
        return datetime.now() - self._timestamps[key] > timedelta(seconds=self.ttl)

    def _refresh_if_needed(self, category: str) -> None:
        """Refresh cache for a category if expired."""
        with self._lock:
            if self._is_expired(category):
                self._refresh_category(category)

    def _refresh_category(self, category: str) -> None:
        """Refresh a specific category of metadata."""
        try:
            if category == "asset_types":
                data = self._fetch_all_pages(
                    self.connector.metadata.get_asset_types
                    if hasattr(self.connector.metadata, 'get_asset_types')
                    else lambda **kw: self._get_via_base_api("/assetTypes", **kw)
                )
                self._cache["asset_types"] = {item["name"]: item["id"] for item in data}

            elif category == "statuses":
                data = self._fetch_all_pages(
                    lambda **kw: self._get_via_base_api("/statuses", **kw)
                )
                self._cache["statuses"] = {item["name"]: item["id"] for item in data}

            elif category == "attribute_types":
                data = self._fetch_all_pages(
                    lambda **kw: self._get_via_base_api("/attributeTypes", **kw)
                )
                self._cache["attribute_types"] = {item["name"]: item["id"] for item in data}

            elif category == "domain_types":
                data = self._fetch_all_pages(
                    lambda **kw: self._get_via_base_api("/domainTypes", **kw)
                )
                self._cache["domain_types"] = {item["name"]: item["id"] for item in data}

            elif category == "relation_types":
                data = self._fetch_all_pages(
                    lambda **kw: self._get_via_base_api("/relationTypes", **kw)
                )
                self._cache["relation_types"] = {
                    f"{item['sourceType']['name']}_{item['targetType']['name']}": item["id"]
                    for item in data
                }

            elif category == "roles":
                data = self._fetch_all_pages(
                    lambda **kw: self._get_via_base_api("/roles", **kw)
                )
                self._cache["roles"] = {item["name"]: item["id"] for item in data}

            self._timestamps[category] = datetime.now()

        except Exception:
            # On error, set empty cache to avoid repeated failures
            self._cache[category] = {}
            self._timestamps[category] = datetime.now()

    def _get_via_base_api(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a request via the base API."""
        import requests
        url = f"{self.connector.api}{endpoint}"
        response = requests.get(
            url,
            auth=self.connector.auth,
            params=kwargs,
            timeout=self.connector.timeout
        )
        response.raise_for_status()
        return response.json()

    def _fetch_all_pages(self, fetch_func: Callable[..., Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch all pages of a paginated endpoint."""
        all_results = []
        offset = 0
        limit = 1000

        while True:
            response = fetch_func(offset=offset, limit=limit)
            results = response.get("results", [])
            all_results.extend(results)

            if len(results) < limit:
                break
            offset += limit

        return all_results

    def get_asset_type_id(self, name: str) -> Optional[str]:
        """Get asset type UUID by name."""
        self._refresh_if_needed("asset_types")
        return self._cache.get("asset_types", {}).get(name)

    def get_status_id(self, name: str) -> Optional[str]:
        """Get status UUID by name."""
        self._refresh_if_needed("statuses")
        return self._cache.get("statuses", {}).get(name)

    def get_attribute_type_id(self, name: str) -> Optional[str]:
        """Get attribute type UUID by name."""
        self._refresh_if_needed("attribute_types")
        return self._cache.get("attribute_types", {}).get(name)

    def get_domain_type_id(self, name: str) -> Optional[str]:
        """Get domain type UUID by name."""
        self._refresh_if_needed("domain_types")
        return self._cache.get("domain_types", {}).get(name)

    def get_role_id(self, name: str) -> Optional[str]:
        """Get role UUID by name."""
        self._refresh_if_needed("roles")
        return self._cache.get("roles", {}).get(name)

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def refresh_all(self) -> None:
        """Force refresh of all cached data."""
        categories = ["asset_types", "statuses", "attribute_types",
                      "domain_types", "relation_types", "roles"]
        for category in categories:
            self._refresh_category(category)


def timed_cache(ttl_seconds: int = 300) -> Callable:
    """
    Decorator for caching function results with TTL.

    Args:
        ttl_seconds: Time-to-live in seconds for cached results.

    Example:
        >>> @timed_cache(ttl_seconds=60)
        ... def expensive_operation():
        ...     return fetch_data()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: Dict[str, tuple] = {}
        lock = Lock()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key from args
            key = str((args, sorted(kwargs.items())))

            with lock:
                if key in cache:
                    result, timestamp = cache[key]
                    if datetime.now() - timestamp < timedelta(seconds=ttl_seconds):
                        return result

                # Call function and cache result
                result = func(*args, **kwargs)
                cache[key] = (result, datetime.now())
                return result

        # Add method to clear cache
        def clear_cache() -> None:
            with lock:
                cache.clear()

        wrapper.clear_cache = clear_cache  # type: ignore
        return wrapper

    return decorator


class DataFrameExporter:
    """
    Utility class for exporting Collibra data to pandas DataFrames.

    Provides methods for converting API responses and asset profiles
    to pandas DataFrames for analysis and export.

    Note: Requires pandas to be installed (`pip install pandas`).

    Example:
        >>> from collibra_connector import CollibraConnector, DataFrameExporter
        >>> connector = CollibraConnector(...)
        >>> exporter = DataFrameExporter(connector)
        >>> df = exporter.assets_to_dataframe(domain_id="domain-uuid")
        >>> df.to_csv("assets.csv")
    """

    def __init__(self, connector: "CollibraConnector") -> None:
        """
        Initialize the DataFrame exporter.

        Args:
            connector: The CollibraConnector instance.
        """
        self.connector = connector
        self._pandas = None

    def _get_pandas(self) -> Any:
        """Lazy load pandas to avoid import errors if not installed."""
        if self._pandas is None:
            try:
                import pandas as pd
                self._pandas = pd
            except ImportError:
                raise ImportError(
                    "pandas is required for DataFrame export. "
                    "Install it with: pip install pandas"
                )
        return self._pandas

    def assets_to_dataframe(
        self,
        domain_id: Optional[str] = None,
        community_id: Optional[str] = None,
        asset_type_ids: Optional[List[str]] = None,
        limit: int = 1000,
        include_attributes: bool = True,
        include_relations: bool = False
    ) -> Any:
        """
        Export assets to a pandas DataFrame.

        Args:
            domain_id: Filter by domain ID.
            community_id: Filter by community ID.
            asset_type_ids: Filter by asset type IDs.
            limit: Maximum number of assets to fetch.
            include_attributes: Include asset attributes as columns.
            include_relations: Include relation summaries (slower).

        Returns:
            pandas DataFrame with asset data.

        Example:
            >>> df = exporter.assets_to_dataframe(domain_id="uuid", limit=500)
            >>> print(df.columns)
            >>> df.to_excel("assets.xlsx")
        """
        pd = self._get_pandas()

        # Fetch assets
        assets_result = self.connector.asset.find_assets(
            domain_id=domain_id,
            community_id=community_id,
            asset_type_ids=asset_type_ids,
            limit=limit
        )

        records = []
        for asset in assets_result.get("results", []):
            record = {
                "id": asset.get("id"),
                "name": asset.get("name"),
                "display_name": asset.get("displayName"),
                "type": asset.get("type", {}).get("name"),
                "status": asset.get("status", {}).get("name"),
                "domain": asset.get("domain", {}).get("name"),
                "created_on": asset.get("createdOn"),
                "last_modified_on": asset.get("lastModifiedOn"),
            }

            # Add attributes
            if include_attributes:
                try:
                    attrs = self.connector.attribute.get_attributes_as_dict(asset["id"])
                    for attr_name, attr_value in attrs.items():
                        col_name = f"attr_{attr_name.lower().replace(' ', '_')}"
                        # Clean HTML
                        if isinstance(attr_value, str) and '<' in attr_value:
                            import re
                            attr_value = re.sub(r'<[^>]+>', '', attr_value)
                        record[col_name] = attr_value
                except Exception:
                    pass

            # Add relations summary
            if include_relations:
                try:
                    relations = self.connector.relation.get_asset_relations(
                        asset["id"],
                        include_type_details=True
                    )
                    record["relations_outgoing"] = relations.get("outgoing_count", 0)
                    record["relations_incoming"] = relations.get("incoming_count", 0)
                except Exception:
                    pass

            records.append(record)

        return pd.DataFrame(records)

    def profiles_to_dataframe(
        self,
        asset_ids: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Any:
        """
        Export multiple asset profiles to a pandas DataFrame.

        Uses get_full_profile_flat() to get comprehensive data for each asset.

        Args:
            asset_ids: List of asset UUIDs to export.
            progress_callback: Optional callback(current, total) for progress updates.

        Returns:
            pandas DataFrame with flattened profile data.

        Example:
            >>> asset_ids = ["uuid1", "uuid2", "uuid3"]
            >>> df = exporter.profiles_to_dataframe(asset_ids)
            >>> df.to_csv("profiles.csv")
        """
        pd = self._get_pandas()

        records = []
        total = len(asset_ids)

        for i, asset_id in enumerate(asset_ids):
            try:
                flat_profile = self.connector.asset.get_full_profile_flat(asset_id)
                records.append(flat_profile)
            except Exception as e:
                # Include partial record with error
                records.append({
                    "id": asset_id,
                    "error": str(e)
                })

            if progress_callback:
                progress_callback(i + 1, total)

        return pd.DataFrame(records)

    def communities_to_dataframe(self, limit: int = 1000) -> Any:
        """
        Export communities to a pandas DataFrame.

        Args:
            limit: Maximum number of communities to fetch.

        Returns:
            pandas DataFrame with community data.
        """
        pd = self._get_pandas()

        result = self.connector.community.find_communities(limit=limit)

        records = []
        for comm in result.get("results", []):
            records.append({
                "id": comm.get("id"),
                "name": comm.get("name"),
                "description": comm.get("description"),
                "parent_id": comm.get("parent", {}).get("id") if comm.get("parent") else None,
                "parent_name": comm.get("parent", {}).get("name") if comm.get("parent") else None,
                "created_on": comm.get("createdOn"),
            })

        return pd.DataFrame(records)

    def domains_to_dataframe(
        self,
        community_id: Optional[str] = None,
        limit: int = 1000
    ) -> Any:
        """
        Export domains to a pandas DataFrame.

        Args:
            community_id: Filter by community ID.
            limit: Maximum number of domains to fetch.

        Returns:
            pandas DataFrame with domain data.
        """
        pd = self._get_pandas()

        result = self.connector.domain.find_domains(
            community_id=community_id,
            limit=limit
        )

        records = []
        for domain in result.get("results", []):
            records.append({
                "id": domain.get("id"),
                "name": domain.get("name"),
                "description": domain.get("description"),
                "type": domain.get("type", {}).get("name"),
                "community_id": domain.get("community", {}).get("id"),
                "community_name": domain.get("community", {}).get("name"),
                "created_on": domain.get("createdOn"),
            })

        return pd.DataFrame(records)


class DataTransformer:
    """
    Utility class for transforming Collibra data structures.

    Provides methods for flattening nested responses, converting
    between formats, and extracting specific fields.
    """

    @staticmethod
    def flatten_asset(asset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten a nested asset response into a flat dictionary.

        Args:
            asset: The asset dictionary from the API.

        Returns:
            Flattened dictionary with dot-notation keys.
        """
        flat = {}

        def _flatten(obj: Any, prefix: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        _flatten(value, new_key)
                    else:
                        flat[new_key] = value
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    _flatten(item, f"{prefix}[{i}]")
            else:
                flat[prefix] = obj

        _flatten(asset)
        return flat

    @staticmethod
    def extract_ids(items: List[Dict[str, Any]], key: str = "id") -> List[str]:
        """
        Extract a specific field from a list of dictionaries.

        Args:
            items: List of dictionaries.
            key: The key to extract.

        Returns:
            List of extracted values.
        """
        return [item.get(key) for item in items if item.get(key)]

    @staticmethod
    def group_by(items: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group items by a specific key value.

        Args:
            items: List of dictionaries.
            key: The key to group by.

        Returns:
            Dictionary mapping key values to lists of items.
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            value = item.get(key, "unknown")
            if value not in grouped:
                grouped[value] = []
            grouped[value].append(item)
        return grouped

    @staticmethod
    def to_name_id_map(items: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Convert a list of items to a name->id mapping.

        Args:
            items: List of dictionaries with 'name' and 'id' keys.

        Returns:
            Dictionary mapping names to IDs.
        """
        return {item["name"]: item["id"] for item in items if "name" in item and "id" in item}

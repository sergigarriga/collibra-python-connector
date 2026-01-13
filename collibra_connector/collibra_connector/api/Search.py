from typing import Any, Dict, List, Optional
from .Base import BaseAPI
from ..models import parse_search_results


class Search(BaseAPI):
    """
    Search API implementation.
    Wraps the /search endpoint of Collibra DGC.
    """

    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api + "/search"

    def find(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        filter_options: Optional[Dict[str, Any]] = None,
        sort_options: Optional[Dict[str, Any]] = None,
        highlight_options: Optional[Dict[str, Any]] = None,
        search_fields: Optional[List[str]] = None,
    ):
        """
        Perform a search query.

        Args:
            query: The search query string (can use wildcards like *).
            limit: Max number of results.
            offset: Offset for pagination.
            filter_options: Dictionary of filters (e.g., {'category': 'ASSET', 'typeIds': [...]}).
            sort_options: Dictionary of sort options (e.g., {'field': 'name', 'order': 'ASC'}).
            highlight_options: Dictionary of highlight options.
            search_fields: List of fields to search in.

        Returns:
            Search results model.
        """
        data = {
            "keywords": query,
            "limit": limit,
            "offset": offset,
        }

        if filter_options:
            data.update(filter_options)
        
        if sort_options:
            data["sort"] = [sort_options]  # API expects a list of sorts
        
        if highlight_options:
            data["highlights"] = [highlight_options]
            
        if search_fields:
            data["searchFields"] = search_fields

        # Default to ASSET category if not specified, usually what users want
        # But maybe better to leave it open. The API defaults to all.
        
        response = self._post(url=self.__base_api, data=data)
        return parse_search_results(self._handle_response(response))

    def search(self, query: str, limit: int = 10, offset: int = 0, **kwargs):
        """
        Alias for find() to match common naming patterns.
        """
        return self.find(query=query, limit=limit, offset=offset, **kwargs)

    def find_assets(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        type_ids: Optional[List[str]] = None,
        domain_ids: Optional[List[str]] = None,
        community_ids: Optional[List[str]] = None,
        status_ids: Optional[List[str]] = None,
    ):
        """
        Helper specifically for searching assets.
        
        Args:
            query: Search text.
            limit: Max results.
            offset: Pagination offset.
            type_ids: Filter by asset type IDs.
            domain_ids: Filter by domain IDs.
            community_ids: Filter by community IDs.
            status_ids: Filter by status IDs.
            
        Returns:
            Search results.
        """
        filters = {
            "category": "ASSET"
        }
        
        if type_ids:
            filters["typeIds"] = type_ids
        if domain_ids:
            filters["domainIds"] = domain_ids
        if community_ids:
            filters["communityIds"] = community_ids
        if status_ids:
            filters["statusIds"] = status_ids
            
        return self.find(query=query, limit=limit, offset=offset, filter_options=filters)

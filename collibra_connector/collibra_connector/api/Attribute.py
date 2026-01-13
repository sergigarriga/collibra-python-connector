"""
Attribute API module for Collibra Connector.

Provides methods for working with asset attributes.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .Base import BaseAPI
from ..models import parse_attribute, parse_attributes

if TYPE_CHECKING:
    pass


class Attribute(BaseAPI):
    """API class for attribute operations."""

    def __init__(self, connector: Any) -> None:
        """Initialize the Attribute API."""
        super().__init__(connector)
        self.__base_api = connector.api + "/attributes"

    def find_attributes(
        self,
        asset_id: str,
        type_ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """
        Find attributes for an asset.

        Args:
            asset_id: The UUID of the asset.
            type_ids: Optional list of attribute type IDs to filter by.
            limit: Maximum number of results.
            offset: Offset for pagination.

        Returns:
            Paginated list of attributes.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        params: Dict[str, Any] = {
            "assetId": asset_id,
            "limit": limit,
            "offset": offset
        }

        if type_ids:
            params["typeIds"] = type_ids

        response = self._get(url=self.__base_api, params=params)
        return parse_attributes(self._handle_response(response))

    def get_attributes(self, *args, **kwargs):
        """Alias for find_attributes."""
        return self.find_attributes(*args, **kwargs)

    def get_attribute(self, attribute_id: str):
        """
        Get a specific attribute by ID.

        Args:
            attribute_id: The UUID of the attribute.

        Returns:
            Attribute details.
        """
        if not attribute_id:
            raise ValueError("attribute_id is required")

        try:
            uuid.UUID(attribute_id)
        except ValueError as exc:
            raise ValueError("attribute_id must be a valid UUID") from exc

        response = self._get(url=f"{self.__base_api}/{attribute_id}")
        return parse_attribute(self._handle_response(response))

    def add_attribute(
        self,
        asset_id: str,
        type_id: str,
        value: Any
    ):
        """
        Add an attribute to an asset.

        Args:
            asset_id: The UUID of the asset.
            type_id: The UUID of the attribute type.
            value: The value of the attribute.

        Returns:
            Created attribute details.
        """
        if not asset_id or not type_id:
            raise ValueError("asset_id and type_id are required")

        for param_name, param_value in [("asset_id", asset_id), ("type_id", type_id)]:
            try:
                uuid.UUID(param_value)
            except ValueError as exc:
                raise ValueError(f"{param_name} must be a valid UUID") from exc

        data = {
            "assetId": asset_id,
            "typeId": type_id,
            "value": value
        }

        response = self._post(url=self.__base_api, data=data)
        return parse_attribute(self._handle_response(response))

    def change_attribute(
        self,
        attribute_id: str,
        value: Any
    ):
        """
        Update an attribute value.

        Args:
            attribute_id: The UUID of the attribute.
            value: The new value.

        Returns:
            Updated attribute details.
        """
        if not attribute_id:
            raise ValueError("attribute_id is required")

        try:
            uuid.UUID(attribute_id)
        except ValueError as exc:
            raise ValueError("attribute_id must be a valid UUID") from exc

        data = {
            "id": attribute_id,
            "value": value
        }

        response = self._patch(url=f"{self.__base_api}/{attribute_id}", data=data)
        return parse_attribute(self._handle_response(response))

    def remove_attribute(self, attribute_id: str) -> Dict[str, Any]:
        """
        Remove an attribute.

        Args:
            attribute_id: The UUID of the attribute to remove.

        Returns:
            Response from the removal operation.
        """
        if not attribute_id:
            raise ValueError("attribute_id is required")

        try:
            uuid.UUID(attribute_id)
        except ValueError as exc:
            raise ValueError("attribute_id must be a valid UUID") from exc

        response = self._delete(url=f"{self.__base_api}/{attribute_id}")
        return self._handle_response(response)

    def get_attributes_as_dict(self, asset_id: str) -> Dict[str, Any]:
        """
        Get all attributes for an asset as a simple dictionary.

        Convenience method that returns attribute values keyed by attribute type name.

        Args:
            asset_id: The UUID of the asset.

        Returns:
            Dictionary mapping attribute type names to values.

        Example:
            >>> attrs = connector.attribute.get_attributes_as_dict("asset-uuid")
            >>> print(attrs['Description'])
            >>> print(attrs['Personal Data Classification'])
        """
        result = self.get_attributes(asset_id, limit=500)
        attrs_dict: Dict[str, Any] = {}

        for attr in result:
            type_name = attr.type.name or "Unknown"
            value = attr.value
            attrs_dict[type_name] = value

        return attrs_dict

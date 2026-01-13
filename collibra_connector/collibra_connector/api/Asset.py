import uuid
from .Base import BaseAPI
from ..models import parse_asset, parse_assets


class Asset(BaseAPI):
    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api + "/assets"

    def _get(self, url: str = None, params: dict = None, headers: dict = None):
        """
        Makes a GET request to the asset API.
        :param url: The URL to send the GET request to.
        :param params: Optional parameters to include in the GET request.
        :param headers: Optional headers to include in the GET request.
        :return: The response from the GET request.
        """
        return super()._get(self.__base_api if not url else url, params, headers)

    def get_asset(self, asset_id):
        """
        Retrieves an asset by its ID.
        :param asset_id: The ID of the asset to retrieve.
        :return: AssetModel object.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")
        
        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        response = self._get(url=f"{self.__base_api}/{asset_id}")
        return parse_asset(self._handle_response(response))

    def add_asset(
        self,
        name: str,
        domain_id: str,
        display_name: str = None,
        type_id: str = None,
        _id: str = None,
        status_id: str = None,
        excluded_from_auto_hyperlinking: bool = False,
        type_public_id: str = None,
    ):
        """
        Adds a new asset.
        :param name: The name of the asset.
        :param domain_id: The ID of the domain to which the asset belongs.
        :param display_name: Optional display name for the asset.
        :param type_id: Optional type ID for the asset.
        :param id: Optional ID for the asset.
        :param status_id: Optional status ID for the asset.
        :param excluded_from_auto_hyperlinking: Whether the asset is excluded from auto hyperlinking.
        :param type_public_id: Optional public ID for the asset type.
        :return: AssetModel of the created asset.
        """
        # Parameter type validation
        if not name or not domain_id:
            raise ValueError("Name and domain_id are required parameters.")
        if not isinstance(excluded_from_auto_hyperlinking, bool):
            raise ValueError("excluded_from_auto_hyperlinking must be a boolean value.")
        if type_id and not isinstance(type_id, str):
            raise ValueError("type_id must be a string if provided.")
        if _id and not isinstance(_id, str):
            raise ValueError("_id must be a string if provided.")
        if status_id and not isinstance(status_id, str):
            raise ValueError("status_id must be a string if provided.")
        if type_public_id and not isinstance(type_public_id, str):
            raise ValueError("type_public_id must be a string if provided.")

        # Check Ids are UUIDS
        if _id and self._uuid_validation(_id) is False:
            raise ValueError("id must be a valid UUID.")
        if domain_id and self._uuid_validation(domain_id) is False:
            raise ValueError("domain_id must be a valid UUID.")
        if type_id and self._uuid_validation(type_id) is False:
            raise ValueError("type_id must be a valid UUID.")
        if status_id and self._uuid_validation(status_id) is False:
            raise ValueError("status_id must be a valid UUID.")

        data = {
            "name": name,
            "domainId": domain_id,
            "displayName": display_name,
            "typeId": type_id,
            "id": _id,
            "statusId": status_id,
            "excludedFromAutoHyperlinking": excluded_from_auto_hyperlinking,
            "typePublicId": type_public_id
        }
        response = self._post(url=self.__base_api, data=data)
        return parse_asset(self._handle_response(response))

    def change_asset(
        self,
        asset_id: str,
        name: str = None,
        display_name: str = None,
        type_id: str = None,
        status_id: str = None,
        domain_id: str = None,
        excluded_from_auto_hyperlinking: bool = None,
        type_public_id: str = None
    ):
        """
        Update asset properties.
        :param asset_id: The ID of the asset to update.
        :param name: Optional new name for the asset.
        :param display_name: Optional new display name.
        :param type_id: Optional new type ID.
        :param status_id: Optional new status ID.
        :param domain_id: Optional new domain ID.
        :param excluded_from_auto_hyperlinking: Optional auto-hyperlinking setting.
        :param type_public_id: Optional new type public ID.
        :return: AssetModel of the updated asset.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        # Validate UUID fields if provided
        uuid_fields = [
            ("type_id", type_id),
            ("status_id", status_id),
            ("domain_id", domain_id)
        ]

        for field_name, field_value in uuid_fields:
            if field_value:
                if not isinstance(field_value, str):
                    raise ValueError(f"{field_name} must be a string")
                try:
                    uuid.UUID(field_value)
                except ValueError as exc:
                    raise ValueError(f"{field_name} must be a valid UUID") from exc

        data = {
            "id": asset_id,
            "name": name,
            "displayName": display_name,
            "typeId": type_id,
            "statusId": status_id,
            "domainId": domain_id,
            "excludedFromAutoHyperlinking": excluded_from_auto_hyperlinking,
            "typePublicId": type_public_id,
        }

        response = self._patch(url=f"{self.__base_api}/{asset_id}", data=data)
        return parse_asset(self._handle_response(response))

    def update_asset_attribute(self, asset_id: str, attribute_id: str, value):
        """
        Update an asset attribute.
        :param asset_id: The ID of the asset.
        :param attribute_id: The ID of the attribute type.
        :param value: The new value for the attribute.
        :return: The response from updating the attribute.
        """
        if not all([asset_id, attribute_id]):
            raise ValueError("asset_id and attribute_id are required")

        for param_name, param_value in [("asset_id", asset_id), ("attribute_id", attribute_id)]:
            if not isinstance(param_value, str):
                raise ValueError(f"{param_name} must be a string")
            try:
                uuid.UUID(param_value)
            except ValueError as exc:
                raise ValueError(f"{param_name} must be a valid UUID") from exc

        data = {
            "values": [value],
            "typeId": attribute_id
        }

        response = self._put(url=f"{self.__base_api}/{asset_id}/attributes", data=data)
        return self._handle_response(response)

    def set_asset_attributes(self, asset_id: str, type_id: str = None, type_public_id: str = None, values: list = None):
        """
        Set asset attributes. Replaces all attributes of the asset with the given ID
        (of given attribute type) with the attributes from the request.
        :param asset_id: The ID of the asset.
        :param type_id: The ID of the attribute type for the new attribute.
        :param type_public_id: The public ID of the attribute type for the new attribute.
        :param values: The values for the new attribute (list of objects).
        :return: The response from setting the attributes.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        if not values:
            raise ValueError("values is required")
        if not isinstance(values, list):
            raise ValueError("values must be a list")

        # Validate that either type_id or type_public_id is provided
        if not type_id and not type_public_id:
            raise ValueError("Either type_id or type_public_id must be provided")

        # Validate type_id if provided
        if type_id:
            if not isinstance(type_id, str):
                raise ValueError("type_id must be a string")
            try:
                uuid.UUID(type_id)
            except ValueError as exc:
                raise ValueError("type_id must be a valid UUID") from exc

        # Validate type_public_id if provided
        if type_public_id and not isinstance(type_public_id, str):
            raise ValueError("type_public_id must be a string")

        data = {
            "values": values
        }

        # Add type_id or type_public_id to the data
        if type_id:
            data["typeId"] = type_id
        if type_public_id:
            data["typePublicId"] = type_public_id

        response = self._put(url=f"{self.__base_api}/{asset_id}/attributes", data=data)
        return self._handle_response(response)

    def remove_asset(self, asset_id: str):
        """
        Remove an asset identified by given ID.
        :param asset_id: The ID of the asset to remove.
        :return: The response from removing the asset.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        response = self._delete(url=f"{self.__base_api}/{asset_id}")
        return self._handle_response(response)

    def set_asset_relations(self, asset_id: str, related_asset_ids: list, relation_direction: str,
                            type_id: str = None, type_public_id: str = None):
        """
        Set relations for the asset with the given ID. All relations described by this request
        will replace the existing ones (identified with asset as one end, relation type and direction).
        :param asset_id: The ID of the asset.
        :param related_asset_ids: The IDs of the related assets (list of UUIDs).
        :param relation_direction: The relation direction ('TO_TARGET' or 'TO_SOURCE').
        :param type_id: The ID of the relation type for the relations to be set.
        :param type_public_id: The public ID of the relation type for the relations to be set.
        :return: The response from setting the relations.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        if not related_asset_ids:
            raise ValueError("related_asset_ids is required")
        if not isinstance(related_asset_ids, list):
            raise ValueError("related_asset_ids must be a list")

        # Validate all related asset IDs are valid UUIDs
        for i, related_id in enumerate(related_asset_ids):
            if not isinstance(related_id, str):
                raise ValueError(f"related_asset_ids[{i}] must be a string")
            try:
                uuid.UUID(related_id)
            except ValueError as exc:
                raise ValueError(f"related_asset_ids[{i}] must be a valid UUID") from exc

        if not relation_direction:
            raise ValueError("relation_direction is required")
        if relation_direction not in ["TO_TARGET", "TO_SOURCE"]:
            raise ValueError("relation_direction must be either 'TO_TARGET' or 'TO_SOURCE'")

        # Validate that either type_id or type_public_id is provided
        if not type_id and not type_public_id:
            raise ValueError("Either type_id or type_public_id must be provided")

        # Validate type_id if provided
        if type_id:
            if not isinstance(type_id, str):
                raise ValueError("type_id must be a string")
            try:
                uuid.UUID(type_id)
            except ValueError as exc:
                raise ValueError("type_id must be a valid UUID") from exc

        # Validate type_public_id if provided
        if type_public_id and not isinstance(type_public_id, str):
            raise ValueError("type_public_id must be a string")

        data = {
            "relatedAssetIds": related_asset_ids,
            "relationDirection": relation_direction
        }

        # Add type_id or type_public_id to the data
        if type_id:
            data["typeId"] = type_id
        if type_public_id:
            data["typePublicId"] = type_public_id

        response = self._put(url=f"{self.__base_api}/{asset_id}/relations", data=data)
        return self._handle_response(response)

    def set_asset_responsibilities(self, asset_id: str, role_id: str, owner_ids: list):
        """
        Set responsibilities for the asset with the given ID.
        :param asset_id: The ID of the asset.
        :param role_id: The ID of the role for the responsibilities to be set.
        :param owner_ids: The IDs of the owners (list of UUIDs). An owner is either user or group.
        :return: The response from setting the responsibilities.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        if not role_id:
            raise ValueError("role_id is required")
        if not isinstance(role_id, str):
            raise ValueError("role_id must be a string")

        try:
            uuid.UUID(role_id)
        except ValueError as exc:
            raise ValueError("role_id must be a valid UUID") from exc

        if not owner_ids:
            raise ValueError("owner_ids is required")
        if not isinstance(owner_ids, list):
            raise ValueError("owner_ids must be a list")

        # Validate all owner IDs are valid UUIDs
        for i, owner_id in enumerate(owner_ids):
            if not isinstance(owner_id, str):
                raise ValueError(f"owner_ids[{i}] must be a string")
            try:
                uuid.UUID(owner_id)
            except ValueError as exc:
                raise ValueError(f"owner_ids[{i}] must be a valid UUID") from exc

        data = {
            "roleId": role_id,
            "ownerIds": owner_ids
        }

        response = self._put(url=f"{self.__base_api}/{asset_id}/responsibilities", data=data)
        return self._handle_response(response)

    def find_assets(
        self,
        community_id: str = None,
        asset_type_ids: list = None,
        domain_id: str = None,
        name: str = None,
        name_match_mode: str = "ANYWHERE",
        limit: int = 1000,
        offset: int = 0
    ):
        """
        Find assets with optional filters.
        :param community_id: Optional community ID to filter by.
        :param asset_type_ids: Optional list of asset type IDs to filter by.
        :param domain_id: Optional domain ID to filter by.
        :param name: Optional name to filter by.
        :param name_match_mode: Mode for name matching (ANYWHERE, START, END, EXACT).
        :param limit: Maximum number of results per page.
        :param offset: First result to retrieve.
        :return: AssetList matching the criteria.
        """
        params = {"limit": limit, "offset": offset}

        if community_id:
            if not isinstance(community_id, str):
                raise ValueError("community_id must be a string")
            try:
                uuid.UUID(community_id)
            except ValueError as exc:
                raise ValueError("community_id must be a valid UUID") from exc
            params["communityId"] = community_id

        if asset_type_ids:
            if not isinstance(asset_type_ids, list):
                raise ValueError("asset_type_ids must be a list")
            for type_id in asset_type_ids:
                if not isinstance(type_id, str):
                    raise ValueError("All asset_type_ids must be strings")
                try:
                    uuid.UUID(type_id)
                except ValueError as exc:
                    raise ValueError("All asset_type_ids must be valid UUIDs") from exc
            params["typeIds"] = asset_type_ids

        if domain_id:
            if not isinstance(domain_id, str):
                raise ValueError("domain_id must be a string")
            try:
                uuid.UUID(domain_id)
            except ValueError as exc:
                raise ValueError("domain_id must be a valid UUID") from exc
            params["domainId"] = domain_id

        if name:
            params["name"] = name
            params["nameMatchMode"] = name_match_mode

        response = self._get(params=params)
        return parse_assets(self._handle_response(response))

    def get_asset_activities(self, asset_id: str, limit: int = 50):
        """
        Get activities for a specific asset.
        :param asset_id: The ID of the asset.
        :param limit: Maximum number of activities to retrieve.
        :return: List of activities for the asset.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        params = {
            "contextId": asset_id,
            "resourceTypes": ["Asset"],
            "limit": limit
        }

        response = self._get(url=f"{self.__base_api}/activities", params=params)
        result = self._handle_response(response)
        return result.get("results", [])

    def get_full_profile(
        self,
        asset_id: str,
        include_attributes: bool = True,
        include_relations: bool = True,
        include_responsibilities: bool = True,
        include_comments: bool = False,
        include_activities: bool = False
    ):
        """
        Get a complete profile of an asset including all related information.

        This is a convenience method that fetches all relevant data about an asset
        in a single call, perfect for data cataloging and governance use cases.

        Args:
            asset_id: The UUID of the asset.
            include_attributes: Include asset attributes (default: True).
            include_relations: Include incoming/outgoing relations (default: True).
            include_responsibilities: Include responsibility assignments (default: True).
            include_comments: Include comments on the asset (default: False).
            include_activities: Include activity history (default: False).

        Returns:
            AssetProfileModel containing:
                - asset: AssetModel with basic asset information
                - attributes: Dict of attribute name -> value
                - relations: RelationsGrouped with 'outgoing' and 'incoming' relations
                - responsibilities: List of ResponsibilitySummary objects
                - comments: List of CommentModel objects (if requested)
                - activities: List of activities (if requested)

        Example:
            >>> profile = connector.asset.get_full_profile("asset-uuid")
            >>> print(profile.asset.name)
            >>> print(profile.attributes.get('Description'))
            >>> print(profile.data_steward)
        """
        if not asset_id:
            raise ValueError("asset_id is required")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        # Get the connector reference for accessing other APIs
        connector = self._BaseAPI__connector

        from ..models import (
            AssetProfileModel,
            RelationsGrouped,
            ResponsibilitySummary,
            CommentModel
        )

        asset_data = self.get_asset(asset_id)
        attributes_dict = {}
        relations_data = {"outgoing": {}, "incoming": {}, "outgoing_count": 0, "incoming_count": 0}
        responsibilities_list = []
        comments_list = []
        activities_list = []

        # 2. Get attributes
        if include_attributes:
            try:
                attributes_dict = connector.attribute.get_attributes_as_dict(asset_id)
            except Exception:
                pass  # Attributes are optional

        # 3. Get relations
        if include_relations:
            try:
                relations_data = connector.relation.get_asset_relations(
                    asset_id,
                    include_type_details=True
                )
            except Exception:
                pass  # Relations are optional

        # 4. Get responsibilities
        if include_responsibilities:
            try:
                resp_list = connector.responsibility.find_responsibilities(
                    resource_ids=[asset_id],
                    limit=50
                )
                for resp in resp_list:
                    role_name = resp.role.name or "Unknown"
                    owner_name = resp.owner.name or "Unknown"
                    responsibilities_list.append(ResponsibilitySummary(
                        role=role_name,
                        owner=owner_name,
                        owner_id=resp.owner.id
                    ))
            except Exception:
                pass  # Responsibilities are optional

        # 5. Get comments
        if include_comments:
            try:
                comments_result = connector.comment.get_comments(asset_id)
                for comment_data in comments_result.get('results', []):
                    try:
                        comments_list.append(CommentModel.model_validate(comment_data))
                    except Exception:
                        pass
            except Exception:
                pass  # Comments are optional

        # 6. Get activities
        if include_activities:
            try:
                activities_list = self.get_asset_activities(asset_id)
            except Exception:
                pass  # Activities are optional

        # Create and return AssetProfileModel
        return AssetProfileModel(
            asset=asset_data,
            attributes=attributes_dict,
            relations=RelationsGrouped(**relations_data),
            responsibilities=responsibilities_list,
            comments=comments_list,
            activities=activities_list
        )

    def get_full_profile_flat(self, asset_id: str):
        """
        Get a flattened profile of an asset suitable for export to CSV/DataFrame.

        Returns a dictionary with all values as simple types (strings, numbers, lists).

        Args:
            asset_id: The UUID of the asset.

        Returns:
            Flattened dictionary with all asset information.

        Example:
            >>> flat = connector.asset.get_full_profile_flat("asset-uuid")
            >>> import pandas as pd
            >>> df = pd.DataFrame([flat])
        """
        profile = self.get_full_profile(asset_id)

        flat = {
            # Basic info
            "id": profile.asset.id,
            "name": profile.asset.name,
            "display_name": profile.asset.display_name,
            "type": profile.asset.type_name,
            "type_id": profile.asset.type.id,
            "status": profile.asset.status_name,
            "status_id": profile.asset.status.id,
            "domain": profile.asset.domain_name,
            "domain_id": profile.asset.domain.id,
            "created_on": profile.asset.created_on,
            "last_modified_on": profile.asset.last_modified_on,
        }

        # Add attributes with prefix
        for attr_name, attr_value in profile.attributes.items():
            # Clean HTML from description
            if attr_name == "Description" and isinstance(attr_value, str):
                import re
                attr_value = re.sub(r'<[^>]+>', '', attr_value)
            flat[f"attr_{attr_name.lower().replace(' ', '_')}"] = attr_value

        # Add relation counts
        flat["relations_outgoing_count"] = profile.relations.outgoing_count
        flat["relations_incoming_count"] = profile.relations.incoming_count

        # Add relation summaries
        outgoing_summary = []
        for rel_type, targets in profile.relations.outgoing.items():
            outgoing_summary.append(f"{rel_type}: {len(targets)}")
        flat["relations_outgoing_summary"] = "; ".join(outgoing_summary)

        incoming_summary = []
        for rel_type, sources in profile.relations.incoming.items():
            incoming_summary.append(f"{rel_type}: {len(sources)}")
        flat["relations_incoming_summary"] = "; ".join(incoming_summary)

        # Add responsibilities
        resp_list = [f"{r.role}: {r.owner}" for r in profile.responsibilities]
        flat["responsibilities"] = "; ".join(resp_list)

        return flat

    def add_tags(self, asset_id: str, tags: list):
        """
        Add tags to an asset.
        :param asset_id: The ID of the asset.
        :param tags: List of tags (strings) to add.
        :return: Response from the API.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not tags or not isinstance(tags, list):
            raise ValueError("tags must be a non-empty list of strings")

        url = f"{self.__base_api}/{asset_id}/tags"
        data = {"tagNames": tags}
        
        response = self._post(url=url, data=data)
        return self._handle_response(response)

    def remove_tags(self, asset_id: str, tags: list):
        """
        Remove tags from an asset.
        :param asset_id: The ID of the asset.
        :param tags: List of tags (strings) to remove.
        :return: Response from the API.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not tags or not isinstance(tags, list):
            raise ValueError("tags must be a non-empty list of strings")

        url = f"{self.__base_api}/{asset_id}/tags"
        # DELETE with body is not standard in many libs but Collibra might support it or use a different endpoint?
        # Checking Collibra API: DELETE /assets/{assetId}/tags takes list of tags in body.
        # BaseAPI._delete does not support data.
        # We need to use requests directly or extend BaseAPI.
        
        import requests
        # Access connector auth and timeout
        connector = self._BaseAPI__connector
        
        response = requests.delete(
            url, 
            json=tags, # Pass tags directly as list or {"tags": ...}? API says list of strings usually.
                       # Checking Collibra docs: DELETE /assets/{assetId}/tags body is ["tag1", "tag2"]
            auth=connector.auth,
            timeout=connector.timeout,
            headers={"Content-Type": "application/json"}
        )
        
        return self._handle_response(response)

    def add_attachment(self, asset_id: str, file_path: str):
        """
        Upload an attachment to an asset.
        :param asset_id: The ID of the asset.
        :param file_path: Path to the file to upload.
        :return: Response from the API.
        """
        import os
        import requests
        
        if not asset_id:
            raise ValueError("asset_id is required")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        url = f"{self._BaseAPI__connector.api}/attachments"
        filename = os.path.basename(file_path)
        
        # Open file in binary mode and ensure it's closed
        with open(file_path, 'rb') as f:
            files = {
                'file': (filename, f, 'application/octet-stream'),
                'resourceId': (None, str(asset_id)),
                'resourceType': (None, 'Asset')
            }
            
            response = requests.post(
                url,
                files=files,
                auth=self._BaseAPI__connector.auth,
                timeout=self._BaseAPI__connector.timeout
            )
        
        return self._handle_response(response)

    def get_attachments(self, asset_id: str):
        """
        Get attachments for an asset.
        :param asset_id: The ID of the asset.
        :return: List of attachments.
        """
        url = f"{self._BaseAPI__connector.api}/attachments"
        params = {
            "resourceId": asset_id,
            "resourceType": "Asset"
        }
        
        response = self._get(url=url, params=params)
        return self._handle_response(response).get("results", [])

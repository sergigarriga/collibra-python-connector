import uuid
from .Base import BaseAPI
from ..models import parse_responsibility, parse_responsibilities


class Responsibility(BaseAPI):
    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api + "/responsibilities"

    def add_responsibility(
        self,
        role_id: str,
        owner_id: str,
        resource_id: str = None,
        resource_type: str = None,
        resource_discriminator: str = None
    ):
        """
        Add a new responsibility. Assigns given user to resource with given role.
        :param role_id: The ID of the role that should be assigned to user.
        :param owner_id: The ID of the user who the responsibility is created for.
        :param resource_id: The ID of the resource which the responsibility is created for.
            If None, creates global responsibility.
        :param resource_type: The type of the resource (e.g., Asset, Community, Domain, etc.).
        :param resource_discriminator: The discriminator for resource type. Valid values: "Community", "Domain", "Asset"
        :return: The responsibility model.
        """
        # Validate required parameters
        if not role_id or not owner_id:
            raise ValueError("role_id and owner_id are required parameters")

        # Validate UUIDs
        for param_name, param_value in [("role_id", role_id), ("owner_id", owner_id)]:
            if not isinstance(param_value, str):
                raise ValueError(f"{param_name} must be a string")
            try:
                uuid.UUID(param_value)
            except ValueError as exc:
                raise ValueError(f"{param_name} must be a valid UUID") from exc

        # Validate resource_id if provided
        if resource_id is not None:
            if not isinstance(resource_id, str):
                raise ValueError("resource_id must be a string")
            try:
                uuid.UUID(resource_id)
            except ValueError as exc:
                raise ValueError("resource_id must be a valid UUID") from exc

        # Validate resource_type if provided
        valid_resource_types = [
            "View", "Asset", "Community", "Domain", "AssetType", "DomainType", "Status", "User",
            "Classification", "MatchUser", "Group", "Attribute", "StringAttribute", "ScriptAttribute",
            "BooleanAttribute", "DateAttribute", "NumericAttribute", "SingleValueListAttribute",
            "MultiValueListAttribute", "Comment", "Attachment", "Responsibility", "Workflow", "Job",
            "Relation", "RelationType", "ComplexRelation", "ComplexRelationType", "ArticulationRule",
            "Assignment", "ScopeRelation", "Trace", "ValidationRule", "DataQualityRule", "DataQualityMetric",
            "Address", "InstantMessagingAccount", "Email", "PhoneNumber", "Website", "Activity",
            "FormProperty", "WorkflowTask", "ActivityChange", "WorkflowInstance", "Role", "AttributeType",
            "BooleanAttributeType", "DateAttributeType", "DateTimeAttributeType", "MultiValueListAttributeType",
            "NumericAttributeType", "ScriptAttributeType", "SingleValueListAttributeType", "StringAttributeType",
            "ViewSharingRule", "ViewAssignmentRule", "JdbcDriver", "File", "JdbcDriverJdbcIngestionProperties",
            "CsvIngestionProperties", "ExcelIngestionProperties", "ConnectionStringParameter",
            "AssignedCharacteristicType", "Notification", "Tag", "ComplexRelationLegType",
            "ComplexRelationAttributeType", "ComplexRelationLeg", "BaseDataType", "AdvancedDataType",
            "Diagram", "Picture", "DiagramPictureSharingRule", "DiagramPictureAssignmentRule", "Rating",
            "ClassificationPhysicalData", "ConnectorContext"
        ]

        if resource_type is not None and resource_type not in valid_resource_types:
            raise ValueError(
                "resource_type must be one of the valid resource types. See API documentation for full list."
            )

        # Validate resource_discriminator if provided
        valid_discriminators = ["Community", "Domain", "Asset"]
        if resource_discriminator is not None and resource_discriminator not in valid_discriminators:
            raise ValueError(f"resource_discriminator must be one of: {', '.join(valid_discriminators)}")

        # Build request data - only include non-None values
        data = {
            "roleId": role_id,
            "ownerId": owner_id
        }

        if resource_id is not None:
            data["resourceId"] = resource_id
        if resource_type is not None:
            data["resourceType"] = resource_type
        if resource_discriminator is not None:
            data["resourceDiscriminator"] = resource_discriminator

        response = self._post(url=self.__base_api, data=data)
        return parse_responsibility(self._handle_response(response))

    def get_responsibility(self, responsibility_id: str):
        """
        Get details of a specific responsibility.
        :param responsibility_id: The ID of the responsibility.
        :return: Responsibility model.
        """
        if not responsibility_id:
            raise ValueError("responsibility_id is required")
        if not isinstance(responsibility_id, str):
            raise ValueError("responsibility_id must be a string")

        try:
            uuid.UUID(responsibility_id)
        except ValueError as exc:
            raise ValueError("responsibility_id must be a valid UUID") from exc

        response = self._get(url=f"{self.__base_api}/{responsibility_id}")
        return parse_responsibility(self._handle_response(response))

    def delete_responsibility(self, responsibility_id: str):
        """
        Remove the responsibility identified by the given id.
        :param responsibility_id: The unique identifier of the responsibility.
        :return: None
        """
        if not responsibility_id:
            raise ValueError("responsibility_id is required")
        if not isinstance(responsibility_id, str):
            raise ValueError("responsibility_id must be a string")

        try:
            uuid.UUID(responsibility_id)
        except ValueError as exc:
            raise ValueError("responsibility_id must be a valid UUID") from exc

        response = self._delete(url=f"{self.__base_api}/{responsibility_id}")
        self._handle_response(response)

    def find_responsibilities(
        self,
        count_limit: int = -1,
        exclude_empty_groups: bool = None,
        global_only: bool = None,
        include_inherited: bool = True,
        limit: int = 0,
        offset: int = 0,
        owner_ids: list = None,
        resource_ids: list = None,
        role_ids: list = None,
        sort_field: str = "LAST_MODIFIED",
        sort_order: str = "DESC",
        _type: str = None
    ):
        """
        Find responsibilities matching the given search criteria.
        :param count_limit: Limit the number of elements counted. -1 counts everything, 0 skips count.
        :param exclude_empty_groups: Whether responsibilities assigned to empty groups should be excluded.
        :param global_only: Whether only global responsibilities should be searched (deprecated).
        :param include_inherited: Whether inherited responsibilities should be included.
        :param limit: Maximum number of results to retrieve. 0 uses default, max 1000.
        :param offset: First result to retrieve. 0 starts from beginning.
        :param owner_ids: List of owner IDs to filter responsibilities by.
        :param resource_ids: List of resource IDs to filter responsibilities by.
        :param role_ids: List of role IDs to filter responsibilities by.
        :param sort_field: Field to sort results by. Options: CREATED_BY, CREATED_ON, LAST_MODIFIED, NAME
        :param sort_order: Sort order. Options: ASC, DESC
        :param type: Type of responsibilities. Options: ALL, GLOBAL, RESOURCE
        :return: List of responsibilities matching the criteria.
        """
        # Validate sort_field
        valid_sort_fields = ["CREATED_BY", "CREATED_ON", "LAST_MODIFIED", "NAME"]
        if sort_field not in valid_sort_fields:
            raise ValueError(f"sort_field must be one of: {', '.join(valid_sort_fields)}")

        # Validate sort_order
        if sort_order not in ["ASC", "DESC"]:
            raise ValueError("sort_order must be 'ASC' or 'DESC'")

        # Validate limit
        if limit < 0 or limit > 1000:
            raise ValueError("limit must be between 0 and 1000")

        # Validate type if provided
        valid_types = ["ALL", "GLOBAL", "RESOURCE"]
        if _type is not None and _type not in valid_types:
            raise ValueError(f"type must be one of: {', '.join(valid_types)}")

        # Validate that globalOnly and type are mutually exclusive
        if global_only is not None and _type is not None:
            raise ValueError("globalOnly and type parameters are mutually exclusive")

        # Validate owner_ids if provided
        if owner_ids is not None:
            if not isinstance(owner_ids, list):
                raise ValueError("owner_id must be a list")
            for owner_id in owner_ids:
                if not isinstance(owner_id, str):
                    raise ValueError("owner_id must be a string")
                try:
                    uuid.UUID(owner_id)
                except ValueError as exc:
                    raise ValueError("owner_id must be a valid UUID") from exc

        # Validate resource_ids if provided
        if resource_ids is not None:
            if not isinstance(resource_ids, list):
                raise ValueError("resource_ids must be a list")
            for resource_id in resource_ids:
                if not isinstance(resource_id, str):
                    raise ValueError("resource_id must be a string")
                try:
                    uuid.UUID(resource_id)
                except ValueError as exc:
                    raise ValueError("resource_id must be a valid UUID") from exc

        # Validate role_ids if provided
        if role_ids is not None:
            if not isinstance(role_ids, list):
                raise ValueError("role_ids must be a list")
            for role_id in role_ids:
                if not isinstance(role_id, str):
                    raise ValueError("role_id must be a string")
                try:
                    uuid.UUID(role_id)
                except ValueError as exc:
                    raise ValueError("role_id must be a valid UUID") from exc

        # Build parameters - only include non-default values
        params = {}

        if count_limit != -1:
            params["countLimit"] = count_limit
        if exclude_empty_groups is not None:
            params["excludeEmptyGroups"] = exclude_empty_groups
        if global_only is not None:
            params["globalOnly"] = global_only
        if include_inherited is not True:
            params["includeInherited"] = include_inherited
        if limit != 0:
            params["limit"] = limit
        if offset != 0:
            params["offset"] = offset
        if owner_ids is not None:
            params["ownerIds"] = owner_ids
        if resource_ids is not None:
            params["resourceIds"] = resource_ids
        if role_ids is not None:
            params["roleIds"] = role_ids
        if sort_field != "LAST_MODIFIED":
            params["sortField"] = sort_field
        if sort_order != "DESC":
            params["sortOrder"] = sort_order
        if _type is not None:
            params["type"] = _type

        response = self._get(url=self.__base_api, params=params)
        return parse_responsibilities(self._handle_response(response))

    def get_asset_responsibilities(self, asset_id: str, role_ids: list = None):
        """
        Get responsibilities for an asset (convenience method).
        :param asset_id: The ID of the asset.
        :param role_ids: Optional list of role IDs to filter by.
        :return: List of responsibilities.
        """
        if not asset_id:
            raise ValueError("asset_id is required")
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        return self.find_responsibilities(
            resource_ids=[asset_id],
            role_ids=role_ids
        )

    def get_user_responsibilities(self, user_id: str, role_id: str = None):
        """
        Get responsibilities for a user (convenience method).
        :param user_id: The ID of the user.
        :param role_id: Optional role ID to filter by.
        :return: List of responsibilities.
        """
        if not user_id:
            raise ValueError("user_id is required")
        if not isinstance(user_id, str):
            raise ValueError("user_id must be a string")

        try:
            uuid.UUID(user_id)
        except ValueError as exc:
            raise ValueError("user_id must be a valid UUID") from exc

        role_ids = [role_id] if role_id else None
        return self.find_responsibilities(
            owner_ids=[user_id],
            role_ids=role_ids
        )

    def get_global_responsibilities(self, role_ids: list = None):
        """
        Get global responsibilities (convenience method).
        :param role_ids: Optional list of role IDs to filter by.
        :return: List of global responsibilities.
        """
        return self.find_responsibilities(
            _type="GLOBAL",
            role_ids=role_ids
        )

    def get_resource_responsibilities(self, resource_ids: list = None, role_ids: list = None):
        """
        Get resource-specific responsibilities (convenience method).
        :param resource_ids: Optional list of resource IDs to filter by.
        :param role_ids: Optional list of role IDs to filter by.
        :return: List of resource responsibilities.
        """
        return self.find_responsibilities(
            _type="RESOURCE",
            resource_ids=resource_ids,
            role_ids=role_ids
        )

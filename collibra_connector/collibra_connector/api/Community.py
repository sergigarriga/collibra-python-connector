import uuid
from .Base import BaseAPI
from ..models import parse_community, parse_communities


class Community(BaseAPI):
    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api + "/communities"

    def get_community(self, community_id: str):
        """
        Get a community by its ID.
        :param community_id: The ID of the community to retrieve.
        :return: Community details.
        """
        if not community_id:
            raise ValueError("community_id is required")
        if not isinstance(community_id, str):
            raise ValueError("community_id must be a string")

        try:
            uuid.UUID(community_id)
        except ValueError as exc:
            raise ValueError("community_id must be a valid UUID") from exc

        response = self._get(url=f"{self.__base_api}/{community_id}")
        return parse_community(self._handle_response(response))

    def find_communities(
        self,
        sort_field: str = "NAME",
        count_limit: int = -1,
        cursor: str = None,
        exclude_meta: bool = True,
        limit: int = 0,
        name: str = None,
        name_match_mode: str = "ANYWHERE",
        offset: int = 0,
        parent_id: str = None,
        sort_order: str = "ASC"
    ):
        """
        Find communities matching the given search criteria.
        :param sort_field: Field to sort results by. Options: NAME, CREATED_BY, CREATED_ON, LAST_MODIFIED, ID
        :param count_limit: Limit elements counted. -1 counts all, 0 skips count. Ignored with cursor pagination.
        :param cursor: Cursor for pagination. Pass empty string for first page, use nextCursor for subsequent pages.
        :param exclude_meta: Whether to exclude meta communities (not manually created by users).
        :param limit: Maximum results to retrieve. 0 uses default, max 1000.
        :param name: Name of community to search for.
        :param name_match_mode: Name matching mode. Options: START, END, ANYWHERE, EXACT
        :param offset: First result to retrieve (deprecated, use cursor instead).
        :param parent_id: Parent community ID to filter by.
        :param sort_order: Sort order. Options: ASC, DESC
        :return: List of communities matching criteria.
        """
        # Validate sort_field
        valid_sort_fields = ["NAME", "CREATED_BY", "CREATED_ON", "LAST_MODIFIED", "ID"]
        if sort_field not in valid_sort_fields:
            raise ValueError(f"sort_field must be one of: {', '.join(valid_sort_fields)}")

        # Validate name_match_mode
        valid_match_modes = ["START", "END", "ANYWHERE", "EXACT"]
        if name_match_mode not in valid_match_modes:
            raise ValueError(f"name_match_mode must be one of: {', '.join(valid_match_modes)}")

        # Validate sort_order
        if sort_order not in ["ASC", "DESC"]:
            raise ValueError("sort_order must be 'ASC' or 'DESC'")

        # Validate limit
        if limit < 0 or limit > 1000:
            raise ValueError("limit must be between 0 and 1000")

        # Validate parent_id if provided
        if parent_id is not None:
            if not isinstance(parent_id, str):
                raise ValueError("parent_id must be a string")
            try:
                uuid.UUID(parent_id)
            except ValueError as exc:
                raise ValueError("parent_id must be a valid UUID") from exc

        # Validate cursor and offset usage
        if cursor is not None and offset != 0:
            raise ValueError("Cannot use both cursor and offset in the same request")

        # Build parameters - only include non-default values
        params = {}

        if sort_field != "NAME":
            params["sortField"] = sort_field
        if count_limit != -1:
            params["countLimit"] = count_limit
        if cursor is not None:
            params["cursor"] = cursor
        if exclude_meta is not True:
            params["excludeMeta"] = exclude_meta
        if limit != 0:
            params["limit"] = limit
        if name is not None:
            params["name"] = name
        if name_match_mode != "ANYWHERE":
            params["nameMatchMode"] = name_match_mode
        if offset != 0:
            params["offset"] = offset
        if parent_id is not None:
            params["parentId"] = parent_id
        if sort_order != "ASC":
            params["sortOrder"] = sort_order

        response = self._get(url=self.__base_api, params=params)
        return parse_communities(self._handle_response(response))

    def add_community(
        self,
        name: str,
        parent_id: str = None,
        description: str = None,
        community_id: str = None
    ):
        """
        Adds a new community with the given parameters.
        :param name: The name of the new community. Should be unique across all communities
                    (required, 1-255 characters).
        :param parent_id: The ID of the parent for the new community (optional UUID).
        :param description: The description of the new community (optional).
        :param community_id: The ID of the new community. Should be unique within all communities
                           (optional UUID).
        :return: Details of the created community.
        """
        # Validate required parameters
        if not name:
            raise ValueError("name is required")
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        if len(name.strip()) < 1 or len(name) > 255:
            raise ValueError("name must be between 1 and 255 characters")

        # Validate parent_id if provided
        if parent_id is not None:
            if not isinstance(parent_id, str):
                raise ValueError("parent_id must be a string")
            try:
                uuid.UUID(parent_id)
            except ValueError as exc:
                raise ValueError("parent_id must be a valid UUID") from exc

        # Validate description if provided
        if description is not None and not isinstance(description, str):
            raise ValueError("description must be a string")

        # Validate community_id if provided
        if community_id is not None:
            if not isinstance(community_id, str):
                raise ValueError("community_id must be a string")
            try:
                parsed_uuid = uuid.UUID(community_id)
                # Check if UUID starts with reserved prefix
                if str(parsed_uuid).startswith("00000000-0000-0000-"):
                    raise ValueError("community_id cannot start with reserved prefix '00000000-0000-0000-'")
            except ValueError as exc:
                if "reserved prefix" in str(exc):
                    raise exc
                raise ValueError("community_id must be a valid UUID") from exc

        # Build request body - only include provided values
        data = {"name": name.strip()}

        if parent_id is not None:
            data["parentId"] = parent_id
        if description is not None:
            data["description"] = description
        if community_id is not None:
            data["id"] = community_id

        response = self._post(url=self.__base_api, data=data)
        return parse_community(self._handle_response(response))

    def change_community(
        self,
        community_id: str,
        name: str = None,
        parent_id: str = None,
        description: str = None,
        remove_scope_overlap_on_move: bool = None
    ):
        """
        Changes the community with the information that is present in the request.
        Only properties that are specified in this request and have non-null values are updated.
        :param community_id: The ID of the community to be changed (required UUID).
        :param name: The new name for the community (optional, 1-255 characters).
        :param parent_id: The ID of the new parent community (optional UUID).
        :param description: The new description for the community (optional).
        :param remove_scope_overlap_on_move: Whether scopes assigned to domain community
                                           and its children should be removed on move if there
                                           are any inherited scopes in new parent community.
        :return: Details of the updated community.
        """
        # Validate required parameters
        if not community_id:
            raise ValueError("community_id is required")
        if not isinstance(community_id, str):
            raise ValueError("community_id must be a string")

        try:
            uuid.UUID(community_id)
        except ValueError as exc:
            raise ValueError("community_id must be a valid UUID") from exc

        # Validate name if provided
        if name is not None:
            if not isinstance(name, str):
                raise ValueError("name must be a string")
            if len(name.strip()) < 1 or len(name) > 255:
                raise ValueError("name must be between 1 and 255 characters")

        # Validate parent_id if provided
        if parent_id is not None:
            if not isinstance(parent_id, str):
                raise ValueError("parent_id must be a string")
            try:
                uuid.UUID(parent_id)
            except ValueError as exc:
                raise ValueError("parent_id must be a valid UUID") from exc

        # Validate description if provided
        if description is not None and not isinstance(description, str):
            raise ValueError("description must be a string")

        # Validate remove_scope_overlap_on_move if provided
        if remove_scope_overlap_on_move is not None and not isinstance(remove_scope_overlap_on_move, bool):
            raise ValueError("remove_scope_overlap_on_move must be a boolean")

        # Build request body - only include provided values
        # Include the community_id in the body as required by the API
        data = {"id": community_id}

        if name is not None:
            data["name"] = name.strip()
        if parent_id is not None:
            data["parentId"] = parent_id
        if description is not None:
            data["description"] = description
        if remove_scope_overlap_on_move is not None:
            data["removeScopeOverlapOnMove"] = remove_scope_overlap_on_move

        response = self._patch(url=f"{self.__base_api}/{community_id}", data=data)
        return parse_community(self._handle_response(response))

    def remove_community(self, community_id: str):
        """
        Remove a community by its ID.

        **DEPRECATED**: This endpoint will be removed in the future.
        Please use POST /communities/removalJobs instead.

        :param community_id: The ID of the community to remove (required UUID).
        :return: Response from the removal operation.
        """
        # Validate required parameters
        if not community_id:
            raise ValueError("community_id is required")
        if not isinstance(community_id, str):
            raise ValueError("community_id must be a string")

        try:
            uuid.UUID(community_id)
        except ValueError as exc:
            raise ValueError("community_id must be a valid UUID") from exc

        response = self._delete(url=f"{self.__base_api}/{community_id}")
        return self._handle_response(response)

    def change_to_root_community(self, community_id: str):
        """
        Changes the community with given ID to a root community.
        :param community_id: The ID of the community that will be changed to a root community (required UUID).
        :return: Details of the updated community.
        """
        # Validate required parameters
        if not community_id:
            raise ValueError("community_id is required")
        if not isinstance(community_id, str):
            raise ValueError("community_id must be a string")

        try:
            uuid.UUID(community_id)
        except ValueError as exc:
            raise ValueError("community_id must be a valid UUID") from exc

        response = self._post(url=f"{self.__base_api}/{community_id}/root", data={})
        return parse_community(self._handle_response(response))

import uuid
from .Base import BaseAPI
from ..models import parse_domain, parse_domains


class Domain(BaseAPI):
    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api + "/domains"

    def get_domain(self, domain_id: str):
        """
        Get a domain by its ID.
        :param domain_id: The ID of the domain to retrieve.
        :return: Domain details.
        """
        if not domain_id:
            raise ValueError("domain_id is required")
        if not isinstance(domain_id, str):
            raise ValueError("domain_id must be a string")

        try:
            uuid.UUID(domain_id)
        except ValueError as exc:
            raise ValueError("domain_id must be a valid UUID") from exc

        response = self._get(url=f"{self.__base_api}/{domain_id}")
        return parse_domain(self._handle_response(response))

    def find_domains(
        self,
        community_id: str = None,
        count_limit: int = -1,
        cursor: str = None,
        exclude_meta: bool = True,
        include_sub_communities: bool = False,
        limit: int = 0,
        name: str = None,
        name_match_mode: str = "ANYWHERE",
        offset: int = 0,
        type_id: str = None,
        type_public_id: str = None
    ):
        """
        Find domains matching the given search criteria.
        :param community_id: ID of the community to find domains in.
        :param count_limit: Limit elements counted. -1 counts all, 0 skips count. Ignored with cursor pagination.
        :param cursor: Cursor for pagination. Pass empty string for first page, use nextCursor for subsequent pages.
        :param exclude_meta: Whether to exclude meta domains (not manually created by users).
        :param include_sub_communities: Whether to search in sub-communities of the specified community.
        :param limit: Maximum results to retrieve. 0 uses default, max 1000.
        :param name: Name of domain to search for.
        :param name_match_mode: Name matching mode. Options: START, END, ANYWHERE, EXACT
        :param offset: First result to retrieve (deprecated, use cursor instead).
        :param type_id: Domain type ID to filter by.
        :param type_public_id: Domain type public ID to filter by.
        :return: List of domains matching criteria.
        """
        # Validate name_match_mode
        valid_match_modes = ["START", "END", "ANYWHERE", "EXACT"]
        if name_match_mode not in valid_match_modes:
            raise ValueError(f"name_match_mode must be one of: {', '.join(valid_match_modes)}")

        # Validate limit
        if limit < 0 or limit > 1000:
            raise ValueError("limit must be between 0 and 1000")

        # Validate community_id if provided
        if community_id is not None:
            if not isinstance(community_id, str):
                raise ValueError("community_id must be a string")
            try:
                uuid.UUID(community_id)
            except ValueError as exc:
                raise ValueError("community_id must be a valid UUID") from exc

        # Validate type_id if provided
        if type_id is not None:
            if not isinstance(type_id, str):
                raise ValueError("type_id must be a string")
            try:
                uuid.UUID(type_id)
            except ValueError as exc:
                raise ValueError("type_id must be a valid UUID") from exc

        # Validate cursor and offset usage
        if cursor is not None and offset != 0:
            raise ValueError("Cannot use both cursor and offset in the same request")

        # Build parameters - only include non-default values
        params = {}

        if community_id is not None:
            params["communityId"] = community_id
        if count_limit != -1:
            params["countLimit"] = count_limit
        if cursor is not None:
            params["cursor"] = cursor
        if exclude_meta is not True:
            params["excludeMeta"] = exclude_meta
        if include_sub_communities is not False:
            params["includeSubCommunities"] = include_sub_communities
        if limit != 0:
            params["limit"] = limit
        if name is not None:
            params["name"] = name
        if name_match_mode != "ANYWHERE":
            params["nameMatchMode"] = name_match_mode
        if offset != 0:
            params["offset"] = offset
        if type_id is not None:
            params["typeId"] = type_id
        if type_public_id is not None:
            params["typePublicId"] = type_public_id

        response = self._get(url=self.__base_api, params=params)
        return parse_domains(self._handle_response(response))

    def add_domain(
        self,
        name: str,
        community_id: str,
        type_id: str = None,
        description: str = None,
        domain_id: str = None,
        excluded_from_auto_hyperlinking: bool = None,
        type_public_id: str = None
    ):
        """
        Adds a new domain with given data into a community.
        :param name: The name of the new domain. Should be unique within the community
                    (required, 1-255 characters).
        :param community_id: The ID of the community that the new domain should be added to (required UUID).
        :param type_id: The ID of the domain type of the new domain (optional UUID).
        :param description: The description of the new domain (optional).
        :param domain_id: The ID of the new domain. Should be unique within all domains (optional UUID).
        :param excluded_from_auto_hyperlinking: Whether to exclude from auto hyperlinking (optional boolean).
        :param type_public_id: The public ID of the domain type of the new domain (optional).
        :return: Details of the created domain.
        """
        # Validate required parameters
        if not name:
            raise ValueError("name is required")
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        if len(name.strip()) < 1 or len(name) > 255:
            raise ValueError("name must be between 1 and 255 characters")

        if not community_id:
            raise ValueError("community_id is required")
        if not isinstance(community_id, str):
            raise ValueError("community_id must be a string")
        try:
            uuid.UUID(community_id)
        except ValueError as exc:
            raise ValueError("community_id must be a valid UUID") from exc

        # Validate type_id if provided
        if type_id is not None:
            if not isinstance(type_id, str):
                raise ValueError("type_id must be a string")
            try:
                uuid.UUID(type_id)
            except ValueError as exc:
                raise ValueError("type_id must be a valid UUID") from exc

        # Validate description if provided
        if description is not None and not isinstance(description, str):
            raise ValueError("description must be a string")

        # Validate domain_id if provided
        if domain_id is not None:
            if not isinstance(domain_id, str):
                raise ValueError("domain_id must be a string")
            try:
                parsed_uuid = uuid.UUID(domain_id)
                # Check if UUID starts with reserved prefix
                if str(parsed_uuid).startswith("00000000-0000-0000-"):
                    raise ValueError("domain_id cannot start with reserved prefix '00000000-0000-0000-'")
            except ValueError as exc:
                if "reserved prefix" in str(exc):
                    raise exc
                raise ValueError("domain_id must be a valid UUID") from exc

        # Validate excluded_from_auto_hyperlinking if provided
        if excluded_from_auto_hyperlinking is not None and not isinstance(excluded_from_auto_hyperlinking, bool):
            raise ValueError("excluded_from_auto_hyperlinking must be a boolean")

        # Validate type_public_id if provided
        if type_public_id is not None and not isinstance(type_public_id, str):
            raise ValueError("type_public_id must be a string")

        # Build request body - only include provided values
        data = {
            "name": name.strip(),
            "communityId": community_id
        }

        if type_id is not None:
            data["typeId"] = type_id
        if description is not None:
            data["description"] = description
        if domain_id is not None:
            data["id"] = domain_id
        if excluded_from_auto_hyperlinking is not None:
            data["excludedFromAutoHyperlinking"] = excluded_from_auto_hyperlinking
        if type_public_id is not None:
            data["typePublicId"] = type_public_id

        response = self._post(url=self.__base_api, data=data)
        return parse_domain(self._handle_response(response))

    def remove_domain(self, domain_id: str):
        """
        Remove a domain by its ID.

        **DEPRECATED**: This endpoint will be removed in the future.
        Please use POST /domains/removalJobs instead.

        :param domain_id: The ID of the domain to remove (required UUID).
        :return: Response from the removal operation.
        """
        # Validate required parameters
        if not domain_id:
            raise ValueError("domain_id is required")
        if not isinstance(domain_id, str):
            raise ValueError("domain_id must be a string")

        try:
            uuid.UUID(domain_id)
        except ValueError as exc:
            raise ValueError("domain_id must be a valid UUID") from exc

        response = self._delete(url=f"{self.__base_api}/{domain_id}")
        return self._handle_response(response)

    def change_domain(
        self,
        domain_id: str,
        name: str = None,
        description: str = None,
        type_id: str = None,
        type_public_id: str = None,
        excluded_from_auto_hyperlinking: bool = None
    ):
        """
        Changes the domain with the information that is present in the request.
        Only properties that are specified in this request and have non-null values are updated.
        :param domain_id: The ID of the domain to be changed (required UUID).
        :param name: The new name for the domain (optional, 1-255 characters).
        :param description: The new description for the domain (optional).
        :param type_id: The ID of the domain type (optional UUID).
        :param type_public_id: The public ID of the domain type (optional).
        :param excluded_from_auto_hyperlinking: Whether to exclude from auto hyperlinking (optional boolean).
        :return: Details of the updated domain.
        """
        # Validate required parameters
        if not domain_id:
            raise ValueError("domain_id is required")
        if not isinstance(domain_id, str):
            raise ValueError("domain_id must be a string")

        try:
            uuid.UUID(domain_id)
        except ValueError as exc:
            raise ValueError("domain_id must be a valid UUID") from exc

        # Validate name if provided
        if name is not None:
            if not isinstance(name, str):
                raise ValueError("name must be a string")
            if len(name.strip()) < 1 or len(name) > 255:
                raise ValueError("name must be between 1 and 255 characters")

        # Validate description if provided
        if description is not None and not isinstance(description, str):
            raise ValueError("description must be a string")

        # Validate type_id if provided
        if type_id is not None:
            if not isinstance(type_id, str):
                raise ValueError("type_id must be a string")
            try:
                uuid.UUID(type_id)
            except ValueError as exc:
                raise ValueError("type_id must be a valid UUID") from exc

        # Validate type_public_id if provided
        if type_public_id is not None and not isinstance(type_public_id, str):
            raise ValueError("type_public_id must be a string")

        # Validate excluded_from_auto_hyperlinking if provided
        if excluded_from_auto_hyperlinking is not None and not isinstance(excluded_from_auto_hyperlinking, bool):
            raise ValueError("excluded_from_auto_hyperlinking must be a boolean")

        # Build request body - only include provided values
        # Include the domain_id in the body as required by the API
        data = {"id": domain_id}

        if name is not None:
            data["name"] = name.strip()
        if description is not None:
            data["description"] = description
        if type_id is not None:
            data["typeId"] = type_id
        if type_public_id is not None:
            data["typePublicId"] = type_public_id
        if excluded_from_auto_hyperlinking is not None:
            data["excludedFromAutoHyperlinking"] = excluded_from_auto_hyperlinking

        response = self._patch(url=f"{self.__base_api}/{domain_id}", data=data)
        return parse_domain(self._handle_response(response))

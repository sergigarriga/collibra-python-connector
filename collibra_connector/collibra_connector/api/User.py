import uuid
from .Base import BaseAPI
from ..models import parse_user, parse_users


class User(BaseAPI):
    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api + "/users"

    def get_user(self, user_id: str):
        """
        Get user information by user ID.
        :param user_id: The ID of the user.
        :return: User details.
        """
        if not user_id:
            raise ValueError("user_id is required")
        if not isinstance(user_id, str):
            raise ValueError("user_id must be a string")

        try:
            uuid.UUID(user_id)
        except ValueError as exc:
            raise ValueError("user_id must be a valid UUID") from exc

        response = self._get(url=f"{self.__base_api}/{user_id}")
        return parse_user(self._handle_response(response))

    def get_user_by_username(self, username: str):
        """
        Get user ID by username (convenience method).
        :param username: The username to search for.
        :return: User ID if found, None otherwise.
        """
        if not username:
            raise ValueError("username is required")
        if not isinstance(username, str):
            raise ValueError("username must be a string")

        result = self.find_users(
            name=username,
            name_search_fields=["USERNAME"],
            include_disabled=True,
            limit=1
        )

        if result.get("total", 0) > 0:
            return result.get("results", [{}])[0].get("id", "")
        return None

    def create_user(self, username: str, email_address: str):
        """
        Create a new user.
        :param username: The username for the new user.
        :param email_address: The email address for the new user.
        :return: The created user details.
        """
        if not username or not email_address:
            raise ValueError("username and email_address are required")
        if not isinstance(username, str) or not isinstance(email_address, str):
            raise ValueError("username and email_address must be strings")

        data = {
            "userName": username,
            "emailAddress": email_address
        }

        response = self._post(url=self.__base_api, data=data)
        return parse_user(self._handle_response(response))

    def find_users(
        self,
        count_limit: int = -1,
        group_id: str = None,
        include_disabled: bool = None,
        limit: int = 0,
        name: str = None,
        name_search_fields: list = None,
        offset: int = 0,
        only_logged_in: bool = None,
        sort_field: str = "USERNAME",
        sort_order: str = "ASC",
        user_ids: list = None
    ):
        """
        Find users based on various criteria.
        :param count_limit: Limit the number of elements that will be counted. -1 counts everything, 0 skips count.
        :param group_id: The ID of the group the searched users should belong to.
        :param include_disabled: Whether disabled users should be included in the search results.
        :param limit: Maximum number of results to retrieve (0 = default limit, max 1000).
        :param name: Name to search for in the fields specified by name_search_fields.
        :param name_search_fields: User fields to search for the 'name' parameter.
        :param offset: First result to retrieve (0-based).
        :param only_logged_in: Whether only currently logged in users should be returned.
        :param sort_field: Field for sorting.
        :param sort_order: Order of sorting (ASC/DESC).
        :param user_ids: List of user IDs to look for.
        :return: Search results with users matching the criteria.
        """
        # Validate count_limit
        if not isinstance(count_limit, int):
            raise ValueError("count_limit must be an integer")

        # Validate group_id if provided
        if group_id is not None:
            if not isinstance(group_id, str):
                raise ValueError("group_id must be a string")
            try:
                uuid.UUID(group_id)
            except ValueError as exc:
                raise ValueError("group_id must be a valid UUID") from exc

        # Validate include_disabled
        if include_disabled is not None and not isinstance(include_disabled, bool):
            raise ValueError("include_disabled must be a boolean")

        # Validate limit
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")
        if limit > 1000:
            raise ValueError("limit cannot exceed 1000")

        # Validate name
        if name is not None and not isinstance(name, str):
            raise ValueError("name must be a string")

        # Validate name_search_fields
        valid_name_search_fields = [
            "USERNAME", "FIRSTNAME", "LASTNAME", "LASTNAME_FIRSTNAME",
            "FIRSTNAME_LASTNAME", "EMAIL"
        ]
        if name_search_fields is not None:
            if not isinstance(name_search_fields, list):
                raise ValueError("name_search_fields must be a list")
            for field in name_search_fields:
                if field not in valid_name_search_fields:
                    raise ValueError(f"Invalid name search field: {field}. "
                                     f"Allowed values: {valid_name_search_fields}")
        # Validate offset
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a non-negative integer")

        # Validate only_logged_in
        if only_logged_in is not None and not isinstance(only_logged_in, bool):
            raise ValueError("only_logged_in must be a boolean")
        # Validate sort_field
        valid_sort_fields = [
            "USERNAME", "FIRSTNAME", "LASTNAME", "LASTNAME_FIRSTNAME",
            "FIRSTNAME_LASTNAME", "EMAIL"
        ]
        if sort_field not in valid_sort_fields:
            raise ValueError(f"Invalid sort field: {sort_field}. "
                             f"Allowed values: {valid_sort_fields}")
        # Validate sort_order
        if sort_order not in ["ASC", "DESC"]:
            raise ValueError("sort_order must be 'ASC' or 'DESC'")

        # Validate user_ids
        if user_ids is not None:
            if not isinstance(user_ids, list):
                raise ValueError("user_ids must be a list")
            for user_id in user_ids:
                if not isinstance(user_id, str):
                    raise ValueError("All user IDs must be strings")
                try:
                    uuid.UUID(user_id)
                except ValueError as exc:
                    raise ValueError(f"Invalid UUID in user_ids: {user_id}") from exc

        # Build parameters
        params = {
            "countLimit": count_limit,
            "limit": limit,
            "offset": offset,
            "sortField": sort_field,
            "sortOrder": sort_order
        }

        # Add optional parameters
        if group_id is not None:
            params["groupId"] = group_id

        if include_disabled is not None:
            params["includeDisabled"] = include_disabled

        if name is not None:
            params["name"] = name

        if name_search_fields is not None:
            params["nameSearchFields"] = name_search_fields

        if only_logged_in is not None:
            params["onlyLoggedIn"] = only_logged_in

        if user_ids is not None:
            # The API expects multiple userId parameters for each ID
            for user_id in user_ids:
                if "userId" not in params:
                    params["userId"] = []
                params["userId"].append(user_id)

        response = self._get(url=self.__base_api, params=params)
        return parse_users(self._handle_response(response))

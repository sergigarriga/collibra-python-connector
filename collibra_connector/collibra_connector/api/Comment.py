import uuid
from .Base import BaseAPI
from ..models import parse_comment, parse_comments


class Comment(BaseAPI):
    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api + "/comments"

    def add_comment(self, asset_id: str, content: str):
        """
        Add a comment to an asset.
        :param asset_id: The ID of the asset to comment on.
        :param content: The content of the comment.
        :return: The created comment model.
        """
        if not asset_id or not content:
            raise ValueError("asset_id and content are required parameters")
        if not isinstance(asset_id, str) or not isinstance(content, str):
            raise ValueError("asset_id and content must be strings")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        data = {
            "content": content,
            "baseResource": {
                "id": asset_id,
                "resourceType": "Asset"
            },
        }

        response = self._post(url=self.__base_api, data=data)
        return parse_comment(self._handle_response(response))

    def find_comments(
        self,
        base_resource_id: str = None,
        count_limit: int = -1,
        limit: int = 0,
        offset: int = 0,
        parent_id: str = None,
        resolved: bool = None,
        root_comment: bool = None,
        sort_order: str = "DESC",
        user_id: str = None,
        user_threads: bool = False
    ):
        """
        Find comments matching the given search criteria.
        :param base_resource_id: The ID of the resource which the searched comments refer to.
        :param count_limit: Limit the number of elements counted. -1 counts everything, 0 skips count.
        :param limit: Maximum number of results to retrieve. 0 uses default, max 1000.
        :param offset: First result to retrieve. 0 starts from beginning.
        :param parent_id: ID of the comment for which reply comments should be searched.
        :param resolved: Whether the searched comments should be resolved.
        :param root_comment: Whether the searched comments should be root comments.
        :param sort_order: Sort order on creation date. 'ASC' or 'DESC'.
        :param user_id: ID of the user to filter comments by.
        :param user_threads: Whether to search for root comments created by or mentioning the user.
        :return: Paginated list of comments.
        """
        # Validate base_resource_id if provided
        if base_resource_id is not None:
            if not isinstance(base_resource_id, str):
                raise ValueError("base_resource_id must be a string")
            try:
                uuid.UUID(base_resource_id)
            except ValueError as exc:
                raise ValueError("base_resource_id must be a valid UUID") from exc

        # Validate parent_id if provided
        if parent_id is not None:
            if not isinstance(parent_id, str):
                raise ValueError("parent_id must be a string")
            try:
                uuid.UUID(parent_id)
            except ValueError as exc:
                raise ValueError("parent_id must be a valid UUID") from exc

        # Validate user_id if provided
        if user_id is not None:
            if not isinstance(user_id, str):
                raise ValueError("user_id must be a string")
            try:
                uuid.UUID(user_id)
            except ValueError as exc:
                raise ValueError("user_id must be a valid UUID") from exc

        # Validate sort_order
        if sort_order not in ["ASC", "DESC"]:
            raise ValueError("sort_order must be 'ASC' or 'DESC'")

        # Validate limit
        if limit < 0 or limit > 1000:
            raise ValueError("limit must be between 0 and 1000")

        # Build parameters - only include non-None values
        params = {}

        if base_resource_id is not None:
            params["baseResourceId"] = base_resource_id
        if count_limit != -1:  # Only add if different from default
            params["countLimit"] = count_limit
        if limit != 0:  # Only add if different from default
            params["limit"] = limit
        if offset != 0:  # Only add if different from default
            params["offset"] = offset
        if parent_id is not None:
            params["parentId"] = parent_id
        if resolved is not None:
            params["resolved"] = resolved
        if root_comment is not None:
            params["rootComment"] = root_comment
        if sort_order != "DESC":  # Only add if different from default
            params["sortOrder"] = sort_order
        if user_id is not None:
            params["userId"] = user_id
        if user_threads is not False:  # Only add if different from default
            params["userThreads"] = user_threads

        response = self._get(url=self.__base_api, params=params)
        return parse_comments(self._handle_response(response))

import uuid
from .Base import BaseAPI
from ..models import parse_relation, parse_relations, RelationTypeModel


class Relation(BaseAPI):
    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api + "/relations"

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        type_id: str = None,
        starting_date: int = None,
        ending_date: int = None,
        type_public_id: str = None
    ):
        """
        Adds a new relation.
        :param source_id: The ID of the source of the relation (required UUID).
        :param target_id: The ID of the target of the relation (required UUID).
        :param type_id: The ID of the type of the relation (optional UUID).
        :param starting_date: The starting date of the relation (deprecated, int64).
        :param ending_date: The ending date of the relation (deprecated, int64).
        :param type_public_id: The public ID of the type of the relation (optional).
        :return: Details of the created relation.
        """
        # Validate required parameters
        if not source_id:
            raise ValueError("source_id is required")
        if not isinstance(source_id, str):
            raise ValueError("source_id must be a string")
        try:
            uuid.UUID(source_id)
        except ValueError as exc:
            raise ValueError("source_id must be a valid UUID") from exc

        if not target_id:
            raise ValueError("target_id is required")
        if not isinstance(target_id, str):
            raise ValueError("target_id must be a string")
        try:
            uuid.UUID(target_id)
        except ValueError as exc:
            raise ValueError("target_id must be a valid UUID") from exc

        # Validate type_id if provided
        if type_id is not None:
            if not isinstance(type_id, str):
                raise ValueError("type_id must be a string")
            try:
                uuid.UUID(type_id)
            except ValueError as exc:
                raise ValueError("type_id must be a valid UUID") from exc

        # Validate starting_date if provided
        if starting_date is not None:
            if not isinstance(starting_date, int):
                raise ValueError("starting_date must be an integer")
            if starting_date < 0:
                raise ValueError("starting_date must be a positive integer")

        # Validate ending_date if provided
        if ending_date is not None:
            if not isinstance(ending_date, int):
                raise ValueError("ending_date must be an integer")
            if ending_date < 0:
                raise ValueError("ending_date must be a positive integer")

        # Validate type_public_id if provided
        if type_public_id is not None and not isinstance(type_public_id, str):
            raise ValueError("type_public_id must be a string")

        # Build request data - only include provided values
        data = {
            "sourceId": source_id,
            "targetId": target_id
        }

        if type_id is not None:
            data["typeId"] = type_id
        if starting_date is not None:
            data["startingDate"] = starting_date
        if ending_date is not None:
            data["endingDate"] = ending_date
        if type_public_id is not None:
            data["typePublicId"] = type_public_id

        response = self._post(url=self.__base_api, data=data)
        return parse_relation(self._handle_response(response))

    def get_relation(self, relation_id: str):
        """
        Returns a relation identified by given id.
        :param relation_id: The ID of the relation (required UUID).
        :return: Relation details.
        """
        if not relation_id:
            raise ValueError("relation_id is required")
        if not isinstance(relation_id, str):
            raise ValueError("relation_id must be a string")

        try:
            uuid.UUID(relation_id)
        except ValueError as exc:
            raise ValueError("relation_id must be a valid UUID") from exc

        response = self._get(url=f"{self.__base_api}/{relation_id}")
        return parse_relation(self._handle_response(response))

    def remove_relation(self, relation_id: str):
        """
        Removes a relation identified by given id.
        :param relation_id: The ID of the relation to remove (required UUID).
        :return: Response from the removal operation.
        """
        if not relation_id:
            raise ValueError("relation_id is required")
        if not isinstance(relation_id, str):
            raise ValueError("relation_id must be a string")

        try:
            uuid.UUID(relation_id)
        except ValueError as exc:
            raise ValueError("relation_id must be a valid UUID") from exc

        response = self._delete(url=f"{self.__base_api}/{relation_id}")
        return self._handle_response(response)

    def change_relation(
        self,
        relation_id: str,
        source_id: str = None,
        target_id: str = None,
        starting_date: int = None,
        ending_date: int = None
    ):
        """
        Changes the relation with the information that is present in the request.
        Only properties that are specified in this request and have non-null values are updated.
        :param relation_id: The ID of the relation to be changed (required UUID).
        :param source_id: The ID of the new source for the relation (optional UUID).
        :param target_id: The ID of the new target for the relation (optional UUID).
        :param starting_date: The new starting date for the relation (deprecated, int64).
        :param ending_date: The new ending date for the relation (deprecated, int64).
        :return: Details of the updated relation.
        """
        # Validate required parameters
        if not relation_id:
            raise ValueError("relation_id is required")
        if not isinstance(relation_id, str):
            raise ValueError("relation_id must be a string")

        try:
            uuid.UUID(relation_id)
        except ValueError as exc:
            raise ValueError("relation_id must be a valid UUID") from exc

        # Validate source_id if provided
        if source_id is not None:
            if not isinstance(source_id, str):
                raise ValueError("source_id must be a string")
            try:
                uuid.UUID(source_id)
            except ValueError as exc:
                raise ValueError("source_id must be a valid UUID") from exc

        # Validate target_id if provided
        if target_id is not None:
            if not isinstance(target_id, str):
                raise ValueError("target_id must be a string")
            try:
                uuid.UUID(target_id)
            except ValueError as exc:
                raise ValueError("target_id must be a valid UUID") from exc

        # Validate starting_date if provided
        if starting_date is not None:
            if not isinstance(starting_date, int):
                raise ValueError("starting_date must be an integer")
            if starting_date < 0:
                raise ValueError("starting_date must be a positive integer")

        # Validate ending_date if provided
        if ending_date is not None:
            if not isinstance(ending_date, int):
                raise ValueError("ending_date must be an integer")
            if ending_date < 0:
                raise ValueError("ending_date must be a positive integer")

        # Build request body - only include provided values
        # Include the relation_id in the body as required by the API
        data = {"id": relation_id}

        if source_id is not None:
            data["sourceId"] = source_id
        if target_id is not None:
            data["targetId"] = target_id
        if starting_date is not None:
            data["startingDate"] = starting_date
        if ending_date is not None:
            data["endingDate"] = ending_date

        response = self._patch(url=f"{self.__base_api}/{relation_id}", data=data)
        return parse_relation(self._handle_response(response))

    def find_relations(
        self,
        source_id: str = None,
        target_id: str = None,
        type_id: str = None,
        source_type_id: str = None,
        target_type_id: str = None,
        limit: int = 100,
        offset: int = 0
    ):
        """
        Find relations matching the given criteria.

        Args:
            source_id: Filter by source asset ID.
            target_id: Filter by target asset ID.
            type_id: Filter by relation type ID.
            source_type_id: Filter by source asset type ID.
            target_type_id: Filter by target asset type ID.
            limit: Maximum results to retrieve (max 1000).
            offset: First result to retrieve.

        Returns:
            List of relations matching criteria.

        Example:
            >>> # Get all outgoing relations from an asset
            >>> relations = connector.relation.find_relations(source_id="asset-uuid")
            >>> # Get all incoming relations to an asset
            >>> relations = connector.relation.find_relations(target_id="asset-uuid")
        """
        params = {
            "limit": limit,
            "offset": offset
        }

        # Validate and add source_id
        if source_id is not None:
            if not isinstance(source_id, str):
                raise ValueError("source_id must be a string")
            try:
                uuid.UUID(source_id)
            except ValueError as exc:
                raise ValueError("source_id must be a valid UUID") from exc
            params["sourceId"] = source_id

        # Validate and add target_id
        if target_id is not None:
            if not isinstance(target_id, str):
                raise ValueError("target_id must be a string")
            try:
                uuid.UUID(target_id)
            except ValueError as exc:
                raise ValueError("target_id must be a valid UUID") from exc
            params["targetId"] = target_id

        # Validate and add type_id
        if type_id is not None:
            if not isinstance(type_id, str):
                raise ValueError("type_id must be a string")
            try:
                uuid.UUID(type_id)
            except ValueError as exc:
                raise ValueError("type_id must be a valid UUID") from exc
            params["typeId"] = type_id

        # Add optional type filters
        if source_type_id is not None:
            params["sourceTypeId"] = source_type_id
        if target_type_id is not None:
            params["targetTypeId"] = target_type_id

        response = self._get(url=self.__base_api, params=params)
        return parse_relations(self._handle_response(response))

    def get_relation_type(self, relation_type_id: str):
        """
        Get relation type details by ID.

        Args:
            relation_type_id: The UUID of the relation type.

        Returns:
            Relation type details including role and coRole names.
        """
        if not relation_type_id:
            raise ValueError("relation_type_id is required")

        try:
            uuid.UUID(relation_type_id)
        except ValueError as exc:
            raise ValueError("relation_type_id must be a valid UUID") from exc

        url = self._BaseAPI__connector.api + f"/relationTypes/{relation_type_id}"
        response = self._get(url=url)
        return RelationTypeModel.model_validate(self._handle_response(response))

    def get_asset_relations(
        self,
        asset_id: str,
        direction: str = "BOTH",
        limit: int = 500,
        include_type_details: bool = True
    ):
        """
        Get all relations for an asset, grouped by direction and type.

        Convenience method that returns a structured view of all relations.

        Args:
            asset_id: The UUID of the asset.
            direction: "OUTGOING", "INCOMING", or "BOTH".
            limit: Maximum relations per direction.
            include_type_details: If True, fetches relation type names (slower but more informative).

        Returns:
            Dictionary with 'outgoing' and 'incoming' keys, each containing
            relations grouped by relation type name.

        Example:
            >>> relations = connector.relation.get_asset_relations("asset-uuid")
            >>> print(relations['outgoing'])  # Relations where asset is source
            >>> print(relations['incoming'])  # Relations where asset is target
        """
        if not asset_id:
            raise ValueError("asset_id is required")

        try:
            uuid.UUID(asset_id)
        except ValueError as exc:
            raise ValueError("asset_id must be a valid UUID") from exc

        result = {
            "outgoing": {},
            "incoming": {},
            "outgoing_count": 0,
            "incoming_count": 0
        }

        # Cache for relation type details
        type_cache = {}

        def get_type_name(type_id, is_source=True):
            """Get relation type name, using cache."""
            if not include_type_details or not type_id:
                return "Unknown"

            if type_id not in type_cache:
                try:
                    type_details = self.get_relation_type(type_id)
                    type_cache[type_id] = type_details
                except Exception:
                    # Cache empty dict or None to avoid refetching
                    type_cache[type_id] = None

            cached = type_cache.get(type_id)
            if not cached:
                return "Unknown"
                
            if is_source:
                return cached.role or "Unknown"
            else:
                return cached.co_role or "Unknown"

        # Get outgoing relations
        if direction in ("BOTH", "OUTGOING"):
            outgoing = self.find_relations(source_id=asset_id, limit=limit)
            result["outgoing_count"] = outgoing.total

            for rel in outgoing:
                type_id = rel.type.id
                type_name = get_type_name(type_id, is_source=True)
                target = rel.target

                # Get target asset type by looking up the relation type
                target_type_name = None
                if type_id in type_cache:
                    target_type_name = type_cache[type_id].target_type.name if type_cache[type_id].target_type else None

                if type_name not in result["outgoing"]:
                    result["outgoing"][type_name] = []

                result["outgoing"][type_name].append({
                    "id": rel.id,
                    "target_id": target.id,
                    "target_name": target.name,
                    "target_type": target_type_name,
                    "target_status": "N/A" # Status is not in Reference
                })

        # Get incoming relations
        if direction in ("BOTH", "INCOMING"):
            incoming = self.find_relations(target_id=asset_id, limit=limit)
            result["incoming_count"] = incoming.total

            for rel in incoming:
                type_id = rel.type.id
                type_name = get_type_name(type_id, is_source=False)
                source = rel.source

                # Get source asset type by looking up the relation type
                source_type_name = None
                if type_id in type_cache:
                    source_type_name = type_cache[type_id].source_type.name if type_cache[type_id].source_type else None

                if type_name not in result["incoming"]:
                    result["incoming"][type_name] = []

                result["incoming"][type_name].append({
                    "id": rel.id,
                    "source_id": source.id,
                    "source_name": source.name,
                    "source_type": source_type_name,
                    "source_status": "N/A"
                })

        return result

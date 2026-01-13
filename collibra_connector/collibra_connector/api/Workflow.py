import uuid
from .Base import BaseAPI
from ..models import (
    parse_workflow_task, 
    parse_workflow_tasks, 
    parse_workflow_instance, 
    parse_workflow_instances,
    parse_workflow_definition,
    parse_workflow_definitions
)


class Workflow(BaseAPI):
    def __init__(self, connector):
        super().__init__(connector)
        self.__base_api = connector.api

    def start_workflow_instance(
        self,
        workflow_definition_id: str,
        asset_id: str = None,
        return_all: bool = False
    ):
        """
        Start a workflow instance.
        :param workflow_definition_id: The ID of the workflow definition.
        :param asset_id: Optional asset ID to associate with the workflow.
        :param return_all: Whether to return all workflow data or just the ID.
        :return: Workflow instance ID or full response data.
        """
        if not workflow_definition_id:
            raise ValueError("workflow_definition_id is required")
        if not isinstance(workflow_definition_id, str):
            raise ValueError("workflow_definition_id must be a string")

        try:
            uuid.UUID(workflow_definition_id)
        except ValueError as exc:
            raise ValueError("workflow_definition_id must be a valid UUID") from exc

        data = {
            "workflowDefinitionId": workflow_definition_id,
            "sendNotification": True
        }

        if asset_id:
            if not isinstance(asset_id, str):
                raise ValueError("asset_id must be a string")
            try:
                uuid.UUID(asset_id)
            except ValueError as exc:
                raise ValueError("asset_id must be a valid UUID") from exc

            data.update({
                "businessItemIds": [asset_id],
                "businessItemType": "ASSET",
            })

        response = self._post(url=f"{self.__base_api}/workflowInstances", data=data)
        result = self._handle_response(response)

        if return_all:
            return result
        return result[0].get("id") if result else None

    def find_workflow_task(
        self,
        business_item_id: str = None,
        business_item_name: str = None,
        business_item_type: str = None,
        count_limit: int = -1,
        create_date: str = None,
        description: str = None,
        due_date: str = None,
        limit: int = 0,
        offset: int = 0,
        sort_field: str = "DUE_DATE",
        sort_order: str = "DESC",
        title: str = None,
        user_id: str = None,
        workflow_task_user_relation: str = "ALL"
    ):
        """
        Find workflow tasks matching the given search criteria.
        :param business_item_id: ID of the business item associated with the task.
        :param business_item_name: Name of the business item associated with the task.
        :param business_item_type: Type of the business item (e.g., ASSET).
        :param count_limit: Limit elements counted. -1 counts all, 0 skips count.
        :param create_date: Creation date of the task.
        :param description: Description of the task.
        :param due_date: Due date of the task.
        :param limit: Maximum results to retrieve. 0 uses default, max 1000.
        :param offset: First result to retrieve (deprecated, use cursor instead).
        :param sort_field: Field to sort results by. Default is DUE_DATE.
        :param sort_order: Sort order. Options: ASC, DESC. Default is DESC.
        :param title: Title of the task
        :param user_id: ID of the user associated with the task.
        :param workflow_task_user_relation: Relation of the user to the task. Options: ALL, ASSIGNED, INVOLVED.
        :return: List of workflow tasks matching criteria.
        """
        # Validate business_item_id if provided
        if business_item_id is not None:
            if not isinstance(business_item_id, str):
                raise ValueError("business_item_id must be a string")
            try:
                uuid.UUID(business_item_id)
            except ValueError as exc:
                raise ValueError("business_item_id must be a valid UUID") from exc

        # Validate business_item_type if provided
        if business_item_type is not None and not isinstance(business_item_type, str):
            raise ValueError("business_item_type must be a string")

        # Validate count_limit
        if not isinstance(count_limit, int):
            raise ValueError("count_limit must be an integer")

        # Validate create_date if provided
        if create_date is not None and not isinstance(create_date, str):
            raise ValueError("create_date must be a string")

        # Validate description if provided
        if description is not None and not isinstance(description, str):
            raise ValueError("description must be a string")

        # Validate due_date if provided
        if due_date is not None and not isinstance(due_date, str):
            raise ValueError("due_date must be a string")

        # Validate limit
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")
        if limit > 1000:
            raise ValueError("limit cannot exceed 1000")

        # Validate offset
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a non-negative integer")

        # Validate sort_field
        valid_sort_fields = ["DUE_DATE", "CREATE_DATE", "TITLE"]
        if sort_field not in valid_sort_fields:
            raise ValueError(f"sort_field must be one of: {', '.join(valid_sort_fields)}")

        # Validate sort_order
        if sort_order not in ["ASC", "DESC"]:
            raise ValueError("sort_order must be 'ASC' or 'DESC'")

        # Validate title if provided
        if title is not None and not isinstance(title, str):
            raise ValueError("title must be a string")

        # Validate user_id if provided
        if user_id is not None:
            if not isinstance(user_id, str):
                raise ValueError("user_id must be a string")
            try:
                uuid.UUID(user_id)
            except ValueError as exc:
                raise ValueError("user_id must be a valid UUID") from exc

        # Validate workflow_task_user_relation
        valid_relations = ["ALL", "ASSIGNED", "INVOLVED"]
        if workflow_task_user_relation not in valid_relations:
            raise ValueError(f"workflow_task_user_relation must be one of: {', '.join(valid_relations)}")

        # Build parameters - only include non-default values
        params = {
            "countLimit": count_limit,
            "limit": limit,
            "offset": offset,
            "sortField": sort_field,
            "sortOrder": sort_order,
            "workflowTaskUserRelation": workflow_task_user_relation
        }

        if business_item_id is not None:
            params["businessItemId"] = business_item_id
        if business_item_name is not None:
            params["businessItemName"] = business_item_name
        if business_item_type is not None:
            params["businessItemType"] = business_item_type
        if create_date is not None:
            params["createDate"] = create_date
        if description is not None:
            params["description"] = description
        if due_date is not None:
            params["dueDate"] = due_date
        if title is not None:
            params["title"] = title
        if user_id is not None:
            params["userId"] = user_id

        response = self._get(url=f"{self.__base_api}/workflowTasks", params=params)
        return parse_workflow_tasks(self._handle_response(response))

    def get_workflow_task_id(self, instance_id: str, workflow_definition_id: str):
        """
        Get the task ID for a workflow instance.
        :param instance_id: The workflow instance ID.
        :param workflow_definition_id: The workflow definition ID.
        :return: The task ID.
        """
        if not all([instance_id, workflow_definition_id]):
            raise ValueError("instance_id and workflow_definition_id are required")

        for param_name, param_value in [
            ("instance_id", instance_id), ("workflow_definition_id", workflow_definition_id)
        ]:
            if not isinstance(param_value, str):
                raise ValueError(f"{param_name} must be a string")
            try:
                uuid.UUID(param_value)
            except ValueError as exc:
                raise ValueError(f"{param_name} must be a valid UUID") from exc

        params = {
            "offset": 0,
            "limit": 0,
            "countLimit": -1,
            "workflowDefinitionId": workflow_definition_id,
            "instanceId": instance_id,
            "sortField": "START_DATE",
            "sortOrder": "DESC",
        }

        response = self._get(url=f"{self.__base_api}/workflowInstances", params=params)
        result = self._handle_response(response)

        tasks = result.get("results", [{}])[0].get("tasks", [])
        return tasks[0].get("id") if tasks else None

    def complete_workflow_task(self, task_ids: list[str], task_form_properties: dict):
        """
        Complete a workflow task.
        :param task_ids: The IDs of the tasks to complete.
        :param task_form_properties: The form properties for the tasks.
        :return: The response from completing the tasks.
        """
        if not task_ids or not isinstance(task_ids, list):
            raise ValueError("task_ids must be a non-empty list")
        if not all(isinstance(task_id, str) for task_id in task_ids):
            raise ValueError("All task_ids must be strings")

        response = self._post(
            url=f"{self.__base_api}/workflowTasks/completed",
            data={"taskIds": task_ids, "taskFormProperties": task_form_properties}
        )
        return self._handle_response(response)

    def get_task_form_data(self, task_id: str):
        """
        Get form data for a workflow task.
        :param task_id: The ID of the workflow task.
        :return: The task form data.
        """
        if not task_id:
            raise ValueError("task_id is required")
        if not isinstance(task_id, str):
            raise ValueError("task_id must be a string")

        try:
            uuid.UUID(task_id)
        except ValueError as exc:
            raise ValueError("task_id must be a valid UUID") from exc

        response = self._get(url=f"{self.__base_api}/workflowTasks/{task_id}/taskFormData")
        return self._handle_response(response)

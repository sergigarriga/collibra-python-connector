import re
import requests
from .Exceptions import (
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError
)


class BaseAPI:

    def __init__(self, connector):
        self.__connector = connector
        self.__base_api = connector.api
        self.__header = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.__params = None

    def _get(self, url: str = None, params: dict = None, headers: dict = None):
        """
        Makes a GET request to the specified URL.
        :param url: The URL to send the GET request to.
        :param params: Optional parameters to include in the GET request.
        :param headers: Optional headers to include in the GET request.
        :return: The response from the GET request.
        """
        url = self.__base_api if not url else url
        headers = self.__header if not headers else headers
        params = self.__params if not params else params
        return requests.get(
            url,
            auth=self.__connector.auth,
            params=params,
            headers=headers,
            timeout=self.__connector.timeout
        )

    def _post(self, url: str, data: dict, headers: dict = None, params: dict = None):
        """
        Makes a POST request to the specified URL with the given data.
        :param url: The URL to send the POST request to.
        :param data: The data to send in the POST request.
        :return: The response from the POST request.
        """
        url = self.__base_api if not url else url
        headers = self.__header if not headers else headers
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        if not data:
            raise ValueError("Data cannot be empty")
        return requests.post(
            url,
            auth=self.__connector.auth,
            json=data,
            headers=headers,
            params=params,
            timeout=self.__connector.timeout
        )

    def _put(self, url: str, data: dict, headers: dict = None):
        """
        Makes a PUT request to the specified URL with the given data.
        :param url: The URL to send the PUT request to.
        :param data: The data to send in the PUT request.
        :return: The response from the PUT request.
        """
        url = self.__base_api if not url else url
        headers = self.__header if not headers else headers
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        if not data:
            raise ValueError("Data cannot be empty")
        return requests.put(
            url,
            auth=self.__connector.auth,
            json=data,
            headers=headers,
            timeout=self.__connector.timeout
        )

    def _delete(self, url: str, headers: dict = None):
        """
        Makes a DELETE request to the specified URL.
        :param url: The URL to send the DELETE request to.
        :return: The response from the DELETE request.
        """
        url = self.__base_api if not url else url
        headers = self.__header if not headers else headers
        return requests.delete(
            url,
            auth=self.__connector.auth,
            headers=headers,
            timeout=self.__connector.timeout
        )

    def _patch(self, url: str, data: dict, headers: dict = None):
        """
        Makes a PATCH request to the specified URL with the given data.
        :param url: The URL to send the PATCH request to.
        :param data: The data to send in the PATCH request.
        :return: The response from the PATCH request.
        """
        url = self.__base_api if not url else url
        headers = self.__header if not headers else headers
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        if not data:
            raise ValueError("Data cannot be empty")
        return requests.patch(
            url,
            auth=self.__connector.auth,
            json=data,
            headers=headers,
            timeout=self.__connector.timeout
        )

    def _handle_response(self, response):
        """
        Handles the response from the API.
        :param response: The response object from the API request.
        :return: The JSON content of the response if successful, otherwise raises an error.
        """
        if response.status_code in [200, 201, 204]:
            # Check if response has content before trying to parse JSON
            if response.status_code != 204 and response.text.strip():
                try:
                    return response.json()
                except ValueError as e:
                    raise ValueError(f"Invalid JSON response: {e}") from e
            return {}
        elif response.status_code == 401:
            raise UnauthorizedError("Unauthorized access - invalid credentials: " + response.text)
        elif response.status_code == 403:
            raise ForbiddenError("Forbidden access - insufficient permissions: " + response.text)
        elif response.status_code == 404:
            raise NotFoundError("The specified resource was not found: " + response.text)
        elif response.status_code == 400:
            raise CollibraAPIError("Bad Request - Invalid parameters: " + response.text, response.status_code)
        elif response.status_code >= 500:
            raise ServerError("Internal server error - something went wrong on the server: " + response.text)
        else:
            raise Exception(f"Unexpected status code {response.status_code}: {response.text}")

    def _uuid_validation(self, id: str):
        """
        Validates if the provided ID is a valid UUID.
        :param id: The ID to validate.
        :return: True if the ID is a valid UUID, False otherwise.
        """
        if not id or not isinstance(id, str):
            return False
        pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
        return bool(pattern.match(id))

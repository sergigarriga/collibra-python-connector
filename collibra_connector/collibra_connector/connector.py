"""
Collibra Connector - Main connector class for Collibra API.

This module provides the CollibraConnector class which serves as the main
entry point for interacting with the Collibra Data Governance Center API.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, TYPE_CHECKING

import requests
from requests.auth import HTTPBasicAuth

from .api import (
    Asset,
    Attribute,
    Community,
    Domain,
    User,
    Responsibility,
    Workflow,
    Metadata,
    Comment,
    Relation,
    OutputModule,
    Utils,
    Search
)

if TYPE_CHECKING:
    from requests.auth import AuthBase


class CollibraConnector:
    """
    Main connector class for interacting with the Collibra API.

    This class provides a unified interface to connect to and interact with
    the Collibra Data Governance Center API. It handles authentication,
    connection management, and provides access to all API modules.

    Attributes:
        asset: Asset API operations
        community: Community API operations
        domain: Domain API operations
        user: User API operations
        responsibility: Responsibility API operations
        workflow: Workflow API operations
        metadata: Metadata API operations
        comment: Comment API operations
        relation: Relation API operations
        output_module: Output Module API operations
        utils: Utility operations

    Example:
        >>> connector = CollibraConnector(
        ...     api="https://your-collibra-instance.com",
        ...     username="your-username",
        ...     password="your-password"
        ... )
        >>> if connector.test_connection():
        ...     assets = connector.asset.find_assets()

        # Using as context manager:
        >>> with CollibraConnector(api="...", username="...", password="...") as conn:
        ...     assets = conn.asset.find_assets()
    """

    DEFAULT_TIMEOUT: int = 30
    DEFAULT_MAX_RETRIES: int = 3
    DEFAULT_RETRY_DELAY: float = 1.0
    RETRYABLE_STATUS_CODES: tuple = (429, 500, 502, 503, 504)

    def __init__(
        self,
        api: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        **kwargs: Any
    ) -> None:
        """
        Initialize the CollibraConnector with API URL and authentication credentials.
        
        Credentials can be provided as arguments or via environment variables:
        COLLIBRA_URL, COLLIBRA_USERNAME, COLLIBRA_PASSWORD.

        Args:
            api: The base API URL for Collibra (e.g., 'https://your-instance.collibra.com').
            username: The username for authentication.
            password: The password for authentication.
            timeout: Request timeout in seconds. Defaults to 30.
            max_retries: Maximum number of retry attempts for failed requests. Defaults to 3.
            retry_delay: Base delay between retries in seconds (uses exponential backoff). Defaults to 1.0.
            **kwargs: Additional keyword arguments.
                - uuids (bool): If True, fetches all UUIDs on initialization.

        Raises:
            ValueError: If api, username, or password is empty and not in env vars.
        """
        import os

        # Load from env vars if not provided (None means not provided, "" means empty)
        if api is None:
            api = os.environ.get("COLLIBRA_URL")
        if username is None:
            username = os.environ.get("COLLIBRA_USERNAME")
        if password is None:
            password = os.environ.get("COLLIBRA_PASSWORD")

        if not api or not api.strip():
            raise ValueError("API URL cannot be empty")
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        if not password or not password.strip():
            raise ValueError("Password cannot be empty")

        self.__auth: AuthBase = HTTPBasicAuth(username, password)
        self.__api: str = api.rstrip("/") + "/rest/2.0"
        self.__base_url: str = api.rstrip("/")
        self.__timeout: int = timeout
        self.__max_retries: int = max_retries
        self.__retry_delay: float = retry_delay
        self.__session: Optional[requests.Session] = None

        # Initialize all API classes
        self.asset: Asset = Asset(self)
        self.attribute: Attribute = Attribute(self)
        self.community: Community = Community(self)
        self.domain: Domain = Domain(self)
        self.user: User = User(self)
        self.responsibility: Responsibility = Responsibility(self)
        self.workflow: Workflow = Workflow(self)
        self.metadata: Metadata = Metadata(self)
        self.comment: Comment = Comment(self)
        self.relation: Relation = Relation(self)
        self.output_module: OutputModule = OutputModule(self)
        self.utils: Utils = Utils(self)
        self.search: Search = Search(self)
        
        # Initialize Logger without basicConfig
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())

        self.uuids: Dict[str, Dict[str, str]] = {}
        if kwargs.get('uuids'):
            self.uuids = self.utils.get_uuids() or {}

    def __enter__(self) -> "CollibraConnector":
        """Enter context manager, creating a session for connection pooling."""
        self.__session = requests.Session()
        self.__session.auth = self.__auth
        self.__session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager, closing the session."""
        if self.__session:
            self.__session.close()
            self.__session = None

    def __repr__(self) -> str:
        """Return string representation of the connector."""
        return f"CollibraConnector(api={self.__base_url})"

    def __str__(self) -> str:
        """Return user-friendly string representation."""
        return f"CollibraConnector connected to {self.__base_url}"

    @property
    def api(self) -> str:
        """Get the full API URL including the REST version path."""
        return self.__api

    @property
    def auth(self) -> "AuthBase":
        """Get the authentication object."""
        return self.__auth

    @property
    def base_url(self) -> str:
        """Get the base URL without the REST version path."""
        return self.__base_url

    @property
    def timeout(self) -> int:
        """Get the request timeout in seconds."""
        return self.__timeout

    @property
    def max_retries(self) -> int:
        """Get the maximum number of retry attempts."""
        return self.__max_retries

    @property
    def retry_delay(self) -> float:
        """Get the base retry delay in seconds."""
        return self.__retry_delay

    @property
    def session(self) -> Optional[requests.Session]:
        """Get the current session (if using context manager)."""
        return self.__session

    def test_connection(self) -> bool:
        """
        Test the connection to the Collibra API.

        Makes a request to verify that the credentials are valid and
        the API is reachable.

        Returns:
            True if connection is successful, False otherwise.

        Example:
            >>> connector = CollibraConnector(api="...", username="...", password="...")
            >>> if connector.test_connection():
            ...     print("Connected successfully!")
        """
        try:
            response = self._make_request(
                method="GET",
                url=f"{self.__api}/auth/sessions/current"
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> requests.Response:
        """
        Make an HTTP request with automatic retry logic.

        This method handles retries with exponential backoff for transient errors.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            url: The URL to make the request to.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            The response object from the request.

        Raises:
            requests.RequestException: If all retry attempts fail.
        """
        kwargs.setdefault("timeout", self.__timeout)
        kwargs.setdefault("auth", self.__auth)

        request_func = self.__session.request if self.__session else requests.request
        last_exception: Optional[Exception] = None

        for attempt in range(self.__max_retries):
            try:
                response = request_func(method, url, **kwargs)

                # Don't retry on success or client errors (except rate limiting)
                if response.status_code < 500 and response.status_code != 429:
                    return response

                # Retry on server errors and rate limiting
                if response.status_code in self.RETRYABLE_STATUS_CODES:
                    if attempt < self.__max_retries - 1:
                        delay = self.__retry_delay * (2 ** attempt)
                        self.logger.warning(
                            f"Request failed with status {response.status_code}, "
                            f"retrying in {delay:.1f}s (attempt {attempt + 1}/{self.__max_retries})"
                        )
                        time.sleep(delay)
                        continue

                return response

            except (requests.ConnectionError, requests.Timeout) as e:
                last_exception = e
                if attempt < self.__max_retries - 1:
                    delay = self.__retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Request failed with {type(e).__name__}, "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1}/{self.__max_retries})"
                    )
                    time.sleep(delay)
                else:
                    raise

        # This should not be reached, but just in case
        if last_exception:
            raise last_exception
        raise requests.RequestException("Request failed after all retries")

    def get_version(self) -> str:
        """
        Get the version of this connector library.

        Returns:
            The version string of the collibra-connector package.
        """
        from . import __version__
        return __version__

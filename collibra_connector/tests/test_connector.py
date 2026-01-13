"""Tests for the CollibraConnector class."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from collibra_connector import CollibraConnector
from collibra_connector.api.Exceptions import (
    CollibraAPIError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError,
)


class TestCollibraConnectorInit:
    """Tests for CollibraConnector initialization."""

    def test_init_with_valid_credentials(self):
        """Test initialization with valid credentials."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )
        assert connector.api == "https://test.collibra.com/rest/2.0"
        assert connector.base_url == "https://test.collibra.com"
        assert connector.timeout == 30

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass",
            timeout=60
        )
        assert connector.timeout == 60

    def test_init_with_trailing_slash(self):
        """Test that trailing slashes are handled correctly."""
        connector = CollibraConnector(
            api="https://test.collibra.com/",
            username="testuser",
            password="testpass"
        )
        assert connector.api == "https://test.collibra.com/rest/2.0"
        assert connector.base_url == "https://test.collibra.com"

    def test_init_empty_api_raises_error(self):
        """Test that empty API URL raises ValueError."""
        with pytest.raises(ValueError, match="API URL cannot be empty"):
            CollibraConnector(api="", username="user", password="pass")

    def test_init_empty_username_raises_error(self):
        """Test that empty username raises ValueError."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            CollibraConnector(api="https://test.com", username="", password="pass")

    def test_init_empty_password_raises_error(self):
        """Test that empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            CollibraConnector(api="https://test.com", username="user", password="")

    def test_init_whitespace_api_raises_error(self):
        """Test that whitespace-only API URL raises ValueError."""
        with pytest.raises(ValueError, match="API URL cannot be empty"):
            CollibraConnector(api="   ", username="user", password="pass")


class TestCollibraConnectorContextManager:
    """Tests for context manager functionality."""

    def test_context_manager_creates_session(self):
        """Test that context manager creates a session."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )

        assert connector.session is None

        with connector as conn:
            assert conn.session is not None
            assert isinstance(conn.session, requests.Session)

        assert connector.session is None

    def test_context_manager_closes_session_on_exception(self):
        """Test that session is closed even on exception."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )

        try:
            with connector:
                assert connector.session is not None
                raise RuntimeError("Test exception")
        except RuntimeError:
            pass

        assert connector.session is None


class TestCollibraConnectorRepresentation:
    """Tests for string representations."""

    def test_repr(self):
        """Test __repr__ method."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )
        assert repr(connector) == "CollibraConnector(api=https://test.collibra.com)"

    def test_str(self):
        """Test __str__ method."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )
        assert str(connector) == "CollibraConnector connected to https://test.collibra.com"


class TestCollibraConnectorRetry:
    """Tests for retry logic."""

    def test_retry_on_connection_error(self):
        """Test that connection errors trigger retry."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass",
            max_retries=3,
            retry_delay=0.01  # Short delay for testing
        )

        with patch('requests.request') as mock_request:
            mock_request.side_effect = [
                requests.ConnectionError("Connection failed"),
                requests.ConnectionError("Connection failed"),
                Mock(status_code=200),
            ]

            response = connector._make_request("GET", "https://test.com/api")
            assert response.status_code == 200
            assert mock_request.call_count == 3

    def test_retry_on_server_error(self):
        """Test that server errors (5xx) trigger retry."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass",
            max_retries=3,
            retry_delay=0.01
        )

        with patch('requests.request') as mock_request:
            mock_request.side_effect = [
                Mock(status_code=503),
                Mock(status_code=503),
                Mock(status_code=200),
            ]

            response = connector._make_request("GET", "https://test.com/api")
            assert response.status_code == 200
            assert mock_request.call_count == 3

    def test_no_retry_on_client_error(self):
        """Test that client errors (4xx except 429) don't trigger retry."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass",
            max_retries=3,
            retry_delay=0.01
        )

        with patch('requests.request') as mock_request:
            mock_request.return_value = Mock(status_code=404)

            response = connector._make_request("GET", "https://test.com/api")
            assert response.status_code == 404
            assert mock_request.call_count == 1

    def test_retry_on_rate_limit(self):
        """Test that rate limiting (429) triggers retry."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass",
            max_retries=3,
            retry_delay=0.01
        )

        with patch('requests.request') as mock_request:
            mock_request.side_effect = [
                Mock(status_code=429),
                Mock(status_code=200),
            ]

            response = connector._make_request("GET", "https://test.com/api")
            assert response.status_code == 200
            assert mock_request.call_count == 2


class TestCollibraConnectorTestConnection:
    """Tests for test_connection method."""

    def test_test_connection_success(self):
        """Test successful connection test."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )

        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=200)

            assert connector.test_connection() is True

    def test_test_connection_failure(self):
        """Test failed connection test."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )

        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = Mock(status_code=401)

            assert connector.test_connection() is False

    def test_test_connection_exception(self):
        """Test connection test with exception."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )

        with patch.object(connector, '_make_request') as mock_request:
            mock_request.side_effect = requests.ConnectionError("Failed")

            assert connector.test_connection() is False


class TestCollibraConnectorVersion:
    """Tests for version method."""

    def test_get_version(self):
        """Test getting connector version."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )

        version = connector.get_version()
        assert version == "1.2.0"


class TestCollibraConnectorAPIModules:
    """Tests for API module initialization."""

    def test_all_modules_initialized(self):
        """Test that all API modules are initialized."""
        connector = CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )

        assert connector.asset is not None
        assert connector.community is not None
        assert connector.domain is not None
        assert connector.user is not None
        assert connector.responsibility is not None
        assert connector.workflow is not None
        assert connector.metadata is not None
        assert connector.comment is not None
        assert connector.relation is not None
        assert connector.output_module is not None
        assert connector.utils is not None

"""Tests for custom exceptions."""
import pytest

from collibra_connector import (
    CollibraAPIError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError,
)


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_unauthorized_error_is_collibra_error(self):
        """Test UnauthorizedError inherits from CollibraAPIError."""
        assert issubclass(UnauthorizedError, CollibraAPIError)

    def test_forbidden_error_is_collibra_error(self):
        """Test ForbiddenError inherits from CollibraAPIError."""
        assert issubclass(ForbiddenError, CollibraAPIError)

    def test_not_found_error_is_collibra_error(self):
        """Test NotFoundError inherits from CollibraAPIError."""
        assert issubclass(NotFoundError, CollibraAPIError)

    def test_server_error_is_collibra_error(self):
        """Test ServerError inherits from CollibraAPIError."""
        assert issubclass(ServerError, CollibraAPIError)

    def test_collibra_error_is_exception(self):
        """Test CollibraAPIError inherits from Exception."""
        assert issubclass(CollibraAPIError, Exception)


class TestExceptionMessages:
    """Tests for exception message handling."""

    def test_unauthorized_error_message(self):
        """Test UnauthorizedError with custom message."""
        error = UnauthorizedError("Invalid credentials")
        assert str(error) == "Invalid credentials"

    def test_forbidden_error_message(self):
        """Test ForbiddenError with custom message."""
        error = ForbiddenError("Access denied")
        assert str(error) == "Access denied"

    def test_not_found_error_message(self):
        """Test NotFoundError with custom message."""
        error = NotFoundError("Resource not found")
        assert str(error) == "Resource not found"

    def test_server_error_message(self):
        """Test ServerError with custom message."""
        error = ServerError("Internal server error")
        assert str(error) == "Internal server error"


class TestExceptionCatching:
    """Tests for exception catching behavior."""

    def test_catch_unauthorized_as_collibra_error(self):
        """Test that UnauthorizedError can be caught as CollibraAPIError."""
        with pytest.raises(CollibraAPIError):
            raise UnauthorizedError("Test")

    def test_catch_forbidden_as_collibra_error(self):
        """Test that ForbiddenError can be caught as CollibraAPIError."""
        with pytest.raises(CollibraAPIError):
            raise ForbiddenError("Test")

    def test_catch_not_found_as_collibra_error(self):
        """Test that NotFoundError can be caught as CollibraAPIError."""
        with pytest.raises(CollibraAPIError):
            raise NotFoundError("Test")

    def test_catch_server_error_as_collibra_error(self):
        """Test that ServerError can be caught as CollibraAPIError."""
        with pytest.raises(CollibraAPIError):
            raise ServerError("Test")

    def test_catch_all_as_base_exception(self):
        """Test that all errors can be caught as Exception."""
        errors = [
            UnauthorizedError("Test"),
            ForbiddenError("Test"),
            NotFoundError("Test"),
            ServerError("Test"),
            CollibraAPIError("Test"),
        ]

        for error in errors:
            with pytest.raises(Exception):
                raise error

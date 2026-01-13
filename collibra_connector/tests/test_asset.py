"""Tests for the Asset API class."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from collibra_connector import CollibraConnector
from collibra_connector.api.Asset import Asset


@pytest.fixture
def connector():
    """Create a mock connector for testing."""
    return CollibraConnector(
        api="https://test.collibra.com",
        username="testuser",
        password="testpass"
    )


@pytest.fixture
def asset_api(connector):
    """Create an Asset API instance."""
    return connector.asset


class TestAssetAddAsset:
    """Tests for add_asset method - including the bug fix verification."""

    def test_add_asset_with_id_parameter(self, asset_api):
        """Test that _id parameter is correctly passed as 'id' in the request body.

        This test verifies the bug fix where `id` (Python built-in) was incorrectly
        used instead of `_id` (the parameter) in the request body.
        """
        with patch.object(asset_api, '_post') as mock_post:
            with patch.object(asset_api, '_handle_response') as mock_handle:
                mock_post.return_value = Mock()
                mock_handle.return_value = {"id": "test-asset-id"}

                asset_api.add_asset(
                    name="Test Asset",
                    domain_id="12345678-1234-1234-1234-123456789012",
                    _id="87654321-4321-4321-4321-210987654321"
                )

                # Verify the data passed to _post contains the correct _id value
                call_args = mock_post.call_args
                data = call_args.kwargs.get('data') or call_args[1].get('data')

                # The key assertion: 'id' in data should be the _id parameter value,
                # NOT the built-in id() function result
                assert data["id"] == "87654321-4321-4321-4321-210987654321"

    def test_add_asset_without_id_parameter(self, asset_api):
        """Test add_asset when _id is not provided."""
        with patch.object(asset_api, '_post') as mock_post:
            with patch.object(asset_api, '_handle_response') as mock_handle:
                mock_post.return_value = Mock()
                mock_handle.return_value = {"id": "generated-id"}

                asset_api.add_asset(
                    name="Test Asset",
                    domain_id="12345678-1234-1234-1234-123456789012"
                )

                call_args = mock_post.call_args
                data = call_args.kwargs.get('data') or call_args[1].get('data')

                # When _id is not provided, it should be None
                assert data["id"] is None

    def test_add_asset_requires_name(self, asset_api):
        """Test that name is required."""
        with pytest.raises(ValueError, match="Name and domain_id are required"):
            asset_api.add_asset(
                name="",
                domain_id="12345678-1234-1234-1234-123456789012"
            )

    def test_add_asset_requires_domain_id(self, asset_api):
        """Test that domain_id is required."""
        with pytest.raises(ValueError, match="Name and domain_id are required"):
            asset_api.add_asset(
                name="Test Asset",
                domain_id=""
            )

    def test_add_asset_validates_domain_id_uuid(self, asset_api):
        """Test that domain_id must be a valid UUID."""
        with pytest.raises(ValueError, match="domain_id must be a valid UUID"):
            asset_api.add_asset(
                name="Test Asset",
                domain_id="not-a-uuid"
            )

    def test_add_asset_validates_id_uuid(self, asset_api):
        """Test that _id must be a valid UUID if provided."""
        with pytest.raises(ValueError, match="id must be a valid UUID"):
            asset_api.add_asset(
                name="Test Asset",
                domain_id="12345678-1234-1234-1234-123456789012",
                _id="not-a-uuid"
            )

    def test_add_asset_validates_type_id_uuid(self, asset_api):
        """Test that type_id must be a valid UUID if provided."""
        with pytest.raises(ValueError, match="type_id must be a valid UUID"):
            asset_api.add_asset(
                name="Test Asset",
                domain_id="12345678-1234-1234-1234-123456789012",
                type_id="not-a-uuid"
            )

    def test_add_asset_validates_excluded_from_auto_hyperlinking_type(self, asset_api):
        """Test that excluded_from_auto_hyperlinking must be boolean."""
        with pytest.raises(ValueError, match="excluded_from_auto_hyperlinking must be a boolean"):
            asset_api.add_asset(
                name="Test",
                domain_id="12345678-1234-1234-1234-123456789012",
                excluded_from_auto_hyperlinking="yes"
            )


class TestAssetGetAsset:
    """Tests for get_asset method."""

    def test_get_asset_success(self, asset_api):
        """Test successful asset retrieval."""
        with patch.object(asset_api, '_get') as mock_get:
            with patch.object(asset_api, '_handle_response') as mock_handle:
                mock_get.return_value = Mock()
                mock_handle.return_value = {
                    "id": "12345678-1234-1234-1234-123456789012",
                    "name": "Test Asset",
                    "type": {"id": "type-uuid", "name": "Table"},
                    "status": {"id": "status-uuid", "name": "Accepted"},
                    "domain": {"id": "domain-uuid", "name": "Physical Data"}
                }

                result = asset_api.get_asset("12345678-1234-1234-1234-123456789012")

                assert result.name == "Test Asset"
                assert result.id == "12345678-1234-1234-1234-123456789012"


class TestAssetRemoveAsset:
    """Tests for remove_asset method."""

    def test_remove_asset_requires_asset_id(self, asset_api):
        """Test that asset_id is required."""
        with pytest.raises(ValueError, match="asset_id is required"):
            asset_api.remove_asset("")

    def test_remove_asset_validates_uuid(self, asset_api):
        """Test that asset_id must be a valid UUID."""
        with pytest.raises(ValueError, match="asset_id must be a valid UUID"):
            asset_api.remove_asset("not-a-uuid")


class TestAssetFindAssets:
    """Tests for find_assets method."""

    def test_find_assets_default_params(self, asset_api):
        """Test find_assets with default parameters."""
        with patch.object(asset_api, '_get') as mock_get:
            with patch.object(asset_api, '_handle_response') as mock_handle:
                mock_get.return_value = Mock()
                mock_handle.return_value = {"results": [], "total": 0, "offset": 0, "limit": 1000}

                result = asset_api.find_assets()

                # Verify default limit is passed
                call_args = mock_get.call_args
                params = call_args.kwargs.get('params') or call_args[1].get('params')
                assert params["limit"] == 1000
                assert len(result) == 0

    def test_find_assets_with_filters(self, asset_api):
        """Test find_assets with filters."""
        with patch.object(asset_api, '_get') as mock_get:
            with patch.object(asset_api, '_handle_response') as mock_handle:
                mock_get.return_value = Mock()
                mock_handle.return_value = {"results": [], "total": 0}

                result = asset_api.find_assets(
                    community_id="12345678-1234-1234-1234-123456789012",
                    domain_id="87654321-4321-4321-4321-210987654321",
                    limit=500,
                    offset=100
                )

                call_args = mock_get.call_args
                params = call_args.kwargs.get('params') or call_args[1].get('params')
                assert params["communityId"] == "12345678-1234-1234-1234-123456789012"
                assert params["domainId"] == "87654321-4321-4321-4321-210987654321"
                assert params["limit"] == 500
                assert params["offset"] == 100

    def test_find_assets_validates_community_id_uuid(self, asset_api):
        """Test that community_id must be a valid UUID."""
        with pytest.raises(ValueError, match="community_id must be a valid UUID"):
            asset_api.find_assets(community_id="not-a-uuid")


class TestAssetTags:
    """Tests for tag methods."""

    def test_add_tags_success(self, asset_api):
        """Test adding tags successfully."""
        with patch.object(asset_api, '_post') as mock_post:
            with patch.object(asset_api, '_handle_response') as mock_handle:
                mock_post.return_value = Mock()
                mock_handle.return_value = {"id": "asset-id", "tags": ["tag1", "tag2"]}

                result = asset_api.add_tags("asset-id", ["tag1", "tag2"])

                assert "tags" in result
                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                assert kwargs['url'].endswith("/asset-id/tags")
                assert kwargs['data'] == {"tagNames": ["tag1", "tag2"]}

    def test_remove_tags_success(self, asset_api):
        """Test removing tags successfully."""
        with patch('requests.delete') as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "{}"
            mock_delete.return_value = mock_response
            
            with patch.object(asset_api, '_handle_response') as mock_handle:
                mock_handle.return_value = {}
                
                asset_api.remove_tags("asset-id", ["tag1"])
                
                mock_delete.assert_called_once()
                args, kwargs = mock_delete.call_args
                assert args[0].endswith("/asset-id/tags")
                assert kwargs['json'] == ["tag1"]


class TestAssetAttachments:
    """Tests for attachment methods."""

    def test_add_attachment_success(self, asset_api):
        """Test adding attachment successfully."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                with patch('requests.post') as mock_post:
                    mock_response = Mock()
                    mock_response.status_code = 201
                    mock_response.text = '{"id": "file-id"}'
                    mock_response.json.return_value = {"id": "file-id"}
                    mock_post.return_value = mock_response
                    
                    result = asset_api.add_attachment("asset-id", "/path/to/file.txt")
                    
                    assert result == {"id": "file-id"}
                    mock_post.assert_called_once()
                    args, kwargs = mock_post.call_args
                    assert 'files' in kwargs
                    assert kwargs['files']['file'][0] == 'file.txt'

    def test_get_attachments_success(self, asset_api):
        """Test getting attachments successfully."""
        with patch.object(asset_api, '_get') as mock_get:
            with patch.object(asset_api, '_handle_response') as mock_handle:
                mock_get.return_value = Mock()
                mock_handle.return_value = {"results": [{"id": "att-1"}]}

                result = asset_api.get_attachments("asset-id")
                
                assert len(result) == 1
                assert result[0]["id"] == "att-1"

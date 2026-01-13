"""Tests for Search API."""
import pytest
from unittest.mock import Mock, patch
from collibra_connector import CollibraConnector


@pytest.fixture
def connector():
    return CollibraConnector("https://test.collibra.com", "user", "pass")


@pytest.fixture
def search_api(connector):
    return connector.search


class TestSearch:
    def test_find_basic(self, search_api):
        """Test basic search query."""
        with patch.object(search_api, '_post') as mock_post:
            with patch.object(search_api, '_handle_response') as mock_handle:
                mock_handle.return_value = {"results": []}
                
                search_api.find("test query")
                
                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                data = kwargs['data']
                assert data['keywords'] == "test query"
                assert data['limit'] == 10
                assert data['offset'] == 0

    def test_find_assets_helper(self, search_api):
        """Test find_assets helper method."""
        with patch.object(search_api, 'find') as mock_find:
            mock_find.return_value = {}
            
            search_api.find_assets(
                "query",
                type_ids=["type1"],
                domain_ids=["dom1"]
            )
            
            mock_find.assert_called_once()
            args, kwargs = mock_find.call_args
            assert kwargs['query'] == "query"
            assert kwargs['filter_options'] == {
                "category": "ASSET",
                "typeIds": ["type1"],
                "domainIds": ["dom1"]
            }

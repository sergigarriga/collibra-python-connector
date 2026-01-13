"""Tests for the Mocking Engine."""
import pytest
from collibra_connector.testing import (
    MockCollibraConnector,
    MockDataStore,
    mock_collibra_context,
    CollibraTestCase,
    generate_uuid,
)
from collibra_connector.models import AssetModel, DomainModel


class TestMockCollibraConnector:
    """Tests for MockCollibraConnector."""

    def test_init(self):
        """Test initialization of mock connector."""
        mock = MockCollibraConnector()
        assert mock.get_version() == "1.2.0-mock"
        assert mock.asset is not None

    def test_context_manager(self):
        with MockCollibraConnector() as mock:
            assert mock.test_connection() is True

    def test_asset_get_returns_model(self):
        mock = MockCollibraConnector()
        asset = mock.asset.get_asset("any-uuid")
        assert isinstance(asset, AssetModel)
        assert asset.id is not None
        assert asset.name is not None

    def test_asset_add_mock_and_get(self):
        mock = MockCollibraConnector()
        mock.asset.add_mock_asset({
            "id": "custom-id",
            "name": "Custom Asset",
            "type": {"id": "t1", "name": "Business Term"}
        })

        asset = mock.asset.get_asset("custom-id")
        assert asset.name == "Custom Asset"

    def test_asset_find_returns_list(self):
        mock = MockCollibraConnector()
        mock.asset.add_mock_asset({"id": "a1", "name": "Asset 1"})
        mock.asset.add_mock_asset({"id": "a2", "name": "Asset 2"})

        results = mock.asset.find_assets(limit=10)
        assert len(results) >= 2

    def test_asset_add_and_change(self):
        mock = MockCollibraConnector()
        created = mock.asset.add_asset(
            name="New Asset",
            domain_id="domain-1"
        )
        assert created.name == "New Asset"

        updated = mock.asset.change_asset(
            asset_id=created.id,
            name="Updated Asset"
        )
        assert updated.name == "Updated Asset"

    def test_asset_remove(self):
        mock = MockCollibraConnector()
        mock.asset.add_mock_asset({"id": "to-delete", "name": "Delete Me"})
        mock.asset.remove_asset("to-delete")
        # Should return default mock, not the deleted one
        asset = mock.asset.get_asset("to-delete")
        assert asset.name != "Delete Me"

    def test_domain_operations(self):
        mock = MockCollibraConnector()
        domain = mock.domain.get_domain("any-uuid")
        assert isinstance(domain, DomainModel)

    def test_community_operations(self):
        mock = MockCollibraConnector()
        communities = mock.community.find_communities(limit=10)
        assert len(communities) > 0

    def test_attribute_operations(self):
        mock = MockCollibraConnector()
        attrs = mock.attribute.get_attributes_as_dict("any-asset")
        assert "Description" in attrs
        assert "Definition" in attrs

    def test_relation_operations(self):
        mock = MockCollibraConnector()
        relation = mock.relation.add_relation(
            source_id="source-1",
            target_id="target-1",
            type_id="type-1"
        )
        assert relation.source.id == "source-1"
        assert relation.target.id == "target-1"

    def test_search_operations(self):
        mock = MockCollibraConnector()
        mock.asset.add_mock_asset({"id": "s1", "name": "Searchable Asset"})

        results = mock.search.find("Searchable")
        assert len(results) > 0

    def test_metadata_operations(self):
        mock = MockCollibraConnector()
        types = mock.metadata.get_asset_types()
        assert "results" in types
        assert len(types["results"]) > 0

    def test_responsibility_operations(self):
        mock = MockCollibraConnector()
        resps = mock.responsibility.get_asset_responsibilities("any-asset")
        assert len(resps) > 0
        assert "role" in resps[0]
        assert "owner" in resps[0]

    def test_full_profile(self):
        mock = MockCollibraConnector()
        profile = mock.asset.get_full_profile("any-uuid")
        assert profile.asset is not None
        assert profile.attributes is not None
        assert "Description" in profile.attributes

    def test_clear_all_data(self):
        mock = MockCollibraConnector()
        mock.asset.add_mock_asset({"id": "a1", "name": "Asset 1"})
        mock.clear_all_data()

        # Store should be empty
        results = mock.asset.find_assets(limit=10)
        # Will get default mock data since store is empty
        for asset in results:
            assert asset.name != "Asset 1"


class TestMockCollibraContext:
    """Tests for mock_collibra_context."""

    def test_context_manager(self):
        with mock_collibra_context() as mock:
            assert mock.test_connection() is True
            asset = mock.asset.get_asset("uuid")
            assert asset is not None

    def test_context_with_custom_data(self):
        custom = {
            "assets": [
                {"id": "custom-1", "name": "Custom Asset"}
            ]
        }
        with mock_collibra_context(custom_data=custom) as mock:
            asset = mock.asset.get_asset("custom-1")
            assert asset.name == "Custom Asset"


class TestCollibraTestCase:
    """Tests for CollibraTestCase base class."""

    def test_setup_creates_connector(self):
        tc = CollibraTestCase()
        tc.setUp()
        assert tc.connector is not None
        assert tc.connector.test_connection() is True

    def test_add_test_asset(self):
        tc = CollibraTestCase()
        tc.setUp()

        asset_id = tc.add_test_asset(name="Test Asset")
        assert asset_id is not None

        asset = tc.connector.asset.get_asset(asset_id)
        assert asset.name == "Test Asset"

    def test_add_test_domain(self):
        tc = CollibraTestCase()
        tc.setUp()

        domain_id = tc.add_test_domain(name="Test Domain")
        assert domain_id is not None

        domain = tc.connector.domain.get_domain(domain_id)
        assert domain.name == "Test Domain"

    def test_teardown_clears_data(self):
        tc = CollibraTestCase()
        tc.setUp()
        tc.add_test_asset(name="Asset to Clear")
        tc.tearDown()
        # Data should be cleared


class TestMockDataStore:
    """Tests for MockDataStore."""

    def test_clear(self):
        store = MockDataStore()
        store.assets["a1"] = {"id": "a1", "name": "Asset"}
        store.domains["d1"] = {"id": "d1", "name": "Domain"}

        store.clear()

        assert len(store.assets) == 0
        assert len(store.domains) == 0


class TestGenerateUuid:
    """Tests for generate_uuid helper."""

    def test_generates_valid_uuid(self):
        uuid = generate_uuid()
        assert uuid is not None
        assert len(uuid) == 36  # UUID format: 8-4-4-4-12
        assert uuid.count("-") == 4

"""Tests for Pydantic Models."""
import pytest
from collibra_connector.models import (
    AssetModel,
    DomainModel,
    CommunityModel,
    UserModel,
    AttributeModel,
    RelationModel,
    ResourceReference,
    PaginatedResponseModel,
    AssetProfileModel,
    RelationsGrouped,
    ResponsibilitySummary,
    SearchResultModel,
    parse_asset,
    parse_assets,
    parse_domain,
    parse_community,
    parse_user,
)


class TestResourceReference:
    """Tests for ResourceReference model."""

    def test_create_from_dict(self):
        data = {"id": "123", "resourceType": "Asset", "name": "Test"}
        ref = ResourceReference.model_validate(data)
        assert ref.id == "123"
        assert ref.resource_type == "Asset"
        assert ref.name == "Test"

    def test_string_representation(self):
        ref = ResourceReference(id="123", name="Test Asset")
        assert str(ref) == "Test Asset"

    def test_string_representation_no_name(self):
        ref = ResourceReference(id="123")
        assert str(ref) == "123"


class TestAssetModel:
    """Tests for AssetModel."""

    def test_create_from_dict(self):
        data = {
            "id": "asset-123",
            "resourceType": "Asset",
            "name": "Test Asset",
            "displayName": "Test Display",
            "type": {"id": "type-1", "resourceType": "AssetType", "name": "Business Term"},
            "status": {"id": "status-1", "resourceType": "Status", "name": "Approved"},
            "domain": {"id": "domain-1", "resourceType": "Domain", "name": "Glossary"},
            "avgRating": 4.5,
            "ratingsCount": 10,
            "createdOn": 1704067200000,
            "lastModifiedOn": 1704153600000,
        }
        asset = AssetModel.model_validate(data)

        assert asset.id == "asset-123"
        assert asset.name == "Test Asset"
        assert asset.display_name == "Test Display"
        assert asset.type.name == "Business Term"
        assert asset.status.name == "Approved"
        assert asset.domain.name == "Glossary"
        assert asset.avg_rating == 4.5
        assert asset.ratings_count == 10

    def test_effective_name(self):
        asset = AssetModel(
            id="1",
            name="Name",
            display_name="Display Name",
            type=ResourceReference(id="t1", name="Type"),
            status=ResourceReference(id="s1", name="Status"),
            domain=ResourceReference(id="d1", name="Domain"),
        )
        assert asset.effective_name == "Display Name"

    def test_effective_name_no_display(self):
        asset = AssetModel(
            id="1",
            name="Name",
            type=ResourceReference(id="t1", name="Type"),
            status=ResourceReference(id="s1", name="Status"),
            domain=ResourceReference(id="d1", name="Domain"),
        )
        assert asset.effective_name == "Name"

    def test_convenience_properties(self):
        asset = AssetModel(
            id="1",
            name="Name",
            type=ResourceReference(id="t1", name="Business Term"),
            status=ResourceReference(id="s1", name="Approved"),
            domain=ResourceReference(id="d1", name="Glossary"),
        )
        assert asset.type_name == "Business Term"
        assert asset.status_name == "Approved"
        assert asset.domain_name == "Glossary"

    def test_has_rating(self):
        asset = AssetModel(
            id="1",
            name="Name",
            type=ResourceReference(id="t1", name="Type"),
            status=ResourceReference(id="s1", name="Status"),
            domain=ResourceReference(id="d1", name="Domain"),
            ratings_count=5,
        )
        assert asset.has_rating is True

        asset2 = AssetModel(
            id="1",
            name="Name",
            type=ResourceReference(id="t1", name="Type"),
            status=ResourceReference(id="s1", name="Status"),
            domain=ResourceReference(id="d1", name="Domain"),
            ratings_count=0,
        )
        assert asset2.has_rating is False

    def test_to_dict(self):
        asset = AssetModel(
            id="1",
            name="Name",
            type=ResourceReference(id="t1", name="Type"),
            status=ResourceReference(id="s1", name="Status"),
            domain=ResourceReference(id="d1", name="Domain"),
        )
        d = asset.to_dict()
        assert d["id"] == "1"
        assert d["name"] == "Name"

    def test_created_datetime(self):
        asset = AssetModel(
            id="1",
            name="Name",
            type=ResourceReference(id="t1", name="Type"),
            status=ResourceReference(id="s1", name="Status"),
            domain=ResourceReference(id="d1", name="Domain"),
            created_on=1704067200000,
        )
        dt = asset.created_datetime
        assert dt is not None
        assert dt.year == 2024


class TestUserModel:
    """Tests for UserModel."""

    def test_full_name(self):
        user = UserModel(
            id="u1",
            name="jdoe",
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"

    def test_full_name_partial(self):
        user = UserModel(id="u1", name="jdoe", first_name="John")
        assert user.full_name == "John"

    def test_is_active(self):
        user = UserModel(id="u1", name="jdoe", activated=True, enabled=True)
        assert user.is_active is True

        user2 = UserModel(id="u1", name="jdoe", activated=True, enabled=False)
        assert user2.is_active is False


class TestPaginatedResponseModel:
    """Tests for PaginatedResponseModel."""

    def test_iteration(self):
        assets = [
            AssetModel(
                id=f"a{i}",
                name=f"Asset {i}",
                type=ResourceReference(id="t1", name="Type"),
                status=ResourceReference(id="s1", name="Status"),
                domain=ResourceReference(id="d1", name="Domain"),
            )
            for i in range(3)
        ]
        paginated = PaginatedResponseModel[AssetModel](
            results=assets, total=10, offset=0, limit=3
        )

        names = [a.name for a in paginated]
        assert names == ["Asset 0", "Asset 1", "Asset 2"]

    def test_has_more(self):
        paginated = PaginatedResponseModel[AssetModel](
            results=[], total=10, offset=0, limit=3
        )
        assert paginated.has_more is True

        paginated2 = PaginatedResponseModel[AssetModel](
            results=[], total=3, offset=0, limit=3
        )
        assert paginated2.has_more is False

    def test_next_offset(self):
        assets = [
            AssetModel(
                id="a1",
                name="Asset",
                type=ResourceReference(id="t1", name="Type"),
                status=ResourceReference(id="s1", name="Status"),
                domain=ResourceReference(id="d1", name="Domain"),
            )
        ] * 3
        paginated = PaginatedResponseModel[AssetModel](
            results=assets, total=10, offset=0, limit=3
        )
        assert paginated.next_offset == 3

    def test_page_count(self):
        paginated = PaginatedResponseModel[AssetModel](
            results=[], total=25, offset=0, limit=10
        )
        assert paginated.page_count == 3

    def test_current_page(self):
        paginated = PaginatedResponseModel[AssetModel](
            results=[], total=25, offset=10, limit=10
        )
        assert paginated.current_page == 2

    def test_len(self):
        assets = [
            AssetModel(
                id="a1",
                name="Asset",
                type=ResourceReference(id="t1", name="Type"),
                status=ResourceReference(id="s1", name="Status"),
                domain=ResourceReference(id="d1", name="Domain"),
            )
        ] * 5
        paginated = PaginatedResponseModel[AssetModel](
            results=assets, total=100, offset=0, limit=5
        )
        assert len(paginated) == 5

    def test_bool(self):
        paginated = PaginatedResponseModel[AssetModel](
            results=[], total=0, offset=0, limit=10
        )
        assert bool(paginated) is False

        assets = [
            AssetModel(
                id="a1",
                name="Asset",
                type=ResourceReference(id="t1", name="Type"),
                status=ResourceReference(id="s1", name="Status"),
                domain=ResourceReference(id="d1", name="Domain"),
            )
        ]
        paginated2 = PaginatedResponseModel[AssetModel](
            results=assets, total=1, offset=0, limit=10
        )
        assert bool(paginated2) is True


class TestParseAsset:
    """Tests for parse_asset function."""

    def test_parse_single_asset(self):
        data = {
            "id": "asset-123",
            "name": "Test Asset",
            "type": {"id": "t1", "name": "Business Term"},
            "status": {"id": "s1", "name": "Approved"},
            "domain": {"id": "d1", "name": "Glossary"},
        }
        asset = parse_asset(data)
        assert isinstance(asset, AssetModel)
        assert asset.name == "Test Asset"

    def test_parse_assets_list(self):
        data = {
            "results": [
                {
                    "id": f"a{i}",
                    "name": f"Asset {i}",
                    "type": {"id": "t1", "name": "Type"},
                    "status": {"id": "s1", "name": "Status"},
                    "domain": {"id": "d1", "name": "Domain"},
                }
                for i in range(3)
            ],
            "total": 10,
            "offset": 0,
            "limit": 3,
        }
        result = parse_assets(data)
        assert isinstance(result, PaginatedResponseModel)
        assert len(result) == 3
        assert result.total == 10


class TestAssetProfileModel:
    """Tests for AssetProfileModel."""

    def test_create_profile(self):
        asset = AssetModel(
            id="1",
            name="Test Asset",
            type=ResourceReference(id="t1", name="Business Term"),
            status=ResourceReference(id="s1", name="Approved"),
            domain=ResourceReference(id="d1", name="Glossary"),
        )
        profile = AssetProfileModel(
            asset=asset,
            attributes={"Description": "Test description"},
            relations=RelationsGrouped(),
            responsibilities=[
                ResponsibilitySummary(role="Data Steward", owner="John Doe")
            ],
        )

        assert profile.description == "Test description"
        assert profile.data_steward == "John Doe"

    def test_data_steward_not_found(self):
        asset = AssetModel(
            id="1",
            name="Test Asset",
            type=ResourceReference(id="t1", name="Type"),
            status=ResourceReference(id="s1", name="Status"),
            domain=ResourceReference(id="d1", name="Domain"),
        )
        profile = AssetProfileModel(
            asset=asset,
            attributes={},
            relations=RelationsGrouped(),
            responsibilities=[
                ResponsibilitySummary(role="Technical Owner", owner="Jane Doe")
            ],
        )

        assert profile.data_steward is None


class TestSearchResultModel:
    """Tests for SearchResultModel."""

    def test_search_result_model_parsing(self):
        """Test parsing JSON into SearchResultModel."""
        data = {
            "resource": {
                "id": "uuid-s",
                "resourceType": "Asset",
                "name": "Search Result",
                "displayName": "Display Search"
            },
            "score": 1.5,
            "highlights": [{"field": "name", "values": ["Search"]}]
        }

        result = SearchResultModel.model_validate(data)
        assert result.resource.id == "uuid-s"
        assert result.resource.name == "Search Result"
        assert result.score == 1.5
        assert result.id == "uuid-s"
        assert result.name == "Display Search"


class TestDomainModel:
    """Tests for DomainModel."""

    def test_domain_model_parsing(self):
        """Test parsing JSON into DomainModel."""
        data = {
            "id": "dom-1",
            "resourceType": "Domain",
            "name": "Test Domain",
            "type": {"id": "type-d", "resourceType": "DomainType", "name": "Glossary"},
            "community": {"id": "comm-1", "resourceType": "Community", "name": "Comm 1"},
            "excludedFromAutoHyperlinking": True
        }

        domain = DomainModel.model_validate(data)

        assert domain.name == "Test Domain"
        assert domain.community.name == "Comm 1"
        assert domain.excluded_from_auto_hyperlinking is True


class TestCommunityModel:
    """Tests for CommunityModel."""

    def test_is_root(self):
        comm = CommunityModel(id="c1", name="Root Community")
        assert comm.is_root() is True

        comm2 = CommunityModel(
            id="c2",
            name="Child Community",
            parent=ResourceReference(id="c1", name="Root")
        )
        assert comm2.is_root() is False

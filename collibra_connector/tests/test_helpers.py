"""Tests for helper utilities."""
import pytest
from unittest.mock import Mock, MagicMock
import time

from collibra_connector import (
    Paginator,
    PaginatedResponse,
    BatchProcessor,
    BatchResult,
    DataTransformer,
    timed_cache,
)


class TestPaginatedResponse:
    """Tests for PaginatedResponse dataclass."""

    def test_from_response(self):
        """Test creating PaginatedResponse from API response."""
        response = {
            "results": [{"id": "1"}, {"id": "2"}],
            "total": 100,
            "offset": 0,
            "limit": 10,
            "nextCursor": "abc123"
        }

        page = PaginatedResponse.from_response(response)

        assert len(page.results) == 2
        assert page.total == 100
        assert page.offset == 0
        assert page.limit == 10
        assert page.next_cursor == "abc123"

    def test_has_more_with_cursor(self):
        """Test has_more with cursor pagination."""
        page = PaginatedResponse(
            results=[{"id": "1"}],
            total=100,
            next_cursor="abc"
        )
        assert page.has_more() is True

        page_no_cursor = PaginatedResponse(
            results=[{"id": "1"}],
            total=100,
            next_cursor=None
        )
        assert page_no_cursor.has_more() is True  # Still has more based on total

    def test_has_more_with_offset(self):
        """Test has_more with offset pagination."""
        # Has more
        page = PaginatedResponse(
            results=[{"id": "1"}, {"id": "2"}],
            total=100,
            offset=0
        )
        assert page.has_more() is True

        # No more
        page_end = PaginatedResponse(
            results=[{"id": "1"}],
            total=3,
            offset=2
        )
        assert page_end.has_more() is False

    def test_len(self):
        """Test __len__ returns result count."""
        page = PaginatedResponse(
            results=[{"id": "1"}, {"id": "2"}, {"id": "3"}],
            total=100
        )
        assert len(page) == 3

    def test_iter(self):
        """Test iteration over results."""
        results = [{"id": "1"}, {"id": "2"}]
        page = PaginatedResponse(results=results, total=2)

        iterated = list(page)
        assert iterated == results


class TestPaginator:
    """Tests for Paginator class."""

    def test_items_iteration(self):
        """Test iterating over items."""
        def mock_fetch(limit=10, offset=0):
            if offset >= 25:
                return {"results": [], "total": 25}
            items = [{"id": str(i)} for i in range(offset, min(offset + limit, 25))]
            return {"results": items, "total": 25}

        paginator = Paginator(mock_fetch, limit=10)
        items = list(paginator.items())

        assert len(items) == 25
        assert paginator.total_fetched == 25

    def test_pages_iteration(self):
        """Test iterating over pages."""
        def mock_fetch(limit=10, offset=0):
            if offset >= 25:
                return {"results": [], "total": 25}
            items = [{"id": str(i)} for i in range(offset, min(offset + limit, 25))]
            return {"results": items, "total": 25}

        paginator = Paginator(mock_fetch, limit=10)
        pages = list(paginator.pages())

        assert len(pages) == 3  # 10 + 10 + 5
        assert len(pages[0]) == 10
        assert len(pages[1]) == 10
        assert len(pages[2]) == 5

    def test_max_items_limit(self):
        """Test max_items parameter."""
        def mock_fetch(limit=10, offset=0):
            items = [{"id": str(i)} for i in range(offset, offset + limit)]
            return {"results": items, "total": 1000}

        paginator = Paginator(mock_fetch, limit=10, max_items=25)
        items = list(paginator.items())

        assert len(items) == 25
        assert paginator.total_fetched == 25

    def test_collect(self):
        """Test collect method."""
        def mock_fetch(limit=10, offset=0):
            if offset >= 15:
                return {"results": [], "total": 15}
            items = [{"id": str(i)} for i in range(offset, min(offset + limit, 15))]
            return {"results": items, "total": 15}

        paginator = Paginator(mock_fetch, limit=10)
        all_items = paginator.collect()

        assert len(all_items) == 15

    def test_with_kwargs(self):
        """Test passing additional kwargs to fetch function."""
        def mock_fetch(limit=10, offset=0, community_id=None):
            assert community_id == "test-uuid"
            return {"results": [{"id": "1"}], "total": 1}

        paginator = Paginator(mock_fetch, limit=10, community_id="test-uuid")
        list(paginator.items())


class TestBatchProcessor:
    """Tests for BatchProcessor class."""

    def test_process_all_success(self):
        """Test batch processing with all successes."""
        mock_operation = Mock(return_value={"id": "created"})

        processor = BatchProcessor(batch_size=2, delay=0)
        items = [{"name": f"item{i}"} for i in range(5)]

        result = processor.process(
            items=items,
            operation=mock_operation,
            item_mapper=lambda x: x
        )

        assert result.success_count == 5
        assert result.error_count == 0
        assert result.success_rate == 100.0
        assert mock_operation.call_count == 5

    def test_process_with_errors(self):
        """Test batch processing with some errors."""
        def mock_operation(**kwargs):
            if "error" in kwargs.get("name", ""):
                raise ValueError("Test error")
            return {"id": "created"}

        processor = BatchProcessor(batch_size=2, delay=0, on_error="continue")
        items = [
            {"name": "item1"},
            {"name": "error_item"},
            {"name": "item3"}
        ]

        result = processor.process(
            items=items,
            operation=mock_operation,
            item_mapper=lambda x: x
        )

        assert result.success_count == 2
        assert result.error_count == 1
        assert result.total_count == 3

    def test_process_stop_on_error(self):
        """Test batch processing stops on error when configured."""
        call_count = 0

        def mock_operation(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Stop here")
            return {"id": "created"}

        processor = BatchProcessor(batch_size=10, delay=0, on_error="stop")
        items = [{"name": f"item{i}"} for i in range(5)]

        result = processor.process(
            items=items,
            operation=mock_operation,
            item_mapper=lambda x: x
        )

        assert result.success_count == 1
        assert result.error_count == 1
        assert call_count == 2

    def test_progress_callback(self):
        """Test progress callback is called."""
        mock_operation = Mock(return_value={"id": "created"})
        progress_calls = []

        def progress_callback(done, total):
            progress_calls.append((done, total))

        processor = BatchProcessor(batch_size=10, delay=0)
        items = [{"name": f"item{i}"} for i in range(3)]

        processor.process(
            items=items,
            operation=mock_operation,
            item_mapper=lambda x: x,
            progress_callback=progress_callback
        )

        assert progress_calls == [(1, 3), (2, 3), (3, 3)]


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_add_success(self):
        """Test adding successful results."""
        result = BatchResult()
        result.add_success({"name": "item1"}, {"id": "1"})
        result.add_success({"name": "item2"}, {"id": "2"})

        assert result.success_count == 2
        assert result.error_count == 0

    def test_add_error(self):
        """Test adding error results."""
        result = BatchResult()
        result.add_error({"name": "item1"}, ValueError("test"))

        assert result.success_count == 0
        assert result.error_count == 1

    def test_success_rate(self):
        """Test success rate calculation."""
        result = BatchResult()
        result.add_success({}, {})
        result.add_success({}, {})
        result.add_error({}, ValueError())

        assert result.success_rate == pytest.approx(66.67, rel=0.1)

    def test_success_rate_empty(self):
        """Test success rate with no operations."""
        result = BatchResult()
        assert result.success_rate == 0.0

    def test_repr(self):
        """Test string representation."""
        result = BatchResult()
        result.add_success({}, {})
        result.add_error({}, ValueError())

        assert repr(result) == "BatchResult(successes=1, errors=1)"


class TestDataTransformer:
    """Tests for DataTransformer class."""

    def test_flatten_asset(self):
        """Test flattening nested asset structure."""
        asset = {
            "id": "123",
            "name": "Test Asset",
            "type": {
                "id": "type-123",
                "name": "Business Term"
            },
            "domain": {
                "id": "domain-123",
                "community": {
                    "id": "comm-123"
                }
            }
        }

        flat = DataTransformer.flatten_asset(asset)

        assert flat["id"] == "123"
        assert flat["name"] == "Test Asset"
        assert flat["type.id"] == "type-123"
        assert flat["type.name"] == "Business Term"
        assert flat["domain.id"] == "domain-123"
        assert flat["domain.community.id"] == "comm-123"

    def test_extract_ids(self):
        """Test extracting IDs from items."""
        items = [
            {"id": "1", "name": "a"},
            {"id": "2", "name": "b"},
            {"name": "c"},  # No id
        ]

        ids = DataTransformer.extract_ids(items)

        assert ids == ["1", "2"]

    def test_extract_ids_custom_key(self):
        """Test extracting custom field."""
        items = [
            {"uuid": "1", "name": "a"},
            {"uuid": "2", "name": "b"},
        ]

        ids = DataTransformer.extract_ids(items, key="uuid")

        assert ids == ["1", "2"]

    def test_group_by(self):
        """Test grouping items by field."""
        items = [
            {"type": "A", "name": "item1"},
            {"type": "B", "name": "item2"},
            {"type": "A", "name": "item3"},
        ]

        grouped = DataTransformer.group_by(items, "type")

        assert len(grouped["A"]) == 2
        assert len(grouped["B"]) == 1

    def test_to_name_id_map(self):
        """Test creating name->id mapping."""
        items = [
            {"name": "Item A", "id": "1"},
            {"name": "Item B", "id": "2"},
            {"id": "3"},  # No name
        ]

        mapping = DataTransformer.to_name_id_map(items)

        assert mapping == {"Item A": "1", "Item B": "2"}


class TestTimedCache:
    """Tests for timed_cache decorator."""

    def test_caches_result(self):
        """Test that results are cached."""
        call_count = 0

        @timed_cache(ttl_seconds=60)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_func(5)
        # Second call (should be cached)
        result2 = expensive_func(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1

    def test_different_args_not_cached(self):
        """Test that different arguments are cached separately."""
        call_count = 0

        @timed_cache(ttl_seconds=60)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        expensive_func(5)
        expensive_func(10)

        assert call_count == 2

    def test_clear_cache(self):
        """Test clearing the cache."""
        call_count = 0

        @timed_cache(ttl_seconds=60)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        expensive_func(5)
        expensive_func.clear_cache()
        expensive_func(5)

        assert call_count == 2

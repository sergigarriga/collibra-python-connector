"""Tests for the Lineage Builder."""
import pytest
from collibra_connector.lineage import (
    LineageBuilder,
    LineageNode,
    LineageEdge,
    LineageCommitResult,
    LineageDirection,
    LineageRelationType,
)
from collibra_connector.testing import MockCollibraConnector


class TestLineageNode:
    """Tests for LineageNode."""

    def test_create_basic_node(self):
        node = LineageNode(name="Test Node", asset_type="Table")
        assert node.name == "Test Node"
        assert node.asset_type == "Table"
        assert node.asset_id is None

    def test_create_node_with_existing_id(self):
        node = LineageNode.from_id("existing-uuid", name="Existing")
        assert node.asset_id == "existing-uuid"

    def test_table_factory(self):
        node = LineageNode.table("orders", schema="public", database="postgres")
        assert node.name == "postgres.public.orders"
        assert node.asset_type == "Table"

    def test_column_factory(self):
        node = LineageNode.column("id", table="orders")
        assert node.name == "orders.id"
        assert node.asset_type == "Column"

    def test_pipeline_factory(self):
        node = LineageNode.pipeline("etl_job")
        assert node.name == "etl_job"
        assert node.asset_type == "Data Pipeline"

    def test_report_factory(self):
        node = LineageNode.report("Sales Report")
        assert node.asset_type == "Report"

    def test_dashboard_factory(self):
        node = LineageNode.dashboard("Analytics Dashboard")
        assert node.asset_type == "Dashboard"

    def test_node_with_attributes(self):
        node = LineageNode(
            name="Table",
            asset_type="Table",
            description="Test table",
            attributes={"Data Source": "S3"}
        )
        assert node.description == "Test table"
        assert node.attributes["Data Source"] == "S3"

    def test_node_equality(self):
        node1 = LineageNode(name="Table", asset_type="Table")
        node2 = LineageNode(name="Table", asset_type="Table")
        # Different nodes even with same name (different internal ID)
        assert node1 != node2

    def test_node_hashable(self):
        node = LineageNode(name="Table", asset_type="Table")
        node_set = {node}
        assert len(node_set) == 1


class TestLineageEdge:
    """Tests for LineageEdge."""

    def test_create_edge(self):
        source = LineageNode(name="Source", asset_type="Table")
        target = LineageNode(name="Target", asset_type="Table")
        edge = LineageEdge(source=source, target=target, relation_type="is source for")

        assert edge.source == source
        assert edge.target == target
        assert edge.relation_type == "is source for"


class TestLineageBuilder:
    """Tests for LineageBuilder."""

    def test_init(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)
        assert builder.connector == mock

    def test_add_node(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)
        node = LineageNode(name="Test", asset_type="Table")

        builder.add_node(node)

        assert len(builder.get_nodes()) == 1

    def test_add_edge(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        source = LineageNode.table("source")
        target = LineageNode.table("target")

        builder.add_edge(source, target, "is source for")

        nodes = builder.get_nodes()
        edges = builder.get_edges()

        assert len(nodes) == 2
        assert len(edges) == 1
        assert edges[0].source == source
        assert edges[0].target == target

    def test_add_edges_batch(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        a = LineageNode.table("a")
        b = LineageNode.table("b")
        c = LineageNode.table("c")

        builder.add_edges([
            (a, b, "is source for"),
            (b, c, "is source for"),
        ])

        assert len(builder.get_edges()) == 2

    def test_fluent_source_to(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        source = LineageNode.table("source")
        target = LineageNode.table("target")

        builder.source(source).to(target)

        assert len(builder.get_edges()) == 1

    def test_fluent_source_through_to(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        source = LineageNode.table("source")
        etl = LineageNode.pipeline("etl")
        target = LineageNode.table("target")

        builder.source(source).through(etl).to(target)

        edges = builder.get_edges()
        assert len(edges) == 2
        assert edges[0].source == source
        assert edges[0].target == etl
        assert edges[1].source == etl
        assert edges[1].target == target

    def test_chain(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        a = LineageNode.table("a")
        b = LineageNode.pipeline("b")
        c = LineageNode.table("c")
        d = LineageNode.report("d")

        builder.chain(a, b, c, d)

        assert len(builder.get_edges()) == 3

    def test_fan_in(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        sources = [LineageNode.table(f"src{i}") for i in range(3)]
        target = LineageNode.pipeline("etl")

        builder.fan_in(sources, target)

        edges = builder.get_edges()
        assert len(edges) == 3
        for edge in edges:
            assert edge.target == target

    def test_fan_out(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        source = LineageNode.pipeline("etl")
        targets = [LineageNode.table(f"tgt{i}") for i in range(3)]

        builder.fan_out(source, targets)

        edges = builder.get_edges()
        assert len(edges) == 3
        for edge in edges:
            assert edge.source == source

    def test_clear(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        builder.add_edge(
            LineageNode.table("a"),
            LineageNode.table("b")
        )
        builder.clear()

        assert len(builder.get_nodes()) == 0
        assert len(builder.get_edges()) == 0

    def test_to_dict(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        source = LineageNode.table("source")
        target = LineageNode.table("target")
        builder.add_edge(source, target)

        data = builder.to_dict()

        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_from_dict(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        data = {
            "nodes": [
                {"id": "n1", "name": "Node 1", "asset_type": "Table"},
                {"id": "n2", "name": "Node 2", "asset_type": "Table"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "relation_type": "is source for"}
            ]
        }

        builder.from_dict(data)

        assert len(builder.get_nodes()) == 2
        assert len(builder.get_edges()) == 1

    def test_visualize(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        source = LineageNode.table("source")
        target = LineageNode.table("target")
        builder.add_edge(source, target)

        viz = builder.visualize()

        assert "Lineage Graph" in viz
        assert "source" in viz
        assert "target" in viz

    def test_dry_run_commit(self):
        mock = MockCollibraConnector()
        builder = LineageBuilder(mock)

        source = LineageNode.table("source")
        target = LineageNode.table("target")
        builder.add_edge(source, target)

        result = builder.commit(domain_id="test-domain", dry_run=True)

        assert result.assets_created == 2
        assert result.relations_created == 1


class TestLineageCommitResult:
    """Tests for LineageCommitResult."""

    def test_default_values(self):
        result = LineageCommitResult()
        assert result.success is True
        assert result.assets_created == 0
        assert result.relations_created == 0
        assert len(result.errors) == 0

    def test_with_values(self):
        result = LineageCommitResult(
            success=True,
            assets_created=5,
            relations_created=3,
            assets={"n1": "a1", "n2": "a2"},
            relations=["r1", "r2"],
        )
        assert result.assets_created == 5
        assert len(result.assets) == 2
        assert len(result.relations) == 2


class TestLineageEnums:
    """Tests for lineage enums."""

    def test_direction_enum(self):
        assert LineageDirection.UPSTREAM == "upstream"
        assert LineageDirection.DOWNSTREAM == "downstream"
        assert LineageDirection.BIDIRECTIONAL == "bidirectional"

    def test_relation_type_enum(self):
        assert LineageRelationType.SOURCE_FOR == "is source for"
        assert LineageRelationType.TARGET_FOR == "is target for"
        assert LineageRelationType.TRANSFORMS == "transforms"

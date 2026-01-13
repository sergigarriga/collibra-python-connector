"""
Lineage Builder - Declarative data lineage creation.

This module provides a fluent API for building and committing
technical data lineage in Collibra, including assets and relations.

Example:
    >>> from collibra_connector import CollibraConnector
    >>> from collibra_connector.lineage import LineageBuilder, LineageNode
    >>>
    >>> conn = CollibraConnector(...)
    >>> builder = LineageBuilder(conn)
    >>>
    >>> # Define nodes
    >>> s3_table = LineageNode("s3://bucket/raw/customers", "Table")
    >>> glue_job = LineageNode("etl_transform_customers", "Data Pipeline")
    >>> redshift_table = LineageNode("warehouse.customers", "Table")
    >>>
    >>> # Build lineage
    >>> builder.add_edge(s3_table, glue_job, "is source for")
    >>> builder.add_edge(glue_job, redshift_table, "is target for")
    >>>
    >>> # Commit to Collibra
    >>> result = builder.commit(domain_id="lineage-domain-uuid")
    >>> print(f"Created {result.assets_created} assets, {result.relations_created} relations")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .connector import CollibraConnector


class LineageDirection(str, Enum):
    """Direction of data flow in lineage."""
    UPSTREAM = "upstream"      # Data flows TO this node
    DOWNSTREAM = "downstream"  # Data flows FROM this node
    BIDIRECTIONAL = "bidirectional"


class LineageRelationType(str, Enum):
    """Common lineage relation types."""
    SOURCE_FOR = "is source for"
    TARGET_FOR = "is target for"
    TRANSFORMS = "transforms"
    DERIVED_FROM = "is derived from"
    CONTAINS = "contains"
    PART_OF = "is part of"
    USES = "uses"
    PRODUCES = "produces"


@dataclass
class LineageNode:
    """
    Represents a node in the lineage graph.

    A node can represent any data asset: a table, a file, an ETL job,
    a dashboard, etc. Nodes can either reference existing Collibra assets
    by ID or define new assets to be created.

    Attributes:
        name: The name of the node/asset.
        asset_type: The asset type name (e.g., "Table", "Data Pipeline").
        asset_id: Optional existing asset ID (if referencing existing asset).
        display_name: Optional display name.
        description: Optional description.
        attributes: Optional dict of attribute name -> value.
        metadata: Optional dict of additional metadata.

    Example:
        >>> # Reference existing asset
        >>> existing = LineageNode.from_id("existing-asset-uuid")
        >>>
        >>> # Define new asset to create
        >>> new_table = LineageNode(
        ...     name="raw.customers",
        ...     asset_type="Table",
        ...     description="Raw customer data from CRM",
        ...     attributes={"Data Source": "Salesforce"}
        ... )
    """
    name: str
    asset_type: str = "Data Asset"
    asset_id: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _internal_id: str = field(default_factory=lambda: str(uuid4()))

    @classmethod
    def from_id(cls, asset_id: str, name: str = "") -> "LineageNode":
        """Create a node referencing an existing Collibra asset."""
        return cls(name=name, asset_id=asset_id)

    @classmethod
    def table(
        cls,
        name: str,
        schema: Optional[str] = None,
        database: Optional[str] = None,
        **kwargs: Any
    ) -> "LineageNode":
        """Create a Table node."""
        full_name = name
        if schema:
            full_name = f"{schema}.{name}"
        if database:
            full_name = f"{database}.{full_name}"
        return cls(name=full_name, asset_type="Table", **kwargs)

    @classmethod
    def column(cls, name: str, table: Optional[str] = None, **kwargs: Any) -> "LineageNode":
        """Create a Column node."""
        full_name = f"{table}.{name}" if table else name
        return cls(name=full_name, asset_type="Column", **kwargs)

    @classmethod
    def pipeline(cls, name: str, **kwargs: Any) -> "LineageNode":
        """Create a Data Pipeline node."""
        return cls(name=name, asset_type="Data Pipeline", **kwargs)

    @classmethod
    def report(cls, name: str, **kwargs: Any) -> "LineageNode":
        """Create a Report node."""
        return cls(name=name, asset_type="Report", **kwargs)

    @classmethod
    def dashboard(cls, name: str, **kwargs: Any) -> "LineageNode":
        """Create a Dashboard node."""
        return cls(name=name, asset_type="Dashboard", **kwargs)

    def __hash__(self) -> int:
        return hash(self._internal_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, LineageNode):
            return self._internal_id == other._internal_id
        return False


@dataclass
class LineageEdge:
    """
    Represents an edge (relation) in the lineage graph.

    An edge connects two nodes with a specific relation type,
    representing data flow or dependency.

    Attributes:
        source: The source node.
        target: The target node.
        relation_type: The type of relation.
        relation_type_id: Optional specific relation type UUID.
        metadata: Optional additional metadata for the edge.
    """
    source: LineageNode
    target: LineageNode
    relation_type: str = "is source for"
    relation_type_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LineageCommitResult:
    """
    Result of committing lineage to Collibra.

    Attributes:
        success: Whether the commit was successful.
        assets_created: Number of new assets created.
        assets_updated: Number of existing assets updated.
        relations_created: Number of relations created.
        assets: Dict mapping node internal IDs to created asset IDs.
        relations: List of created relation IDs.
        errors: List of error messages.
    """
    success: bool = True
    assets_created: int = 0
    assets_updated: int = 0
    relations_created: int = 0
    assets: Dict[str, str] = field(default_factory=dict)
    relations: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class LineageBuilder:
    """
    Fluent builder for creating data lineage in Collibra.

    This class provides a declarative API for defining lineage graphs
    and committing them to Collibra. It handles asset creation,
    relation creation, and error handling automatically.

    Example:
        >>> builder = LineageBuilder(connector)
        >>>
        >>> # Define the lineage
        >>> source = LineageNode.table("raw.orders", database="s3")
        >>> transform = LineageNode.pipeline("transform_orders")
        >>> target = LineageNode.table("orders", schema="warehouse")
        >>>
        >>> builder.add_edge(source, transform, "is source for")
        >>> builder.add_edge(transform, target, "is source for")
        >>>
        >>> # Or use method chaining
        >>> builder.source(source).through(transform).to(target)
        >>>
        >>> # Commit
        >>> result = builder.commit(domain_id="lineage-domain-uuid")

    Advanced Example with multiple paths:
        >>> # Multiple sources to one target
        >>> builder.add_edges([
        ...     (table_a, etl_job, "is source for"),
        ...     (table_b, etl_job, "is source for"),
        ...     (table_c, etl_job, "is source for"),
        ...     (etl_job, output_table, "is source for"),
        ... ])
    """

    def __init__(
        self,
        connector: "CollibraConnector",
        default_relation_type: str = "is source for"
    ) -> None:
        """
        Initialize the LineageBuilder.

        Args:
            connector: The CollibraConnector instance.
            default_relation_type: Default relation type for edges.
        """
        self.connector = connector
        self.default_relation_type = default_relation_type
        self._nodes: Dict[str, LineageNode] = {}
        self._edges: List[LineageEdge] = []
        self._current_source: Optional[LineageNode] = None
        self._type_id_cache: Dict[str, str] = {}
        self._relation_type_cache: Dict[str, str] = {}

    def add_node(self, node: LineageNode) -> "LineageBuilder":
        """
        Add a node to the lineage graph.

        Args:
            node: The LineageNode to add.

        Returns:
            Self for method chaining.
        """
        self._nodes[node._internal_id] = node
        return self

    def add_edge(
        self,
        source: LineageNode,
        target: LineageNode,
        relation_type: Optional[str] = None,
        relation_type_id: Optional[str] = None
    ) -> "LineageBuilder":
        """
        Add an edge (relation) between two nodes.

        Args:
            source: The source node.
            target: The target node.
            relation_type: Relation type name (uses default if not specified).
            relation_type_id: Optional specific relation type UUID.

        Returns:
            Self for method chaining.
        """
        # Auto-add nodes
        self.add_node(source)
        self.add_node(target)

        edge = LineageEdge(
            source=source,
            target=target,
            relation_type=relation_type or self.default_relation_type,
            relation_type_id=relation_type_id
        )
        self._edges.append(edge)
        return self

    def add_edges(
        self,
        edges: List[Tuple[LineageNode, LineageNode, str]]
    ) -> "LineageBuilder":
        """
        Add multiple edges at once.

        Args:
            edges: List of (source, target, relation_type) tuples.

        Returns:
            Self for method chaining.
        """
        for source, target, relation_type in edges:
            self.add_edge(source, target, relation_type)
        return self

    def source(self, node: LineageNode) -> "LineageBuilder":
        """
        Set the current source node for fluent API.

        Args:
            node: The source node.

        Returns:
            Self for method chaining.

        Example:
            >>> builder.source(table_a).to(table_b)
        """
        self.add_node(node)
        self._current_source = node
        return self

    def through(
        self,
        node: LineageNode,
        relation_type: Optional[str] = None
    ) -> "LineageBuilder":
        """
        Add an intermediate node (like an ETL job).

        Args:
            node: The intermediate node.
            relation_type: Relation type from source to this node.

        Returns:
            Self for method chaining.

        Example:
            >>> builder.source(raw_table).through(etl_job).to(warehouse_table)
        """
        if self._current_source is None:
            raise ValueError("Must call source() before through()")

        self.add_edge(self._current_source, node, relation_type)
        self._current_source = node
        return self

    def to(
        self,
        node: LineageNode,
        relation_type: Optional[str] = None
    ) -> "LineageBuilder":
        """
        Add the target node and create edge from current source.

        Args:
            node: The target node.
            relation_type: Relation type to target.

        Returns:
            Self for method chaining.

        Example:
            >>> builder.source(table_a).to(table_b)
        """
        if self._current_source is None:
            raise ValueError("Must call source() before to()")

        self.add_edge(self._current_source, node, relation_type)
        return self

    def chain(
        self,
        *nodes: LineageNode,
        relation_type: Optional[str] = None
    ) -> "LineageBuilder":
        """
        Create a chain of nodes with edges between consecutive pairs.

        Args:
            *nodes: Nodes to chain together.
            relation_type: Relation type for all edges.

        Returns:
            Self for method chaining.

        Example:
            >>> builder.chain(source, transform1, transform2, target)
        """
        for i in range(len(nodes) - 1):
            self.add_edge(nodes[i], nodes[i + 1], relation_type)
        return self

    def fan_in(
        self,
        sources: List[LineageNode],
        target: LineageNode,
        relation_type: Optional[str] = None
    ) -> "LineageBuilder":
        """
        Multiple sources feeding into one target.

        Args:
            sources: List of source nodes.
            target: The target node.
            relation_type: Relation type for all edges.

        Returns:
            Self for method chaining.

        Example:
            >>> # Multiple tables feeding into one ETL job
            >>> builder.fan_in([table_a, table_b, table_c], etl_job)
        """
        for source in sources:
            self.add_edge(source, target, relation_type)
        return self

    def fan_out(
        self,
        source: LineageNode,
        targets: List[LineageNode],
        relation_type: Optional[str] = None
    ) -> "LineageBuilder":
        """
        One source feeding into multiple targets.

        Args:
            source: The source node.
            targets: List of target nodes.
            relation_type: Relation type for all edges.

        Returns:
            Self for method chaining.

        Example:
            >>> # One ETL job producing multiple tables
            >>> builder.fan_out(etl_job, [table_a, table_b, table_c])
        """
        for target in targets:
            self.add_edge(source, target, relation_type)
        return self

    def _resolve_asset_type_id(self, type_name: str) -> Optional[str]:
        """Get asset type ID by name, with caching."""
        if type_name in self._type_id_cache:
            return self._type_id_cache[type_name]

        try:
            # Try to find the asset type
            result = self.connector.metadata.get_asset_types(name=type_name, limit=1)
            types = result.get("results", [])
            if types:
                type_id = types[0].get("id")
                self._type_id_cache[type_name] = type_id
                return type_id
        except Exception:
            pass

        return None

    def _resolve_relation_type_id(self, role: str) -> Optional[str]:
        """Get relation type ID by role name, with caching."""
        if role in self._relation_type_cache:
            return self._relation_type_cache[role]

        try:
            # Search for relation type by role
            result = self.connector.metadata.get_relation_types(role=role, limit=1)
            types = result.get("results", [])
            if types:
                type_id = types[0].get("id")
                self._relation_type_cache[role] = type_id
                return type_id
        except Exception:
            pass

        return None

    def commit(
        self,
        domain_id: str,
        status_id: Optional[str] = None,
        dry_run: bool = False,
        create_missing_types: bool = False
    ) -> LineageCommitResult:
        """
        Commit the lineage graph to Collibra.

        This method:
        1. Creates any new assets defined in nodes
        2. Creates relations between assets
        3. Sets attributes on new assets

        Args:
            domain_id: The domain to create assets in.
            status_id: Optional status for new assets.
            dry_run: If True, validate but don't create anything.
            create_missing_types: If True, log warnings for missing types.

        Returns:
            LineageCommitResult with success status and created IDs.

        Example:
            >>> result = builder.commit(domain_id="lineage-domain")
            >>> if result.success:
            ...     print(f"Created {result.assets_created} assets")
            ...     print(f"Created {result.relations_created} relations")
            >>> else:
            ...     for error in result.errors:
            ...         print(f"Error: {error}")
        """
        result = LineageCommitResult()

        if dry_run:
            result.assets_created = len([n for n in self._nodes.values() if not n.asset_id])
            result.relations_created = len(self._edges)
            return result

        # Phase 1: Create or resolve all assets
        for internal_id, node in self._nodes.items():
            try:
                if node.asset_id:
                    # Existing asset - just map the ID
                    result.assets[internal_id] = node.asset_id
                else:
                    # New asset - create it
                    type_id = self._resolve_asset_type_id(node.asset_type)

                    if not type_id:
                        result.errors.append(
                            f"Asset type not found: {node.asset_type} for node {node.name}"
                        )
                        continue

                    asset_data = {
                        "name": node.name,
                        "domain_id": domain_id,
                        "type_id": type_id,
                    }
                    if node.display_name:
                        asset_data["display_name"] = node.display_name
                    if status_id:
                        asset_data["status_id"] = status_id

                    created = self.connector.asset.add_asset(**asset_data)
                    asset_id = created.id
                    result.assets[internal_id] = asset_id
                    result.assets_created += 1

                    # Set description attribute if provided
                    if node.description:
                        try:
                            self.connector.asset.set_asset_attributes(
                                asset_id=asset_id,
                                type_public_id="Description",
                                values=[node.description]
                            )
                        except Exception:
                            pass  # Description is optional

                    # Set custom attributes
                    for attr_name, attr_value in node.attributes.items():
                        try:
                            self.connector.asset.set_asset_attributes(
                                asset_id=asset_id,
                                type_public_id=attr_name,
                                values=[attr_value]
                            )
                        except Exception:
                            pass  # Custom attributes are optional

            except Exception as e:
                result.errors.append(f"Failed to create asset {node.name}: {str(e)}")
                result.success = False

        # Phase 2: Create relations
        for edge in self._edges:
            try:
                source_id = result.assets.get(edge.source._internal_id)
                target_id = result.assets.get(edge.target._internal_id)

                if not source_id:
                    result.errors.append(
                        f"Source asset not found for edge: {edge.source.name}"
                    )
                    continue

                if not target_id:
                    result.errors.append(
                        f"Target asset not found for edge: {edge.target.name}"
                    )
                    continue

                # Resolve relation type
                relation_type_id = edge.relation_type_id
                if not relation_type_id:
                    relation_type_id = self._resolve_relation_type_id(edge.relation_type)

                if not relation_type_id:
                    result.errors.append(
                        f"Relation type not found: {edge.relation_type}"
                    )
                    continue

                created = self.connector.relation.add_relation(
                    source_id=source_id,
                    target_id=target_id,
                    type_id=relation_type_id
                )
                relation_id = created.id
                result.relations.append(relation_id)
                result.relations_created += 1

            except Exception as e:
                result.errors.append(
                    f"Failed to create relation {edge.source.name} -> {edge.target.name}: {str(e)}"
                )
                result.success = False

        if result.errors:
            result.success = False

        return result

    def clear(self) -> "LineageBuilder":
        """Clear all nodes and edges."""
        self._nodes.clear()
        self._edges.clear()
        self._current_source = None
        return self

    def get_nodes(self) -> List[LineageNode]:
        """Get all nodes in the graph."""
        return list(self._nodes.values())

    def get_edges(self) -> List[LineageEdge]:
        """Get all edges in the graph."""
        return list(self._edges)

    def to_dict(self) -> Dict[str, Any]:
        """Export the lineage graph as a dictionary."""
        return {
            "nodes": [
                {
                    "id": n._internal_id,
                    "name": n.name,
                    "asset_type": n.asset_type,
                    "asset_id": n.asset_id,
                    "description": n.description,
                    "attributes": n.attributes
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "source": e.source._internal_id,
                    "target": e.target._internal_id,
                    "relation_type": e.relation_type
                }
                for e in self._edges
            ]
        }

    def from_dict(self, data: Dict[str, Any]) -> "LineageBuilder":
        """Import lineage graph from a dictionary."""
        self.clear()

        node_map: Dict[str, LineageNode] = {}

        for node_data in data.get("nodes", []):
            node = LineageNode(
                name=node_data["name"],
                asset_type=node_data.get("asset_type", "Data Asset"),
                asset_id=node_data.get("asset_id"),
                description=node_data.get("description"),
                attributes=node_data.get("attributes", {})
            )
            node._internal_id = node_data.get("id", node._internal_id)
            node_map[node._internal_id] = node
            self.add_node(node)

        for edge_data in data.get("edges", []):
            source = node_map.get(edge_data["source"])
            target = node_map.get(edge_data["target"])
            if source and target:
                self.add_edge(source, target, edge_data.get("relation_type"))

        return self

    def visualize(self) -> str:
        """
        Generate a simple ASCII visualization of the lineage.

        Returns:
            ASCII representation of the lineage graph.
        """
        lines = ["Lineage Graph:", "=" * 40]

        # Group edges by source
        by_source: Dict[str, List[LineageEdge]] = {}
        for edge in self._edges:
            key = edge.source.name
            if key not in by_source:
                by_source[key] = []
            by_source[key].append(edge)

        for source_name, edges in by_source.items():
            lines.append(f"\n[{source_name}]")
            for edge in edges:
                lines.append(f"  --({edge.relation_type})--> [{edge.target.name}]")

        return "\n".join(lines)

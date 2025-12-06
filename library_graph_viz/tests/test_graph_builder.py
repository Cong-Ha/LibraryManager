"""Tests for graph builder component."""

import pytest
from pyvis.network import Network


class TestNetworkCreation:
    """Tests for network creation."""

    def test_create_network_default_settings(self):
        """Test network creation with default settings."""
        from app.components.graph_builder import create_network

        net = create_network()

        assert isinstance(net, Network)
        assert net.height == "600px"
        assert net.width == "100%"
        assert net.bgcolor == "#0e1117"

    def test_create_network_custom_settings(self):
        """Test network creation with custom settings."""
        from app.components.graph_builder import create_network

        net = create_network(
            height="800px",
            width="50%",
            bgcolor="#ffffff",
            directed=False,
        )

        assert net.height == "800px"
        assert net.width == "50%"
        assert net.bgcolor == "#ffffff"

    def test_create_network_physics_layouts(self):
        """Test different physics layouts."""
        from app.components.graph_builder import create_network

        # Test barnes_hut layout
        net_bh = create_network(layout="barnes_hut")
        assert net_bh is not None

        # Test force_atlas layout
        net_fa = create_network(layout="force_atlas")
        assert net_fa is not None


class TestNodeOperations:
    """Tests for node operations."""

    def test_add_nodes_basic(self, sample_graph_nodes):
        """Test adding basic nodes to network."""
        from app.components.graph_builder import create_network, add_nodes

        net = create_network()
        add_nodes(net, sample_graph_nodes)

        # Check that nodes were added
        assert len(net.nodes) == 4

    def test_add_nodes_with_colors(self, sample_graph_nodes):
        """Test that nodes get correct colors by type."""
        from app.components.graph_builder import create_network, add_nodes, NODE_COLORS

        net = create_network()
        add_nodes(net, sample_graph_nodes)

        # Find a book node and check its color
        book_node = next(n for n in net.nodes if "book" in str(n["id"]))
        assert book_node["color"] == NODE_COLORS["Book"]

    def test_add_nodes_with_custom_sizes(self):
        """Test adding nodes with custom sizes."""
        from app.components.graph_builder import create_network, add_nodes

        nodes = [
            {"id": "n1", "label": "Large", "type": "Book", "size": 50},
            {"id": "n2", "label": "Small", "type": "Book", "size": 10},
        ]

        net = create_network()
        add_nodes(net, nodes)

        large_node = next(n for n in net.nodes if n["id"] == "n1")
        small_node = next(n for n in net.nodes if n["id"] == "n2")

        assert large_node["size"] == 50
        assert small_node["size"] == 10

    def test_node_colors_mapping(self):
        """Test that all node types have colors defined."""
        from app.components.graph_builder import NODE_COLORS

        expected_types = ["Member", "Book", "Author", "Category", "Staff", "Loan", "Fine"]

        for node_type in expected_types:
            assert node_type in NODE_COLORS
            assert NODE_COLORS[node_type].startswith("#")

    def test_node_shapes_mapping(self):
        """Test that all node types have shapes defined."""
        from app.components.graph_builder import NODE_SHAPES

        expected_types = ["Member", "Book", "Author", "Category", "Staff", "Loan", "Fine"]

        for node_type in expected_types:
            assert node_type in NODE_SHAPES

    def test_node_sizes_mapping(self):
        """Test that all node types have sizes defined."""
        from app.components.graph_builder import NODE_SIZES

        expected_types = ["Member", "Book", "Author", "Category", "Staff", "Loan", "Fine"]

        for node_type in expected_types:
            assert node_type in NODE_SIZES
            assert isinstance(NODE_SIZES[node_type], int)


class TestEdgeOperations:
    """Tests for edge operations."""

    def test_add_edges_basic(self, sample_graph_nodes, sample_graph_edges):
        """Test adding basic edges to network."""
        from app.components.graph_builder import create_network, add_nodes, add_edges

        net = create_network()
        add_nodes(net, sample_graph_nodes)
        add_edges(net, sample_graph_edges)

        assert len(net.edges) == 2

    def test_add_edges_with_labels(self):
        """Test adding edges with labels."""
        from app.components.graph_builder import create_network, add_nodes, add_edges

        nodes = [
            {"id": "a", "label": "A", "type": "Author"},
            {"id": "b", "label": "B", "type": "Book"},
        ]
        edges = [
            {"from": "a", "to": "b", "label": "WROTE", "title": "Author wrote book"},
        ]

        net = create_network()
        add_nodes(net, nodes)
        add_edges(net, edges)

        edge = net.edges[0]
        assert edge["label"] == "WROTE"
        assert edge["title"] == "Author wrote book"

    def test_add_edges_custom_color(self):
        """Test adding edges with custom colors."""
        from app.components.graph_builder import create_network, add_nodes, add_edges

        nodes = [
            {"id": "a", "label": "A", "type": "Author"},
            {"id": "b", "label": "B", "type": "Book"},
        ]
        edges = [
            {"from": "a", "to": "b", "color": "#ff0000"},
        ]

        net = create_network()
        add_nodes(net, nodes)
        add_edges(net, edges)

        edge = net.edges[0]
        assert edge["color"] == "#ff0000"


class TestGraphRendering:
    """Tests for graph rendering."""

    def test_render_graph_returns_html(self, sample_graph_nodes, sample_graph_edges):
        """Test that render_graph returns valid HTML."""
        from app.components.graph_builder import (
            create_network,
            add_nodes,
            add_edges,
            render_graph,
        )

        net = create_network()
        add_nodes(net, sample_graph_nodes)
        add_edges(net, sample_graph_edges)

        html = render_graph(net)

        assert isinstance(html, str)
        assert "<html>" in html or "<!DOCTYPE" in html
        assert "vis-network" in html or "vis.Network" in html

    def test_create_legend_returns_html(self):
        """Test that legend creation returns valid HTML."""
        from app.components.graph_builder import create_legend

        legend_html = create_legend()

        assert isinstance(legend_html, str)
        assert "<div" in legend_html
        assert "Node Types" in legend_html


class TestBuildGraphFromResults:
    """Tests for building graphs from Neo4j results."""

    def test_build_graph_from_neo4j_results(self, sample_graph_nodes, sample_graph_edges):
        """Test building a complete graph from results."""
        from app.components.graph_builder import build_graph_from_neo4j_results

        net = build_graph_from_neo4j_results(
            sample_graph_nodes,
            sample_graph_edges,
            height="500px",
        )

        assert isinstance(net, Network)
        assert len(net.nodes) == 4
        assert len(net.edges) == 2

    def test_build_empty_graph(self):
        """Test building a graph with no data."""
        from app.components.graph_builder import build_graph_from_neo4j_results

        net = build_graph_from_neo4j_results([], [])

        assert isinstance(net, Network)
        assert len(net.nodes) == 0
        assert len(net.edges) == 0

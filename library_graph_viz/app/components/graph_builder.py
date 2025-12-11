"""PyVis graph construction and styling utilities."""

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from typing import Any, Optional

# Node color scheme by type
NODE_COLORS = {
    "Member": "#ff6b6b",     # Coral red
    "Book": "#4ecdc4",       # Teal
    "Author": "#45b7d1",     # Sky blue
    "Category": "#96ceb4",   # Sage green
    "Staff": "#ffeaa7",      # Soft yellow
    "Loan": "#dfe6e9",       # Light gray
    "Fine": "#fd79a8",       # Pink
}

# Node shapes by type
NODE_SHAPES = {
    "Member": "dot",
    "Book": "box",
    "Author": "dot",
    "Category": "diamond",
    "Staff": "triangle",
    "Loan": "dot",
    "Fine": "dot",
}

# Node sizes by type
NODE_SIZES = {
    "Member": 25,
    "Book": 25,
    "Author": 30,
    "Category": 35,
    "Staff": 25,
    "Loan": 20,
    "Fine": 15,
}

# ERD OLTP Schema colors (for normalized tables)
ERD_OLTP_COLORS = {
    "member": "#4CAF50",       # Green
    "author": "#9C27B0",       # Purple
    "book": "#2196F3",         # Blue
    "category": "#FF9800",     # Orange
    "staff": "#795548",        # Brown
    "loan": "#F44336",         # Red
    "fine": "#E91E63",         # Pink
    "book_author": "#607D8B",  # Gray (junction)
    "book_category": "#607D8B", # Gray (junction)
}

ERD_OLTP_SHAPES = {
    "member": "box",
    "author": "box",
    "book": "box",
    "category": "box",
    "staff": "box",
    "loan": "box",
    "fine": "box",
    "book_author": "diamond",  # Junction tables
    "book_category": "diamond",
}

ERD_OLTP_SIZES = {
    "member": 35,
    "author": 30,
    "book": 40,
    "category": 30,
    "staff": 30,
    "loan": 35,
    "fine": 25,
    "book_author": 20,
    "book_category": 20,
}

# ERD OLAP Star Schema colors
ERD_OLAP_COLORS = {
    "fact_loan": "#F44336",           # Red (fact table)
    "dim_date": "#2196F3",            # Blue
    "dim_member": "#4CAF50",          # Green
    "dim_book": "#9C27B0",            # Purple
    "dim_staff": "#795548",           # Brown
    "dim_category": "#FF9800",        # Orange
    "bridge_book_category": "#607D8B", # Gray (bridge)
}

ERD_OLAP_SHAPES = {
    "fact_loan": "star",      # Fact table as star
    "dim_date": "box",
    "dim_member": "box",
    "dim_book": "box",
    "dim_staff": "box",
    "dim_category": "box",
    "bridge_book_category": "diamond",
}

ERD_OLAP_SIZES = {
    "fact_loan": 60,          # Fact table larger
    "dim_date": 35,
    "dim_member": 35,
    "dim_book": 35,
    "dim_staff": 35,
    "dim_category": 35,
    "bridge_book_category": 25,
}


def create_network(
    height: str = "600px",
    width: str = "100%",
    bgcolor: str = "#0e1117",
    directed: bool = True,
    physics_enabled: bool = True,
    layout: str = "barnes_hut",
) -> Network:
    """
    Create a PyVis Network with consistent styling.

    Args:
        height: Network height (CSS value).
        width: Network width (CSS value).
        bgcolor: Background color.
        directed: Whether edges should be directed.
        physics_enabled: Whether to enable physics simulation.
        layout: Physics layout algorithm ('barnes_hut' or 'force_atlas').

    Returns:
        Configured PyVis Network instance.
    """
    net = Network(
        height=height,
        width=width,
        bgcolor=bgcolor,
        font_color="#ffffff",
        directed=directed,
    )

    if physics_enabled:
        if layout == "barnes_hut":
            net.barnes_hut(
                gravity=-3000,
                central_gravity=0.3,
                spring_length=200,
                spring_strength=0.001,
                damping=0.09,
            )
        else:  # force_atlas
            net.force_atlas_2based(
                gravity=-80,
                central_gravity=0.005,
                spring_length=150,
                spring_strength=0.04,
                damping=0.4,
            )
    else:
        net.toggle_physics(False)

    # Set options for better visualization
    net.set_options("""
    {
        "nodes": {
            "font": {
                "size": 14,
                "face": "arial"
            },
            "borderWidth": 2,
            "borderWidthSelected": 4
        },
        "edges": {
            "color": {
                "inherit": true
            },
            "smooth": {
                "enabled": true,
                "type": "dynamic"
            },
            "font": {
                "size": 10,
                "color": "#ffffff",
                "strokeWidth": 0
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "hideEdgesOnDrag": true,
            "navigationButtons": true,
            "keyboard": {
                "enabled": true
            },
            "multiselect": true
        }
    }
    """)

    return net


def add_nodes(
    net: Network,
    nodes: list[dict[str, Any]],
    colors: Optional[dict[str, str]] = None,
    shapes: Optional[dict[str, str]] = None,
    sizes: Optional[dict[str, int]] = None,
) -> Network:
    """
    Add nodes to a network with consistent styling.

    Args:
        net: PyVis Network instance.
        nodes: List of node dictionaries with keys:
            - id: Unique node identifier
            - label: Display label
            - type: Node type (Member, Book, Author, etc.)
            - title: Optional tooltip text
            - size: Optional custom size
        colors: Optional color mapping by type.
        shapes: Optional shape mapping by type.
        sizes: Optional size mapping by type.

    Returns:
        Updated Network instance.
    """
    colors = colors or NODE_COLORS
    shapes = shapes or NODE_SHAPES
    sizes = sizes or NODE_SIZES

    for node in nodes:
        node_id = node["id"]
        node_label = node.get("label", str(node_id))
        node_type = node.get("type", "default")
        node_title = node.get("title", f"{node_type}: {node_label}")
        node_size = node.get("size", sizes.get(node_type, 25))

        net.add_node(
            node_id,
            label=node_label,
            title=node_title,
            color=colors.get(node_type, "#888888"),
            shape=shapes.get(node_type, "dot"),
            size=node_size,
        )

    return net


def add_edges(
    net: Network,
    edges: list[dict[str, Any]],
    default_color: str = "#888888",
) -> Network:
    """
    Add edges to a network.

    Args:
        net: PyVis Network instance.
        edges: List of edge dictionaries with keys:
            - from: Source node ID
            - to: Target node ID
            - label: Optional edge label
            - title: Optional edge tooltip
            - color: Optional edge color

    Returns:
        Updated Network instance.
    """
    for edge in edges:
        source = edge["from"]
        target = edge["to"]
        label = edge.get("label", "")
        title = edge.get("title", label)
        color = edge.get("color", default_color)

        net.add_edge(
            source,
            target,
            label=label,
            title=title,
            color=color,
        )

    return net


def render_graph(net: Network) -> str:
    """
    Render a PyVis network to HTML string.

    Args:
        net: PyVis Network instance.

    Returns:
        HTML string representation of the graph.
    """
    return net.generate_html()


def display_in_streamlit(
    net: Network,
    height: int = 620,
    key: Optional[str] = None,
) -> None:
    """
    Display a PyVis network in Streamlit using components.html().

    Args:
        net: PyVis Network instance.
        height: Height of the component in pixels.
        key: Optional unique key for the component (used for container).
    """
    html = net.generate_html()
    components.html(html, height=height, scrolling=True)


def create_legend() -> str:
    """
    Create an HTML legend for node types.

    Returns:
        HTML string for the legend.
    """
    legend_html = "<div style='padding: 10px; background-color: #1e1e1e; border-radius: 5px;'>"
    legend_html += "<h4 style='color: white; margin-bottom: 10px;'>Node Types</h4>"

    for node_type, color in NODE_COLORS.items():
        legend_html += f"""
        <div style='display: flex; align-items: center; margin: 5px 0;'>
            <div style='width: 20px; height: 20px; background-color: {color};
                        border-radius: 50%; margin-right: 10px;'></div>
            <span style='color: white;'>{node_type}</span>
        </div>
        """

    legend_html += "</div>"
    return legend_html


def display_legend() -> None:
    """Display the node type legend in Streamlit."""
    st.markdown(create_legend(), unsafe_allow_html=True)


def build_graph_from_neo4j_results(
    nodes_data: list[dict],
    edges_data: list[dict],
    height: str = "600px",
    layout: str = "barnes_hut",
) -> Network:
    """
    Build a complete graph from Neo4j query results.

    Args:
        nodes_data: List of node dictionaries from Neo4j.
        edges_data: List of edge dictionaries from Neo4j.
        height: Graph height.
        layout: Physics layout algorithm.

    Returns:
        Configured PyVis Network with nodes and edges.
    """
    net = create_network(height=height, layout=layout)
    add_nodes(net, nodes_data)
    add_edges(net, edges_data)
    return net

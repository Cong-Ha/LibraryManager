"""Interactive Graph Visualization Component for Streamlit.

This module provides a custom Streamlit component for displaying interactive
graph visualizations using vis-network. It supports dynamic physics switching,
node/edge click events, and multi-selection.
"""

import os
from typing import Any, Optional

import streamlit.components.v1 as components

# Determine if we're in development mode
_DEVELOPMENT = os.environ.get("STREAMLIT_GRAPH_DEV", "false").lower() == "true"

if _DEVELOPMENT:
    # Development mode: use local dev server
    _component_func = components.declare_component(
        "streamlit_graph",
        url="http://localhost:3001",
    )
else:
    # Production mode: use built files
    _COMPONENT_PATH = os.path.join(os.path.dirname(__file__), "frontend", "build")
    _component_func = components.declare_component(
        "streamlit_graph",
        path=_COMPONENT_PATH,
    )

# Import constants from graph_builder for backward compatibility
from app.components.graph_builder import (
    NODE_COLORS,
    NODE_SHAPES,
    NODE_SIZES,
    ERD_OLTP_COLORS,
    ERD_OLTP_SHAPES,
    ERD_OLTP_SIZES,
    ERD_OLAP_COLORS,
    ERD_OLAP_SHAPES,
    ERD_OLAP_SIZES,
)

# Re-export for convenience
__all__ = [
    "streamlit_graph",
    "display_interactive_graph",
    "InteractiveNetwork",
    "NODE_COLORS",
    "NODE_SHAPES",
    "NODE_SIZES",
    "ERD_OLTP_COLORS",
    "ERD_OLTP_SHAPES",
    "ERD_OLTP_SIZES",
    "ERD_OLAP_COLORS",
    "ERD_OLAP_SHAPES",
    "ERD_OLAP_SIZES",
    "PHYSICS_PRESETS",
]

# Physics presets matching current PyVis implementation
PHYSICS_PRESETS = {
    "barnes_hut": {
        "layout": "barnes_hut",
        "gravity": -3000,
        "centralGravity": 0.3,
        "springLength": 200,
        "springStrength": 0.001,
        "damping": 0.09,
    },
    "force_atlas": {
        "layout": "force_atlas",
        "gravity": -80,
        "centralGravity": 0.005,
        "springLength": 150,
        "springStrength": 0.04,
        "damping": 0.4,
    },
}


def streamlit_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    layout: str = "barnes_hut",
    height: int = 600,
    directed: bool = True,
    multi_select: bool = True,
    key: Optional[str] = None,
) -> Optional[dict]:
    """
    Display an interactive graph visualization.

    Args:
        nodes: List of node dictionaries with keys:
            - id: Unique node identifier
            - label: Display label
            - type: Node type (for styling lookup)
            - title: Optional tooltip text
            - size: Optional custom size
            - color: Optional custom color (overrides type-based color)
            - shape: Optional custom shape (overrides type-based shape)
        edges: List of edge dictionaries with keys:
            - from: Source node ID
            - to: Target node ID
            - label: Optional edge label
            - title: Optional edge tooltip
            - color: Optional edge color
        layout: Physics layout algorithm ('barnes_hut' or 'force_atlas')
        height: Height of the component in pixels
        directed: Whether edges should show arrows
        multi_select: Allow selecting multiple nodes
        key: Optional unique key for the component

    Returns:
        Event dictionary if user interaction occurred, None otherwise.
        Event types:
            - nodeClick: {type, nodeId, nodeData}
            - nodeSelect: {type, nodeIds}
            - edgeClick: {type, edgeId, edgeData}
            - hover: {type, nodeId, nodeData}
            - doubleClick: {type, nodeId, nodeData}
    """
    # Get physics configuration
    physics = PHYSICS_PRESETS.get(layout, PHYSICS_PRESETS["barnes_hut"])

    # Call the component
    event = _component_func(
        nodes=nodes,
        edges=edges,
        physics=physics,
        height=height,
        directed=directed,
        multiSelect=multi_select,
        key=key,
        default=None,
    )

    return event


def display_interactive_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    height: int = 620,
    layout: str = "barnes_hut",
    directed: bool = True,
    key: Optional[str] = None,
    colors: Optional[dict[str, str]] = None,
    shapes: Optional[dict[str, str]] = None,
    sizes: Optional[dict[str, int]] = None,
) -> Optional[dict]:
    """
    Display an interactive graph - drop-in replacement for display_in_streamlit.

    This function applies styling based on node types and displays the graph
    with full interactivity support.

    Args:
        nodes: List of node dictionaries (same format as streamlit_graph)
        edges: List of edge dictionaries (same format as streamlit_graph)
        height: Height of the component in pixels
        layout: Physics layout algorithm ('barnes_hut' or 'force_atlas')
        directed: Whether edges should show arrows
        key: Optional unique key for the component
        colors: Optional color mapping by node type (defaults to NODE_COLORS)
        shapes: Optional shape mapping by node type (defaults to NODE_SHAPES)
        sizes: Optional size mapping by node type (defaults to NODE_SIZES)

    Returns:
        Event dictionary if user interaction occurred, None otherwise.
    """
    # Apply custom styling
    color_map = colors or NODE_COLORS
    shape_map = shapes or NODE_SHAPES
    size_map = sizes or NODE_SIZES

    styled_nodes = []
    for node in nodes:
        node_type = node.get("type", "default")
        styled_nodes.append({
            **node,
            "color": node.get("color") or color_map.get(node_type, "#888888"),
            "shape": node.get("shape") or shape_map.get(node_type, "dot"),
            "size": node.get("size") or size_map.get(node_type, 25),
        })

    return streamlit_graph(
        nodes=styled_nodes,
        edges=edges,
        layout=layout,
        height=height,
        directed=directed,
        key=key,
    )


class InteractiveNetwork:
    """
    Drop-in replacement for PyVis Network with interactive capabilities.

    This class provides a similar API to the current graph_builder functions
    while adding full interactivity support.

    Example:
        net = InteractiveNetwork(height="600px", layout="barnes_hut")
        net.add_nodes(nodes_list)
        net.add_edges(edges_list)
        event = net.display(key="my_network")

        if event and event["type"] == "nodeClick":
            st.write(f"Clicked: {event['nodeData']}")
    """

    def __init__(
        self,
        height: str = "600px",
        bgcolor: str = "#0e1117",
        directed: bool = True,
        physics_enabled: bool = True,
        layout: str = "barnes_hut",
    ):
        """
        Initialize an interactive network.

        Args:
            height: Height as CSS string (e.g., "600px")
            bgcolor: Background color (currently fixed to dark theme)
            directed: Whether edges should show arrows
            physics_enabled: Whether physics simulation is enabled
            layout: Physics layout algorithm ('barnes_hut' or 'force_atlas')
        """
        self.height = int(height.replace("px", ""))
        self.bgcolor = bgcolor
        self.directed = directed
        self.physics_enabled = physics_enabled
        self.layout = layout
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self._colors = NODE_COLORS.copy()
        self._shapes = NODE_SHAPES.copy()
        self._sizes = NODE_SIZES.copy()

    def set_styling(
        self,
        colors: Optional[dict[str, str]] = None,
        shapes: Optional[dict[str, str]] = None,
        sizes: Optional[dict[str, int]] = None,
    ) -> None:
        """Set custom styling maps for node types."""
        if colors:
            self._colors.update(colors)
        if shapes:
            self._shapes.update(shapes)
        if sizes:
            self._sizes.update(sizes)

    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: str = "default",
        title: Optional[str] = None,
        size: Optional[int] = None,
        color: Optional[str] = None,
        shape: Optional[str] = None,
    ) -> None:
        """Add a node to the network."""
        self.nodes.append({
            "id": node_id,
            "label": label,
            "type": node_type,
            "title": title or f"{node_type}: {label}",
            "size": size or self._sizes.get(node_type, 25),
            "color": color or self._colors.get(node_type, "#888888"),
            "shape": shape or self._shapes.get(node_type, "dot"),
        })

    def add_nodes(self, nodes: list[dict[str, Any]]) -> None:
        """Add multiple nodes at once."""
        for node in nodes:
            self.add_node(
                node_id=node["id"],
                label=node.get("label", str(node["id"])),
                node_type=node.get("type", "default"),
                title=node.get("title"),
                size=node.get("size"),
                color=node.get("color"),
                shape=node.get("shape"),
            )

    def add_edge(
        self,
        source: str,
        target: str,
        label: str = "",
        title: Optional[str] = None,
        color: str = "#888888",
    ) -> None:
        """Add an edge to the network."""
        self.edges.append({
            "from": source,
            "to": target,
            "label": label,
            "title": title or label,
            "color": color,
        })

    def add_edges(self, edges: list[dict[str, Any]]) -> None:
        """Add multiple edges at once."""
        for edge in edges:
            self.add_edge(
                source=edge["from"],
                target=edge["to"],
                label=edge.get("label", ""),
                title=edge.get("title"),
                color=edge.get("color", "#888888"),
            )

    def set_layout(self, layout: str) -> None:
        """Change the physics layout."""
        self.layout = layout

    def display(self, key: Optional[str] = None) -> Optional[dict]:
        """
        Display the network in Streamlit and return interaction events.

        Args:
            key: Optional unique key for the component

        Returns:
            Event dictionary if user interaction occurred, None otherwise.
        """
        return streamlit_graph(
            nodes=self.nodes,
            edges=self.edges,
            layout=self.layout,
            height=self.height,
            directed=self.directed,
            key=key,
        )

    def clear(self) -> None:
        """Clear all nodes and edges from the network."""
        self.nodes = []
        self.edges = []

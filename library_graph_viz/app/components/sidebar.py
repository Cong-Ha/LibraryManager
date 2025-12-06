"""Sidebar component for navigation and statistics."""

import streamlit as st
from typing import Callable, Optional
from datetime import datetime

from etl.neo4j_connector import Neo4jConnector


def render_sidebar(
    views: dict[str, Callable],
    neo4j: Optional[Neo4jConnector] = None,
    on_sync: Optional[Callable] = None,
    last_sync: Optional[datetime] = None,
) -> str:
    """
    Render the sidebar with navigation and statistics.

    Args:
        views: Dictionary mapping view names to render functions.
        neo4j: Optional Neo4j connector for statistics.
        on_sync: Optional callback for sync button.
        last_sync: Optional timestamp of last sync.

    Returns:
        Name of the selected view.
    """
    st.sidebar.title("📚 Library Graph Explorer")

    # View selection
    st.sidebar.markdown("### Navigation")
    selected_view = st.sidebar.selectbox(
        "Select View",
        list(views.keys()),
        help="Choose a visualization to explore",
    )

    # Sync section
    if on_sync:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Data Sync")

        if last_sync:
            st.sidebar.text(f"Last sync: {last_sync.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.sidebar.text("Never synced")

        if st.sidebar.button("🔄 Sync Now", help="Run ETL to refresh graph data"):
            on_sync()

    # Statistics section
    if neo4j:
        render_statistics(neo4j)

    # Legend
    st.sidebar.markdown("---")
    render_legend()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style='text-align: center; color: #888;'>
            <small>Library Graph Viz v1.0</small><br>
            <small>Neo4j + PyVis + Streamlit</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return selected_view


def render_statistics(neo4j: Neo4jConnector) -> None:
    """
    Render graph statistics in the sidebar.

    Args:
        neo4j: Neo4j connector instance.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Graph Statistics")

    try:
        stats = neo4j.get_statistics()

        # Total counts
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Total Nodes", stats.get("total_nodes", 0))
        col2.metric("Total Rels", stats.get("total_relationships", 0))

        # Node counts by type
        with st.sidebar.expander("📊 Node Counts", expanded=False):
            for label, count in stats.get("nodes", {}).items():
                st.text(f"{label}: {count}")

        # Relationship counts by type
        with st.sidebar.expander("🔗 Relationship Counts", expanded=False):
            for rel_type, count in stats.get("relationships", {}).items():
                st.text(f"{rel_type}: {count}")

    except Exception as e:
        st.sidebar.warning(f"Could not load statistics: {e}")


def render_legend() -> None:
    """Render the node type legend in the sidebar."""
    from app.components.graph_builder import NODE_COLORS

    st.sidebar.markdown("### Legend")

    legend_items = []
    for node_type, color in NODE_COLORS.items():
        legend_items.append(
            f'<span style="color: {color};">●</span> {node_type}'
        )

    st.sidebar.markdown(
        "<br>".join(legend_items),
        unsafe_allow_html=True,
    )

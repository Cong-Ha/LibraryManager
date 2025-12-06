"""Main Streamlit application for Library Graph Visualization."""

import streamlit as st
import logging
from datetime import datetime
from typing import Optional

from config.settings import get_settings, Settings
from etl.neo4j_connector import Neo4jConnector
from etl.mysql_connector import MySQLConnector
from etl.etl_pipeline import LibraryETL
from app.views import (
    full_network,
    books_authors,
    member_history,
    category_explorer,
    staff_activity,
    custom_query,
    analytics,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Library Graph Explorer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #1e1e1e;
        padding: 10px;
        border-radius: 5px;
    }
    .stExpander {
        background-color: #1e1e1e;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


# View mapping
VIEWS = {
    "🌐 Full Library Network": full_network,
    "📖 Books & Authors": books_authors,
    "👤 Member Borrowing History": member_history,
    "📂 Category Explorer": category_explorer,
    "👥 Staff Activity": staff_activity,
    "🔍 Custom Cypher Query": custom_query,
    "📊 Analytics & Recommendations": analytics,
}


@st.cache_resource
def get_neo4j_connector() -> Neo4jConnector:
    """
    Get a cached Neo4j connector instance.

    Returns:
        Neo4jConnector instance.
    """
    settings = get_settings()
    connector = Neo4jConnector(settings)
    # Enter context to establish connection
    connector.__enter__()
    return connector


def run_etl_sync() -> Optional[dict]:
    """
    Run the ETL pipeline to sync data.

    Returns:
        Dictionary with sync results or None if failed.
    """
    settings = get_settings()
    try:
        with MySQLConnector(settings) as mysql:
            with Neo4jConnector(settings) as neo4j:
                etl = LibraryETL(mysql, neo4j)
                return etl.run(clear_first=True)
    except Exception as e:
        logger.error(f"ETL sync failed: {e}")
        return None


def render_sidebar(neo4j: Neo4jConnector) -> str:
    """
    Render the sidebar navigation.

    Args:
        neo4j: Neo4j connector instance.

    Returns:
        Selected view name.
    """
    st.sidebar.title("📚 Library Graph Explorer")

    # View selection
    st.sidebar.markdown("### Navigation")
    selected_view = st.sidebar.selectbox(
        "Select View",
        list(VIEWS.keys()),
        help="Choose a visualization to explore",
    )

    # Sync section
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Sync")

    if "last_sync" not in st.session_state:
        st.session_state["last_sync"] = None

    if st.session_state["last_sync"]:
        st.sidebar.text(f"Last sync: {st.session_state['last_sync'].strftime('%Y-%m-%d %H:%M')}")
    else:
        st.sidebar.text("Never synced")

    if st.sidebar.button("🔄 Sync Data", help="Run ETL to refresh graph data from MySQL"):
        with st.spinner("Running ETL sync..."):
            result = run_etl_sync()
            if result:
                st.session_state["last_sync"] = datetime.now()
                st.sidebar.success("Sync completed!")
                # Clear cache to refresh data
                st.cache_resource.clear()
                st.rerun()
            else:
                st.sidebar.error("Sync failed. Check database connections.")

    # Statistics section
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Graph Statistics")

    try:
        stats = neo4j.get_statistics()

        col1, col2 = st.sidebar.columns(2)
        col1.metric("Nodes", stats.get("total_nodes", 0))
        col2.metric("Relationships", stats.get("total_relationships", 0))

        with st.sidebar.expander("📊 Node Counts"):
            for label, count in stats.get("nodes", {}).items():
                st.text(f"{label}: {count}")

        with st.sidebar.expander("🔗 Relationship Counts"):
            for rel_type, count in stats.get("relationships", {}).items():
                st.text(f"{rel_type}: {count}")

    except Exception as e:
        st.sidebar.warning("Could not load statistics")
        st.sidebar.info("Run ETL sync to populate the graph")

    # Legend
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Legend")

    from app.components.graph_builder import NODE_COLORS

    legend_items = []
    for node_type, color in NODE_COLORS.items():
        legend_items.append(f'<span style="color: {color};">●</span> {node_type}')

    st.sidebar.markdown("<br>".join(legend_items), unsafe_allow_html=True)

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


def main():
    """Main application entry point."""
    # Get Neo4j connection
    try:
        neo4j = get_neo4j_connector()
    except Exception as e:
        st.error("❌ Could not connect to Neo4j database")
        st.info(
            "Please make sure:\n"
            "1. Docker containers are running (`docker-compose up -d`)\n"
            "2. Neo4j is accessible at the configured URI\n"
            "3. Credentials in `.env` are correct"
        )
        st.code(f"Error: {e}")

        if st.button("🔄 Retry Connection"):
            st.cache_resource.clear()
            st.rerun()

        return

    # Render sidebar and get selected view
    selected_view = render_sidebar(neo4j)

    # Main content
    st.title("Library Management Graph Visualization")

    # Render the selected view
    view_module = VIEWS[selected_view]
    view_module.render(neo4j)


if __name__ == "__main__":
    main()

"""Full Library Network View - Shows all node types and relationships."""

import streamlit as st
from etl.neo4j_connector import Neo4jConnector
from app.components.graph_builder import (
    create_network,
    add_nodes,
    add_edges,
    display_in_streamlit,
    display_legend,
    NODE_COLORS,
)


def render(neo4j: Neo4jConnector) -> None:
    """
    Render the full library network view.

    Args:
        neo4j: Neo4j connector instance.
    """
    st.subheader("🌐 Full Library Network")
    st.markdown(
        "Explore the complete library graph with all entities and relationships."
    )

    # Controls
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        node_limit = st.slider(
            "Node Limit",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="Limit the number of nodes displayed for performance",
        )

    with col2:
        layout = st.selectbox(
            "Physics Layout",
            ["barnes_hut", "force_atlas"],
            help="Choose the graph layout algorithm",
        )

    with col3:
        show_labels = st.checkbox("Show Relationship Labels", value=False)

    # Query Neo4j for nodes and relationships
    try:
        # Get nodes with limit
        nodes_query = """
            MATCH (n)
            WITH n, labels(n)[0] AS label
            RETURN
                id(n) AS neo4j_id,
                label,
                CASE label
                    WHEN 'Member' THEN n.name
                    WHEN 'Book' THEN n.title
                    WHEN 'Author' THEN n.name
                    WHEN 'Category' THEN n.name
                    WHEN 'Staff' THEN n.name
                    WHEN 'Loan' THEN 'Loan #' + toString(n.id)
                    WHEN 'Fine' THEN 'Fine $' + toString(n.amount)
                    ELSE toString(n.id)
                END AS display_name,
                n AS properties
            LIMIT $limit
        """
        nodes_result = neo4j.run_query(nodes_query, {"limit": node_limit})

        # Get relationships between the fetched nodes
        node_ids = [n["neo4j_id"] for n in nodes_result]

        rels_query = """
            MATCH (a)-[r]->(b)
            WHERE id(a) IN $node_ids AND id(b) IN $node_ids
            RETURN id(a) AS source, id(b) AS target, type(r) AS rel_type
        """
        rels_result = neo4j.run_query(rels_query, {"node_ids": node_ids})

        # Build the graph
        nodes = [
            {
                "id": f"n_{n['neo4j_id']}",
                "label": n["display_name"][:20] + "..." if len(n["display_name"]) > 20 else n["display_name"],
                "type": n["label"],
                "title": f"{n['label']}: {n['display_name']}",
            }
            for n in nodes_result
        ]

        edges = [
            {
                "from": f"n_{r['source']}",
                "to": f"n_{r['target']}",
                "label": r["rel_type"] if show_labels else "",
                "title": r["rel_type"],
            }
            for r in rels_result
        ]

        # Create and display the network
        net = create_network(height="650px", layout=layout)
        add_nodes(net, nodes)
        add_edges(net, edges)

        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Nodes Displayed", len(nodes))
        col2.metric("Relationships", len(edges))

        # Count by type
        type_counts = {}
        for n in nodes:
            t = n["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        col3.metric("Node Types", len(type_counts))
        col4.metric("Most Common", max(type_counts, key=type_counts.get) if type_counts else "N/A")

        # Display the graph
        display_in_streamlit(net, height=670)

        # Show breakdown
        with st.expander("📊 Node Type Breakdown"):
            for node_type, color in NODE_COLORS.items():
                count = type_counts.get(node_type, 0)
                if count > 0:
                    st.markdown(
                        f'<span style="color: {color};">●</span> **{node_type}**: {count}',
                        unsafe_allow_html=True,
                    )

    except Exception as e:
        st.error(f"Error loading graph: {e}")
        st.info("Make sure the ETL pipeline has been run to populate Neo4j.")

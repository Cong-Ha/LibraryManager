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

# Define node type categories
SMALL_TYPES = {"Category": 15, "Staff": 20, "Author": 100}  # Show ALL of these
LARGE_TYPES = {"Member": 200, "Book": 500, "Loan": 2000, "Fine": 1234}  # Sample from these


def get_node_counts(neo4j: Neo4jConnector) -> dict:
    """Get actual node counts from Neo4j."""
    query = """
        MATCH (n)
        WITH labels(n)[0] AS label, count(*) AS cnt
        RETURN label, cnt
    """
    result = neo4j.run_query(query)
    return {r["label"]: r["cnt"] for r in result}


def build_connectivity_query(selected_types: dict, node_limit: int, actual_counts: dict) -> tuple:
    """
    Build a connectivity-aware query that ensures relationships are visible.

    Strategy:
    1. Sample Loans first (they're the hub connecting Member, Book, Staff, Fine)
    2. Expand to get connected nodes
    3. Add all small types (Category, Staff, Author)

    Returns:
        Tuple of (query_string, parameters_dict)
    """
    # Calculate small type totals
    small_total = sum(
        actual_counts.get(t, 0)
        for t in SMALL_TYPES.keys()
        if selected_types.get(t, False)
    )

    # Remaining for large types
    remaining = max(0, node_limit - small_total)

    # Allocate roughly: 40% to loans, 60% to connected entities
    loan_sample = min(actual_counts.get('Loan', 0), max(10, remaining // 3)) if selected_types.get('Loan') else 0

    params = {"loan_sample": loan_sample}
    query_parts = []

    # Part 1: Sample Loans and their connected nodes (Member, Book, Staff, Fine)
    if loan_sample > 0:
        # Get loans and all their connected nodes in one query
        connected_query = """
            MATCH (l:Loan)
            WITH l LIMIT $loan_sample
            OPTIONAL MATCH (m:Member)-[:BORROWED]->(l)
            OPTIONAL MATCH (l)-[:CONTAINS]->(b:Book)
            OPTIONAL MATCH (l)-[:PROCESSED_BY]->(s:Staff)
            OPTIONAL MATCH (l)-[:HAS_FINE]->(f:Fine)
            WITH collect(DISTINCT l) + collect(DISTINCT m) + collect(DISTINCT b) + collect(DISTINCT s) + collect(DISTINCT f) AS nodes
            UNWIND nodes AS n
            WITH n WHERE n IS NOT NULL
            RETURN DISTINCT id(n) AS neo4j_id, labels(n)[0] AS label,
                CASE labels(n)[0]
                    WHEN 'Member' THEN n.name
                    WHEN 'Book' THEN n.title
                    WHEN 'Loan' THEN 'Loan #' + toString(n.id)
                    WHEN 'Fine' THEN 'Fine $' + toString(n.amount)
                    WHEN 'Staff' THEN n.name
                END AS display_name,
                n AS properties
        """
        query_parts.append(connected_query)

    # Part 2: Add ALL small types (Category, Author - Staff already included via loans)
    if selected_types.get('Category', False):
        query_parts.append("""
            MATCH (n:Category)
            RETURN id(n) AS neo4j_id, 'Category' AS label, n.name AS display_name, n AS properties
        """)

    if selected_types.get('Author', False):
        query_parts.append("""
            MATCH (n:Author)
            RETURN id(n) AS neo4j_id, 'Author' AS label, n.name AS display_name, n AS properties
        """)

    # If no loans selected, fall back to independent sampling
    if loan_sample == 0:
        if selected_types.get('Staff', False):
            query_parts.append("""
                MATCH (n:Staff)
                RETURN id(n) AS neo4j_id, 'Staff' AS label, n.name AS display_name, n AS properties
            """)

        if selected_types.get('Member', False):
            member_limit = min(actual_counts.get('Member', 0), remaining // 4)
            params["member_limit"] = member_limit
            query_parts.append("""
                MATCH (n:Member) WITH n LIMIT $member_limit
                RETURN id(n) AS neo4j_id, 'Member' AS label, n.name AS display_name, n AS properties
            """)

        if selected_types.get('Book', False):
            book_limit = min(actual_counts.get('Book', 0), remaining // 4)
            params["book_limit"] = book_limit
            query_parts.append("""
                MATCH (n:Book) WITH n LIMIT $book_limit
                RETURN id(n) AS neo4j_id, 'Book' AS label, n.title AS display_name, n AS properties
            """)

        if selected_types.get('Fine', False):
            fine_limit = min(actual_counts.get('Fine', 0), remaining // 4)
            params["fine_limit"] = fine_limit
            query_parts.append("""
                MATCH (n:Fine) WITH n LIMIT $fine_limit
                RETURN id(n) AS neo4j_id, 'Fine' AS label, 'Fine $' + toString(n.amount) AS display_name, n AS properties
            """)

    if not query_parts:
        return None, None

    full_query = " UNION ".join(query_parts)
    return full_query, params


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

    # Get actual node counts
    try:
        actual_counts = get_node_counts(neo4j)
    except Exception:
        actual_counts = {**SMALL_TYPES, **LARGE_TYPES}  # Use defaults if query fails

    # Node Type Selection
    st.markdown("**Select Node Types to Display:**")

    col1, col2, col3, col4 = st.columns(4)

    # Small types (first row) - always show all when selected
    with col1:
        show_category = st.checkbox(
            f"Categories ({actual_counts.get('Category', 0)})",
            value=True,
            help="Show ALL categories"
        )
    with col2:
        show_staff = st.checkbox(
            f"Staff ({actual_counts.get('Staff', 0)})",
            value=True,
            help="Show ALL staff members"
        )
    with col3:
        show_author = st.checkbox(
            f"Authors ({actual_counts.get('Author', 0)})",
            value=True,
            help="Show ALL authors"
        )
    with col4:
        show_member = st.checkbox(
            f"Members ({actual_counts.get('Member', 0)})",
            value=True,
            help="Sample from members"
        )

    col5, col6, col7, col8 = st.columns(4)

    # Large types (second row) - sampled
    with col5:
        show_book = st.checkbox(
            f"Books ({actual_counts.get('Book', 0)})",
            value=True,
            help="Sample from books"
        )
    with col6:
        show_loan = st.checkbox(
            f"Loans ({actual_counts.get('Loan', 0)})",
            value=True,
            help="Sample from loans"
        )
    with col7:
        show_fine = st.checkbox(
            f"Fines ({actual_counts.get('Fine', 0)})",
            value=True,
            help="Sample from fines"
        )

    selected_types = {
        "Category": show_category,
        "Staff": show_staff,
        "Author": show_author,
        "Member": show_member,
        "Book": show_book,
        "Loan": show_loan,
        "Fine": show_fine,
    }

    st.markdown("---")

    # Controls row
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        # Calculate minimum based on small types selected
        small_selected = sum(
            actual_counts.get(t, 0)
            for t, selected in selected_types.items()
            if selected and t in SMALL_TYPES
        )
        min_nodes = max(50, small_selected + 10)

        node_limit = st.slider(
            "Max Nodes to Display",
            min_value=min_nodes,
            max_value=500,
            value=max(200, min_nodes),
            step=25,
            help=f"Small types ({small_selected} nodes) are always shown completely. Remaining slots are distributed to large types.",
        )

    with col2:
        layout = st.selectbox(
            "Physics Layout",
            ["barnes_hut", "force_atlas"],
            help="Choose the graph layout algorithm",
        )

    with col3:
        show_labels = st.checkbox("Show Relationship Labels", value=False)

    # Check if any types selected
    if not any(selected_types.values()):
        st.warning("Please select at least one node type to display.")
        return

    # Query Neo4j for nodes and relationships
    try:
        # Build connectivity-aware query to ensure relationships are visible
        nodes_query, params = build_connectivity_query(selected_types, node_limit, actual_counts)

        if nodes_query is None:
            st.warning("No node types selected for display.")
            return

        nodes_result = neo4j.run_query(nodes_query, params)

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

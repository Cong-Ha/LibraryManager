"""Member Borrowing History View - Shows member loan chains."""

import streamlit as st
import pandas as pd
from etl.neo4j_connector import Neo4jConnector
from app.components.graph_builder import (
    create_network,
    add_nodes,
    add_edges,
    display_in_streamlit,
)


def render(neo4j: Neo4jConnector) -> None:
    """
    Render the member borrowing history view.

    Args:
        neo4j: Neo4j connector instance.
    """
    st.subheader("👤 Member Borrowing History")
    st.markdown("Explore a member's complete borrowing history with loan chains.")

    try:
        # Get list of members for dropdown
        members_query = """
            MATCH (m:Member)
            RETURN m.id AS id, m.name AS name
            ORDER BY m.name
        """
        members = neo4j.run_query(members_query)

        if not members:
            st.warning("No members found in the database.")
            return

        # Member selector
        member_options = {f"{m['name']} (ID: {m['id']})": m['id'] for m in members}
        selected_member = st.selectbox(
            "Select Member",
            list(member_options.keys()),
            help="Choose a member to view their borrowing history",
        )
        member_id = member_options[selected_member]

        # Controls
        col1, col2 = st.columns([2, 2])
        with col1:
            include_authors = st.checkbox("Include Book Authors", value=True)
        with col2:
            show_returned_only = st.checkbox("Show Only Returned Books", value=False)

        # Query for member's borrowing history
        if include_authors:
            query = """
                MATCH (m:Member {id: $member_id})-[:BORROWED]->(l:Loan)-[:CONTAINS]->(b:Book)
                OPTIONAL MATCH (b)<-[:WROTE]-(a:Author)
                WHERE ($show_returned = false OR l.return_date IS NOT NULL)
                RETURN
                    m.id AS member_id,
                    m.name AS member_name,
                    m.email AS member_email,
                    l.id AS loan_id,
                    l.loan_date AS loan_date,
                    l.due_date AS due_date,
                    l.return_date AS return_date,
                    b.id AS book_id,
                    b.title AS book_title,
                    a.id AS author_id,
                    a.name AS author_name
                ORDER BY l.loan_date DESC
            """
        else:
            query = """
                MATCH (m:Member {id: $member_id})-[:BORROWED]->(l:Loan)-[:CONTAINS]->(b:Book)
                WHERE ($show_returned = false OR l.return_date IS NOT NULL)
                RETURN
                    m.id AS member_id,
                    m.name AS member_name,
                    m.email AS member_email,
                    l.id AS loan_id,
                    l.loan_date AS loan_date,
                    l.due_date AS due_date,
                    l.return_date AS return_date,
                    b.id AS book_id,
                    b.title AS book_title,
                    null AS author_id,
                    null AS author_name
                ORDER BY l.loan_date DESC
            """

        results = neo4j.run_query(
            query,
            {"member_id": member_id, "show_returned": show_returned_only}
        )

        if not results:
            st.info(f"No borrowing history found for this member.")
            return

        # Build graph nodes and edges
        nodes = []
        edges = []
        seen_nodes = set()

        # Add member node
        member_node_id = f"member_{member_id}"
        if member_node_id not in seen_nodes:
            nodes.append({
                "id": member_node_id,
                "label": results[0]["member_name"],
                "type": "Member",
                "title": f"Member: {results[0]['member_name']}\nEmail: {results[0]['member_email']}",
                "size": 40,
            })
            seen_nodes.add(member_node_id)

        for r in results:
            # Loan node
            loan_node_id = f"loan_{r['loan_id']}"
            if loan_node_id not in seen_nodes:
                status = "Returned" if r["return_date"] else "Active"
                nodes.append({
                    "id": loan_node_id,
                    "label": f"Loan #{r['loan_id']}",
                    "type": "Loan",
                    "title": f"Loan #{r['loan_id']}\nDate: {r['loan_date']}\nDue: {r['due_date']}\nReturned: {r['return_date'] or 'Not yet'}\nStatus: {status}",
                })
                seen_nodes.add(loan_node_id)

                # Member -> Loan edge
                edges.append({
                    "from": member_node_id,
                    "to": loan_node_id,
                    "label": "BORROWED",
                    "title": f"Borrowed on {r['loan_date']}",
                })

            # Book node
            book_node_id = f"book_{r['book_id']}"
            if book_node_id not in seen_nodes:
                nodes.append({
                    "id": book_node_id,
                    "label": r["book_title"][:20] + "..." if len(r["book_title"]) > 20 else r["book_title"],
                    "type": "Book",
                    "title": f"Book: {r['book_title']}",
                })
                seen_nodes.add(book_node_id)

            # Loan -> Book edge
            edge_id = f"{loan_node_id}_{book_node_id}"
            if edge_id not in seen_nodes:
                edges.append({
                    "from": loan_node_id,
                    "to": book_node_id,
                    "label": "CONTAINS",
                    "title": "CONTAINS",
                })
                seen_nodes.add(edge_id)

            # Author node and edge
            if include_authors and r["author_id"]:
                author_node_id = f"author_{r['author_id']}"
                if author_node_id not in seen_nodes:
                    nodes.append({
                        "id": author_node_id,
                        "label": r["author_name"],
                        "type": "Author",
                        "title": f"Author: {r['author_name']}",
                    })
                    seen_nodes.add(author_node_id)

                # Author -> Book edge
                author_edge_id = f"{author_node_id}_{book_node_id}"
                if author_edge_id not in seen_nodes:
                    edges.append({
                        "from": author_node_id,
                        "to": book_node_id,
                        "label": "WROTE",
                        "title": "WROTE",
                    })
                    seen_nodes.add(author_edge_id)

        # Create and display network
        net = create_network(height="550px", layout="force_atlas")
        add_nodes(net, nodes)
        add_edges(net, edges)

        # Statistics
        unique_books = len(set(r["book_id"] for r in results))
        active_loans = len([r for r in results if not r["return_date"]])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Loans", len(set(r["loan_id"] for r in results)))
        col2.metric("Unique Books", unique_books)
        col3.metric("Active Loans", active_loans)
        if include_authors:
            unique_authors = len(set(r["author_id"] for r in results if r["author_id"]))
            col4.metric("Authors Read", unique_authors)

        display_in_streamlit(net, height=570)

        # Data table
        with st.expander("📋 Loan History Table"):
            df = pd.DataFrame(results)
            df = df[["loan_date", "due_date", "return_date", "book_title", "author_name"]]
            df.columns = ["Loan Date", "Due Date", "Return Date", "Book", "Author"]
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the ETL pipeline has been run to populate Neo4j.")

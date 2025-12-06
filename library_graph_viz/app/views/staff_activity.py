"""Staff Activity View - Shows staff and their processed loans."""

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
    Render the staff activity view.

    Args:
        neo4j: Neo4j connector instance.
    """
    st.subheader("👥 Staff Activity")
    st.markdown("View library staff members and the loans they've processed.")

    try:
        # Query for staff activity
        query = """
            MATCH (s:Staff)<-[:PROCESSED_BY]-(l:Loan)-[:CONTAINS]->(b:Book)
            RETURN
                s.id AS staff_id,
                s.name AS staff_name,
                s.email AS staff_email,
                s.role AS staff_role,
                s.hire_date AS hire_date,
                count(DISTINCT l) AS loan_count,
                collect(DISTINCT b.title)[0..5] AS sample_books
            ORDER BY loan_count DESC
        """
        results = neo4j.run_query(query)

        if not results:
            st.warning("No staff activity found in the database.")
            return

        # Controls
        col1, col2 = st.columns([2, 2])
        with col1:
            max_books_display = st.slider(
                "Sample Books per Staff",
                min_value=1,
                max_value=10,
                value=3,
                help="Number of sample books to show for each staff member",
            )
        with col2:
            scale_nodes = st.checkbox(
                "Scale Nodes by Activity",
                value=True,
                help="Make node size proportional to loan count",
            )

        # Build graph
        nodes = []
        edges = []
        seen_nodes = set()

        # Calculate max loan count for scaling
        max_loans = max(r["loan_count"] for r in results) if results else 1

        for r in results:
            # Staff node
            staff_node_id = f"staff_{r['staff_id']}"
            if staff_node_id not in seen_nodes:
                # Scale size based on loan count
                if scale_nodes:
                    size = 20 + (r["loan_count"] / max_loans) * 40
                else:
                    size = 30

                nodes.append({
                    "id": staff_node_id,
                    "label": f"{r['staff_name']}\n({r['loan_count']} loans)",
                    "type": "Staff",
                    "title": f"Staff: {r['staff_name']}\nRole: {r['staff_role']}\nEmail: {r['staff_email']}\nHired: {r['hire_date']}\nLoans Processed: {r['loan_count']}",
                    "size": size,
                })
                seen_nodes.add(staff_node_id)

            # Sample book nodes
            for i, book_title in enumerate(r["sample_books"][:max_books_display]):
                book_node_id = f"book_{staff_node_id}_{i}"
                if book_node_id not in seen_nodes:
                    nodes.append({
                        "id": book_node_id,
                        "label": book_title[:20] + "..." if len(book_title) > 20 else book_title,
                        "type": "Book",
                        "title": f"Book: {book_title}",
                        "size": 15,
                    })
                    seen_nodes.add(book_node_id)

                    # Staff -> Book edge (through loans)
                    edges.append({
                        "from": staff_node_id,
                        "to": book_node_id,
                        "label": "",
                        "title": "Processed loan for this book",
                    })

        # Create network
        net = create_network(height="550px", layout="force_atlas")
        add_nodes(net, nodes)
        add_edges(net, edges)

        # Statistics
        total_loans = sum(r["loan_count"] for r in results)
        avg_loans = total_loans / len(results) if results else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Staff Members", len(results))
        col2.metric("Total Loans Processed", total_loans)
        col3.metric("Avg Loans/Staff", f"{avg_loans:.1f}")
        col4.metric("Most Active", results[0]["staff_name"] if results else "N/A")

        display_in_streamlit(net, height=570)

        # Staff leaderboard
        with st.expander("📊 Staff Leaderboard"):
            df = pd.DataFrame([
                {
                    "Name": r["staff_name"],
                    "Role": r["staff_role"],
                    "Email": r["staff_email"],
                    "Hire Date": r["hire_date"],
                    "Loans Processed": r["loan_count"],
                }
                for r in results
            ])
            st.dataframe(df, use_container_width=True)

            # Download
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="staff_activity.csv",
                mime="text/csv",
            )

        # Role breakdown
        with st.expander("👔 Activity by Role"):
            role_data = {}
            for r in results:
                role = r["staff_role"]
                if role not in role_data:
                    role_data[role] = {"count": 0, "loans": 0}
                role_data[role]["count"] += 1
                role_data[role]["loans"] += r["loan_count"]

            for role, data in sorted(role_data.items(), key=lambda x: x[1]["loans"], reverse=True):
                st.markdown(f"**{role}**: {data['count']} staff, {data['loans']} loans processed")

    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the ETL pipeline has been run to populate Neo4j.")

"""Books & Authors View - Shows author-book relationships."""

import streamlit as st
import pandas as pd
from etl.neo4j_connector import Neo4jConnector
from app.components.streamlit_graph import (
    display_interactive_graph,
    NODE_COLORS,
)


def render(neo4j: Neo4jConnector) -> None:
    """
    Render the books and authors view.

    Args:
        neo4j: Neo4j connector instance.
    """
    st.subheader("📖 Books & Authors")
    st.markdown("Explore the relationships between authors and their books.")

    # Controls
    col1, col2 = st.columns([2, 2])

    with col1:
        min_books = st.slider(
            "Minimum Books per Author",
            min_value=1,
            max_value=10,
            value=1,
            help="Filter authors by minimum number of books",
        )

    with col2:
        layout = st.selectbox(
            "Layout",
            ["barnes_hut", "force_atlas"],
            key="ba_layout",
        )

    try:
        # Query for authors and books
        query = """
            MATCH (a:Author)-[:WROTE]->(b:Book)
            WITH a, collect(b) AS books, count(b) AS book_count
            WHERE book_count >= $min_books
            UNWIND books AS book
            RETURN
                a.id AS author_id,
                a.name AS author_name,
                book.id AS book_id,
                book.title AS book_title,
                book.publication_year AS publication_year,
                book.isbn AS isbn
            ORDER BY author_name, book_title
        """
        results = neo4j.run_query(query, {"min_books": min_books})

        if not results:
            st.warning("No author-book relationships found with the current filter.")
            return

        # Build unique nodes
        authors = {}
        books = {}
        edges = []

        for r in results:
            # Author node
            author_id = f"author_{r['author_id']}"
            if author_id not in authors:
                authors[author_id] = {
                    "id": author_id,
                    "label": r["author_name"],
                    "type": "Author",
                    "title": f"Author: {r['author_name']}",
                    "size": 35,  # Authors are larger
                }

            # Book node
            book_id = f"book_{r['book_id']}"
            if book_id not in books:
                books[book_id] = {
                    "id": book_id,
                    "label": r["book_title"][:25] + "..." if len(r["book_title"]) > 25 else r["book_title"],
                    "type": "Book",
                    "title": f"Book: {r['book_title']}\nYear: {r['publication_year'] or 'Unknown'}\nISBN: {r['isbn'] or 'N/A'}",
                }

            # Edge
            edges.append({
                "from": author_id,
                "to": book_id,
                "label": "WROTE",
                "title": "WROTE",
            })

        # Combine all nodes
        all_nodes = list(authors.values()) + list(books.values())

        # Display statistics
        col1, col2, col3 = st.columns(3)
        col1.metric("Authors", len(authors))
        col2.metric("Books", len(books))
        col3.metric("Relationships", len(edges))

        # Display the interactive graph
        event = display_interactive_graph(
            nodes=all_nodes,
            edges=edges,
            height=620,
            layout=layout,
            key="books_authors_graph",
        )

        # Handle graph events
        if event:
            if event["type"] == "nodeClick":
                node_data = event.get("nodeData", {})
                with st.sidebar:
                    st.markdown("### Selected Node")
                    st.write(f"**{node_data.get('label', 'Unknown')}**")
                    st.write(f"Type: {node_data.get('type', 'Unknown')}")

        # Data table
        with st.expander("📋 View Data Table"):
            df = pd.DataFrame(results)
            df = df.rename(columns={
                "author_name": "Author",
                "book_title": "Book Title",
                "publication_year": "Year",
                "isbn": "ISBN",
            })
            df = df[["Author", "Book Title", "Year", "ISBN"]]
            st.dataframe(df, width="stretch")

            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="books_authors.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the ETL pipeline has been run to populate Neo4j.")

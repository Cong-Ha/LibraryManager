"""Category Explorer View - Shows books and authors by category."""

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
    Render the category explorer view.

    Args:
        neo4j: Neo4j connector instance.
    """
    st.subheader("📂 Category Explorer")
    st.markdown("Explore books and authors organized by category.")

    try:
        # Get list of categories with book counts
        categories_query = """
            MATCH (c:Category)<-[:BELONGS_TO]-(b:Book)
            RETURN c.id AS id, c.name AS name, c.description AS description, count(b) AS book_count
            ORDER BY book_count DESC
        """
        categories = neo4j.run_query(categories_query)

        if not categories:
            st.warning("No categories found in the database.")
            return

        # Category selector
        category_options = {
            f"{c['name']} ({c['book_count']} books)": c['id']
            for c in categories
        }
        selected_category = st.selectbox(
            "Select Category",
            list(category_options.keys()),
            help="Choose a category to explore",
        )
        category_id = category_options[selected_category]

        # Get category details
        category_info = next(c for c in categories if c['id'] == category_id)

        # Display category info
        st.info(f"**{category_info['name']}**: {category_info['description'] or 'No description available'}")

        # Query for books in category with authors
        query = """
            MATCH (b:Book)-[:BELONGS_TO]->(c:Category {id: $category_id})
            OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
            RETURN
                c.id AS category_id,
                c.name AS category_name,
                b.id AS book_id,
                b.title AS book_title,
                b.publication_year AS publication_year,
                b.isbn AS isbn,
                collect(DISTINCT {id: a.id, name: a.name}) AS authors
            ORDER BY b.title
        """
        results = neo4j.run_query(query, {"category_id": category_id})

        if not results:
            st.info("No books found in this category.")
            return

        # Build graph
        nodes = []
        edges = []
        seen_nodes = set()

        # Add central category node
        category_node_id = f"category_{category_id}"
        nodes.append({
            "id": category_node_id,
            "label": category_info["name"],
            "type": "Category",
            "title": f"Category: {category_info['name']}\nBooks: {category_info['book_count']}",
            "size": 50,  # Larger central node
        })
        seen_nodes.add(category_node_id)

        for r in results:
            # Book node
            book_node_id = f"book_{r['book_id']}"
            if book_node_id not in seen_nodes:
                title = r["book_title"]
                nodes.append({
                    "id": book_node_id,
                    "label": title[:25] + "..." if len(title) > 25 else title,
                    "type": "Book",
                    "title": f"Book: {title}\nYear: {r['publication_year'] or 'Unknown'}\nISBN: {r['isbn'] or 'N/A'}",
                })
                seen_nodes.add(book_node_id)

                # Book -> Category edge
                edges.append({
                    "from": book_node_id,
                    "to": category_node_id,
                    "label": "BELONGS_TO",
                    "title": "BELONGS_TO",
                })

            # Author nodes
            for author in r["authors"]:
                if author["id"]:
                    author_node_id = f"author_{author['id']}"
                    if author_node_id not in seen_nodes:
                        nodes.append({
                            "id": author_node_id,
                            "label": author["name"],
                            "type": "Author",
                            "title": f"Author: {author['name']}",
                        })
                        seen_nodes.add(author_node_id)

                    # Author -> Book edge
                    edge_id = f"{author_node_id}_{book_node_id}"
                    if edge_id not in seen_nodes:
                        edges.append({
                            "from": author_node_id,
                            "to": book_node_id,
                            "label": "WROTE",
                            "title": "WROTE",
                        })
                        seen_nodes.add(edge_id)

        # Create network
        net = create_network(height="550px", layout="force_atlas")
        add_nodes(net, nodes)
        add_edges(net, edges)

        # Statistics
        unique_authors = len([n for n in nodes if n["type"] == "Author"])
        col1, col2, col3 = st.columns(3)
        col1.metric("Books in Category", len(results))
        col2.metric("Authors", unique_authors)
        col3.metric("Total Connections", len(edges))

        display_in_streamlit(net, height=570)

        # Data table
        with st.expander("📋 Books in Category"):
            table_data = []
            for r in results:
                authors_str = ", ".join([a["name"] for a in r["authors"] if a["name"]])
                table_data.append({
                    "Title": r["book_title"],
                    "Year": r["publication_year"] or "Unknown",
                    "Authors": authors_str or "Unknown",
                    "ISBN": r["isbn"] or "N/A",
                })

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)

            # Download
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"category_{category_info['name'].lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the ETL pipeline has been run to populate Neo4j.")

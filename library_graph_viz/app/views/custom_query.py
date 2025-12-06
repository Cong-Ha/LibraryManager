"""Custom Cypher Query View - Execute custom queries against Neo4j."""

import streamlit as st
import pandas as pd
from etl.neo4j_connector import Neo4jConnector


# Example queries for users
EXAMPLE_QUERIES = {
    "Find all books by a specific author": """
MATCH (a:Author {name: 'Jane Austen'})-[:WROTE]->(b:Book)
RETURN a.name AS author, b.title AS book, b.publication_year AS year
ORDER BY year""",

    "Find members with unreturned books": """
MATCH (m:Member)-[:BORROWED]->(l:Loan)-[:CONTAINS]->(b:Book)
WHERE l.return_date IS NULL
RETURN m.name AS member, b.title AS book, l.due_date AS due_date
ORDER BY l.due_date""",

    "Most borrowed books": """
MATCH (b:Book)<-[:CONTAINS]-(l:Loan)
RETURN b.title AS book, count(l) AS borrow_count
ORDER BY borrow_count DESC
LIMIT 10""",

    "Authors with most books": """
MATCH (a:Author)-[:WROTE]->(b:Book)
RETURN a.name AS author, count(b) AS book_count
ORDER BY book_count DESC
LIMIT 10""",

    "Category popularity by loans": """
MATCH (c:Category)<-[:BELONGS_TO]-(b:Book)<-[:CONTAINS]-(l:Loan)
RETURN c.name AS category, count(l) AS total_loans
ORDER BY total_loans DESC""",

    "Staff with most processed loans": """
MATCH (s:Staff)<-[:PROCESSED_BY]-(l:Loan)
RETURN s.name AS staff, s.role AS role, count(l) AS loans_processed
ORDER BY loans_processed DESC""",

    "Members who read books by same author": """
MATCH (m1:Member)-[:BORROWED]->(:Loan)-[:CONTAINS]->(b:Book)<-[:WROTE]-(a:Author)
MATCH (m2:Member)-[:BORROWED]->(:Loan)-[:CONTAINS]->(b2:Book)<-[:WROTE]-(a)
WHERE m1 <> m2 AND b <> b2
RETURN m1.name AS member1, m2.name AS member2, a.name AS shared_author,
       collect(DISTINCT b.title)[0..3] AS books_m1,
       collect(DISTINCT b2.title)[0..3] AS books_m2
LIMIT 20""",

    "Graph statistics": """
MATCH (n)
WITH labels(n)[0] AS label, count(*) AS count
RETURN label, count
ORDER BY count DESC""",
}


def render(neo4j: Neo4jConnector) -> None:
    """
    Render the custom Cypher query view.

    Args:
        neo4j: Neo4j connector instance.
    """
    st.subheader("🔍 Custom Cypher Query")
    st.markdown("Execute custom Cypher queries against the Neo4j graph database.")

    # Example queries section
    with st.expander("📝 Example Queries", expanded=False):
        st.markdown("Click on a query to load it into the editor:")

        for name, query in EXAMPLE_QUERIES.items():
            if st.button(f"📋 {name}", key=f"example_{name}"):
                st.session_state["custom_query"] = query

            with st.container():
                st.code(query, language="cypher")
                st.markdown("---")

    # Query editor
    st.markdown("### Query Editor")

    # Initialize session state for query
    if "custom_query" not in st.session_state:
        st.session_state["custom_query"] = ""

    query = st.text_area(
        "Enter Cypher Query",
        value=st.session_state.get("custom_query", ""),
        height=200,
        placeholder="MATCH (n) RETURN n LIMIT 10",
        help="Enter a valid Cypher query. Results will be displayed as a table.",
    )

    # Update session state
    st.session_state["custom_query"] = query

    # Controls
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        execute_button = st.button("▶️ Execute Query", type="primary")

    with col2:
        clear_button = st.button("🗑️ Clear")
        if clear_button:
            st.session_state["custom_query"] = ""
            st.rerun()

    with col3:
        result_limit = st.number_input(
            "Result Limit",
            min_value=1,
            max_value=1000,
            value=100,
            help="Maximum number of results to return",
        )

    # Execute query
    if execute_button and query.strip():
        try:
            with st.spinner("Executing query..."):
                # Add LIMIT if not present
                query_lower = query.lower()
                if "limit" not in query_lower and result_limit:
                    # Check if it ends with a number (likely already has limit)
                    final_query = f"{query.rstrip().rstrip(';')} LIMIT {result_limit}"
                else:
                    final_query = query

                results = neo4j.run_query(final_query)

                if results:
                    st.success(f"Query returned {len(results)} results")

                    # Display as DataFrame
                    df = pd.DataFrame(results)
                    st.dataframe(df, use_container_width=True)

                    # Download options
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv,
                            file_name="query_results.csv",
                            mime="text/csv",
                        )

                    with col2:
                        json_data = df.to_json(orient="records", indent=2)
                        st.download_button(
                            label="📥 Download as JSON",
                            data=json_data,
                            file_name="query_results.json",
                            mime="application/json",
                        )

                    # Show query info
                    with st.expander("ℹ️ Query Info"):
                        st.code(final_query, language="cypher")
                        st.text(f"Columns: {', '.join(df.columns)}")
                        st.text(f"Rows returned: {len(df)}")

                else:
                    st.info("Query executed successfully but returned no results.")

        except Exception as e:
            st.error(f"Query Error: {e}")
            st.info(
                "Tips:\n"
                "- Check your Cypher syntax\n"
                "- Make sure node labels and property names are correct\n"
                "- Verify relationships exist in the database"
            )

    elif execute_button:
        st.warning("Please enter a query to execute.")

    # Query help section
    with st.expander("❓ Cypher Quick Reference"):
        st.markdown("""
        ### Common Patterns

        **Match nodes:**
        ```cypher
        MATCH (n:Label) RETURN n
        ```

        **Match with properties:**
        ```cypher
        MATCH (n:Label {property: 'value'}) RETURN n
        ```

        **Match relationships:**
        ```cypher
        MATCH (a)-[r:RELATIONSHIP]->(b) RETURN a, r, b
        ```

        **Filter results:**
        ```cypher
        MATCH (n) WHERE n.property > 10 RETURN n
        ```

        **Aggregate:**
        ```cypher
        MATCH (n) RETURN count(n), avg(n.value)
        ```

        **Order and limit:**
        ```cypher
        MATCH (n) RETURN n ORDER BY n.name LIMIT 10
        ```

        ### Node Labels in This Database
        - `Member`, `Book`, `Author`, `Category`, `Staff`, `Loan`, `Fine`

        ### Relationship Types
        - `WROTE` (Author → Book)
        - `BELONGS_TO` (Book → Category)
        - `BORROWED` (Member → Loan)
        - `CONTAINS` (Loan → Book)
        - `PROCESSED_BY` (Loan → Staff)
        - `HAS_FINE` (Loan → Fine)
        """)

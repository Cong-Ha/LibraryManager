"""Analytics View - Advanced analytics and recommendations."""

import streamlit as st
import pandas as pd
from etl.neo4j_connector import Neo4jConnector
from app.components.streamlit_graph import display_interactive_graph


def render(neo4j: Neo4jConnector) -> None:
    """
    Render the analytics view with recommendations and insights.

    Args:
        neo4j: Neo4j connector instance.
    """
    st.subheader("📊 Analytics & Recommendations")
    st.markdown("Advanced analytics powered by graph queries.")

    # Tab selection
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 Book Recommendations",
        "🔗 Member Connections",
        "📈 Trends & Patterns",
        "🌟 Top Performers",
    ])

    with tab1:
        render_book_recommendations(neo4j)

    with tab2:
        render_member_connections(neo4j)

    with tab3:
        render_trends(neo4j)

    with tab4:
        render_top_performers(neo4j)


def render_book_recommendations(neo4j: Neo4jConnector) -> None:
    """Render book recommendations based on borrowing patterns."""
    st.markdown("### 📚 Book Recommendations")
    st.markdown("Find books similar to what you've read based on shared authors and categories.")

    try:
        # Get books for selection
        books_query = """
            MATCH (b:Book)
            RETURN b.id AS id, b.title AS title
            ORDER BY b.title
            LIMIT 100
        """
        books = neo4j.run_query(books_query)

        if not books:
            st.warning("No books found.")
            return

        book_options = {b['title']: b['id'] for b in books}
        selected_book = st.selectbox(
            "Select a book you liked:",
            list(book_options.keys()),
            help="We'll find similar books based on shared authors and categories",
        )
        book_id = book_options[selected_book]

        if st.button("Find Similar Books", type="primary"):
            # Find similar books by same author or same category
            query = """
                MATCH (b:Book {id: $book_id})
                OPTIONAL MATCH (b)<-[:WROTE]-(a:Author)-[:WROTE]->(rec:Book)
                WHERE rec <> b
                WITH b, collect(DISTINCT {book: rec, reason: 'Same Author: ' + a.name}) AS author_recs

                OPTIONAL MATCH (b)-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(rec2:Book)
                WHERE rec2 <> b
                WITH b, author_recs, collect(DISTINCT {book: rec2, reason: 'Same Category: ' + c.name}) AS category_recs

                WITH b, author_recs + category_recs AS all_recs
                UNWIND all_recs AS rec
                WITH rec.book AS book, collect(DISTINCT rec.reason) AS reasons
                WHERE book IS NOT NULL
                RETURN
                    book.id AS id,
                    book.title AS title,
                    book.publication_year AS year,
                    reasons[0..3] AS matching_reasons
                LIMIT 10
            """
            results = neo4j.run_query(query, {"book_id": book_id})

            if results:
                st.success(f"Found {len(results)} recommendations for '{selected_book}'")

                for r in results:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{r['title']}** ({r['year'] or 'Unknown year'})")
                            for reason in r['matching_reasons']:
                                st.caption(f"• {reason}")
                        st.markdown("---")
            else:
                st.info("No similar books found. Try a different book.")

    except Exception as e:
        st.error(f"Error: {e}")


def render_member_connections(neo4j: Neo4jConnector) -> None:
    """Find connections between members through shared books."""
    st.markdown("### 🔗 Member Connections")
    st.markdown("Discover how members are connected through shared reading interests.")

    try:
        # Get members
        members_query = """
            MATCH (m:Member)-[:BORROWED]->(:Loan)
            RETURN m.id AS id, m.name AS name
            ORDER BY m.name
        """
        members = neo4j.run_query(members_query)

        if not members:
            st.warning("No members with borrowing history found.")
            return

        member_options = {m['name']: m['id'] for m in members}
        selected_member = st.selectbox(
            "Select a member:",
            list(member_options.keys()),
            key="member_connections",
        )
        member_id = member_options[selected_member]

        if st.button("Find Connections", type="primary"):
            # Find other members who borrowed same books
            query = """
                MATCH (m1:Member {id: $member_id})-[:BORROWED]->(:Loan)-[:CONTAINS]->(b:Book)
                      <-[:CONTAINS]-(:Loan)<-[:BORROWED]-(m2:Member)
                WHERE m1 <> m2
                WITH m1, m2, collect(DISTINCT b.title) AS shared_books
                RETURN
                    m2.id AS member_id,
                    m2.name AS member_name,
                    size(shared_books) AS shared_count,
                    shared_books[0..5] AS sample_books
                ORDER BY shared_count DESC
                LIMIT 10
            """
            results = neo4j.run_query(query, {"member_id": member_id})

            if results:
                st.success(f"Found {len(results)} members with similar reading interests")

                # Build visualization
                nodes = [{
                    "id": f"m_{member_id}",
                    "label": selected_member,
                    "type": "Member",
                    "size": 40,
                    "title": f"Selected: {selected_member}",
                }]

                edges = []

                for r in results:
                    node_id = f"m_{r['member_id']}"
                    nodes.append({
                        "id": node_id,
                        "label": r["member_name"],
                        "type": "Member",
                        "size": 20 + r["shared_count"] * 2,
                        "title": f"{r['member_name']}\nShared books: {r['shared_count']}",
                    })
                    edges.append({
                        "from": f"m_{member_id}",
                        "to": node_id,
                        "label": str(r["shared_count"]),
                        "title": f"Shared {r['shared_count']} books: {', '.join(r['sample_books'][:3])}",
                    })

                display_interactive_graph(
                    nodes=nodes,
                    edges=edges,
                    height=420,
                    layout="force_atlas",
                    key="member_connections_graph",
                )

                # Table
                df = pd.DataFrame([{
                    "Member": r["member_name"],
                    "Shared Books": r["shared_count"],
                    "Sample": ", ".join(r["sample_books"][:3]),
                } for r in results])
                st.dataframe(df, width="stretch")

            else:
                st.info("No connections found. This member may have unique reading tastes!")

    except Exception as e:
        st.error(f"Error: {e}")


def render_trends(neo4j: Neo4jConnector) -> None:
    """Show borrowing trends and patterns."""
    st.markdown("### 📈 Borrowing Trends & Patterns")

    try:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Most Popular Books")
            popular_query = """
                MATCH (b:Book)<-[:CONTAINS]-(l:Loan)
                RETURN b.title AS book, count(l) AS borrows
                ORDER BY borrows DESC
                LIMIT 10
            """
            popular = neo4j.run_query(popular_query)

            if popular:
                df = pd.DataFrame(popular)
                st.bar_chart(df.set_index("book")["borrows"])

        with col2:
            st.markdown("#### Most Active Categories")
            category_query = """
                MATCH (c:Category)<-[:BELONGS_TO]-(b:Book)<-[:CONTAINS]-(l:Loan)
                RETURN c.name AS category, count(l) AS borrows
                ORDER BY borrows DESC
            """
            categories = neo4j.run_query(category_query)

            if categories:
                df = pd.DataFrame(categories)
                st.bar_chart(df.set_index("category")["borrows"])

        # Overdue analysis
        st.markdown("#### 📅 Loan Status Overview")
        status_query = """
            MATCH (l:Loan)
            RETURN
                CASE
                    WHEN l.return_date IS NOT NULL THEN 'Returned'
                    WHEN l.due_date < date() THEN 'Overdue'
                    ELSE 'Active'
                END AS status,
                count(l) AS count
        """
        status = neo4j.run_query(status_query)

        if status:
            cols = st.columns(len(status))
            for i, s in enumerate(status):
                cols[i].metric(s["status"], s["count"])

    except Exception as e:
        st.error(f"Error: {e}")


def render_top_performers(neo4j: Neo4jConnector) -> None:
    """Show top performing entities."""
    st.markdown("### 🌟 Top Performers")

    try:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Most Prolific Authors")
            authors_query = """
                MATCH (a:Author)-[:WROTE]->(b:Book)
                RETURN a.name AS author, count(b) AS books
                ORDER BY books DESC
                LIMIT 10
            """
            authors = neo4j.run_query(authors_query)

            if authors:
                for i, a in enumerate(authors, 1):
                    st.markdown(f"{i}. **{a['author']}** - {a['books']} books")

        with col2:
            st.markdown("#### Most Active Members")
            members_query = """
                MATCH (m:Member)-[:BORROWED]->(l:Loan)
                RETURN m.name AS member, count(l) AS loans
                ORDER BY loans DESC
                LIMIT 10
            """
            members = neo4j.run_query(members_query)

            if members:
                for i, m in enumerate(members, 1):
                    st.markdown(f"{i}. **{m['member']}** - {m['loans']} loans")

        # Cross-category readers
        st.markdown("#### 📖 Most Diverse Readers")
        st.caption("Members who read from the most categories")

        diverse_query = """
            MATCH (m:Member)-[:BORROWED]->(:Loan)-[:CONTAINS]->(b:Book)-[:BELONGS_TO]->(c:Category)
            WITH m, count(DISTINCT c) AS category_count, collect(DISTINCT c.name)[0..5] AS categories
            RETURN m.name AS member, category_count, categories
            ORDER BY category_count DESC
            LIMIT 5
        """
        diverse = neo4j.run_query(diverse_query)

        if diverse:
            df = pd.DataFrame([{
                "Member": d["member"],
                "Categories Read": d["category_count"],
                "Sample Categories": ", ".join(d["categories"]),
            } for d in diverse])
            st.dataframe(df, width="stretch")

    except Exception as e:
        st.error(f"Error: {e}")

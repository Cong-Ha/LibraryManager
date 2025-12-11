"""OLAP Analytics View - Star Schema Analytical Queries."""

import streamlit as st
import pandas as pd
from etl.mysql_connector import MySQLConnector
from config.settings import get_settings


@st.cache_data(ttl=300)
def get_olap_table_counts() -> dict:
    """Fetch OLAP table counts with caching (5 minute TTL)."""
    settings = get_settings()
    with MySQLConnector(settings, database="olap") as db:
        counts = {}
        for table in ["dim_date", "dim_member", "dim_book", "dim_staff", "dim_category", "fact_loan"]:
            counts[table] = db.get_table_count(table)
        return counts


@st.cache_data(ttl=60)
def run_olap_query(query_key: str, sql: str) -> list:
    """Execute OLAP query with caching (1 minute TTL)."""
    settings = get_settings()
    with MySQLConnector(settings, database="olap") as db:
        return db.execute_query(sql)


# OLAP Analytical Queries from Week 4
OLAP_QUERIES = {
    "monthly_trends": {
        "title": "Monthly Loan Trends",
        "description": "Track borrowing patterns over time by month and year",
        "sql": """SELECT
    d.year,
    d.month_name,
    d.month_num,
    COUNT(*) AS total_loans,
    SUM(f.loan_duration_days) AS total_loan_days,
    ROUND(AVG(f.loan_duration_days), 1) AS avg_loan_duration,
    SUM(f.fine_amount) AS total_fines
FROM fact_loan f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month_name, d.month_num
ORDER BY d.year, d.month_num;""",
        "chart_type": "line",
        "chart_x": "month_name",
        "chart_y": "total_loans",
    },
    "top_books": {
        "title": "Top Borrowed Books",
        "description": "Most popular books by number of loans",
        "sql": """SELECT
    b.title,
    b.authors,
    b.publication_year,
    COUNT(*) AS times_borrowed,
    ROUND(AVG(f.loan_duration_days), 1) AS avg_duration,
    SUM(f.fine_amount) AS total_fines
FROM fact_loan f
JOIN dim_book b ON f.book_key = b.book_key
GROUP BY b.book_key, b.title, b.authors, b.publication_year
ORDER BY times_borrowed DESC
LIMIT 20;""",
        "chart_type": "bar",
        "chart_x": "title",
        "chart_y": "times_borrowed",
    },
    "category_analysis": {
        "title": "Loans by Category (Weighted)",
        "description": "Category analysis using bridge table weighting to avoid double-counting",
        "sql": """SELECT
    c.category_name,
    ROUND(SUM(bc.weight_factor), 0) AS weighted_loans,
    COUNT(DISTINCT f.loan_key) AS raw_loan_count,
    ROUND(AVG(f.loan_duration_days), 1) AS avg_duration
FROM fact_loan f
JOIN dim_book b ON f.book_key = b.book_key
JOIN bridge_book_category bc ON b.book_key = bc.book_key
JOIN dim_category c ON bc.category_key = c.category_key
GROUP BY c.category_key, c.category_name
ORDER BY weighted_loans DESC;""",
        "chart_type": "bar",
        "chart_x": "category_name",
        "chart_y": "weighted_loans",
    },
    "staff_performance": {
        "title": "Staff Performance",
        "description": "Analyze loan processing by staff members",
        "sql": """SELECT
    s.full_name,
    s.role,
    COUNT(*) AS loans_processed,
    ROUND(AVG(f.loan_duration_days), 1) AS avg_loan_duration,
    SUM(CASE WHEN f.days_overdue > 0 THEN 1 ELSE 0 END) AS overdue_loans,
    ROUND(100.0 * SUM(CASE WHEN f.days_overdue > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS overdue_pct
FROM fact_loan f
JOIN dim_staff s ON f.staff_key = s.staff_key
GROUP BY s.staff_key, s.full_name, s.role
ORDER BY loans_processed DESC;""",
        "chart_type": "bar",
        "chart_x": "full_name",
        "chart_y": "loans_processed",
    },
    "member_behavior": {
        "title": "Member Behavior Analysis",
        "description": "Understand member borrowing patterns and fine history",
        "sql": """SELECT
    m.full_name,
    m.membership_year,
    m.status,
    COUNT(*) AS total_loans,
    ROUND(AVG(f.loan_duration_days), 1) AS avg_duration,
    SUM(f.days_overdue) AS total_days_overdue,
    SUM(f.fine_amount) AS total_fines
FROM fact_loan f
JOIN dim_member m ON f.member_key = m.member_key
GROUP BY m.member_key, m.full_name, m.membership_year, m.status
ORDER BY total_loans DESC
LIMIT 25;""",
        "chart_type": "bar",
        "chart_x": "full_name",
        "chart_y": "total_loans",
    },
    "weekend_weekday": {
        "title": "Weekend vs Weekday Analysis",
        "description": "Compare borrowing patterns between weekends and weekdays",
        "sql": """SELECT
    CASE WHEN d.is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    d.day_name,
    COUNT(*) AS total_loans,
    ROUND(AVG(f.loan_duration_days), 1) AS avg_duration,
    SUM(f.fine_amount) AS total_fines
FROM fact_loan f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.is_weekend, d.day_name, d.day_of_week
ORDER BY d.day_of_week;""",
        "chart_type": "bar",
        "chart_x": "day_name",
        "chart_y": "total_loans",
    },
    "year_over_year": {
        "title": "Year-over-Year Comparison",
        "description": "Compare metrics across years",
        "sql": """SELECT
    d.year,
    COUNT(*) AS total_loans,
    COUNT(DISTINCT f.member_key) AS unique_members,
    COUNT(DISTINCT f.book_key) AS unique_books,
    ROUND(AVG(f.loan_duration_days), 1) AS avg_duration,
    SUM(f.fine_amount) AS total_fines,
    SUM(CASE WHEN f.days_overdue > 0 THEN 1 ELSE 0 END) AS overdue_count
FROM fact_loan f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year
ORDER BY d.year;""",
        "chart_type": "bar",
        "chart_x": "year",
        "chart_y": "total_loans",
    },
}


def render(neo4j=None) -> None:
    """Render the OLAP analytics view."""
    # Initialize session state for query results
    if "olap_query_results" not in st.session_state:
        st.session_state.olap_query_results = {}

    st.header("OLAP Analytics - Star Schema Queries")
    st.markdown("""
    This view demonstrates **analytical queries** against the dimensional model (star schema).
    These queries are optimized for aggregation and reporting, leveraging:
    - **Fact table** for measures (counts, sums, averages)
    - **Dimension tables** for slicing and filtering
    - **Bridge table** for weighted category analysis
    """)

    # Database connection status
    try:
        counts = get_olap_table_counts()

        st.success(f"Connected to OLAP database | Fact records: {counts.get('fact_loan', 0):,}")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Date Dimension", f"{counts.get('dim_date', 0):,}")
        with col2:
            st.metric("Member Dimension", f"{counts.get('dim_member', 0):,}")
        with col3:
            st.metric("Book Dimension", f"{counts.get('dim_book', 0):,}")
        with col4:
            st.metric("Staff Dimension", f"{counts.get('dim_staff', 0):,}")
        with col5:
            st.metric("Category Dimension", f"{counts.get('dim_category', 0):,}")

    except Exception as e:
        st.error(f"Could not connect to OLAP database: {str(e)}")
        st.info("Make sure the library_olap database exists and is populated with the ETL process.")
        return

    st.divider()

    # Create tabs for each query
    tab_titles = [q["title"] for q in OLAP_QUERIES.values()]
    tabs = st.tabs(tab_titles)

    for i, (query_key, query_info) in enumerate(OLAP_QUERIES.items()):
        with tabs[i]:
            st.subheader(query_info["title"])
            st.markdown(f"*{query_info['description']}*")

            # Show/hide SQL toggle
            with st.expander("View SQL Query", expanded=False):
                st.code(query_info["sql"], language="sql")

            # Execute query button
            if st.button(f"Run Analysis", key=f"run_{query_key}"):
                with st.spinner("Running query..."):
                    try:
                        results = run_olap_query(query_key, query_info["sql"])
                        st.session_state.olap_query_results[query_key] = {
                            "results": results,
                            "error": None
                        }
                    except Exception as e:
                        st.session_state.olap_query_results[query_key] = {
                            "results": None,
                            "error": str(e)
                        }

            # Display results from session state
            if query_key in st.session_state.olap_query_results:
                stored = st.session_state.olap_query_results[query_key]

                if stored["error"]:
                    st.error(f"Query failed: {stored['error']}")
                elif stored["results"]:
                    results = stored["results"]
                    df = pd.DataFrame(results)

                    # Display chart if applicable
                    if query_info.get("chart_type") and len(df) > 0:
                        st.subheader("Visualization")

                        chart_x = query_info["chart_x"]
                        chart_y = query_info["chart_y"]

                        # Prepare chart data
                        if chart_x in df.columns and chart_y in df.columns:
                            chart_df = df[[chart_x, chart_y]].copy()
                            chart_df = chart_df.set_index(chart_x)

                            if query_info["chart_type"] == "bar":
                                st.bar_chart(chart_df)
                            elif query_info["chart_type"] == "line":
                                st.line_chart(chart_df)

                    # Display data table
                    st.subheader("Results")
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"Returned {len(results)} rows")

                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{query_key}_results.csv",
                        mime="text/csv",
                        key=f"download_{query_key}",
                    )
                else:
                    st.info("Query returned no results. The OLAP database may need to be populated.")

    # Summary section
    st.divider()
    st.subheader("Star Schema Benefits")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Query Performance:**
        - Denormalized dimensions reduce JOINs
        - Pre-calculated measures speed aggregation
        - Date dimension enables time intelligence
        - Bridge table handles M:N with weighting
        """)

    with col2:
        st.markdown("""
        **Analytical Capabilities:**
        - Slice by any dimension
        - Drill down/up time hierarchies
        - Compare across categories
        - Track trends over time
        """)

    st.divider()
    st.subheader("OLAP vs OLTP Comparison")

    comparison_data = {
        "Aspect": ["Purpose", "Schema", "Queries", "Updates", "Data Volume"],
        "OLTP (Normalized)": [
            "Transaction processing",
            "3NF normalized (9 tables)",
            "Simple, row-level",
            "Frequent INSERT/UPDATE",
            "Current operational data",
        ],
        "OLAP (Star Schema)": [
            "Analytical reporting",
            "Dimensional (fact + dims)",
            "Complex aggregations",
            "Batch ETL loads",
            "Historical, aggregated",
        ],
    }

    st.table(pd.DataFrame(comparison_data))

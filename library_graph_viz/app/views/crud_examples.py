"""CRUD Operations Examples View."""

import streamlit as st
import pandas as pd
from etl.mysql_connector import MySQLConnector
from config.settings import get_settings


@st.cache_data(ttl=60)
def get_table_statistics() -> dict:
    """Fetch table counts from MySQL with caching (60 second TTL)."""
    settings = get_settings()
    with MySQLConnector(settings, database="oltp") as db:
        counts = {}
        for table in ["member", "book", "author", "category", "staff", "loan", "fine"]:
            counts[table.upper()] = db.get_table_count(table)
        return counts


# SQL Query Examples
CRUD_QUERIES = {
    "CREATE": {
        "title": "CREATE (INSERT)",
        "description": "Add new records to the database",
        "examples": [
            {
                "name": "Add New Member",
                "sql": """INSERT INTO member (first_name, last_name, email, phone, membership_date, status)
VALUES ('Alexandra', 'Peterson', 'alex.peterson@email.com', '555-0199', CURDATE(), 'active');""",
                "explanation": "Adds a new library member with today's date as membership date.",
                "readonly": False,
            },
            {
                "name": "Add New Book",
                "sql": """INSERT INTO book (isbn, title, publication_year, copies_available)
VALUES ('978-1234567890', 'New Book Title', 2024, 5);""",
                "explanation": "Adds a new book to the library catalog.",
                "readonly": False,
            },
        ],
    },
    "READ": {
        "title": "READ (SELECT)",
        "description": "Query and retrieve data from the database",
        "examples": [
            {
                "name": "Active & Overdue Loans",
                "sql": """SELECT
    l.id AS loan_id,
    CONCAT(m.first_name, ' ', m.last_name) AS member_name,
    m.email AS member_email,
    b.title AS book_title,
    l.loan_date,
    l.due_date,
    l.status AS loan_status,
    DATEDIFF(CURDATE(), l.due_date) AS days_overdue
FROM loan l
JOIN member m ON l.member_id = m.id
JOIN book b ON l.book_id = b.id
WHERE l.status IN ('active', 'overdue')
ORDER BY l.due_date ASC
LIMIT 20;""",
                "explanation": "Shows all active and overdue loans with member and book details, ordered by due date.",
                "readonly": True,
            },
            {
                "name": "Books by Author",
                "sql": """SELECT
    b.title,
    b.isbn,
    b.publication_year,
    b.copies_available,
    CONCAT(a.first_name, ' ', a.last_name) AS author_name,
    GROUP_CONCAT(DISTINCT c.name ORDER BY c.name SEPARATOR ', ') AS categories
FROM book b
JOIN book_author ba ON b.id = ba.book_id
JOIN author a ON ba.author_id = a.id
LEFT JOIN book_category bc ON b.id = bc.book_id
LEFT JOIN category c ON bc.category_id = c.id
GROUP BY b.id, b.title, b.isbn, b.publication_year, b.copies_available, a.first_name, a.last_name
LIMIT 20;""",
                "explanation": "Shows books with their authors and categories using JOINs and GROUP_CONCAT.",
                "readonly": True,
            },
            {
                "name": "Books Never Borrowed",
                "sql": """SELECT b.title, b.isbn, b.copies_available
FROM book b
LEFT JOIN loan l ON b.id = l.book_id
WHERE l.id IS NULL
LIMIT 20;""",
                "explanation": "Uses LEFT JOIN to find books that have never been checked out.",
                "readonly": True,
            },
            {
                "name": "Members with Unpaid Fines",
                "sql": """SELECT
    CONCAT(m.first_name, ' ', m.last_name) AS member_name,
    m.email,
    SUM(f.amount) AS total_unpaid_fines,
    COUNT(f.id) AS fine_count
FROM member m
JOIN loan l ON m.id = l.member_id
JOIN fine f ON l.id = f.loan_id
WHERE f.paid_status = 'unpaid'
GROUP BY m.id, m.first_name, m.last_name, m.email
ORDER BY total_unpaid_fines DESC
LIMIT 20;""",
                "explanation": "Aggregates unpaid fines by member using JOINs and GROUP BY.",
                "readonly": True,
            },
            {
                "name": "Most Borrowed Books",
                "sql": """SELECT
    b.title,
    CONCAT(a.first_name, ' ', a.last_name) AS author,
    COUNT(l.id) AS times_borrowed
FROM book b
JOIN book_author ba ON b.id = ba.book_id
JOIN author a ON ba.author_id = a.id
LEFT JOIN loan l ON b.id = l.book_id
GROUP BY b.id, b.title, a.first_name, a.last_name
ORDER BY times_borrowed DESC
LIMIT 10;""",
                "explanation": "Counts loan records per book to find the most popular titles.",
                "readonly": True,
            },
        ],
    },
    "UPDATE": {
        "title": "UPDATE",
        "description": "Modify existing records in the database",
        "examples": [
            {
                "name": "Mark Loan as Returned",
                "sql": """UPDATE loan
SET
    return_date = CURDATE(),
    status = 'returned'
WHERE id = 3;""",
                "explanation": "Updates a loan record when a book is returned, setting return_date and status.",
                "readonly": False,
            },
            {
                "name": "Reactivate Member",
                "sql": """UPDATE member
SET status = 'active'
WHERE id = 4;""",
                "explanation": "Changes a member's status from 'suspended' to 'active' after resolving issues.",
                "readonly": False,
            },
        ],
    },
    "DELETE": {
        "title": "DELETE",
        "description": "Remove records from the database",
        "examples": [
            {
                "name": "Remove Author",
                "sql": """DELETE FROM author
WHERE first_name = 'Test' AND last_name = 'Author';""",
                "explanation": "Removes a mistakenly entered author record. CASCADE rules may affect related records.",
                "readonly": False,
            },
        ],
    },
}


def render(neo4j=None) -> None:
    """Render the CRUD examples view."""
    st.header("CRUD Operations Examples")
    st.markdown("""
    This view demonstrates the four fundamental database operations using the Library Management System.
    **Read-only queries** can be executed against the live database. Write operations are shown for reference only.
    """)

    # Create tabs for each CRUD operation
    tabs = st.tabs(["CREATE", "READ", "UPDATE", "DELETE", "Summary"])

    for i, (operation, data) in enumerate(CRUD_QUERIES.items()):
        with tabs[i]:
            st.subheader(f"{data['title']}")
            st.markdown(f"*{data['description']}*")
            st.divider()

            for example in data["examples"]:
                with st.expander(f"**{example['name']}**", expanded=(i == 1)):  # Expand READ by default
                    st.markdown(f"_{example['explanation']}_")

                    # Show SQL with syntax highlighting
                    st.code(example["sql"], language="sql")

                    # Only allow execution of read-only queries
                    if example["readonly"]:
                        if st.button(f"Run Query", key=f"run_{operation}_{example['name']}"):
                            try:
                                settings = get_settings()
                                with MySQLConnector(settings, database="oltp") as db:
                                    results = db.execute_query(example["sql"])

                                if results:
                                    df = pd.DataFrame(results)
                                    st.dataframe(df, width="stretch")
                                    st.caption(f"Returned {len(results)} rows")
                                else:
                                    st.info("Query returned no results.")
                            except Exception as e:
                                st.error(f"Query failed: {str(e)}")
                    else:
                        st.warning("This is a write operation. Shown for reference only - not executed.")

    # Summary tab
    with tabs[4]:
        st.subheader("CRUD Operations Summary")

        summary_data = {
            "Operation": ["CREATE", "READ", "UPDATE", "DELETE"],
            "SQL Command": ["INSERT", "SELECT", "UPDATE", "DELETE"],
            "Purpose": [
                "Add new records to tables",
                "Query and retrieve data",
                "Modify existing records",
                "Remove records from tables",
            ],
            "Example Use Case": [
                "New member registration",
                "View active/overdue loans",
                "Mark book as returned",
                "Remove erroneous entry",
            ],
        }

        st.table(pd.DataFrame(summary_data))

        st.divider()
        st.subheader("Key SQL Concepts Demonstrated")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **JOIN Operations:**
            - `INNER JOIN` - Match records in both tables
            - `LEFT JOIN` - Include all from left table
            - Multi-table JOINs for complex queries

            **Aggregation:**
            - `COUNT()` - Count records
            - `SUM()` - Sum values
            - `GROUP BY` - Group for aggregation
            - `GROUP_CONCAT()` - Concatenate grouped values
            """)

        with col2:
            st.markdown("""
            **Filtering & Sorting:**
            - `WHERE` - Filter conditions
            - `IN ()` - Multiple value matching
            - `ORDER BY` - Sort results
            - `LIMIT` - Restrict result count

            **Date Functions:**
            - `CURDATE()` - Current date
            - `DATEDIFF()` - Calculate date difference
            """)

        st.divider()
        st.subheader("Database Statistics")

        # Show current table counts (cached for 60 seconds)
        try:
            counts = get_table_statistics()

            col1, col2, col3, col4 = st.columns(4)
            tables = list(counts.items())

            for i, (table, count) in enumerate(tables):
                col = [col1, col2, col3, col4][i % 4]
                with col:
                    st.metric(table, f"{count:,}")

        except Exception as e:
            st.error(f"Could not fetch statistics: {str(e)}")

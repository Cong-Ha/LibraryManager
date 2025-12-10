"""ERD Visualization for OLTP (Normalized) Schema."""

import streamlit as st
from app.components.graph_builder import (
    create_network,
    add_nodes,
    add_edges,
    display_in_streamlit,
    ERD_OLTP_COLORS,
    ERD_OLTP_SHAPES,
    ERD_OLTP_SIZES,
)


# OLTP Schema Definition
OLTP_TABLES = {
    "member": {
        "columns": [
            "id INT PK",
            "first_name VARCHAR(50)",
            "last_name VARCHAR(50)",
            "email VARCHAR(100) UNIQUE",
            "phone VARCHAR(20)",
            "membership_date DATE",
            "status VARCHAR(20)",
        ],
        "description": "Library patrons who can borrow books",
    },
    "author": {
        "columns": [
            "id INT PK",
            "first_name VARCHAR(50)",
            "last_name VARCHAR(50)",
        ],
        "description": "Writers of books",
    },
    "category": {
        "columns": [
            "id INT PK",
            "name VARCHAR(50) UNIQUE",
            "description VARCHAR(255)",
        ],
        "description": "Genre/classification of books",
    },
    "staff": {
        "columns": [
            "id INT PK",
            "first_name VARCHAR(50)",
            "last_name VARCHAR(50)",
            "email VARCHAR(100) UNIQUE",
            "role VARCHAR(30)",
            "hire_date DATE",
        ],
        "description": "Library employees who process transactions",
    },
    "book": {
        "columns": [
            "id INT PK",
            "isbn VARCHAR(20) UNIQUE",
            "title VARCHAR(255)",
            "publication_year INT",
            "copies_available INT",
        ],
        "description": "Books in the library collection",
    },
    "loan": {
        "columns": [
            "id INT PK",
            "member_id INT FK",
            "book_id INT FK",
            "staff_id INT FK",
            "loan_date DATE",
            "due_date DATE",
            "return_date DATE",
            "status VARCHAR(20)",
        ],
        "description": "Checkout transactions tracking book borrowing",
    },
    "fine": {
        "columns": [
            "id INT PK",
            "loan_id INT FK UNIQUE",
            "amount DECIMAL(10,2)",
            "issue_date DATE",
            "paid_status VARCHAR(20)",
        ],
        "description": "Penalties for overdue books",
    },
    "book_author": {
        "columns": [
            "id INT PK",
            "book_id INT FK",
            "author_id INT FK",
        ],
        "description": "Junction: Books to Authors (M:N)",
    },
    "book_category": {
        "columns": [
            "id INT PK",
            "book_id INT FK",
            "category_id INT FK",
        ],
        "description": "Junction: Books to Categories (M:N)",
    },
}

# Foreign Key Relationships
OLTP_RELATIONSHIPS = [
    {"from": "loan", "to": "member", "label": "member_id", "cardinality": "N:1"},
    {"from": "loan", "to": "book", "label": "book_id", "cardinality": "N:1"},
    {"from": "loan", "to": "staff", "label": "staff_id", "cardinality": "N:1"},
    {"from": "fine", "to": "loan", "label": "loan_id", "cardinality": "1:1"},
    {"from": "book_author", "to": "book", "label": "book_id", "cardinality": "N:1"},
    {"from": "book_author", "to": "author", "label": "author_id", "cardinality": "N:1"},
    {"from": "book_category", "to": "book", "label": "book_id", "cardinality": "N:1"},
    {"from": "book_category", "to": "category", "label": "category_id", "cardinality": "N:1"},
]


def build_tooltip(table_name: str, table_info: dict) -> str:
    """Build plain text tooltip showing table columns."""
    lines = [
        table_name.upper(),
        table_info["description"],
        "",
        "Columns:",
    ]
    for col in table_info["columns"]:
        marker = ""
        if "PK" in col:
            marker = " [PK]"
        elif "FK" in col:
            marker = " [FK]"
        lines.append(f"  {col}{marker}")
    return "\n".join(lines)


def render(neo4j=None) -> None:
    """Render the OLTP ERD visualization."""
    st.header("OLTP Schema - Entity Relationship Diagram")
    st.markdown("""
    This diagram shows the **normalized database schema** for the Library Management System.
    - **9 tables** with foreign key relationships
    - **Junction tables** (diamond shaped) handle many-to-many relationships
    - Hover over tables to see column definitions
    """)

    # Legend
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Tooltip Markers:**")
        st.markdown("- `[PK]` - Primary Key")
        st.markdown("- `[FK]` - Foreign Key")
    with col2:
        st.markdown("**Table Types:**")
        st.markdown("- Rectangle - Entity tables")
        st.markdown("- Diamond - Junction tables")
    with col3:
        st.markdown("**Cardinality:**")
        st.markdown("- N:1 - Many to One")
        st.markdown("- 1:1 - One to One")

    st.divider()

    # Build nodes
    nodes = []
    for table_name, table_info in OLTP_TABLES.items():
        nodes.append({
            "id": table_name,
            "label": table_name.upper(),
            "type": table_name,
            "title": build_tooltip(table_name, table_info),
            "size": ERD_OLTP_SIZES.get(table_name, 30),
        })

    # Build edges
    edges = []
    for rel in OLTP_RELATIONSHIPS:
        edges.append({
            "from": rel["from"],
            "to": rel["to"],
            "label": f"{rel['label']} ({rel['cardinality']})",
            "title": f"FK: {rel['from']}.{rel['label']} -> {rel['to']}.id",
            "color": "#888888",
        })

    # Create network
    net = create_network(
        height="700px",
        directed=True,
        physics_enabled=True,
        layout="barnes_hut",
    )

    # Add nodes with ERD styling
    add_nodes(
        net,
        nodes,
        colors=ERD_OLTP_COLORS,
        shapes=ERD_OLTP_SHAPES,
        sizes=ERD_OLTP_SIZES,
    )

    # Add edges
    add_edges(net, edges)

    # Display
    display_in_streamlit(net, height=720, key="erd_oltp_network")

    # Table details section
    st.divider()
    st.subheader("Table Details")

    # Show tables in columns
    col1, col2, col3 = st.columns(3)

    table_list = list(OLTP_TABLES.items())
    for i, (table_name, table_info) in enumerate(table_list):
        col = [col1, col2, col3][i % 3]
        with col:
            with st.expander(f"**{table_name.upper()}**"):
                st.caption(table_info["description"])
                for col_def in table_info["columns"]:
                    if "PK" in col_def:
                        st.markdown(f":green[{col_def}]")
                    elif "FK" in col_def:
                        st.markdown(f":blue[{col_def}]")
                    else:
                        st.markdown(col_def)

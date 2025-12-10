"""ERD Visualization for OLAP (Star Schema)."""

import streamlit as st
from app.components.graph_builder import (
    create_network,
    add_nodes,
    add_edges,
    display_in_streamlit,
    ERD_OLAP_COLORS,
    ERD_OLAP_SHAPES,
    ERD_OLAP_SIZES,
)


# OLAP Star Schema Definition
OLAP_TABLES = {
    "fact_loan": {
        "type": "Fact",
        "columns": [
            "loan_key INT PK",
            "date_key INT FK",
            "return_date_key INT FK",
            "member_key INT FK",
            "book_key INT FK",
            "staff_key INT FK",
            "loan_count INT (measure)",
            "loan_duration_days INT (measure)",
            "days_overdue INT (measure)",
            "fine_amount DECIMAL (measure)",
        ],
        "description": "Central fact table containing loan transaction measures",
    },
    "dim_date": {
        "type": "Dimension",
        "columns": [
            "date_key INT PK",
            "full_date DATE",
            "year INT",
            "quarter INT",
            "month_name VARCHAR",
            "month_num INT",
            "day INT",
            "day_name VARCHAR",
            "day_of_week INT",
            "week_of_year INT",
            "is_weekend BOOLEAN",
        ],
        "description": "Date dimension for time-based analysis",
    },
    "dim_member": {
        "type": "Dimension",
        "columns": [
            "member_key INT PK",
            "source_member_id INT",
            "first_name VARCHAR",
            "last_name VARCHAR",
            "full_name VARCHAR",
            "email VARCHAR",
            "phone VARCHAR",
            "membership_date DATE",
            "membership_year INT",
            "status VARCHAR",
        ],
        "description": "Member dimension with denormalized attributes",
    },
    "dim_book": {
        "type": "Dimension",
        "columns": [
            "book_key INT PK",
            "source_book_id INT",
            "isbn VARCHAR",
            "title VARCHAR",
            "authors VARCHAR (denorm)",
            "publication_year INT",
            "total_copies INT",
        ],
        "description": "Book dimension with denormalized authors",
    },
    "dim_staff": {
        "type": "Dimension",
        "columns": [
            "staff_key INT PK",
            "source_staff_id INT",
            "first_name VARCHAR",
            "last_name VARCHAR",
            "full_name VARCHAR",
            "email VARCHAR",
            "role VARCHAR",
            "hire_date DATE",
            "hire_year INT",
        ],
        "description": "Staff dimension with derived attributes",
    },
    "dim_category": {
        "type": "Dimension",
        "columns": [
            "category_key INT PK",
            "source_category_id INT",
            "category_name VARCHAR",
            "description VARCHAR",
        ],
        "description": "Category dimension for genre analysis",
    },
    "bridge_book_category": {
        "type": "Bridge",
        "columns": [
            "book_key INT FK",
            "category_key INT FK",
            "weight_factor DECIMAL",
        ],
        "description": "Bridge table for M:N book-category with weighting",
    },
}

# Star Schema Relationships
OLAP_RELATIONSHIPS = [
    {"from": "fact_loan", "to": "dim_date", "label": "date_key"},
    {"from": "fact_loan", "to": "dim_date", "label": "return_date_key", "dashed": True},
    {"from": "fact_loan", "to": "dim_member", "label": "member_key"},
    {"from": "fact_loan", "to": "dim_book", "label": "book_key"},
    {"from": "fact_loan", "to": "dim_staff", "label": "staff_key"},
    {"from": "bridge_book_category", "to": "dim_book", "label": "book_key"},
    {"from": "bridge_book_category", "to": "dim_category", "label": "category_key"},
]


def build_tooltip(table_name: str, table_info: dict) -> str:
    """Build plain text tooltip showing table columns."""
    table_type = table_info["type"]
    lines = [
        f"[{table_type}] {table_name.upper()}",
        f"{table_info['description']}",
        "",
        "Columns:",
    ]
    for col in table_info["columns"]:
        marker = ""
        if "PK" in col:
            marker = " [PK]"
        elif "FK" in col:
            marker = " [FK]"
        elif "(measure)" in col:
            marker = " [MEASURE]"
        elif "(denorm)" in col:
            marker = " [DENORM]"
        lines.append(f"  {col}{marker}")
    return "\n".join(lines)


def render(neo4j=None) -> None:
    """Render the OLAP ERD visualization."""
    st.header("OLAP Star Schema - Entity Relationship Diagram")
    st.markdown("""
    This diagram shows the **dimensional model (star schema)** for analytical queries.
    - **Fact table** (star shape) contains measures
    - **Dimension tables** (boxes) contain descriptive attributes
    - **Bridge table** (diamond) handles M:N category relationships with weighting
    """)

    # Legend
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Table Types:**")
        st.markdown("- :red[**Star**] - Fact Table (measures)")
        st.markdown("- :blue[**Box**] - Dimension Tables")
        st.markdown("- :gray[**Diamond**] - Bridge Table")
    with col2:
        st.markdown("**Tooltip Markers:**")
        st.markdown("- `[PK]` - Primary Key")
        st.markdown("- `[FK]` - Foreign Key")
        st.markdown("- `[MEASURE]` - Measure columns")
        st.markdown("- `[DENORM]` - Denormalized columns")
    with col3:
        st.markdown("**ETL Source:**")
        st.markdown("- Populated from OLTP `library` database")
        st.markdown("- ~4,000 date records (2020-2030)")
        st.markdown("- Denormalized for query performance")

    st.divider()

    # Build nodes
    nodes = []
    for table_name, table_info in OLAP_TABLES.items():
        nodes.append({
            "id": table_name,
            "label": table_name.upper().replace("_", "\n"),
            "type": table_name,
            "title": build_tooltip(table_name, table_info),
            "size": ERD_OLAP_SIZES.get(table_name, 30),
        })

    # Build edges
    edges = []
    for rel in OLAP_RELATIONSHIPS:
        edge_style = {
            "from": rel["from"],
            "to": rel["to"],
            "label": rel["label"],
            "title": f"FK: {rel['from']}.{rel['label']} -> {rel['to']}",
            "color": "#888888" if not rel.get("dashed") else "#555555",
        }
        edges.append(edge_style)

    # Create network
    net = create_network(
        height="700px",
        directed=True,
        physics_enabled=True,
        layout="barnes_hut",
    )

    # Add nodes with OLAP styling
    add_nodes(
        net,
        nodes,
        colors=ERD_OLAP_COLORS,
        shapes=ERD_OLAP_SHAPES,
        sizes=ERD_OLAP_SIZES,
    )

    # Add edges
    add_edges(net, edges)

    # Display
    display_in_streamlit(net, height=720, key="erd_olap_network")

    # Schema explanation
    st.divider()
    st.subheader("Star Schema Components")

    # Fact table
    with st.expander("**FACT_LOAN** - Central Fact Table", expanded=True):
        st.markdown("""
        The fact table contains **quantitative measures** that can be aggregated:

        | Measure | Description |
        |---------|-------------|
        | `loan_count` | Always 1, allows COUNT aggregation |
        | `loan_duration_days` | Days between loan and return |
        | `days_overdue` | Days past due date (0 if on time) |
        | `fine_amount` | Fine amount in dollars |

        **Grain:** One row per loan transaction
        """)

    # Dimensions
    col1, col2 = st.columns(2)

    with col1:
        with st.expander("**DIM_DATE** - Time Dimension"):
            st.markdown("""
            Enables time-based analysis:
            - Year, Quarter, Month analysis
            - Weekend vs. Weekday patterns
            - Week-over-week comparisons

            **Records:** ~4,000 (2020-2030)
            """)

        with st.expander("**DIM_MEMBER** - Member Dimension"):
            st.markdown("""
            Member attributes for segmentation:
            - Full name (denormalized)
            - Membership year for cohort analysis
            - Status for filtering

            **Derived:** `full_name`, `membership_year`
            """)

        with st.expander("**DIM_STAFF** - Staff Dimension"):
            st.markdown("""
            Staff attributes for performance analysis:
            - Full name (denormalized)
            - Role-based analysis
            - Hire year for tenure analysis

            **Derived:** `full_name`, `hire_year`
            """)

    with col2:
        with st.expander("**DIM_BOOK** - Book Dimension"):
            st.markdown("""
            Book attributes with denormalized authors:
            - Authors as comma-separated string
            - Publication year for age analysis
            - Total copies for utilization

            **Denormalized:** `authors` field
            """)

        with st.expander("**DIM_CATEGORY** - Category Dimension"):
            st.markdown("""
            Genre classification for collection analysis:
            - Category name
            - Description

            **Note:** Connected via bridge table
            """)

        with st.expander("**BRIDGE_BOOK_CATEGORY** - Bridge Table"):
            st.markdown("""
            Handles **many-to-many** relationship between books and categories:

            | Column | Purpose |
            |--------|---------|
            | `weight_factor` | 1/N where N = categories per book |

            **Example:** A book in 3 categories has weight 0.333 each

            This ensures accurate aggregation without double-counting.
            """)

# Library Management System: Neo4j + PyVis + Streamlit Integration

## Project Overview

This document provides specifications for building a graph visualization layer for an existing MySQL-based Library Management System. The integration adds Neo4j as a graph database for relationship visualization and Streamlit with PyVis for interactive front-end exploration.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit App                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  CRUD Operations │  │  OLAP Reports   │  │ Graph View  │ │
│  │  (MySQL)         │  │  (MySQL Star)   │  │ (Neo4j)     │ │
│  └────────┬─────────┘  └────────┬────────┘  └──────┬──────┘ │
└───────────┼─────────────────────┼──────────────────┼────────┘
            │                     │                  │
            ▼                     ▼                  ▼
      ┌──────────┐          ┌──────────┐       ┌──────────┐
      │  MySQL   │          │  MySQL   │       │  Neo4j   │
      │  OLTP    │───ETL───▶│  OLAP    │       │  Graph   │
      └──────────┘          └──────────┘       └──────────┘
            │                                        ▲
            └────────────── ETL ─────────────────────┘
```

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Graph Database | Neo4j Community | Latest | Store and query graph relationships |
| Visualization | PyVis | 0.3.x | Interactive network graphs |
| Front-end | Streamlit | 1.x | Web application framework |
| OLTP Database | MySQL | 8.x | Existing transactional database |
| Language | Python | 3.10+ | Application development |
| Containerization | Docker | Latest | Neo4j deployment |

---

## Project Structure

```
library_graph_viz/
├── .env.example                 # Environment variables template
├── .gitignore
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker services (Neo4j)
├── README.md                    # Project documentation
│
├── config/
│   └── settings.py              # Configuration management
│
├── etl/
│   ├── __init__.py
│   ├── mysql_connector.py       # MySQL connection utilities
│   ├── neo4j_connector.py       # Neo4j connection utilities
│   └── etl_pipeline.py          # Main ETL script (MySQL → Neo4j)
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # Streamlit entry point
│   ├── components/
│   │   ├── __init__.py
│   │   ├── graph_builder.py     # PyVis graph construction
│   │   └── sidebar.py           # Sidebar navigation
│   └── views/
│       ├── __init__.py
│       ├── full_network.py      # Full library network view
│       ├── books_authors.py     # Books & authors view
│       ├── member_history.py    # Member borrowing history view
│       ├── category_explorer.py # Category exploration view
│       ├── staff_activity.py    # Staff activity view
│       └── custom_query.py      # Custom Cypher query view
│
└── tests/
    ├── __init__.py
    ├── test_etl.py
    └── test_graph_builder.py
```

---

## Dependencies

### requirements.txt

```
streamlit>=1.28.0
neo4j>=5.14.0
pyvis>=0.3.2
mysql-connector-python>=8.2.0
python-dotenv>=1.0.0
pandas>=2.0.0
```

---

## Configuration

### .env.example

```bash
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=library_oltp
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
```

---

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:latest
    container_name: library-neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/librarypass123
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=1G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - library_network

networks:
  library_network:
    driver: bridge

volumes:
  neo4j_data:
  neo4j_logs:
```

---

## Data Model

### MySQL Source Schema (Existing)

The existing MySQL OLTP database contains the following tables:

| Table | Description |
|-------|-------------|
| `member` | Library members |
| `book` | Book catalog |
| `author` | Author information |
| `category` | Book categories |
| `staff` | Library staff |
| `loan` | Loan transactions |
| `fine` | Fine records |
| `book_author` | Junction table (book ↔ author) |
| `book_category` | Junction table (book ↔ category) |

### Neo4j Graph Schema

#### Nodes

| Label | Properties | Source Table |
|-------|------------|--------------|
| `Member` | id, name, email, phone, address, membership_date | member |
| `Book` | id, title, isbn, publication_year, available_count, total_count | book |
| `Author` | id, name, biography | author |
| `Category` | id, name, description | category |
| `Staff` | id, name, email, role, hire_date | staff |
| `Loan` | id, loan_date, due_date, return_date | loan |
| `Fine` | id, amount, paid, paid_date | fine |

#### Relationships

| Type | Pattern | Description |
|------|---------|-------------|
| `WROTE` | (Author)-[:WROTE]->(Book) | Author wrote a book |
| `BELONGS_TO` | (Book)-[:BELONGS_TO]->(Category) | Book belongs to category |
| `BORROWED` | (Member)-[:BORROWED]->(Loan) | Member initiated a loan |
| `CONTAINS` | (Loan)-[:CONTAINS]->(Book) | Loan contains a book |
| `PROCESSED_BY` | (Loan)-[:PROCESSED_BY]->(Staff) | Staff processed the loan |
| `HAS_FINE` | (Loan)-[:HAS_FINE]->(Fine) | Loan has an associated fine |

---

## Implementation Specifications

### 1. Configuration Module (`config/settings.py`)

**Requirements:**
- Load environment variables from `.env` file
- Provide dataclass or Pydantic model for type-safe configuration
- Include default values for development
- Validate required settings on startup

**Functions/Classes:**
```python
class Settings:
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

def get_settings() -> Settings:
    """Load and validate settings from environment."""
```

---

### 2. MySQL Connector (`etl/mysql_connector.py`)

**Requirements:**
- Context manager for database connections
- Query execution with dictionary cursor
- Connection pooling support
- Error handling with meaningful messages

**Functions:**
```python
class MySQLConnector:
    def __init__(self, settings: Settings)
    def __enter__(self) -> MySQLConnector
    def __exit__(self, exc_type, exc_val, exc_tb)
    def execute_query(self, query: str, params: dict = None) -> list[dict]
    def fetch_table(self, table_name: str) -> list[dict]
```

---

### 3. Neo4j Connector (`etl/neo4j_connector.py`)

**Requirements:**
- Context manager for driver lifecycle
- Session management
- Cypher query execution
- Transaction support
- Constraint and index creation utilities

**Functions:**
```python
class Neo4jConnector:
    def __init__(self, settings: Settings)
    def __enter__(self) -> Neo4jConnector
    def __exit__(self, exc_type, exc_val, exc_tb)
    def run_query(self, query: str, params: dict = None) -> list[dict]
    def run_transaction(self, queries: list[tuple[str, dict]])
    def create_constraint(self, label: str, property: str)
    def clear_database(self)
```

---

### 4. ETL Pipeline (`etl/etl_pipeline.py`)

**Requirements:**
- Clear existing Neo4j data before import
- Create uniqueness constraints for all node types
- Load all nodes from MySQL tables
- Create all relationships from junction tables and foreign keys
- Progress logging for each step
- Rollback capability on failure
- CLI interface for manual execution

**Class Structure:**
```python
class LibraryETL:
    def __init__(self, mysql: MySQLConnector, neo4j: Neo4jConnector)
    
    # Setup methods
    def clear_graph(self)
    def create_constraints(self)
    
    # Node loading methods
    def load_members(self) -> int
    def load_books(self) -> int
    def load_authors(self) -> int
    def load_categories(self) -> int
    def load_staff(self) -> int
    def load_loans(self) -> int
    def load_fines(self) -> int
    
    # Relationship methods
    def create_wrote_relationships(self) -> int
    def create_belongs_to_relationships(self) -> int
    def create_loan_relationships(self) -> int
    def create_fine_relationships(self) -> int
    
    # Main execution
    def run(self) -> dict[str, int]  # Returns counts of created entities

if __name__ == "__main__":
    # CLI entry point
```

**Cypher Templates:**

```cypher
-- Create Member nodes
MERGE (m:Member {id: $id})
SET m.name = $name,
    m.email = $email,
    m.phone = $phone,
    m.address = $address,
    m.membership_date = $membership_date

-- Create WROTE relationship
MATCH (a:Author {id: $author_id})
MATCH (b:Book {id: $book_id})
MERGE (a)-[:WROTE]->(b)

-- Create loan relationships (batch)
MATCH (m:Member {id: $member_id})
MATCH (l:Loan {id: $loan_id})
MATCH (b:Book {id: $book_id})
MATCH (s:Staff {id: $staff_id})
MERGE (m)-[:BORROWED]->(l)
MERGE (l)-[:CONTAINS]->(b)
MERGE (l)-[:PROCESSED_BY]->(s)
```

---

### 5. Graph Builder Component (`app/components/graph_builder.py`)

**Requirements:**
- Create PyVis Network objects with consistent styling
- Color scheme for different node types
- Configurable physics settings
- Node sizing based on importance/count
- Edge labels for relationship types
- Tooltip information for nodes
- Export to HTML for Streamlit embedding

**Color Scheme:**
```python
NODE_COLORS = {
    "Member": "#ff6b6b",    # Coral red
    "Book": "#4ecdc4",      # Teal
    "Author": "#45b7d1",    # Sky blue
    "Category": "#96ceb4",  # Sage green
    "Staff": "#ffeaa7",     # Soft yellow
    "Loan": "#dfe6e9",      # Light gray
    "Fine": "#fd79a8"       # Pink
}
```

**Functions:**
```python
def create_network(
    height: str = "600px",
    width: str = "100%",
    bgcolor: str = "#0e1117",
    directed: bool = True
) -> Network

def add_nodes(
    net: Network,
    nodes: list[dict],  # {id, label, type, title?, size?}
    colors: dict = NODE_COLORS
) -> Network

def add_edges(
    net: Network,
    edges: list[dict],  # {from, to, label?}
) -> Network

def render_graph(net: Network) -> str:
    """Return HTML string for Streamlit components.html()"""

def display_in_streamlit(net: Network, height: int = 620):
    """Render PyVis graph in Streamlit using components.html()"""
```

---

### 6. Streamlit Views

Each view module should follow this pattern:

```python
def render():
    """Main render function called from main.py"""
    st.subheader("View Title")
    # ... view implementation
```

#### 6.1 Full Network View (`app/views/full_network.py`)

**Features:**
- Slider to limit number of nodes (10-200, default 50)
- Display all node types and relationships
- Legend showing node colors
- Node count statistics

**Cypher Query:**
```cypher
MATCH (n)
WITH n LIMIT $limit
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m
```

#### 6.2 Books & Authors View (`app/views/books_authors.py`)

**Features:**
- Show all author-book relationships
- Authors as larger nodes
- Books as box-shaped nodes
- Expandable data table below graph

**Cypher Query:**
```cypher
MATCH (a:Author)-[:WROTE]->(b:Book)
RETURN a.id AS author_id, a.name AS author_name,
       b.id AS book_id, b.title AS book_title
```

#### 6.3 Member Borrowing History (`app/views/member_history.py`)

**Features:**
- Dropdown to select member
- Show member's loan chain: Member → Loan → Book
- Include authors of borrowed books
- Display loan dates in tooltips

**Cypher Query:**
```cypher
MATCH (m:Member {id: $member_id})-[:BORROWED]->(l:Loan)-[:CONTAINS]->(b:Book)
OPTIONAL MATCH (b)<-[:WROTE]-(a:Author)
RETURN m.name AS member, b.title AS book, a.name AS author,
       l.loan_date AS loan_date, l.return_date AS return_date,
       m.id AS member_id, b.id AS book_id, a.id AS author_id, l.id AS loan_id
```

#### 6.4 Category Explorer (`app/views/category_explorer.py`)

**Features:**
- Dropdown to select category
- Show category as central node
- Display all books in category with their authors
- Category node larger than others

**Cypher Query:**
```cypher
MATCH (b:Book)-[:BELONGS_TO]->(c:Category {id: $category_id})
OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
RETURN c.name AS category, b.title AS book, b.id AS book_id,
       collect(a.name) AS authors, collect(a.id) AS author_ids
```

#### 6.5 Staff Activity View (`app/views/staff_activity.py`)

**Features:**
- Show all staff members
- Node size based on number of loans processed
- Connect staff to sample of books they processed
- Display loan count in node label

**Cypher Query:**
```cypher
MATCH (s:Staff)<-[:PROCESSED_BY]-(l:Loan)-[:CONTAINS]->(b:Book)
RETURN s.name AS staff, s.id AS staff_id,
       count(l) AS loan_count,
       collect(DISTINCT b.title)[0..5] AS sample_books
```

#### 6.6 Custom Query View (`app/views/custom_query.py`)

**Features:**
- Text area for Cypher query input
- Example queries in collapsible section
- Execute button
- Results displayed as pandas DataFrame
- Error handling with user-friendly messages

**Example Queries to Display:**
```cypher
-- Find all books by a specific author
MATCH (a:Author {name: 'Author Name'})-[:WROTE]->(b:Book) 
RETURN a, b

-- Find members with unreturned books
MATCH (m:Member)-[:BORROWED]->(l:Loan)-[:CONTAINS]->(b:Book)
WHERE l.return_date IS NULL
RETURN m.name, b.title, l.due_date

-- Most borrowed books
MATCH (b:Book)<-[:CONTAINS]-(l:Loan)
RETURN b.title, count(l) AS borrow_count
ORDER BY borrow_count DESC LIMIT 10

-- Authors with most books
MATCH (a:Author)-[:WROTE]->(b:Book)
RETURN a.name, count(b) AS book_count
ORDER BY book_count DESC

-- Category popularity by loans
MATCH (c:Category)<-[:BELONGS_TO]-(b:Book)<-[:CONTAINS]-(l:Loan)
RETURN c.name, count(l) AS total_loans
ORDER BY total_loans DESC
```

---

### 7. Main Application (`app/main.py`)

**Requirements:**
- Page configuration (title, icon, layout)
- Cached Neo4j driver connection
- Sidebar navigation with view selection
- Dynamic view rendering based on selection
- Footer with graph statistics
- Error handling for database connection issues

**Structure:**
```python
import streamlit as st
from config.settings import get_settings
from etl.neo4j_connector import Neo4jConnector
from app.views import (
    full_network,
    books_authors,
    member_history,
    category_explorer,
    staff_activity,
    custom_query
)

# Page config
st.set_page_config(
    page_title="Library Graph Explorer",
    page_icon="📚",
    layout="wide"
)

# Cached connection
@st.cache_resource
def get_neo4j():
    settings = get_settings()
    return Neo4jConnector(settings)

# View mapping
VIEWS = {
    "Full Library Network": full_network,
    "Books & Authors": books_authors,
    "Member Borrowing History": member_history,
    "Category Explorer": category_explorer,
    "Staff Activity": staff_activity,
    "Custom Cypher Query": custom_query
}

def main():
    neo4j = get_neo4j()
    
    # Sidebar
    st.sidebar.title("📚 Library Graph Explorer")
    selected_view = st.sidebar.selectbox("Select View", list(VIEWS.keys()))
    
    # Render selected view
    st.title("Library Management Graph Visualization")
    VIEWS[selected_view].render(neo4j)
    
    # Statistics in sidebar
    render_statistics(neo4j)

def render_statistics(neo4j):
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Graph Statistics**")
    # Query and display node counts by type

if __name__ == "__main__":
    main()
```

---

## Styling Guidelines

### PyVis Network Settings

```python
# Physics configuration for optimal layout
net.barnes_hut(
    gravity=-3000,
    central_gravity=0.3,
    spring_length=200,
    spring_strength=0.001,
    damping=0.09
)

# Alternative for smaller graphs
net.force_atlas_2based(
    gravity=-50,
    central_gravity=0.01,
    spring_length=100,
    spring_strength=0.08
)
```

### Node Shapes by Type

| Node Type | Shape | Size |
|-----------|-------|------|
| Member | dot | 25 |
| Book | box | 25 |
| Author | dot | 30 |
| Category | diamond | 35 |
| Staff | triangle | 25 |
| Loan | dot | 20 |
| Fine | dot | 15 |

---

## Testing Requirements

### Unit Tests (`tests/test_etl.py`)

```python
def test_mysql_connection():
    """Verify MySQL connection with test credentials."""

def test_neo4j_connection():
    """Verify Neo4j connection with test credentials."""

def test_node_creation():
    """Test creating a single node in Neo4j."""

def test_relationship_creation():
    """Test creating a relationship between nodes."""

def test_full_etl_pipeline():
    """Integration test for complete ETL process."""
```

### Component Tests (`tests/test_graph_builder.py`)

```python
def test_create_network():
    """Verify network creation with default settings."""

def test_add_nodes():
    """Test adding nodes with proper styling."""

def test_add_edges():
    """Test adding edges between nodes."""

def test_render_to_html():
    """Verify HTML output generation."""
```

---

## Usage Instructions

### Initial Setup

```bash
# 1. Clone repository and navigate to project
cd library_graph_viz

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Start Neo4j with Docker
docker-compose up -d

# 6. Wait for Neo4j to be ready (check http://localhost:7474)

# 7. Run ETL to populate Neo4j
python -m etl.etl_pipeline

# 8. Start Streamlit application
streamlit run app/main.py
```

### Accessing the Application

- **Streamlit App:** http://localhost:8501
- **Neo4j Browser:** http://localhost:7474

---

## Additional Features (Optional Enhancements)

### 1. Real-time Sync
- Add MySQL triggers or CDC to detect changes
- Implement incremental updates to Neo4j

### 2. Advanced Analytics
- Path finding between members (shared books)
- Community detection for reading groups
- Recommendation engine based on borrowing patterns

### 3. Export Capabilities
- Export graph as PNG/SVG
- Generate PDF reports with embedded graphs
- Export query results as CSV

### 4. Authentication
- Add Streamlit authentication
- Role-based view access

---

## References

- [Neo4j Python Driver Documentation](https://neo4j.com/docs/python-manual/current/)
- [PyVis Documentation](https://pyvis.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-11-27 | Initial specification |

---

*This specification is designed for use with Cursor AI code editor. Feed this document to Cursor to generate the complete implementation.*

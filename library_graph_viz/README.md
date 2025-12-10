# Library Graph Visualization

A comprehensive graph visualization and analytics platform for a Library Management System using Neo4j, PyVis, MySQL, and Streamlit. This application provides interactive network visualizations, CRUD demonstrations, ERD diagrams, and OLAP analytics to explore relationships between library entities including books, authors, members, categories, staff, and loans.

## Features

### Graph Visualizations (Neo4j + PyVis)
- **Full Library Network** - Overview of all entities and relationships
- **Books & Authors** - Author-book relationships visualization
- **Member Borrowing History** - Individual member loan chains
- **Category Explorer** - Books and authors by category
- **Staff Activity** - Staff member loan processing activity
- **Custom Cypher Query** - Execute custom Neo4j queries
- **Analytics & Recommendations** - Book recommendations and member connections

### Database Schema Diagrams
- **ERD: OLTP Schema** - Interactive diagram of the normalized 9-table schema
- **ERD: OLAP Star Schema** - Star schema visualization with fact and dimension tables

### SQL Demonstrations
- **CRUD Examples** - Interactive CREATE, READ, UPDATE, DELETE demonstrations with live query execution
- **OLAP Analytics** - 7 analytical queries against the star schema with charts and CSV export

### Additional Features
- **Data Export**: Export data to CSV, PNG, SVG, and PDF formats
- **Real-time Sync**: Sync data from MySQL to Neo4j with one click
- **ETL Pipeline**: Automated data migration from MySQL OLTP to Neo4j graph database
- **Large Dataset Generator**: Faker-based script to generate realistic sample data

## Architecture

```
+-------------------------------------------------------------+
|                      Streamlit App                          |
|  +---------------+  +---------------+  +-----------------+  |
|  | CRUD Examples |  | OLAP Analytics|  | Graph Views     |  |
|  | (MySQL OLTP)  |  | (MySQL OLAP)  |  | (Neo4j + PyVis) |  |
|  +-------+-------+  +-------+-------+  +--------+--------+  |
|          |                  |                   |           |
|  +-------+-------+  +-------+-------+  +--------+--------+  |
|  | ERD: OLTP     |  | ERD: OLAP     |  | Custom Cypher   |  |
|  | (PyVis)       |  | (PyVis)       |  | Queries         |  |
|  +---------------+  +---------------+  +-----------------+  |
+-------------------------------------------------------------+
           |                  |                   |
           v                  v                   v
      +----------+       +----------+       +----------+
      |  MySQL   |       |  MySQL   |       |  Neo4j   |
      |  OLTP    |--ETL->|  OLAP    |       |  Graph   |
      | (library)|       |(library_ |       |          |
      |          |       |  olap)   |       |          |
      +----------+       +----------+       +----------+
           |                                      ^
           +----------------- ETL ----------------+
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Graph Database | Neo4j 5.x | Store and query graph relationships |
| Visualization | PyVis | Interactive network graphs & ERD diagrams |
| Front-end | Streamlit | Web application framework |
| OLTP Database | MySQL 8.x | Transactional database (normalized) |
| OLAP Database | MySQL 8.x | Analytical database (star schema) |
| Data Generation | Faker | Realistic sample data generation |
| Language | Python 3.10+ | Application development |
| Containerization | Docker | Database deployment |

## Prerequisites

- Python 3.10 or higher (recommend using [pyenv](https://github.com/pyenv/pyenv))
- Docker and Docker Compose
- Git

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd library_graph_viz

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Start Databases

```bash
# Start MySQL and Neo4j containers
docker-compose up -d

# Wait for services to be ready (~30 seconds for initial setup)
# MySQL will automatically run the initialization scripts

# Check container status
docker-compose ps

# Neo4j Browser: http://localhost:7474
# MySQL: localhost:3306
```

### 3. Run ETL Pipeline

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Populate Neo4j with data from MySQL
PYTHONPATH=$(pwd) python -m etl.etl_pipeline

# With verbose logging
PYTHONPATH=$(pwd) python -m etl.etl_pipeline --verbose
```

### 4. Start Application

```bash
# Run Streamlit app (PYTHONPATH is required for module imports)
PYTHONPATH=$(pwd) streamlit run app/main.py

# Or with headless mode (no browser auto-open)
PYTHONPATH=$(pwd) streamlit run app/main.py --server.headless=true

# Access at http://localhost:8501
```

### 5. Stop Everything

```bash
# Stop Streamlit (Ctrl+C or from another terminal)
pkill -f streamlit

# Stop and remove Docker containers
docker-compose down

# Full reset (removes all data volumes)
docker-compose down -v
```

## Project Structure

```
library_graph_viz/
├── .env.example                 # Environment variables template
├── .gitignore
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker services (Neo4j, MySQL)
├── README.md
│
├── config/
│   └── settings.py              # Configuration management (OLTP + OLAP)
│
├── scripts/                     # MySQL initialization scripts (run in order)
│   ├── 01_create_tables.sql     # OLTP schema (member, book, author, etc.)
│   ├── 02_insert_data.sql       # Large sample data (200 members, 500 books)
│   ├── 03_roles_users.sql       # Database roles and users
│   ├── 04_olap_create_tables.sql # OLAP star schema (dimensions & facts)
│   ├── 05_olap_etl.sql          # OLAP ETL (populates star schema)
│   └── generate_sample_data.py  # Faker-based data generator script
│
├── etl/
│   ├── __init__.py
│   ├── mysql_connector.py       # MySQL connection (supports OLTP + OLAP)
│   ├── neo4j_connector.py       # Neo4j connection utilities
│   └── etl_pipeline.py          # Main ETL script (MySQL → Neo4j)
│
├── app/
│   ├── main.py                  # Streamlit entry point
│   ├── components/
│   │   ├── graph_builder.py     # PyVis graph construction + ERD styles
│   │   └── sidebar.py           # Sidebar navigation
│   └── views/
│       ├── full_network.py      # Full library network view
│       ├── books_authors.py     # Books & authors view
│       ├── member_history.py    # Member borrowing history
│       ├── category_explorer.py # Category exploration
│       ├── staff_activity.py    # Staff activity view
│       ├── custom_query.py      # Custom Cypher queries
│       ├── analytics.py         # Analytics & recommendations
│       ├── erd_oltp.py          # ERD: Normalized schema diagram
│       ├── erd_olap.py          # ERD: Star schema diagram
│       ├── crud_examples.py     # CRUD operations examples
│       └── olap_analytics.py    # OLAP analytical queries
│
├── utils/
│   └── export.py                # Export utilities
│
└── tests/
    ├── conftest.py              # Pytest fixtures
    ├── test_etl.py
    ├── test_graph_builder.py
    └── test_export.py
```

## Database Schema

### MySQL OLTP Tables (Normalized - 3NF)

| Table | Description | Records |
|-------|-------------|---------|
| `member` | Library patrons | 200 |
| `author` | Book authors | 100 |
| `category` | Book genres/classifications | 6 |
| `staff` | Library employees | 20 |
| `book` | Book catalog | 500 |
| `book_author` | Book-Author relationships (M:N) | ~660 |
| `book_category` | Book-Category relationships (M:N) | ~890 |
| `loan` | Checkout transactions | 2,000 |
| `fine` | Overdue penalties | ~1,200 |

### MySQL OLAP Tables (Star Schema)

| Table | Type | Description |
|-------|------|-------------|
| `fact_loan` | Fact | Central fact table with loan measures |
| `dim_date` | Dimension | Date dimension (2020-2030) |
| `dim_member` | Dimension | Member attributes |
| `dim_book` | Dimension | Book attributes with denormalized authors |
| `dim_staff` | Dimension | Staff attributes |
| `dim_category` | Dimension | Category attributes |
| `bridge_book_category` | Bridge | M:N book-category with weighting |

### Neo4j Graph Schema

**Nodes:**
- `Member` - Library members (id, name, email, phone, status, membership_date)
- `Book` - Book catalog (id, title, isbn, publication_year, copies_available)
- `Author` - Author information (id, name)
- `Category` - Book categories (id, name, description)
- `Staff` - Library staff (id, name, email, role, hire_date)
- `Loan` - Loan transactions (id, loan_date, due_date, return_date, status)
- `Fine` - Fine records (id, amount, paid_status, issue_date)

**Relationships:**
- `(Author)-[:WROTE]->(Book)`
- `(Book)-[:BELONGS_TO]->(Category)`
- `(Member)-[:BORROWED]->(Loan)`
- `(Loan)-[:CONTAINS]->(Book)`
- `(Loan)-[:PROCESSED_BY]->(Staff)`
- `(Loan)-[:HAS_FINE]->(Fine)`

## Application Views

### Graph Views (Neo4j)

| View | Description |
|------|-------------|
| Full Library Network | Interactive graph with node type selection and connectivity-aware sampling |
| Books & Authors | Explore author-book connections |
| Member Borrowing History | Track individual member loan patterns |
| Category Explorer | Browse books by genre/category |
| Staff Activity | Analyze staff loan processing |
| Custom Cypher Query | Run arbitrary Neo4j queries |
| Analytics & Recommendations | Book recommendations based on borrowing patterns |

#### Full Library Network - Smart Sampling

The Full Library Network view uses **connectivity-aware sampling** to ensure meaningful visualizations:

**Node Type Selection:**
- Checkboxes for each of the 7 node types (all enabled by default)
- Real-time counts displayed next to each type
- Toggle visibility of Categories, Staff, Authors, Members, Books, Loans, and Fines

**Sampling Strategy:**
- **Small types** (Category, Staff, Author): Always shown completely when selected
- **Large types** (Member, Book, Loan, Fine): Sampled using connectivity-aware approach

**How Connectivity-Aware Sampling Works:**
```
Loan (hub) ───┬──► Book (via CONTAINS)
              ├──► Member (via BORROWED)
              ├──► Staff (via PROCESSED_BY)
              └──► Fine (via HAS_FINE)
```

Instead of sampling each node type independently (which can result in disconnected nodes), the view:
1. Samples a set of Loans as the "hub"
2. Automatically includes all connected nodes (Members, Books, Staff, Fines)
3. Guarantees every relationship is visible in the graph

This ensures you see complete transaction chains rather than isolated nodes with missing relationships.

### Schema Diagrams (PyVis)

| View | Description |
|------|-------------|
| ERD: OLTP Schema | 9-table normalized schema with FK relationships |
| ERD: OLAP Star Schema | Fact + dimension tables with star layout |

### SQL Views (MySQL)

| View | Description |
|------|-------------|
| CRUD Examples | Interactive SQL demonstrations (SELECT queries executable) |
| OLAP Analytics | 7 analytical queries with charts and CSV export |

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=library
MYSQL_OLAP_DATABASE=library_olap
MYSQL_USER=root
MYSQL_PASSWORD=librarypass123

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=librarypass123

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
```

## Usage

### Running the ETL Pipeline

```bash
# Full sync (clears Neo4j first)
PYTHONPATH=$(pwd) python -m etl.etl_pipeline

# Incremental update (keeps existing data)
PYTHONPATH=$(pwd) python -m etl.etl_pipeline --no-clear

# Verbose mode
PYTHONPATH=$(pwd) python -m etl.etl_pipeline --verbose
```

### Generating Sample Data

```bash
# Generate new sample data (optional - data is pre-generated)
cd scripts
python generate_sample_data.py

# This creates 02_insert_data.sql with:
# - 200 members
# - 100 authors
# - 500 books
# - 20 staff
# - 2000 loans
# - ~1200 fines
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_etl.py -v
```

### Custom Cypher Queries

The Custom Query view allows you to run any Cypher query. Examples:

```cypher
-- Find all books by an author
MATCH (a:Author {name: 'George Orwell'})-[:WROTE]->(b:Book)
RETURN a.name, b.title

-- Most borrowed books
MATCH (b:Book)<-[:CONTAINS]-(l:Loan)
RETURN b.title, count(l) AS borrows
ORDER BY borrows DESC LIMIT 10

-- Members with overdue books
MATCH (m:Member)-[:BORROWED]->(l:Loan)-[:CONTAINS]->(b:Book)
WHERE l.status = 'overdue'
RETURN m.name, b.title, l.due_date

-- Books by category
MATCH (b:Book)-[:BELONGS_TO]->(c:Category)
RETURN c.name AS category, collect(b.title) AS books
```

### OLAP Analytical Queries

The OLAP Analytics view includes these pre-built queries:

1. **Monthly Loan Trends** - Borrowing patterns over time
2. **Top Borrowed Books** - Most popular titles
3. **Loans by Category (Weighted)** - Genre analysis with bridge table weighting
4. **Staff Performance** - Loan processing metrics by staff
5. **Member Behavior** - Member borrowing patterns and fine history
6. **Weekend vs Weekday** - Day-of-week analysis
7. **Year-over-Year** - Annual comparison metrics

## Troubleshooting

### Connection Issues

```bash
# Check if containers are running
docker-compose ps

# View container logs
docker-compose logs neo4j
docker-compose logs mysql

# Restart containers
docker-compose restart

# Full reset (removes all data)
docker-compose down -v
docker-compose up -d
```

### Neo4j Browser Access

- URL: http://localhost:7474
- Default credentials: neo4j / librarypass123

### Common Issues

1. **"ModuleNotFoundError: No module named 'config'"**
   - Run Streamlit with PYTHONPATH: `PYTHONPATH=$(pwd) streamlit run app/main.py`

2. **"Could not connect to Neo4j"**
   - Ensure Docker containers are running: `docker-compose ps`
   - Wait for Neo4j to fully start (~30 seconds)

3. **"No data in graph"**
   - Run the ETL pipeline: `PYTHONPATH=$(pwd) python -m etl.etl_pipeline`
   - Or click "Sync Data" in the app sidebar

4. **"Table doesn't exist" errors**
   - MySQL scripts may not have run. Check logs: `docker-compose logs mysql`
   - Try restarting: `docker-compose down -v && docker-compose up -d`

5. **"Duplicate entry" errors on startup**
   - Remove old data volumes: `docker-compose down -v`
   - Ensure only one insert script exists (02_insert_data.sql)

6. **OLAP Analytics shows no data**
   - The OLAP database populates via `05_olap_etl.sql` on startup
   - Check logs: `docker-compose logs mysql | grep olap`

## Development

### Adding New Views

1. Create a new file in `app/views/`
2. Implement the `render(neo4j: Neo4jConnector)` function
3. Import in `app/views/__init__.py`
4. Add the view to the `VIEWS` dictionary in `app/main.py`

### Extending the ETL

Add new node/relationship loaders to `etl/etl_pipeline.py`:

```python
def load_new_entity(self) -> int:
    data = self.mysql.fetch_table("new_table")
    query = "MERGE (n:NewLabel {id: $id}) SET n.prop = $prop"
    self.neo4j.run_query(query, {"data": data})
    return len(data)
```

### Multi-Database MySQL Queries

```python
from etl.mysql_connector import MySQLConnector

# OLTP database (default)
with MySQLConnector(database="oltp") as db:
    members = db.fetch_table("member")

# OLAP database
with MySQLConnector(database="olap") as db:
    facts = db.execute_query("SELECT * FROM fact_loan LIMIT 10")
```

## License

MIT License

## References

- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [PyVis Documentation](https://pyvis.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Faker Library](https://faker.readthedocs.io/)

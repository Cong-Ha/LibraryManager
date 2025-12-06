# Library Graph Visualization

A graph visualization layer for a Library Management System using Neo4j, PyVis, and Streamlit. This application provides interactive network visualizations to explore relationships between library entities including books, authors, members, categories, staff, and loans.

## Features

- **Interactive Graph Visualizations**: Explore library data through interactive network graphs
- **Multiple Views**:
  - Full Library Network - Overview of all entities and relationships
  - Books & Authors - Author-book relationships visualization
  - Member Borrowing History - Individual member loan chains
  - Category Explorer - Books and authors by category
  - Staff Activity - Staff member loan processing activity
  - Custom Cypher Query - Execute custom Neo4j queries
  - Analytics & Recommendations - Book recommendations and member connections

- **Data Export**: Export data to CSV, PNG, SVG, and PDF formats
- **Real-time Sync**: Sync data from MySQL to Neo4j with one click
- **ETL Pipeline**: Automated data migration from MySQL OLTP to Neo4j graph database

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

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Graph Database | Neo4j | Store and query graph relationships |
| Visualization | PyVis | Interactive network graphs |
| Front-end | Streamlit | Web application framework |
| OLTP Database | MySQL | Transactional database |
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
python -m etl.etl_pipeline

# With verbose logging
python -m etl.etl_pipeline --verbose
```

### 4. Start Application

```bash
# Run Streamlit app (PYTHONPATH is required for module imports)
PYTHONPATH=$(pwd) streamlit run app/main.py --server.headless=true

# Access at http://localhost:8501
```

### 5. Stop Everything

```bash
# Stop Streamlit (Ctrl+C or from another terminal)
pkill -f streamlit

# Stop and remove Docker containers
docker-compose down
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
│   └── settings.py              # Configuration management
│
├── scripts/                     # MySQL initialization scripts (run in order)
│   ├── 01_create_tables.sql     # OLTP schema (member, book, author, etc.)
│   ├── 02_insert_data.sql       # Sample data (6 members, 10 books, etc.)
│   ├── 03_roles_users.sql       # Database roles and users
│   ├── 04_olap_create_tables.sql # OLAP star schema (dimensions & facts)
│   └── 05_olap_etl.sql          # OLAP ETL (populates star schema)
│
├── etl/
│   ├── __init__.py
│   ├── mysql_connector.py       # MySQL connection utilities
│   ├── neo4j_connector.py       # Neo4j connection utilities
│   └── etl_pipeline.py          # Main ETL script (MySQL → Neo4j)
│
├── app/
│   ├── main.py                  # Streamlit entry point
│   ├── components/
│   │   ├── graph_builder.py     # PyVis graph construction
│   │   └── sidebar.py           # Sidebar navigation
│   └── views/
│       ├── full_network.py      # Full library network view
│       ├── books_authors.py     # Books & authors view
│       ├── member_history.py    # Member borrowing history
│       ├── category_explorer.py # Category exploration
│       ├── staff_activity.py    # Staff activity view
│       ├── custom_query.py      # Custom Cypher queries
│       └── analytics.py         # Analytics & recommendations
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

### MySQL OLTP Tables

| Table | Description | Records |
|-------|-------------|---------|
| `member` | Library patrons | 6 |
| `author` | Book authors | 8 |
| `category` | Book genres/classifications | 6 |
| `staff` | Library employees | 5 |
| `book` | Book catalog | 10 |
| `book_author` | Book-Author relationships (M:N) | 10 |
| `book_category` | Book-Category relationships (M:N) | 17 |
| `loan` | Checkout transactions | 8 |
| `fine` | Overdue penalties | 4 |

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

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=library
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
python -m etl.etl_pipeline

# Incremental update (keeps existing data)
python -m etl.etl_pipeline --no-clear

# Verbose mode
python -m etl.etl_pipeline --verbose
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
   - Run the ETL pipeline: `python -m etl.etl_pipeline`

4. **"Table doesn't exist" errors**
   - MySQL scripts may not have run. Check logs: `docker-compose logs mysql`
   - Try restarting: `docker-compose down && docker-compose up -d`

5. **"Check constraint violated" errors**
   - Ensure sample data meets all constraints (e.g., fine amounts > 0)

## Development

### Adding New Views

1. Create a new file in `app/views/`
2. Implement the `render(neo4j: Neo4jConnector)` function
3. Add the view to the `VIEWS` dictionary in `app/main.py`

### Extending the ETL

Add new node/relationship loaders to `etl/etl_pipeline.py`:

```python
def load_new_entity(self) -> int:
    data = self.mysql.fetch_table("new_table")
    query = "MERGE (n:NewLabel {id: $id}) SET n.prop = $prop"
    self.neo4j.run_query(query, {"data": data})
    return len(data)
```

## Sample Data

The project includes sample data representing a small library:

- **Members**: John Smith, Sarah Johnson, Michael Williams, Emily Brown, David Jones, Jessica Davis
- **Authors**: George Orwell, Jane Austen, Harper Lee, F. Scott Fitzgerald, Ernest Hemingway, Mark Twain, Agatha Christie, Stephen King
- **Books**: 1984, Pride and Prejudice, To Kill a Mockingbird, The Great Gatsby, The Old Man and the Sea, Tom Sawyer, Murder on the Orient Express, It, Animal Farm, A Farewell to Arms
- **Categories**: Fiction, Classic, Mystery, Science Fiction, Biography, Horror

## License

MIT License

## References

- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [PyVis Documentation](https://pyvis.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

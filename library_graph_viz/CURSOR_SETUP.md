# Running and Debugging in Cursor

This guide explains how to run and debug the Library Graph Visualization project in Cursor IDE.

## Architecture Overview

The project has a **hybrid architecture**:
- **Docker Services** (MySQL & Neo4j): Run in containers via `docker-compose`
- **Python App** (Streamlit): Runs locally on your machine, connects to Docker services

## Prerequisites

1. **Docker Desktop** must be installed and running
2. **Python 3.10+** installed
3. **Virtual environment** created and dependencies installed

## Setup Steps

### 1. Start Docker Services

**First, always start the Docker containers:**

```bash
cd library_graph_viz
docker-compose up -d
```

This starts:
- MySQL on `localhost:3306`
- Neo4j on `localhost:7474` (HTTP) and `localhost:7687` (Bolt)

**Verify containers are running:**
```bash
docker-compose ps
```

You should see both `library-mysql` and `library-neo4j` containers running.

### 2. Verify Python Environment

The project uses a virtual environment at `library_graph_viz/venv/`. Cursor should automatically detect it via `.vscode/settings.json`.

**If needed, activate manually:**
```bash
source library_graph_viz/venv/bin/activate  # Mac/Linux
# or
library_graph_viz\venv\Scripts\activate     # Windows
```

### 3. Run Initial ETL (First Time Only)

Before running the app, populate Neo4j with data from MySQL:

```bash
cd library_graph_viz
python -m etl.etl_pipeline
```

## Running in Cursor

### Option 1: Using Debug Configuration (Recommended)

1. **Open the Run and Debug panel** (Cmd+Shift+D / Ctrl+Shift+D)
2. **Select a configuration** from the dropdown:
   - **"Python: Streamlit App"** - Runs the main Streamlit application
   - **"Python: ETL Pipeline"** - Runs the ETL sync process
   - **"Python: Current File"** - Runs the currently open Python file
   - **"Python: Pytest"** - Runs pytest on the current test file
3. **Click the green play button** or press F5

The debugger will:
- Use the virtual environment Python interpreter
- Set `PYTHONPATH` automatically
- Allow you to set breakpoints and debug

### Option 2: Using Terminal

```bash
cd library_graph_viz
source venv/bin/activate  # If not auto-activated
PYTHONPATH=$(pwd) streamlit run app/main.py --server.headless=true
```

Access the app at: http://localhost:8501

## Debugging Workflow

### Setting Breakpoints

1. Click in the gutter (left of line numbers) to set breakpoints
2. Start debugging with F5
3. The debugger will pause at breakpoints
4. Use the Debug toolbar to:
   - **Continue** (F5)
   - **Step Over** (F10)
   - **Step Into** (F11)
   - **Step Out** (Shift+F11)
   - **Restart** (Cmd+Shift+F5)
   - **Stop** (Shift+F5)

### Debugging Streamlit

Streamlit runs in a separate process, so debugging works but:
- Breakpoints in Streamlit callbacks may require `justMyCode: false` (already set)
- The app runs in headless mode (`--server.headless=true`)
- Access the app in your browser while debugging

### Debugging ETL Pipeline

1. Set breakpoints in `etl/etl_pipeline.py`
2. Select **"Python: ETL Pipeline"** configuration
3. Press F5 to start debugging
4. The ETL will pause at your breakpoints

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'config'"

**Solution:** The `PYTHONPATH` is set automatically in launch.json. If running manually, use:
```bash
PYTHONPATH=$(pwd) python -m streamlit run app/main.py
```

### Issue: "Could not connect to Neo4j"

**Solution:**
1. Check Docker containers: `docker-compose ps`
2. Wait ~30 seconds after starting containers for Neo4j to fully initialize
3. Check logs: `docker-compose logs neo4j`
4. Verify Neo4j Browser: http://localhost:7474 (login: neo4j/librarypass123)

### Issue: "Could not connect to MySQL"

**Solution:**
1. Check MySQL container: `docker-compose ps`
2. Check logs: `docker-compose logs mysql`
3. Wait for initialization scripts to complete (~30 seconds first time)

### Issue: "No data in graph"

**Solution:** Run the ETL pipeline:
```bash
python -m etl.etl_pipeline
```

Or use the debug configuration **"Python: ETL Pipeline"**.

### Issue: Debugger not stopping at breakpoints

**Solution:**
- Ensure `justMyCode: false` is set (already configured)
- Check that you're using the correct Python interpreter (virtual environment)
- Try restarting the debugger

## Project Structure Context

The debug configurations set:
- **Working Directory**: `library_graph_viz/`
- **PYTHONPATH**: Root workspace folder (allows imports like `from config.settings import ...`)
- **Python Interpreter**: Virtual environment at `library_graph_viz/venv/bin/python`

## Quick Reference

| Task | Command/Debug Config |
|------|---------------------|
| Start Docker | `docker-compose up -d` |
| Stop Docker | `docker-compose down` |
| Run Streamlit | "Python: Streamlit App" config |
| Run ETL | "Python: ETL Pipeline" config |
| Run Tests | "Python: Pytest" config |
| Check Docker | `docker-compose ps` |
| View Logs | `docker-compose logs [service]` |

## Environment Variables

The app reads from `.env` file (if exists) or uses defaults from `config/settings.py`. Default values:
- MySQL: `localhost:3306`, user: `root`, password: `librarypass123`
- Neo4j: `bolt://localhost:7687`, user: `neo4j`, password: `librarypass123`

Create a `.env` file in `library_graph_viz/` to override defaults.


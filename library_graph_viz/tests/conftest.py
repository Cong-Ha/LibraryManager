"""Pytest configuration and shared fixtures."""

import os
import pytest
from unittest.mock import Mock, MagicMock
from typing import Generator

# Set test environment variables before importing settings
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_PORT", "3306")
os.environ.setdefault("MYSQL_DATABASE", "library_oltp_test")
os.environ.setdefault("MYSQL_USER", "root")
os.environ.setdefault("MYSQL_PASSWORD", "testpass")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "testpass")


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    from config.settings import Settings

    return Settings(
        mysql_host="localhost",
        mysql_port=3306,
        mysql_database="library_oltp_test",
        mysql_user="root",
        mysql_password="testpass",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="testpass",
        debug=True,
        log_level="DEBUG",
    )


@pytest.fixture
def mock_mysql_connector(mock_settings):
    """Create a mock MySQL connector."""
    from etl.mysql_connector import MySQLConnector

    connector = Mock(spec=MySQLConnector)
    connector.settings = mock_settings

    # Mock fetch_table to return sample data
    connector.fetch_table.return_value = [
        {"id": 1, "name": "Test Item"},
        {"id": 2, "name": "Another Item"},
    ]

    connector.execute_query.return_value = [
        {"id": 1, "name": "Query Result"},
    ]

    return connector


@pytest.fixture
def mock_neo4j_connector(mock_settings):
    """Create a mock Neo4j connector."""
    from etl.neo4j_connector import Neo4jConnector

    connector = Mock(spec=Neo4jConnector)
    connector.settings = mock_settings

    connector.run_query.return_value = [
        {"n": {"id": 1, "name": "Node 1"}},
        {"n": {"id": 2, "name": "Node 2"}},
    ]

    connector.run_write.return_value = {
        "nodes_created": 2,
        "nodes_deleted": 0,
        "relationships_created": 1,
        "relationships_deleted": 0,
        "properties_set": 4,
    }

    connector.get_statistics.return_value = {
        "nodes": {"Book": 10, "Author": 5, "Member": 20},
        "relationships": {"WROTE": 15, "BORROWED": 30},
        "total_nodes": 35,
        "total_relationships": 45,
    }

    return connector


@pytest.fixture
def sample_members():
    """Sample member data for testing."""
    from datetime import date
    return [
        {
            "id": 1,
            "first_name": "Alice",
            "last_name": "Cooper",
            "email": "alice@email.com",
            "phone": "555-0101",
            "membership_date": date(2023, 1, 15),
            "status": "active",
        },
        {
            "id": 2,
            "first_name": "Bob",
            "last_name": "Martinez",
            "email": "bob@email.com",
            "phone": "555-0102",
            "membership_date": date(2023, 2, 20),
            "status": "active",
        },
    ]


@pytest.fixture
def sample_books():
    """Sample book data for testing."""
    return [
        {
            "id": 1,
            "title": "Pride and Prejudice",
            "isbn": "978-0141439518",
            "publication_year": 1813,
            "copies_available": 3,
        },
        {
            "id": 2,
            "title": "1984",
            "isbn": "978-0451524935",
            "publication_year": 1949,
            "copies_available": 5,
        },
    ]


@pytest.fixture
def sample_authors():
    """Sample author data for testing."""
    return [
        {
            "id": 1,
            "first_name": "Jane",
            "last_name": "Austen",
        },
        {
            "id": 2,
            "first_name": "George",
            "last_name": "Orwell",
        },
    ]


@pytest.fixture
def sample_graph_nodes():
    """Sample graph nodes for testing visualization."""
    return [
        {"id": "book_1", "label": "Pride and Prejudice", "type": "Book"},
        {"id": "book_2", "label": "1984", "type": "Book"},
        {"id": "author_1", "label": "Jane Austen", "type": "Author"},
        {"id": "author_2", "label": "George Orwell", "type": "Author"},
    ]


@pytest.fixture
def sample_graph_edges():
    """Sample graph edges for testing visualization."""
    return [
        {"from": "author_1", "to": "book_1", "label": "WROTE"},
        {"from": "author_2", "to": "book_2", "label": "WROTE"},
    ]

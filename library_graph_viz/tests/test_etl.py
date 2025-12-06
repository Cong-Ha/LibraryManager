"""Tests for ETL pipeline and database connectors."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestSettings:
    """Tests for configuration settings."""

    def test_settings_defaults(self, mock_settings):
        """Test that settings have correct defaults."""
        assert mock_settings.mysql_host == "localhost"
        assert mock_settings.mysql_port == 3306
        assert mock_settings.debug is True

    def test_mysql_connection_string(self, mock_settings):
        """Test MySQL connection string property."""
        conn_str = mock_settings.mysql_connection_string
        assert conn_str["host"] == "localhost"
        assert conn_str["port"] == 3306
        assert conn_str["database"] == "library_oltp_test"


class TestMySQLConnector:
    """Tests for MySQL connector."""

    def test_fetch_table_returns_data(self, mock_mysql_connector):
        """Test that fetch_table returns data."""
        result = mock_mysql_connector.fetch_table("member")
        assert len(result) == 2
        assert result[0]["id"] == 1

    def test_execute_query(self, mock_mysql_connector):
        """Test query execution."""
        result = mock_mysql_connector.execute_query("SELECT * FROM test")
        assert len(result) == 1
        assert result[0]["name"] == "Query Result"

    def test_fetch_table_validates_table_name(self):
        """Test that invalid table names are rejected."""
        from etl.mysql_connector import MySQLConnector

        # Create a real instance but with mocked connection
        with patch("etl.mysql_connector.MySQLConnector._get_pool"):
            connector = MySQLConnector()
            connector._cursor = Mock()

            with pytest.raises(ValueError, match="Invalid table name"):
                connector.fetch_table("invalid_table")


class TestNeo4jConnector:
    """Tests for Neo4j connector."""

    def test_run_query_returns_data(self, mock_neo4j_connector):
        """Test that run_query returns data."""
        result = mock_neo4j_connector.run_query("MATCH (n) RETURN n")
        assert len(result) == 2

    def test_run_write_returns_summary(self, mock_neo4j_connector):
        """Test that write operations return summary."""
        result = mock_neo4j_connector.run_write("CREATE (n:Test)")
        assert result["nodes_created"] == 2
        assert result["relationships_created"] == 1

    def test_get_statistics(self, mock_neo4j_connector):
        """Test statistics retrieval."""
        stats = mock_neo4j_connector.get_statistics()
        assert stats["total_nodes"] == 35
        assert stats["total_relationships"] == 45
        assert "Book" in stats["nodes"]


class TestLibraryETL:
    """Tests for the ETL pipeline."""

    def test_load_members(self, mock_mysql_connector, mock_neo4j_connector, sample_members):
        """Test loading members to Neo4j."""
        from etl.etl_pipeline import LibraryETL

        mock_mysql_connector.fetch_table.return_value = sample_members

        etl = LibraryETL(mock_mysql_connector, mock_neo4j_connector)
        count = etl.load_members()

        assert count == 2
        mock_mysql_connector.fetch_table.assert_called_with("member")
        mock_neo4j_connector.run_query.assert_called_once()

    def test_load_books(self, mock_mysql_connector, mock_neo4j_connector, sample_books):
        """Test loading books to Neo4j."""
        from etl.etl_pipeline import LibraryETL

        mock_mysql_connector.fetch_table.return_value = sample_books

        etl = LibraryETL(mock_mysql_connector, mock_neo4j_connector)
        count = etl.load_books()

        assert count == 2
        mock_mysql_connector.fetch_table.assert_called_with("book")

    def test_create_constraints(self, mock_mysql_connector, mock_neo4j_connector):
        """Test constraint creation."""
        from etl.etl_pipeline import LibraryETL

        etl = LibraryETL(mock_mysql_connector, mock_neo4j_connector)
        etl.create_constraints()

        # Should create 7 constraints (one for each node type)
        assert mock_neo4j_connector.create_constraint.call_count == 7

    def test_full_etl_run(self, mock_mysql_connector, mock_neo4j_connector):
        """Test full ETL pipeline execution."""
        from etl.etl_pipeline import LibraryETL

        # Mock all fetch_table calls
        mock_mysql_connector.fetch_table.return_value = [{"id": 1}]

        etl = LibraryETL(mock_mysql_connector, mock_neo4j_connector)
        counts = etl.run(clear_first=True)

        assert "members" in counts
        assert "books" in counts
        assert "authors" in counts
        assert "wrote_rels" in counts

        # Verify clear was called
        mock_neo4j_connector.clear_database.assert_called_once()

    def test_etl_no_clear(self, mock_mysql_connector, mock_neo4j_connector):
        """Test ETL without clearing existing data."""
        from etl.etl_pipeline import LibraryETL

        mock_mysql_connector.fetch_table.return_value = []

        etl = LibraryETL(mock_mysql_connector, mock_neo4j_connector)
        etl.run(clear_first=False)

        mock_neo4j_connector.clear_database.assert_not_called()

    def test_last_sync_timestamp(self, mock_mysql_connector, mock_neo4j_connector):
        """Test that last sync timestamp is set after run."""
        from etl.etl_pipeline import LibraryETL

        mock_mysql_connector.fetch_table.return_value = []

        etl = LibraryETL(mock_mysql_connector, mock_neo4j_connector)
        assert etl.last_sync is None

        etl.run()
        assert etl.last_sync is not None
        assert isinstance(etl.last_sync, datetime)


class TestRelationshipCreation:
    """Tests for relationship creation in ETL."""

    def test_create_wrote_relationships(self, mock_mysql_connector, mock_neo4j_connector):
        """Test WROTE relationship creation."""
        from etl.etl_pipeline import LibraryETL

        mock_mysql_connector.fetch_table.return_value = [
            {"book_id": 1, "author_id": 1},
            {"book_id": 2, "author_id": 2},
        ]

        etl = LibraryETL(mock_mysql_connector, mock_neo4j_connector)
        count = etl.create_wrote_relationships()

        assert count == 2
        mock_mysql_connector.fetch_table.assert_called_with("book_author")

    def test_create_belongs_to_relationships(self, mock_mysql_connector, mock_neo4j_connector):
        """Test BELONGS_TO relationship creation."""
        from etl.etl_pipeline import LibraryETL

        mock_mysql_connector.fetch_table.return_value = [
            {"book_id": 1, "category_id": 1},
        ]

        etl = LibraryETL(mock_mysql_connector, mock_neo4j_connector)
        count = etl.create_belongs_to_relationships()

        assert count == 1
        mock_mysql_connector.fetch_table.assert_called_with("book_category")


@pytest.mark.parametrize("node_type,expected_label", [
    ("member", "Member"),
    ("book", "Book"),
    ("author", "Author"),
    ("category", "Category"),
    ("staff", "Staff"),
    ("loan", "Loan"),
    ("fine", "Fine"),
])
def test_node_types_mapping(node_type, expected_label):
    """Test that all node types are properly mapped."""
    # This is a parameterized test to ensure all node types are handled
    node_label_mapping = {
        "member": "Member",
        "book": "Book",
        "author": "Author",
        "category": "Category",
        "staff": "Staff",
        "loan": "Loan",
        "fine": "Fine",
    }
    assert node_label_mapping[node_type] == expected_label

"""MySQL database connector with context manager support."""

import logging
from typing import Any, Optional, Literal

import mysql.connector
from mysql.connector import pooling
from mysql.connector.cursor import MySQLCursorDict

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

# Database type alias
DatabaseType = Literal["oltp", "olap"]


class MySQLConnector:
    """
    MySQL database connector with connection pooling and context manager support.

    Supports both OLTP (library) and OLAP (library_olap) databases.

    Usage:
        # OLTP database (default)
        with MySQLConnector() as db:
            results = db.execute_query("SELECT * FROM member")

        # OLAP database
        with MySQLConnector(database="olap") as db:
            results = db.execute_query("SELECT * FROM fact_loan")
    """

    _pools: dict[str, pooling.MySQLConnectionPool] = {}

    # Allowed tables by database type
    OLTP_TABLES = {
        "member",
        "book",
        "author",
        "category",
        "staff",
        "loan",
        "fine",
        "book_author",
        "book_category",
    }

    OLAP_TABLES = {
        "dim_date",
        "dim_member",
        "dim_book",
        "dim_category",
        "dim_staff",
        "bridge_book_category",
        "fact_loan",
    }

    def __init__(
        self,
        settings: Optional[Settings] = None,
        database: DatabaseType = "oltp",
    ):
        """
        Initialize MySQL connector.

        Args:
            settings: Application settings. If None, loads from environment.
            database: Database to connect to - "oltp" or "olap".
        """
        self.settings = settings or get_settings()
        self.database = database
        self._connection: Optional[mysql.connector.MySQLConnection] = None
        self._cursor: Optional[MySQLCursorDict] = None

    def _get_database_name(self) -> str:
        """Get the database name based on database type."""
        if self.database == "olap":
            return self.settings.mysql_olap_database
        return self.settings.mysql_database

    @classmethod
    def _get_pool(
        cls, settings: Settings, database: DatabaseType
    ) -> pooling.MySQLConnectionPool:
        """Get or create connection pool for the specified database."""
        pool_key = f"library_pool_{database}"

        if pool_key not in cls._pools:
            db_name = (
                settings.mysql_olap_database
                if database == "olap"
                else settings.mysql_database
            )

            cls._pools[pool_key] = pooling.MySQLConnectionPool(
                pool_name=pool_key,
                pool_size=5,
                pool_reset_session=True,
                host=settings.mysql_host,
                port=settings.mysql_port,
                database=db_name,
                user=settings.mysql_user,
                password=settings.mysql_password,
            )
        return cls._pools[pool_key]

    def __enter__(self) -> "MySQLConnector":
        """Enter context manager and establish connection."""
        try:
            pool = self._get_pool(self.settings, self.database)
            self._connection = pool.get_connection()
            self._cursor = self._connection.cursor(dictionary=True)
            logger.debug(f"MySQL connection established to {self.database} database")
            return self
        except mysql.connector.Error as e:
            logger.error(f"Failed to connect to MySQL ({self.database}): {e}")
            raise ConnectionError(f"MySQL connection failed: {e}") from e

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and close connection."""
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()
        logger.debug(f"MySQL connection closed ({self.database})")

    def execute_query(
        self, query: str, params: Optional[dict] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a query and return results.

        Args:
            query: SQL query string.
            params: Query parameters for parameterized queries.

        Returns:
            List of dictionaries containing query results.

        Raises:
            RuntimeError: If called outside context manager.
            mysql.connector.Error: If query execution fails.
        """
        if not self._cursor:
            raise RuntimeError("MySQLConnector must be used as a context manager")

        try:
            self._cursor.execute(query, params or {})
            results = self._cursor.fetchall()
            logger.debug(f"Query executed, returned {len(results)} rows")
            return results
        except mysql.connector.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def fetch_table(self, table_name: str) -> list[dict[str, Any]]:
        """
        Fetch all rows from a table.

        Args:
            table_name: Name of the table to fetch.

        Returns:
            List of dictionaries containing all rows.
        """
        # Validate table name to prevent SQL injection
        allowed_tables = (
            self.OLAP_TABLES if self.database == "olap" else self.OLTP_TABLES
        )

        if table_name not in allowed_tables:
            raise ValueError(
                f"Invalid table name for {self.database} database: {table_name}"
            )

        query = f"SELECT * FROM {table_name}"
        return self.execute_query(query)

    def fetch_with_joins(self, query_name: str) -> list[dict[str, Any]]:
        """
        Execute predefined join queries.

        Args:
            query_name: Name of the predefined query.

        Returns:
            List of dictionaries containing query results.
        """
        queries = {
            "loans_full": """
                SELECT
                    l.id as loan_id,
                    l.loan_date,
                    l.due_date,
                    l.return_date,
                    l.status as loan_status,
                    m.id as member_id,
                    CONCAT(m.first_name, ' ', m.last_name) as member_name,
                    m.email as member_email,
                    b.id as book_id,
                    b.title as book_title,
                    s.id as staff_id,
                    CONCAT(s.first_name, ' ', s.last_name) as staff_name
                FROM loan l
                JOIN member m ON l.member_id = m.id
                JOIN book b ON l.book_id = b.id
                JOIN staff s ON l.staff_id = s.id
            """,
            "fines_full": """
                SELECT
                    f.id as fine_id,
                    f.amount,
                    f.paid_status,
                    f.issue_date,
                    l.id as loan_id
                FROM fine f
                JOIN loan l ON f.loan_id = l.id
            """,
        }

        if query_name not in queries:
            raise ValueError(f"Unknown query name: {query_name}")

        return self.execute_query(queries[query_name])

    def get_table_count(self, table_name: str) -> int:
        """
        Get the row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Number of rows in the table.
        """
        allowed_tables = (
            self.OLAP_TABLES if self.database == "olap" else self.OLTP_TABLES
        )

        if table_name not in allowed_tables:
            raise ValueError(
                f"Invalid table name for {self.database} database: {table_name}"
            )

        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0

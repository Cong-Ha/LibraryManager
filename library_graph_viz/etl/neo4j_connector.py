"""Neo4j database connector with context manager support."""

import logging
from typing import Any, Optional

from neo4j import GraphDatabase, Driver, Session, Result

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class Neo4jConnector:
    """
    Neo4j database connector with driver lifecycle management.

    Usage:
        with Neo4jConnector() as db:
            results = db.run_query("MATCH (n) RETURN n LIMIT 10")
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize Neo4j connector.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self._driver: Optional[Driver] = None

    def __enter__(self) -> "Neo4jConnector":
        """Enter context manager and create driver."""
        try:
            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
            # Verify connectivity
            self._driver.verify_connectivity()
            logger.debug("Neo4j connection established")
            return self
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise ConnectionError(f"Neo4j connection failed: {e}") from e

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and close driver."""
        if self._driver:
            self._driver.close()
        logger.debug("Neo4j connection closed")

    @property
    def driver(self) -> Driver:
        """Get the Neo4j driver instance."""
        if not self._driver:
            raise RuntimeError("Neo4jConnector must be used as a context manager")
        return self._driver

    def run_query(
        self, query: str, params: Optional[dict] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string.
            params: Query parameters.

        Returns:
            List of dictionaries containing query results.
        """
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def run_transaction(
        self, queries: list[tuple[str, Optional[dict]]]
    ) -> list[list[dict[str, Any]]]:
        """
        Execute multiple queries in a single transaction.

        Args:
            queries: List of (query, params) tuples.

        Returns:
            List of result lists for each query.
        """

        def execute_queries(tx):
            results = []
            for query, params in queries:
                result = tx.run(query, params or {})
                results.append([record.data() for record in result])
            return results

        with self.driver.session() as session:
            return session.execute_write(execute_queries)

    def run_write(self, query: str, params: Optional[dict] = None) -> dict[str, Any]:
        """
        Execute a write query and return summary.

        Args:
            query: Cypher write query.
            params: Query parameters.

        Returns:
            Dictionary with counters from the result summary.
        """
        with self.driver.session() as session:
            result = session.run(query, params or {})
            summary = result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "nodes_deleted": summary.counters.nodes_deleted,
                "relationships_created": summary.counters.relationships_created,
                "relationships_deleted": summary.counters.relationships_deleted,
                "properties_set": summary.counters.properties_set,
            }

    def create_constraint(self, label: str, property_name: str) -> None:
        """
        Create a uniqueness constraint on a node property.

        Args:
            label: Node label.
            property_name: Property to constrain.
        """
        constraint_name = f"constraint_{label.lower()}_{property_name}"
        query = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label})
            REQUIRE n.{property_name} IS UNIQUE
        """
        try:
            self.run_query(query)
            logger.info(f"Created constraint: {constraint_name}")
        except Exception as e:
            logger.warning(f"Constraint creation warning: {e}")

    def create_index(self, label: str, property_name: str) -> None:
        """
        Create an index on a node property.

        Args:
            label: Node label.
            property_name: Property to index.
        """
        index_name = f"index_{label.lower()}_{property_name}"
        query = f"""
            CREATE INDEX {index_name} IF NOT EXISTS
            FOR (n:{label})
            ON (n.{property_name})
        """
        try:
            self.run_query(query)
            logger.info(f"Created index: {index_name}")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    def clear_database(self) -> dict[str, Any]:
        """
        Delete all nodes and relationships from the database.

        Returns:
            Dictionary with deletion counts.
        """
        query = "MATCH (n) DETACH DELETE n"
        result = self.run_write(query)
        logger.info(
            f"Database cleared: {result['nodes_deleted']} nodes, "
            f"{result['relationships_deleted']} relationships deleted"
        )
        return result

    def get_statistics(self) -> dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with node and relationship counts by type.
        """
        node_counts = self.run_query("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(*) AS count
        """)

        rel_counts = self.run_query("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(*) AS count
        """)

        stats = {
            "nodes": {row["label"]: row["count"] for row in node_counts},
            "relationships": {row["type"]: row["count"] for row in rel_counts},
        }

        total_nodes = sum(stats["nodes"].values())
        total_rels = sum(stats["relationships"].values())
        stats["total_nodes"] = total_nodes
        stats["total_relationships"] = total_rels

        return stats

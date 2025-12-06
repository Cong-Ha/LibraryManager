"""ETL Pipeline for migrating data from MySQL to Neo4j."""

import argparse
import logging
import sys
from datetime import datetime
from typing import Any, Optional

from config.settings import get_settings
from etl.mysql_connector import MySQLConnector
from etl.neo4j_connector import Neo4jConnector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LibraryETL:
    """
    ETL pipeline for migrating library data from MySQL to Neo4j.

    This class handles the complete data migration including:
    - Creating constraints and indexes
    - Loading all node types
    - Creating all relationships
    """

    def __init__(self, mysql: MySQLConnector, neo4j: Neo4jConnector):
        """
        Initialize ETL pipeline.

        Args:
            mysql: MySQL connector instance.
            neo4j: Neo4j connector instance.
        """
        self.mysql = mysql
        self.neo4j = neo4j
        self._last_sync: Optional[datetime] = None

    def clear_graph(self) -> dict[str, Any]:
        """Clear all data from Neo4j database."""
        logger.info("Clearing existing graph data...")
        return self.neo4j.clear_database()

    def create_constraints(self) -> None:
        """Create uniqueness constraints for all node types."""
        logger.info("Creating constraints...")
        constraints = [
            ("Member", "id"),
            ("Book", "id"),
            ("Author", "id"),
            ("Category", "id"),
            ("Staff", "id"),
            ("Loan", "id"),
            ("Fine", "id"),
        ]
        for label, prop in constraints:
            self.neo4j.create_constraint(label, prop)

    def load_members(self) -> int:
        """Load member nodes from MySQL to Neo4j."""
        logger.info("Loading members...")
        members = self.mysql.fetch_table("member")

        # Transform: concatenate first_name and last_name into name
        for member in members:
            member["name"] = f"{member['first_name']} {member['last_name']}"
            member["membership_date"] = (
                str(member["membership_date"]) if member["membership_date"] else None
            )

        query = """
            UNWIND $members AS m
            MERGE (member:Member {id: m.id})
            SET member.name = m.name,
                member.email = m.email,
                member.phone = m.phone,
                member.status = m.status,
                member.membership_date = m.membership_date
        """
        self.neo4j.run_query(query, {"members": members})
        logger.info(f"Loaded {len(members)} members")
        return len(members)

    def load_books(self) -> int:
        """Load book nodes from MySQL to Neo4j."""
        logger.info("Loading books...")
        books = self.mysql.fetch_table("book")

        query = """
            UNWIND $books AS b
            MERGE (book:Book {id: b.id})
            SET book.title = b.title,
                book.isbn = b.isbn,
                book.publication_year = b.publication_year,
                book.copies_available = b.copies_available
        """
        self.neo4j.run_query(query, {"books": books})
        logger.info(f"Loaded {len(books)} books")
        return len(books)

    def load_authors(self) -> int:
        """Load author nodes from MySQL to Neo4j."""
        logger.info("Loading authors...")
        authors = self.mysql.fetch_table("author")

        # Transform: concatenate first_name and last_name into name
        for author in authors:
            author["name"] = f"{author['first_name']} {author['last_name']}"

        query = """
            UNWIND $authors AS a
            MERGE (author:Author {id: a.id})
            SET author.name = a.name
        """
        self.neo4j.run_query(query, {"authors": authors})
        logger.info(f"Loaded {len(authors)} authors")
        return len(authors)

    def load_categories(self) -> int:
        """Load category nodes from MySQL to Neo4j."""
        logger.info("Loading categories...")
        categories = self.mysql.fetch_table("category")

        query = """
            UNWIND $categories AS c
            MERGE (category:Category {id: c.id})
            SET category.name = c.name,
                category.description = c.description
        """
        self.neo4j.run_query(query, {"categories": categories})
        logger.info(f"Loaded {len(categories)} categories")
        return len(categories)

    def load_staff(self) -> int:
        """Load staff nodes from MySQL to Neo4j."""
        logger.info("Loading staff...")
        staff = self.mysql.fetch_table("staff")

        # Transform: concatenate first_name and last_name into name
        for s in staff:
            s["name"] = f"{s['first_name']} {s['last_name']}"
            s["hire_date"] = str(s["hire_date"]) if s["hire_date"] else None

        query = """
            UNWIND $staff AS s
            MERGE (st:Staff {id: s.id})
            SET st.name = s.name,
                st.email = s.email,
                st.role = s.role,
                st.hire_date = s.hire_date
        """
        self.neo4j.run_query(query, {"staff": staff})
        logger.info(f"Loaded {len(staff)} staff members")
        return len(staff)

    def load_loans(self) -> int:
        """Load loan nodes from MySQL to Neo4j."""
        logger.info("Loading loans...")
        loans = self.mysql.fetch_table("loan")

        # Convert dates to strings for Neo4j
        for loan in loans:
            loan["loan_date"] = str(loan["loan_date"]) if loan["loan_date"] else None
            loan["due_date"] = str(loan["due_date"]) if loan["due_date"] else None
            loan["return_date"] = (
                str(loan["return_date"]) if loan["return_date"] else None
            )

        query = """
            UNWIND $loans AS l
            MERGE (loan:Loan {id: l.id})
            SET loan.loan_date = l.loan_date,
                loan.due_date = l.due_date,
                loan.return_date = l.return_date,
                loan.status = l.status
        """
        self.neo4j.run_query(query, {"loans": loans})
        logger.info(f"Loaded {len(loans)} loans")
        return len(loans)

    def load_fines(self) -> int:
        """Load fine nodes from MySQL to Neo4j."""
        logger.info("Loading fines...")
        fines = self.mysql.fetch_table("fine")

        # Convert data for Neo4j
        for fine in fines:
            fine["amount"] = float(fine["amount"]) if fine["amount"] else 0.0
            fine["issue_date"] = str(fine["issue_date"]) if fine["issue_date"] else None

        query = """
            UNWIND $fines AS f
            MERGE (fine:Fine {id: f.id})
            SET fine.amount = f.amount,
                fine.paid_status = f.paid_status,
                fine.issue_date = f.issue_date
        """
        self.neo4j.run_query(query, {"fines": fines})
        logger.info(f"Loaded {len(fines)} fines")
        return len(fines)

    def create_wrote_relationships(self) -> int:
        """Create WROTE relationships between authors and books."""
        logger.info("Creating WROTE relationships...")
        book_authors = self.mysql.fetch_table("book_author")

        query = """
            UNWIND $relations AS r
            MATCH (a:Author {id: r.author_id})
            MATCH (b:Book {id: r.book_id})
            MERGE (a)-[:WROTE]->(b)
        """
        self.neo4j.run_query(query, {"relations": book_authors})
        logger.info(f"Created {len(book_authors)} WROTE relationships")
        return len(book_authors)

    def create_belongs_to_relationships(self) -> int:
        """Create BELONGS_TO relationships between books and categories."""
        logger.info("Creating BELONGS_TO relationships...")
        book_categories = self.mysql.fetch_table("book_category")

        query = """
            UNWIND $relations AS r
            MATCH (b:Book {id: r.book_id})
            MATCH (c:Category {id: r.category_id})
            MERGE (b)-[:BELONGS_TO]->(c)
        """
        self.neo4j.run_query(query, {"relations": book_categories})
        logger.info(f"Created {len(book_categories)} BELONGS_TO relationships")
        return len(book_categories)

    def create_loan_relationships(self) -> int:
        """Create loan-related relationships (BORROWED, CONTAINS, PROCESSED_BY)."""
        logger.info("Creating loan relationships...")
        loans = self.mysql.fetch_table("loan")

        # Create BORROWED relationships (Member -> Loan)
        query_borrowed = """
            UNWIND $loans AS l
            MATCH (m:Member {id: l.member_id})
            MATCH (loan:Loan {id: l.id})
            MERGE (m)-[:BORROWED]->(loan)
        """
        self.neo4j.run_query(query_borrowed, {"loans": loans})

        # Create CONTAINS relationships (Loan -> Book)
        query_contains = """
            UNWIND $loans AS l
            MATCH (loan:Loan {id: l.id})
            MATCH (b:Book {id: l.book_id})
            MERGE (loan)-[:CONTAINS]->(b)
        """
        self.neo4j.run_query(query_contains, {"loans": loans})

        # Create PROCESSED_BY relationships (Loan -> Staff)
        query_processed = """
            UNWIND $loans AS l
            MATCH (loan:Loan {id: l.id})
            MATCH (s:Staff {id: l.staff_id})
            MERGE (loan)-[:PROCESSED_BY]->(s)
        """
        self.neo4j.run_query(query_processed, {"loans": loans})

        total = len(loans) * 3
        logger.info(f"Created {total} loan relationships (BORROWED, CONTAINS, PROCESSED_BY)")
        return total

    def create_fine_relationships(self) -> int:
        """Create HAS_FINE relationships between loans and fines."""
        logger.info("Creating HAS_FINE relationships...")
        fines = self.mysql.fetch_table("fine")

        # Convert Decimal to float for Neo4j compatibility
        for fine in fines:
            fine["amount"] = float(fine["amount"]) if fine["amount"] else 0.0

        query = """
            UNWIND $fines AS f
            MATCH (loan:Loan {id: f.loan_id})
            MATCH (fine:Fine {id: f.id})
            MERGE (loan)-[:HAS_FINE]->(fine)
        """
        self.neo4j.run_query(query, {"fines": fines})
        logger.info(f"Created {len(fines)} HAS_FINE relationships")
        return len(fines)

    def run(self, clear_first: bool = True) -> dict[str, int]:
        """
        Run the complete ETL pipeline.

        Args:
            clear_first: Whether to clear existing data before import.

        Returns:
            Dictionary with counts of created entities.
        """
        start_time = datetime.now()
        logger.info("Starting ETL pipeline...")

        counts = {}

        if clear_first:
            self.clear_graph()

        # Create constraints
        self.create_constraints()

        # Load nodes
        counts["members"] = self.load_members()
        counts["books"] = self.load_books()
        counts["authors"] = self.load_authors()
        counts["categories"] = self.load_categories()
        counts["staff"] = self.load_staff()
        counts["loans"] = self.load_loans()
        counts["fines"] = self.load_fines()

        # Create relationships
        counts["wrote_rels"] = self.create_wrote_relationships()
        counts["belongs_to_rels"] = self.create_belongs_to_relationships()
        counts["loan_rels"] = self.create_loan_relationships()
        counts["fine_rels"] = self.create_fine_relationships()

        self._last_sync = datetime.now()
        duration = (self._last_sync - start_time).total_seconds()
        logger.info(f"ETL pipeline completed in {duration:.2f} seconds")
        logger.info(f"Summary: {counts}")

        return counts

    @property
    def last_sync(self) -> Optional[datetime]:
        """Get the timestamp of the last synchronization."""
        return self._last_sync


def main():
    """CLI entry point for running the ETL pipeline."""
    parser = argparse.ArgumentParser(
        description="ETL Pipeline: Migrate library data from MySQL to Neo4j"
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Don't clear existing Neo4j data before import",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    settings = get_settings()

    try:
        with MySQLConnector(settings) as mysql:
            with Neo4jConnector(settings) as neo4j:
                etl = LibraryETL(mysql, neo4j)
                counts = etl.run(clear_first=not args.no_clear)

                print("\n" + "=" * 50)
                print("ETL Pipeline Completed Successfully!")
                print("=" * 50)
                print("\nNodes created:")
                print(f"  - Members: {counts['members']}")
                print(f"  - Books: {counts['books']}")
                print(f"  - Authors: {counts['authors']}")
                print(f"  - Categories: {counts['categories']}")
                print(f"  - Staff: {counts['staff']}")
                print(f"  - Loans: {counts['loans']}")
                print(f"  - Fines: {counts['fines']}")
                print("\nRelationships created:")
                print(f"  - WROTE: {counts['wrote_rels']}")
                print(f"  - BELONGS_TO: {counts['belongs_to_rels']}")
                print(f"  - Loan relationships: {counts['loan_rels']}")
                print(f"  - HAS_FINE: {counts['fine_rels']}")
                print("=" * 50)

    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        print(f"\nError: {e}")
        print("Make sure both MySQL and Neo4j are running.")
        print("You can start them with: docker-compose up -d")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"ETL pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

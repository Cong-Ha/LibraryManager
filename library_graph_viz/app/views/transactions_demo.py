"""Transactions Demo View - Interactive ACID Transaction Demonstrations."""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from etl.mysql_connector import MySQLConnector
from config.settings import get_settings


def get_available_books() -> list[dict]:
    """Fetch books with copies available."""
    settings = get_settings()
    with MySQLConnector(settings, database="oltp") as db:
        return db.execute_query("""
            SELECT id, title, copies_available
            FROM book
            WHERE copies_available > 0
            ORDER BY title
            LIMIT 50
        """)


def get_members() -> list[dict]:
    """Fetch active members."""
    settings = get_settings()
    with MySQLConnector(settings, database="oltp") as db:
        return db.execute_query("""
            SELECT id, CONCAT(first_name, ' ', last_name) AS name, email
            FROM member
            WHERE status = 'active'
            ORDER BY last_name, first_name
            LIMIT 50
        """)


def get_staff() -> list[dict]:
    """Fetch staff members."""
    settings = get_settings()
    with MySQLConnector(settings, database="oltp") as db:
        return db.execute_query("""
            SELECT id, CONCAT(first_name, ' ', last_name) AS name, role
            FROM staff
            ORDER BY last_name, first_name
        """)


def get_active_loans() -> list[dict]:
    """Fetch active and overdue loans for return processing."""
    settings = get_settings()
    with MySQLConnector(settings, database="oltp") as db:
        return db.execute_query("""
            SELECT
                l.id AS loan_id,
                CONCAT(m.first_name, ' ', m.last_name) AS member_name,
                b.id AS book_id,
                b.title AS book_title,
                l.loan_date,
                l.due_date,
                l.status,
                DATEDIFF(CURDATE(), l.due_date) AS days_overdue
            FROM loan l
            JOIN member m ON l.member_id = m.id
            JOIN book b ON l.book_id = b.id
            WHERE l.status IN ('active', 'overdue')
            ORDER BY l.due_date ASC
            LIMIT 50
        """)


def get_book_state(book_id: int) -> dict:
    """Get current state of a book."""
    settings = get_settings()
    with MySQLConnector(settings, database="oltp") as db:
        result = db.execute_query(
            "SELECT id, title, copies_available FROM book WHERE id = %(book_id)s",
            {"book_id": book_id}
        )
        return result[0] if result else {}


def render_checkout_tab() -> None:
    """Render the Book Checkout transaction tab."""
    st.subheader("Book Checkout Transaction")
    st.markdown("""
    This transaction demonstrates **atomicity** - both operations (create loan AND
    decrement inventory) must succeed together, or neither should occur.
    """)

    # Load data
    members = get_members()
    books = get_available_books()
    staff = get_staff()

    if not members or not books or not staff:
        st.warning("No data available. Please ensure the database is populated.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Select Checkout Details")

        member_options = {f"{m['name']} ({m['email']})": m['id'] for m in members}
        selected_member = st.selectbox(
            "Member",
            options=list(member_options.keys()),
            key="checkout_member"
        )
        member_id = member_options[selected_member]

        book_options = {f"{b['title']} ({b['copies_available']} available)": b['id'] for b in books}
        selected_book = st.selectbox(
            "Book",
            options=list(book_options.keys()),
            key="checkout_book"
        )
        book_id = book_options[selected_book]

        staff_options = {f"{s['name']} ({s['role']})": s['id'] for s in staff}
        selected_staff = st.selectbox(
            "Processing Staff",
            options=list(staff_options.keys()),
            key="checkout_staff"
        )
        staff_id = staff_options[selected_staff]

        loan_date = date.today()
        due_date = loan_date + timedelta(days=14)

        st.info(f"Loan Date: {loan_date} | Due Date: {due_date}")

    with col2:
        st.markdown("#### Current Book State")
        book_state = get_book_state(book_id)
        if book_state:
            st.metric("Copies Available", book_state['copies_available'])
            st.caption(f"Book: {book_state['title']}")

    st.divider()

    # SQL Preview
    st.markdown("#### Transaction SQL Preview")

    checkout_sql = f"""-- TRANSACTION: Book Checkout
START TRANSACTION;

-- Step 1: Create loan record
INSERT INTO loan (member_id, book_id, staff_id, loan_date, due_date, status)
VALUES ({member_id}, {book_id}, {staff_id}, '{loan_date}', '{due_date}', 'active');

-- Step 2: Decrement available copies
UPDATE book
SET copies_available = copies_available - 1
WHERE id = {book_id};

COMMIT;"""

    st.code(checkout_sql, language="sql")

    # Execute button
    if st.button("Execute Checkout Transaction", type="primary", key="exec_checkout"):
        try:
            settings = get_settings()
            with MySQLConnector(settings, database="oltp") as db:
                db.begin_transaction()

                # Step 1: Insert loan
                db.execute_write(
                    """INSERT INTO loan (member_id, book_id, staff_id, loan_date, due_date, status)
                       VALUES (%(member_id)s, %(book_id)s, %(staff_id)s, %(loan_date)s, %(due_date)s, 'active')""",
                    {
                        "member_id": member_id,
                        "book_id": book_id,
                        "staff_id": staff_id,
                        "loan_date": loan_date,
                        "due_date": due_date
                    },
                    auto_commit=False
                )
                loan_id = db.get_last_insert_id()

                # Step 2: Decrement copies
                db.execute_write(
                    "UPDATE book SET copies_available = copies_available - 1 WHERE id = %(book_id)s",
                    {"book_id": book_id},
                    auto_commit=False
                )

                # Commit transaction
                db.commit()

                st.success(f"Checkout successful! Loan ID: {loan_id}")

                # Show updated state
                st.markdown("#### After Transaction")
                new_book_state = get_book_state(book_id)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Copies Available",
                        new_book_state['copies_available'],
                        delta=-1
                    )
                with col2:
                    st.metric("New Loan ID", loan_id)

        except Exception as e:
            st.error(f"Transaction failed: {str(e)}")


def render_return_tab() -> None:
    """Render the Book Return with Fine transaction tab."""
    st.subheader("Book Return with Fine Processing")
    st.markdown("""
    This transaction demonstrates handling **multiple related operations** atomically:
    update loan status, increment inventory, and create/update fine record.
    """)

    loans = get_active_loans()

    if not loans:
        st.info("No active loans to return.")
        return

    # Loan selector
    loan_options = {
        f"Loan #{l['loan_id']}: {l['book_title']} - {l['member_name']} (Due: {l['due_date']})": l
        for l in loans
    }

    selected_loan_key = st.selectbox(
        "Select Loan to Return",
        options=list(loan_options.keys()),
        key="return_loan"
    )
    selected_loan = loan_options[selected_loan_key]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Loan Details")
        st.write(f"**Member:** {selected_loan['member_name']}")
        st.write(f"**Book:** {selected_loan['book_title']}")
        st.write(f"**Loan Date:** {selected_loan['loan_date']}")
        st.write(f"**Due Date:** {selected_loan['due_date']}")
        st.write(f"**Status:** {selected_loan['status']}")

    with col2:
        st.markdown("#### Fine Calculation")
        days_overdue = selected_loan['days_overdue']
        fine_per_day = 0.25

        if days_overdue > 0:
            fine_amount = days_overdue * fine_per_day
            st.warning(f"Book is **{days_overdue} days overdue**")
            st.metric("Fine Amount", f"${fine_amount:.2f}")
            st.caption(f"Rate: ${fine_per_day}/day")
        else:
            fine_amount = 0
            st.success("Book returned on time - no fine!")

    st.divider()

    # SQL Preview
    st.markdown("#### Transaction SQL Preview")

    return_sql = f"""-- TRANSACTION: Book Return with Fine
START TRANSACTION;

-- Step 1: Update loan record to 'returned'
UPDATE loan
SET return_date = CURDATE(), status = 'returned'
WHERE id = {selected_loan['loan_id']};

-- Step 2: Increment book's available copies
UPDATE book
SET copies_available = copies_available + 1
WHERE id = {selected_loan['book_id']};"""

    if fine_amount > 0:
        return_sql += f"""

-- Step 3: Create fine record
INSERT INTO fine (loan_id, amount, issue_date, paid_status)
VALUES ({selected_loan['loan_id']}, {fine_amount:.2f}, CURDATE(), 'unpaid');"""

    return_sql += "\n\nCOMMIT;"

    st.code(return_sql, language="sql")

    # Execute button
    if st.button("Process Return Transaction", type="primary", key="exec_return"):
        try:
            settings = get_settings()
            with MySQLConnector(settings, database="oltp") as db:
                db.begin_transaction()

                # Step 1: Update loan
                db.execute_write(
                    """UPDATE loan SET return_date = CURDATE(), status = 'returned'
                       WHERE id = %(loan_id)s""",
                    {"loan_id": selected_loan['loan_id']},
                    auto_commit=False
                )

                # Step 2: Increment copies
                db.execute_write(
                    "UPDATE book SET copies_available = copies_available + 1 WHERE id = %(book_id)s",
                    {"book_id": selected_loan['book_id']},
                    auto_commit=False
                )

                # Step 3: Create fine if overdue
                fine_id = None
                if fine_amount > 0:
                    db.execute_write(
                        """INSERT INTO fine (loan_id, amount, issue_date, paid_status)
                           VALUES (%(loan_id)s, %(amount)s, CURDATE(), 'unpaid')""",
                        {"loan_id": selected_loan['loan_id'], "amount": fine_amount},
                        auto_commit=False
                    )
                    fine_id = db.get_last_insert_id()

                # Commit
                db.commit()

                st.success("Return processed successfully!")

                # Show results
                col1, col2 = st.columns(2)
                with col1:
                    new_book_state = get_book_state(selected_loan['book_id'])
                    st.metric(
                        "Copies Available",
                        new_book_state['copies_available'],
                        delta=1
                    )
                with col2:
                    if fine_id:
                        st.metric("Fine Created", f"${fine_amount:.2f}")
                        st.caption(f"Fine ID: {fine_id}")
                    else:
                        st.info("No fine required")

        except Exception as e:
            st.error(f"Transaction failed: {str(e)}")


def render_rollback_tab() -> None:
    """Render the Rollback demonstration tab."""
    st.subheader("Rollback Demonstration")
    st.markdown("""
    This demonstrates what happens when a transaction is **rolled back** - all changes
    are undone as if they never happened. This is the **Atomicity** guarantee in action.
    """)

    books = get_available_books()
    members = get_members()
    staff = get_staff()

    if not books or not members or not staff:
        st.warning("No data available.")
        return

    # Select a book for the demo
    book_options = {f"{b['title']} ({b['copies_available']} available)": b['id'] for b in books}
    selected_book = st.selectbox(
        "Select Book for Demo",
        options=list(book_options.keys()),
        key="rollback_book"
    )
    book_id = book_options[selected_book]

    # Show current state
    st.markdown("#### Current State (Before Transaction)")
    book_state = get_book_state(book_id)
    st.metric("Copies Available", book_state['copies_available'])

    st.divider()

    # SQL Preview
    st.markdown("#### Transaction SQL (with ROLLBACK)")

    rollback_sql = f"""-- TRANSACTION: Checkout with ROLLBACK
START TRANSACTION;

-- Attempt to checkout a book
INSERT INTO loan (member_id, book_id, staff_id, loan_date, due_date, status)
VALUES ({members[0]['id']}, {book_id}, {staff[0]['id']}, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'active');

UPDATE book
SET copies_available = copies_available - 1
WHERE id = {book_id};

-- Simulate something going wrong - ROLLBACK!
ROLLBACK;

-- All changes are undone. Book copies should be unchanged."""

    st.code(rollback_sql, language="sql")

    if st.button("Execute Rollback Demo", type="secondary", key="exec_rollback"):
        try:
            settings = get_settings()
            with MySQLConnector(settings, database="oltp") as db:
                # Show before state
                before_state = get_book_state(book_id)

                db.begin_transaction()

                # Insert loan
                db.execute_write(
                    """INSERT INTO loan (member_id, book_id, staff_id, loan_date, due_date, status)
                       VALUES (%(member_id)s, %(book_id)s, %(staff_id)s, CURDATE(),
                               DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'active')""",
                    {
                        "member_id": members[0]['id'],
                        "book_id": book_id,
                        "staff_id": staff[0]['id']
                    },
                    auto_commit=False
                )

                # Update book
                db.execute_write(
                    "UPDATE book SET copies_available = copies_available - 1 WHERE id = %(book_id)s",
                    {"book_id": book_id},
                    auto_commit=False
                )

                # Show "during" state (uncommitted - only visible to this session)
                st.info("Transaction in progress... loan created, inventory decremented")

                # ROLLBACK!
                db.rollback()

                st.warning("ROLLBACK executed!")

            # Show after state (must be same as before)
            after_state = get_book_state(book_id)

            st.markdown("#### State Comparison")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Before**")
                st.metric("Copies", before_state['copies_available'])

            with col2:
                st.markdown("**Would Have Been**")
                st.metric("Copies", before_state['copies_available'] - 1, delta=-1)

            with col3:
                st.markdown("**After Rollback**")
                st.metric("Copies", after_state['copies_available'])

            if before_state['copies_available'] == after_state['copies_available']:
                st.success("Rollback successful! State unchanged - atomicity preserved.")
            else:
                st.error("Something unexpected happened!")

        except Exception as e:
            st.error(f"Demo failed: {str(e)}")


def render_acid_tab() -> None:
    """Render the ACID properties summary tab."""
    st.subheader("ACID Properties Summary")
    st.markdown("""
    Transactions in MySQL guarantee **ACID** properties - the four pillars of
    reliable database operations.
    """)

    tabs = st.tabs(["Atomicity", "Consistency", "Isolation", "Durability"])

    with tabs[0]:
        st.markdown("### Atomicity")
        st.markdown("""
        **Definition:** All operations in a transaction complete successfully,
        or none of them do. There's no partial completion.

        **Library Example:**
        When checking out a book, we must:
        1. Create a loan record
        2. Decrement the book's available copies

        If step 2 fails, step 1 should be undone. We can't have a loan without
        reducing inventory, or vice versa.
        """)

        st.code("""START TRANSACTION;
INSERT INTO loan (...) VALUES (...);  -- Step 1
UPDATE book SET copies = copies - 1;  -- Step 2
COMMIT;  -- Both succeed together

-- If Step 2 fails:
ROLLBACK;  -- Step 1 is undone too""", language="sql")

    with tabs[1]:
        st.markdown("### Consistency")
        st.markdown("""
        **Definition:** A transaction brings the database from one valid state
        to another valid state. All constraints and rules are maintained.

        **Library Example:**
        - `copies_available` can never go negative (CHECK constraint)
        - A loan must reference a valid member and book (FOREIGN KEY constraint)
        - Member emails must be unique (UNIQUE constraint)

        If a transaction would violate any constraint, it's rejected entirely.
        """)

        st.code("""-- This will fail due to constraint violation:
START TRANSACTION;
UPDATE book SET copies_available = -1 WHERE id = 1;
-- ERROR: Check constraint violation!
-- Transaction fails, database remains consistent""", language="sql")

    with tabs[2]:
        st.markdown("### Isolation")
        st.markdown("""
        **Definition:** Concurrent transactions don't interfere with each other.
        Each transaction sees a consistent view of the data.

        **Library Example:**
        If two librarians try to check out the last copy of a book simultaneously:
        - Transaction A reads: 1 copy available
        - Transaction B reads: 1 copy available
        - Transaction A decrements: 0 copies
        - Transaction B tries to decrement: BLOCKED (or fails with conflict)

        Without isolation, both could succeed, making copies = -1 (invalid).
        """)

        st.info("MySQL uses row-level locking with InnoDB to prevent conflicts.")

    with tabs[3]:
        st.markdown("### Durability")
        st.markdown("""
        **Definition:** Once a transaction is committed, the changes are permanent
        and survive system failures (crashes, power outages, etc.).

        **Library Example:**
        After `COMMIT`:
        - The loan record is permanently saved
        - The book's inventory is permanently updated
        - Even if the server crashes immediately after, these changes persist

        MySQL achieves this through:
        - Write-ahead logging (WAL)
        - Redo logs that can replay committed transactions
        - Periodic checkpoints to disk
        """)

        st.code("""START TRANSACTION;
INSERT INTO loan (...) VALUES (...);
UPDATE book SET copies_available = copies_available - 1;
COMMIT;  -- <-- This is the point of no return

-- After COMMIT, the changes are permanent!
-- Server could crash here and data would survive.""", language="sql")

    st.divider()

    # Summary table
    st.markdown("### Quick Reference")
    summary_df = pd.DataFrame({
        "Property": ["Atomicity", "Consistency", "Isolation", "Durability"],
        "Guarantees": [
            "All or nothing",
            "Valid state to valid state",
            "No interference between transactions",
            "Committed = Permanent"
        ],
        "Key SQL": [
            "START TRANSACTION, COMMIT, ROLLBACK",
            "Constraints (FK, CHECK, UNIQUE)",
            "Locking, MVCC",
            "COMMIT + Write-ahead logging"
        ]
    })
    st.table(summary_df)


def render(neo4j=None) -> None:
    """Render the Transactions Demo view."""
    st.header("Transaction Demonstrations")
    st.markdown("""
    Interactive demonstrations of MySQL transactions showing **ACID properties** in action.
    These examples are from the Library Management System OLTP database.
    """)

    # Create tabs
    tabs = st.tabs([
        "Book Checkout",
        "Book Return + Fine",
        "Rollback Demo",
        "ACID Summary"
    ])

    with tabs[0]:
        render_checkout_tab()

    with tabs[1]:
        render_return_tab()

    with tabs[2]:
        render_rollback_tab()

    with tabs[3]:
        render_acid_tab()

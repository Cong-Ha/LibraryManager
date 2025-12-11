-- ============================================================================
-- Library Management System - Transaction Scripts
-- CWEB 2125 Database Systems: Programming & Admin
-- Week 2 of 4: OLTP Database Implementation
-- Date: 2025-11-26
-- ============================================================================

USE library;

-- ============================================================================
-- TRANSACTIONS OVERVIEW
-- ============================================================================
-- Transactions ensure ACID properties:
--   A - Atomicity: All operations complete or none do
--   C - Consistency: Database remains in a valid state
--   I - Isolation: Concurrent transactions don't interfere
--   D - Durability: Committed changes persist
--
-- This script demonstrates two transaction scenarios:
--   1. Book Checkout: Create loan + decrement inventory (atomicity)
--   2. Book Return with Fine: Update loan + update inventory + create fine
-- ============================================================================

-- ############################################################################
-- TRANSACTION 1: BOOK CHECKOUT
-- ############################################################################
-- Scenario: A member wants to check out a book. This requires:
--   1. Verify book availability (copies_available > 0)
--   2. Create a new loan record
--   3. Decrement the book's copies_available count
-- 
-- Both operations must succeed together, or neither should occur.
-- If we create a loan but fail to decrement inventory, data becomes
-- inconsistent. Transactions prevent this.
-- ############################################################################

-- Show initial state
SELECT 'TRANSACTION 1: BOOK CHECKOUT' AS operation;
SELECT '--- Before Transaction ---' AS status;

SELECT id, title, copies_available 
FROM book 
WHERE id = 1;  -- 1984

SELECT id, first_name, last_name 
FROM member 
WHERE id = 6;  -- Jessica Davis

-- Begin the transaction
START TRANSACTION;

-- Step 1: Check if book is available
SET @book_id = 1;
SET @member_id = 6;
SET @staff_id = 3;
SET @copies = (SELECT copies_available FROM book WHERE id = @book_id);

-- Only proceed if copies are available
-- In a real application, you would use a stored procedure with IF/ELSE logic
-- For this demonstration, we'll assume the book is available

-- Step 2: Create the loan record
INSERT INTO loan (member_id, book_id, staff_id, loan_date, due_date, status)
VALUES (
    @member_id,
    @book_id,
    @staff_id,
    CURDATE(),
    DATE_ADD(CURDATE(), INTERVAL 14 DAY),
    'active'
);

-- Step 3: Decrement the copies_available count
UPDATE book 
SET copies_available = copies_available - 1 
WHERE id = @book_id;

-- Verify changes before committing
SELECT '--- During Transaction (Before Commit) ---' AS status;

SELECT id, title, copies_available 
FROM book 
WHERE id = @book_id;

SELECT id, member_id, book_id, loan_date, due_date, status 
FROM loan 
WHERE member_id = @member_id 
ORDER BY id DESC 
LIMIT 1;

-- Commit the transaction - make changes permanent
COMMIT;

SELECT '--- After Commit ---' AS status;

SELECT id, title, copies_available 
FROM book 
WHERE id = @book_id;

-- ############################################################################
-- TRANSACTION 1B: CHECKOUT WITH ROLLBACK DEMONSTRATION
-- ############################################################################
-- This demonstrates what happens when a transaction is rolled back.
-- Scenario: Start a checkout but cancel it before committing.
-- ############################################################################

SELECT 'TRANSACTION 1B: CHECKOUT WITH ROLLBACK' AS operation;
SELECT '--- Before Transaction ---' AS status;

SELECT id, title, copies_available 
FROM book 
WHERE id = 2;  -- Pride and Prejudice

START TRANSACTION;

-- Attempt to checkout a book
INSERT INTO loan (member_id, book_id, staff_id, loan_date, due_date, status)
VALUES (
    1,  -- John Smith
    2,  -- Pride and Prejudice
    4,  -- Patricia Thomas
    CURDATE(),
    DATE_ADD(CURDATE(), INTERVAL 14 DAY),
    'active'
);

UPDATE book 
SET copies_available = copies_available - 1 
WHERE id = 2;

SELECT '--- During Transaction (Before Rollback) ---' AS status;

SELECT id, title, copies_available 
FROM book 
WHERE id = 2;

-- Something went wrong! Roll back all changes
ROLLBACK;

SELECT '--- After Rollback ---' AS status;

-- Verify the rollback - copies should be unchanged
SELECT id, title, copies_available 
FROM book 
WHERE id = 2;

-- ############################################################################
-- TRANSACTION 2: BOOK RETURN WITH FINE PROCESSING
-- ############################################################################
-- Scenario: A member returns an overdue book. This requires:
--   1. Update the loan record (set return_date, change status)
--   2. Increment the book's copies_available count
--   3. Create a fine record for the overdue period
--
-- All three operations must complete together for data consistency.
-- ############################################################################

SELECT 'TRANSACTION 2: BOOK RETURN WITH FINE' AS operation;
SELECT '--- Before Transaction ---' AS status;

-- Find the overdue loan
SELECT l.id AS loan_id, 
       CONCAT(m.first_name, ' ', m.last_name) AS member_name,
       b.title,
       l.loan_date,
       l.due_date,
       l.status,
       b.copies_available
FROM loan l
JOIN member m ON l.member_id = m.id
JOIN book b ON l.book_id = b.id
WHERE l.id = 6;  -- Emily's overdue loan of "It"

START TRANSACTION;

-- Configuration
SET @loan_id = 6;
SET @book_id = 8;  -- "It" by Stephen King
SET @fine_per_day = 0.25;

-- Calculate days overdue (loan was due 2024-09-15, assuming return today)
SET @days_overdue = DATEDIFF(CURDATE(), '2024-09-15');
SET @fine_amount = @days_overdue * @fine_per_day;

-- Step 1: Update the loan record to 'returned'
UPDATE loan
SET 
    return_date = CURDATE(),
    status = 'returned'
WHERE id = @loan_id;

-- Step 2: Increment the book's available copies
UPDATE book
SET copies_available = copies_available + 1
WHERE id = @book_id;

-- Step 3: Update the existing fine amount (fine record already exists for this loan)
-- First, check if fine exists
SET @existing_fine = (SELECT id FROM fine WHERE loan_id = @loan_id);

-- Update the fine with the calculated amount
UPDATE fine
SET amount = @fine_amount,
    issue_date = CURDATE()
WHERE loan_id = @loan_id;

-- Verify all changes before committing
SELECT '--- During Transaction (Before Commit) ---' AS status;

SELECT 'Loan Status:' AS info;
SELECT l.id, l.return_date, l.status
FROM loan l
WHERE l.id = @loan_id;

SELECT 'Book Inventory:' AS info;
SELECT id, title, copies_available
FROM book
WHERE id = @book_id;

SELECT 'Fine Created:' AS info;
SELECT f.id, f.loan_id, f.amount, f.issue_date, f.paid_status
FROM fine f
WHERE f.loan_id = @loan_id;

-- Commit all changes
COMMIT;

SELECT '--- After Commit ---' AS status;

-- Final verification
SELECT 
    l.id AS loan_id,
    CONCAT(m.first_name, ' ', m.last_name) AS member_name,
    b.title,
    l.loan_date,
    l.due_date,
    l.return_date,
    l.status AS loan_status,
    b.copies_available,
    f.amount AS fine_amount,
    f.paid_status AS fine_status
FROM loan l
JOIN member m ON l.member_id = m.id
JOIN book b ON l.book_id = b.id
LEFT JOIN fine f ON l.id = f.loan_id
WHERE l.id = @loan_id;

-- ############################################################################
-- TRANSACTION SUMMARY
-- ############################################################################
/*
| Transaction | Operations Performed                          | Purpose                        |
|-------------|----------------------------------------------|--------------------------------|
| 1 (Checkout)| INSERT loan + UPDATE book (decrement)        | Ensure loan and inventory sync |
| 1B (Rollback)| Demonstrates ROLLBACK on failed transaction | Show atomicity in action       |
| 2 (Return)  | UPDATE loan + UPDATE book + UPDATE fine      | Ensure return, inventory, fine sync |

Key Concepts Demonstrated:
- START TRANSACTION: Begins an atomic unit of work
- COMMIT: Makes all changes permanent
- ROLLBACK: Undoes all changes since START TRANSACTION
- Atomicity: Either all operations succeed or none do
- Consistency: Database constraints remain valid throughout
*/

-- ############################################################################
-- BONUS: Check Final State of All Tables
-- ############################################################################

SELECT '=== FINAL STATE CHECK ===' AS report;

SELECT 'Active Loans:' AS info;
SELECT l.id, CONCAT(m.first_name, ' ', m.last_name) AS member, 
       b.title, l.status
FROM loan l
JOIN member m ON l.member_id = m.id
JOIN book b ON l.book_id = b.id
WHERE l.status = 'active';

SELECT 'Unpaid Fines:' AS info;
SELECT f.id, CONCAT(m.first_name, ' ', m.last_name) AS member,
       b.title, f.amount, f.paid_status
FROM fine f
JOIN loan l ON f.loan_id = l.id
JOIN member m ON l.member_id = m.id
JOIN book b ON l.book_id = b.id
WHERE f.paid_status = 'unpaid';

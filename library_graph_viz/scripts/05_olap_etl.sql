-- ============================================================================
-- Library Management System - ETL Scripts (OLTP to OLAP)
-- CWEB 2125 Database Systems: Programming & Admin
-- Week 4 of 4: OLAP Database Implementation
-- Date: 2025-11-26
-- ============================================================================

-- ============================================================================
-- ETL OVERVIEW
-- ============================================================================
-- ETL = Extract, Transform, Load
--
-- Source: library (OLTP database)
-- Target: library_olap (OLAP database)
--
-- Order of operations:
--   1. Populate dim_date (generated, not from OLTP)
--   2. Populate dim_member
--   3. Populate dim_category
--   4. Populate dim_staff
--   5. Populate dim_book (with denormalized authors)
--   6. Populate bridge_book_category (with weight factors)
--   7. Populate fact_loan
-- ============================================================================

-- ============================================================================
-- ETL 1: POPULATE dim_date
-- ============================================================================
-- Generate a date dimension covering 2020-2030
-- This is created independently, not extracted from OLTP
-- ============================================================================

USE library_olap;

-- Increase recursion limit for date generation (need ~4000 days)
SET SESSION cte_max_recursion_depth = 5000;

-- Populate dim_date using recursive CTE (no stored procedure needed)
-- Generate dates from 2020-01-01 to 2030-12-31
INSERT INTO dim_date (
    date_key,
    full_date,
    year,
    quarter,
    month_name,
    month_num,
    day,
    day_name,
    day_of_week,
    week_of_year,
    is_weekend
)
WITH RECURSIVE date_series AS (
    SELECT DATE('2020-01-01') AS gen_date
    UNION ALL
    SELECT DATE_ADD(gen_date, INTERVAL 1 DAY)
    FROM date_series
    WHERE gen_date < '2030-12-31'
)
SELECT
    YEAR(gen_date) * 10000 + MONTH(gen_date) * 100 + DAY(gen_date) AS date_key,
    gen_date AS full_date,
    YEAR(gen_date) AS year,
    QUARTER(gen_date) AS quarter,
    MONTHNAME(gen_date) AS month_name,
    MONTH(gen_date) AS month_num,
    DAY(gen_date) AS day,
    DAYNAME(gen_date) AS day_name,
    DAYOFWEEK(gen_date) AS day_of_week,
    WEEK(gen_date) AS week_of_year,
    CASE WHEN DAYOFWEEK(gen_date) IN (1, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_series;

-- Verify
SELECT 'dim_date populated' AS status, COUNT(*) AS record_count FROM dim_date;

-- ============================================================================
-- ETL 2: POPULATE dim_member
-- ============================================================================
-- Transform: Concatenate first_name + last_name into full_name
--            Extract year from membership_date
-- ============================================================================

INSERT INTO dim_member (
    source_member_id,
    first_name,
    last_name,
    full_name,
    email,
    phone,
    membership_date,
    membership_year,
    status
)
SELECT
    m.id AS source_member_id,
    m.first_name,
    m.last_name,
    CONCAT(m.first_name, ' ', m.last_name) AS full_name,
    m.email,
    m.phone,
    m.membership_date,
    YEAR(m.membership_date) AS membership_year,
    m.status
FROM library.member m;

-- Verify
SELECT 'dim_member populated' AS status, COUNT(*) AS record_count FROM dim_member;

-- ============================================================================
-- ETL 3: POPULATE dim_category
-- ============================================================================
-- Simple extraction with no transformation needed
-- ============================================================================

INSERT INTO dim_category (
    source_category_id,
    category_name,
    description
)
SELECT
    c.id AS source_category_id,
    c.name AS category_name,
    c.description
FROM library.category c;

-- Verify
SELECT 'dim_category populated' AS status, COUNT(*) AS record_count FROM dim_category;

-- ============================================================================
-- ETL 4: POPULATE dim_staff
-- ============================================================================
-- Transform: Concatenate names, extract hire year
-- ============================================================================

INSERT INTO dim_staff (
    source_staff_id,
    first_name,
    last_name,
    full_name,
    email,
    role,
    hire_date,
    hire_year
)
SELECT
    s.id AS source_staff_id,
    s.first_name,
    s.last_name,
    CONCAT(s.first_name, ' ', s.last_name) AS full_name,
    s.email,
    s.role,
    s.hire_date,
    YEAR(s.hire_date) AS hire_year
FROM library.staff s;

-- Verify
SELECT 'dim_staff populated' AS status, COUNT(*) AS record_count FROM dim_staff;

-- ============================================================================
-- ETL 5: POPULATE dim_book
-- ============================================================================
-- Transform: Denormalize authors into comma-separated string
--            Authors are joined from book_author and author tables
-- ============================================================================

INSERT INTO dim_book (
    source_book_id,
    isbn,
    title,
    authors,
    publication_year,
    total_copies
)
SELECT
    b.id AS source_book_id,
    b.isbn,
    b.title,
    -- Aggregate authors into comma-separated string
    (SELECT GROUP_CONCAT(CONCAT(a.first_name, ' ', a.last_name) ORDER BY a.last_name SEPARATOR ', ')
     FROM library.book_author ba
     JOIN library.author a ON ba.author_id = a.id
     WHERE ba.book_id = b.id
    ) AS authors,
    b.publication_year,
    b.copies_available AS total_copies
FROM library.book b;

-- Verify
SELECT 'dim_book populated' AS status, COUNT(*) AS record_count FROM dim_book;

-- ============================================================================
-- ETL 6: POPULATE bridge_book_category
-- ============================================================================
-- Transform: Calculate weight_factor as 1 / (number of categories per book)
-- This ensures each book's weights sum to 1.0
-- ============================================================================

INSERT INTO bridge_book_category (
    book_key,
    category_key,
    weight_factor
)
SELECT
    db.book_key,
    dc.category_key,
    -- Calculate weight: 1 / count of categories for this book
    1.0 / (
        SELECT COUNT(*)
        FROM library.book_category bc2
        WHERE bc2.book_id = bc.book_id
    ) AS weight_factor
FROM library.book_category bc
JOIN dim_book db ON bc.book_id = db.source_book_id
JOIN dim_category dc ON bc.category_id = dc.source_category_id;

-- Verify
SELECT 'bridge_book_category populated' AS status, COUNT(*) AS record_count FROM bridge_book_category;

-- Verify weight factors sum to 1.0 per book
SELECT
    db.title,
    SUM(bbc.weight_factor) AS total_weight,
    CASE
        WHEN ABS(SUM(bbc.weight_factor) - 1.0) < 0.001 THEN 'OK'
        ELSE 'ERROR'
    END AS validation
FROM bridge_book_category bbc
JOIN dim_book db ON bbc.book_key = db.book_key
GROUP BY db.book_key, db.title;

-- ============================================================================
-- ETL 7: POPULATE fact_loan
-- ============================================================================
-- Transform:
--   - Convert dates to date_key format (YYYYMMDD)
--   - Calculate loan_duration_days
--   - Calculate days_overdue
--   - Join fine amount from fine table
-- ============================================================================

INSERT INTO fact_loan (
    date_key,
    return_date_key,
    member_key,
    book_key,
    staff_key,
    loan_count,
    loan_duration_days,
    days_overdue,
    fine_amount
)
SELECT
    -- Convert loan_date to date_key format
    YEAR(l.loan_date) * 10000 + MONTH(l.loan_date) * 100 + DAY(l.loan_date) AS date_key,

    -- Convert return_date to date_key format (NULL if not returned)
    CASE
        WHEN l.return_date IS NOT NULL
        THEN YEAR(l.return_date) * 10000 + MONTH(l.return_date) * 100 + DAY(l.return_date)
        ELSE NULL
    END AS return_date_key,

    -- Dimension keys (lookup from dimension tables)
    dm.member_key,
    db.book_key,
    ds.staff_key,

    -- Measures
    1 AS loan_count,

    -- Calculate loan duration
    CASE
        WHEN l.return_date IS NOT NULL
        THEN DATEDIFF(l.return_date, l.loan_date)
        ELSE NULL
    END AS loan_duration_days,

    -- Calculate days overdue
    CASE
        WHEN l.return_date IS NOT NULL AND l.return_date > l.due_date
        THEN DATEDIFF(l.return_date, l.due_date)
        WHEN l.return_date IS NULL AND CURDATE() > l.due_date
        THEN DATEDIFF(CURDATE(), l.due_date)
        ELSE 0
    END AS days_overdue,

    -- Get fine amount (0 if no fine)
    COALESCE(f.amount, 0.00) AS fine_amount

FROM library.loan l
JOIN dim_member dm ON l.member_id = dm.source_member_id
JOIN dim_book db ON l.book_id = db.source_book_id
JOIN dim_staff ds ON l.staff_id = ds.source_staff_id
LEFT JOIN library.fine f ON l.id = f.loan_id;

-- Verify
SELECT 'fact_loan populated' AS status, COUNT(*) AS record_count FROM fact_loan;

-- ============================================================================
-- FINAL VERIFICATION
-- ============================================================================

SELECT '=== ETL COMPLETE ===' AS status;

SELECT 'Final Record Counts:' AS info;

SELECT 'dim_date' AS table_name, COUNT(*) AS records FROM dim_date
UNION ALL
SELECT 'dim_member', COUNT(*) FROM dim_member
UNION ALL
SELECT 'dim_category', COUNT(*) FROM dim_category
UNION ALL
SELECT 'dim_staff', COUNT(*) FROM dim_staff
UNION ALL
SELECT 'dim_book', COUNT(*) FROM dim_book
UNION ALL
SELECT 'bridge_book_category', COUNT(*) FROM bridge_book_category
UNION ALL
SELECT 'fact_loan', COUNT(*) FROM fact_loan;

-- Sample data verification
SELECT 'Sample fact_loan with dimensions:' AS info;

SELECT
    f.loan_key,
    d.full_date AS loan_date,
    m.full_name AS member,
    b.title AS book,
    s.full_name AS staff,
    f.loan_duration_days,
    f.days_overdue,
    f.fine_amount
FROM fact_loan f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_member m ON f.member_key = m.member_key
JOIN dim_book b ON f.book_key = b.book_key
JOIN dim_staff s ON f.staff_key = s.staff_key
LIMIT 5;

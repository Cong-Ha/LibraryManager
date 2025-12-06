-- ============================================================================
-- Library Management System - OLAP Table Creation
-- CWEB 2125 Database Systems: Programming & Admin
-- Week 4 of 4: OLAP Database Implementation
-- Date: 2025-11-26
-- ============================================================================

-- ============================================================================
-- SETUP
-- ============================================================================

CREATE DATABASE IF NOT EXISTS library_olap;
USE library_olap;

-- Disable foreign key checks temporarily for clean setup
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables if they exist
DROP TABLE IF EXISTS fact_loan;
DROP TABLE IF EXISTS bridge_book_category;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_member;
DROP TABLE IF EXISTS dim_book;
DROP TABLE IF EXISTS dim_staff;
DROP TABLE IF EXISTS dim_category;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- DIMENSION TABLE 1: dim_date
-- Purpose: Time-based analysis (when did loans occur?)
-- ============================================================================

CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,                    -- Format: YYYYMMDD
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    month_num INT NOT NULL,
    day INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    day_of_week INT NOT NULL,                    -- 1=Sunday, 7=Saturday
    week_of_year INT NOT NULL,
    is_weekend BOOLEAN NOT NULL,

    -- Indexes for common filters
    INDEX idx_dim_date_year (year),
    INDEX idx_dim_date_month (year, month_num),
    INDEX idx_dim_date_quarter (year, quarter)
) ENGINE=InnoDB;

-- ============================================================================
-- DIMENSION TABLE 2: dim_member
-- Purpose: Member analysis (who borrowed books?)
-- ============================================================================

CREATE TABLE dim_member (
    member_key INT AUTO_INCREMENT PRIMARY KEY,
    source_member_id INT NOT NULL,               -- Original OLTP id
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    membership_date DATE NOT NULL,
    membership_year INT NOT NULL,
    status VARCHAR(20) NOT NULL,

    -- Index for lookups from OLTP
    INDEX idx_dim_member_source (source_member_id)
) ENGINE=InnoDB;

-- ============================================================================
-- DIMENSION TABLE 3: dim_book
-- Purpose: Book analysis (what was borrowed?)
-- Note: Authors are denormalized (flattened) into this table
-- Categories are handled via bridge_book_category
-- ============================================================================

CREATE TABLE dim_book (
    book_key INT AUTO_INCREMENT PRIMARY KEY,
    source_book_id INT NOT NULL,                 -- Original OLTP id
    isbn VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    authors VARCHAR(500) NOT NULL,               -- Comma-separated author names
    publication_year INT,
    total_copies INT NOT NULL,

    -- Index for lookups from OLTP
    INDEX idx_dim_book_source (source_book_id)
) ENGINE=InnoDB;

-- ============================================================================
-- DIMENSION TABLE 4: dim_staff
-- Purpose: Staff performance analysis (who processed loans?)
-- ============================================================================

CREATE TABLE dim_staff (
    staff_key INT AUTO_INCREMENT PRIMARY KEY,
    source_staff_id INT NOT NULL,                -- Original OLTP id
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL,
    hire_date DATE NOT NULL,
    hire_year INT NOT NULL,

    -- Index for lookups from OLTP
    INDEX idx_dim_staff_source (source_staff_id)
) ENGINE=InnoDB;

-- ============================================================================
-- DIMENSION TABLE 5: dim_category
-- Purpose: Category/genre analysis
-- ============================================================================

CREATE TABLE dim_category (
    category_key INT AUTO_INCREMENT PRIMARY KEY,
    source_category_id INT NOT NULL,             -- Original OLTP id
    category_name VARCHAR(50) NOT NULL,
    description VARCHAR(255),

    -- Index for lookups from OLTP
    INDEX idx_dim_category_source (source_category_id)
) ENGINE=InnoDB;

-- ============================================================================
-- BRIDGE TABLE: bridge_book_category
-- Purpose: Resolves M:N relationship between books and categories
-- Uses weight factors for accurate counting
-- ============================================================================

CREATE TABLE bridge_book_category (
    book_key INT NOT NULL,
    category_key INT NOT NULL,
    weight_factor DECIMAL(5,4) NOT NULL,         -- Sum to 1.0 per book

    PRIMARY KEY (book_key, category_key),

    FOREIGN KEY (book_key) REFERENCES dim_book(book_key)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (category_key) REFERENCES dim_category(category_key)
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- Constraint to ensure valid weight
    CONSTRAINT chk_weight_factor CHECK (weight_factor > 0 AND weight_factor <= 1)
) ENGINE=InnoDB;

-- ============================================================================
-- FACT TABLE: fact_loan
-- Purpose: Central fact table capturing loan transaction measures
-- Grain: One row per loan transaction
-- ============================================================================

CREATE TABLE fact_loan (
    loan_key INT AUTO_INCREMENT PRIMARY KEY,

    -- Dimension foreign keys
    date_key INT NOT NULL,                       -- Loan date
    return_date_key INT,                         -- Return date (NULL if not returned)
    member_key INT NOT NULL,
    book_key INT NOT NULL,
    staff_key INT NOT NULL,

    -- Measures
    loan_count INT NOT NULL DEFAULT 1,           -- Always 1, for COUNT aggregations
    loan_duration_days INT,                      -- Actual days borrowed (NULL if not returned)
    days_overdue INT NOT NULL DEFAULT 0,         -- Days past due (0 if on time)
    fine_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    -- Foreign keys
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (return_date_key) REFERENCES dim_date(date_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (member_key) REFERENCES dim_member(member_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (book_key) REFERENCES dim_book(book_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (staff_key) REFERENCES dim_staff(staff_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Indexes for common query patterns
    INDEX idx_fact_loan_date (date_key),
    INDEX idx_fact_loan_member (member_key),
    INDEX idx_fact_loan_book (book_key),
    INDEX idx_fact_loan_staff (staff_key)
) ENGINE=InnoDB;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SHOW TABLES;

-- Show table structures
DESCRIBE dim_date;
DESCRIBE dim_member;
DESCRIBE dim_book;
DESCRIBE dim_staff;
DESCRIBE dim_category;
DESCRIBE bridge_book_category;
DESCRIBE fact_loan;

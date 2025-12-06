-- ============================================================================
-- Library Management System - Table Creation
-- CWEB 2125 Database Systems: Programming & Admin
-- Week 2 of 4: OLTP Database Implementation
-- Date: 2025-11-26
-- ============================================================================

-- ============================================================================
-- SETUP
-- ============================================================================

CREATE DATABASE IF NOT EXISTS library;
USE library;

-- Disable foreign key checks temporarily for clean setup
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS fine;
DROP TABLE IF EXISTS loan;
DROP TABLE IF EXISTS book_category;
DROP TABLE IF EXISTS book_author;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS author;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS member;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- TABLE 1: member
-- Purpose: Library patrons who can borrow books
-- ============================================================================

CREATE TABLE member (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    membership_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Constraints
    CONSTRAINT chk_member_status CHECK (status IN ('active', 'suspended', 'expired'))
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 2: author
-- Purpose: Writers of books
-- ============================================================================

CREATE TABLE author (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 3: category
-- Purpose: Genre/classification of books
-- ============================================================================

CREATE TABLE category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 4: staff
-- Purpose: Library employees who process transactions
-- ============================================================================

CREATE TABLE staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL,
    hire_date DATE NOT NULL,

    -- Constraints
    CONSTRAINT chk_staff_role CHECK (role IN ('librarian', 'assistant'))
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 5: book
-- Purpose: Books in the library collection with inventory count
-- ============================================================================

CREATE TABLE book (
    id INT AUTO_INCREMENT PRIMARY KEY,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    publication_year INT,
    copies_available INT NOT NULL DEFAULT 0,

    -- Constraints
    CONSTRAINT chk_copies_available CHECK (copies_available >= 0),
    CONSTRAINT chk_publication_year CHECK (publication_year >= 1000 AND publication_year <= 2100)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 6: book_author (Junction Table)
-- Purpose: Many-to-many relationship between books and authors
-- ============================================================================

CREATE TABLE book_author (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    author_id INT NOT NULL,

    -- Foreign Keys
    CONSTRAINT fk_book_author_book FOREIGN KEY (book_id)
        REFERENCES book(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_book_author_author FOREIGN KEY (author_id)
        REFERENCES author(id) ON DELETE CASCADE ON UPDATE CASCADE,

    -- Unique constraint to prevent duplicate book-author pairs
    CONSTRAINT uq_book_author UNIQUE (book_id, author_id)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 7: book_category (Junction Table)
-- Purpose: Many-to-many relationship between books and categories
-- ============================================================================

CREATE TABLE book_category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    category_id INT NOT NULL,

    -- Foreign Keys
    CONSTRAINT fk_book_category_book FOREIGN KEY (book_id)
        REFERENCES book(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_book_category_category FOREIGN KEY (category_id)
        REFERENCES category(id) ON DELETE CASCADE ON UPDATE CASCADE,

    -- Unique constraint to prevent duplicate book-category pairs
    CONSTRAINT uq_book_category UNIQUE (book_id, category_id)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 8: loan
-- Purpose: Checkout transactions tracking book borrowing
-- ============================================================================

CREATE TABLE loan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    book_id INT NOT NULL,
    staff_id INT NOT NULL,
    loan_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Foreign Keys
    CONSTRAINT fk_loan_member FOREIGN KEY (member_id)
        REFERENCES member(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_loan_book FOREIGN KEY (book_id)
        REFERENCES book(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_loan_staff FOREIGN KEY (staff_id)
        REFERENCES staff(id) ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Constraints
    CONSTRAINT chk_loan_status CHECK (status IN ('active', 'returned', 'overdue')),
    CONSTRAINT chk_loan_dates CHECK (due_date >= loan_date),
    CONSTRAINT chk_return_date CHECK (return_date IS NULL OR return_date >= loan_date)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 9: fine
-- Purpose: Penalties for overdue books
-- ============================================================================

CREATE TABLE fine (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL UNIQUE,
    amount DECIMAL(10, 2) NOT NULL,
    issue_date DATE NOT NULL,
    paid_status VARCHAR(20) NOT NULL DEFAULT 'unpaid',

    -- Foreign Keys
    CONSTRAINT fk_fine_loan FOREIGN KEY (loan_id)
        REFERENCES loan(id) ON DELETE CASCADE ON UPDATE CASCADE,

    -- Constraints
    CONSTRAINT chk_fine_amount CHECK (amount > 0),
    CONSTRAINT chk_fine_paid_status CHECK (paid_status IN ('paid', 'unpaid'))
) ENGINE=InnoDB;

-- ============================================================================
-- INDEXES (for performance optimization)
-- ============================================================================

-- Index on member email for quick lookups
CREATE INDEX idx_member_email ON member(email);

-- Index on member status for filtering
CREATE INDEX idx_member_status ON member(status);

-- Index on book title for searches
CREATE INDEX idx_book_title ON book(title);

-- Index on book ISBN for lookups
CREATE INDEX idx_book_isbn ON book(isbn);

-- Index on loan status for filtering active/overdue loans
CREATE INDEX idx_loan_status ON loan(status);

-- Index on loan dates for date range queries
CREATE INDEX idx_loan_dates ON loan(loan_date, due_date);

-- Index on fine paid_status for filtering unpaid fines
CREATE INDEX idx_fine_paid_status ON fine(paid_status);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Show all tables
SHOW TABLES;

-- Describe each table (optional)
-- DESCRIBE member;
-- DESCRIBE book;
-- DESCRIBE author;
-- DESCRIBE category;
-- DESCRIBE staff;
-- DESCRIBE loan;
-- DESCRIBE fine;
-- DESCRIBE book_author;
-- DESCRIBE book_category;

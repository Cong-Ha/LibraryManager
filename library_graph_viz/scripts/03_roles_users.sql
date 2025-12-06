-- ============================================================================
-- Library Management System - Roles, Users, and Permissions
-- CWEB 2125 Database Systems: Programming & Admin
-- Week 2 of 4: OLTP Database Implementation
-- Date: 2025-11-26
-- ============================================================================

-- ============================================================================
-- SECTION 1: CREATE DATABASE
-- ============================================================================

CREATE DATABASE IF NOT EXISTS library;
USE library;

-- ============================================================================
-- SECTION 2: CREATE ROLES
-- ============================================================================
-- Roles define permission sets that can be assigned to users
-- Three roles based on library operations:
--   - librarian: Full access to manage books, loans, members, fines
--   - assistant: Can process checkouts/returns, view books and members
--   - member: Can view books and their own loan history
-- ============================================================================

CREATE ROLE IF NOT EXISTS librarian;
CREATE ROLE IF NOT EXISTS assistant;
CREATE ROLE IF NOT EXISTS member;

-- ============================================================================
-- SECTION 3: GRANT PRIVILEGES TO ROLES
-- ============================================================================

-- Librarian: Full CRUD on all tables
GRANT SELECT, INSERT, UPDATE, DELETE ON library.member TO librarian;
GRANT SELECT, INSERT, UPDATE, DELETE ON library.book TO librarian;
GRANT SELECT, INSERT, UPDATE, DELETE ON library.author TO librarian;
GRANT SELECT, INSERT, UPDATE, DELETE ON library.category TO librarian;
GRANT SELECT, INSERT, UPDATE, DELETE ON library.staff TO librarian;
GRANT SELECT, INSERT, UPDATE, DELETE ON library.loan TO librarian;
GRANT SELECT, INSERT, UPDATE, DELETE ON library.fine TO librarian;
GRANT SELECT, INSERT, UPDATE, DELETE ON library.book_author TO librarian;
GRANT SELECT, INSERT, UPDATE, DELETE ON library.book_category TO librarian;

-- Assistant: Can process loans, view books/members, limited updates
GRANT SELECT ON library.member TO assistant;
GRANT SELECT ON library.book TO assistant;
GRANT SELECT ON library.author TO assistant;
GRANT SELECT ON library.category TO assistant;
GRANT SELECT, INSERT, UPDATE ON library.loan TO assistant;
GRANT SELECT ON library.fine TO assistant;
GRANT SELECT ON library.book_author TO assistant;
GRANT SELECT ON library.book_category TO assistant;
-- Assistant can update book inventory (copies_available)
GRANT UPDATE (copies_available) ON library.book TO assistant;

-- Member: Read-only access to books and categories, can view loans
GRANT SELECT ON library.book TO member;
GRANT SELECT ON library.author TO member;
GRANT SELECT ON library.category TO member;
GRANT SELECT ON library.book_author TO member;
GRANT SELECT ON library.book_category TO member;
GRANT SELECT ON library.loan TO member;
GRANT SELECT ON library.fine TO member;

-- ============================================================================
-- SECTION 4: CREATE USERS
-- ============================================================================
-- Creating sample users for each role
-- NOTE: In production, use strong passwords!
-- ============================================================================

-- Librarian user (full privileges)
CREATE USER IF NOT EXISTS 'lib_manager'@'localhost' IDENTIFIED BY 'Manager123!';

-- Assistant user (limited privileges)
CREATE USER IF NOT EXISTS 'lib_assistant'@'localhost' IDENTIFIED BY 'Assistant123!';

-- Member user (read-only for most tables)
CREATE USER IF NOT EXISTS 'lib_member'@'localhost' IDENTIFIED BY 'Member123!';

-- ============================================================================
-- SECTION 5: ASSIGN ROLES TO USERS
-- ============================================================================

GRANT librarian TO 'lib_manager'@'localhost';
GRANT assistant TO 'lib_assistant'@'localhost';
GRANT member TO 'lib_member'@'localhost';

-- ============================================================================
-- SECTION 6: SET DEFAULT ROLES
-- ============================================================================
-- Default roles are automatically activated when the user connects
-- ============================================================================

SET DEFAULT ROLE librarian TO 'lib_manager'@'localhost';
SET DEFAULT ROLE assistant TO 'lib_assistant'@'localhost';
SET DEFAULT ROLE member TO 'lib_member'@'localhost';

-- ============================================================================
-- SECTION 7: APPLY CHANGES
-- ============================================================================

FLUSH PRIVILEGES;

-- ============================================================================
-- VERIFICATION QUERIES (Optional - for testing)
-- ============================================================================

-- Show all roles
-- SELECT * FROM mysql.user WHERE host = 'localhost';

-- Show grants for a specific user
-- SHOW GRANTS FOR 'lib_manager'@'localhost';
-- SHOW GRANTS FOR 'lib_assistant'@'localhost';
-- SHOW GRANTS FOR 'lib_member'@'localhost';

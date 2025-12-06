-- ============================================================================
-- Library Management System - Sample Data
-- CWEB 2125 Database Systems: Programming & Admin
-- Week 2 of 4: OLTP Database Implementation
-- Date: 2025-11-26
-- ============================================================================

USE library;

-- ============================================================================
-- SAMPLE DATA: member (6 records)
-- ============================================================================

INSERT INTO member (first_name, last_name, email, phone, membership_date, status) VALUES
('John', 'Smith', 'john.smith@email.com', '555-0101', '2023-01-15', 'active'),
('Sarah', 'Johnson', 'sarah.johnson@email.com', '555-0102', '2023-03-20', 'active'),
('Michael', 'Williams', 'michael.williams@email.com', '555-0103', '2022-11-10', 'active'),
('Emily', 'Brown', 'emily.brown@email.com', '555-0104', '2023-06-05', 'suspended'),
('David', 'Jones', 'david.jones@email.com', '555-0105', '2021-09-01', 'expired'),
('Jessica', 'Davis', 'jessica.davis@email.com', '555-0106', '2024-01-10', 'active');

-- ============================================================================
-- SAMPLE DATA: author (8 records)
-- ============================================================================

INSERT INTO author (first_name, last_name) VALUES
('George', 'Orwell'),
('Jane', 'Austen'),
('Harper', 'Lee'),
('F. Scott', 'Fitzgerald'),
('Ernest', 'Hemingway'),
('Mark', 'Twain'),
('Agatha', 'Christie'),
('Stephen', 'King');

-- ============================================================================
-- SAMPLE DATA: category (6 records)
-- ============================================================================

INSERT INTO category (name, description) VALUES
('Fiction', 'Narrative literary works based on imagination'),
('Classic', 'Enduring works of literary excellence'),
('Mystery', 'Fiction dealing with puzzling crimes or situations'),
('Science Fiction', 'Fiction based on scientific discoveries or advanced technology'),
('Biography', 'Account of a persons life written by someone else'),
('Horror', 'Fiction intended to frighten or disturb readers');

-- ============================================================================
-- SAMPLE DATA: staff (5 records)
-- ============================================================================

INSERT INTO staff (first_name, last_name, email, role, hire_date) VALUES
('Robert', 'Anderson', 'robert.anderson@library.com', 'librarian', '2020-05-15'),
('Linda', 'Martinez', 'linda.martinez@library.com', 'librarian', '2019-08-20'),
('James', 'Taylor', 'james.taylor@library.com', 'assistant', '2022-01-10'),
('Patricia', 'Thomas', 'patricia.thomas@library.com', 'assistant', '2023-03-25'),
('William', 'Jackson', 'william.jackson@library.com', 'assistant', '2024-02-01');

-- ============================================================================
-- SAMPLE DATA: book (10 records)
-- ============================================================================

INSERT INTO book (isbn, title, publication_year, copies_available) VALUES
('978-0451524935', '1984', 1949, 5),
('978-0141439518', 'Pride and Prejudice', 1813, 3),
('978-0060935467', 'To Kill a Mockingbird', 1960, 4),
('978-0743273565', 'The Great Gatsby', 1925, 6),
('978-0684801223', 'The Old Man and the Sea', 1952, 2),
('978-0142437179', 'The Adventures of Tom Sawyer', 1876, 3),
('978-0062073488', 'Murder on the Orient Express', 1934, 4),
('978-1501142970', 'It', 1986, 2),
('978-0451526342', 'Animal Farm', 1945, 5),
('978-0684830490', 'A Farewell to Arms', 1929, 3);

-- ============================================================================
-- SAMPLE DATA: book_author (12 records - linking books to authors)
-- ============================================================================

INSERT INTO book_author (book_id, author_id) VALUES
(1, 1),   -- 1984 by George Orwell
(2, 2),   -- Pride and Prejudice by Jane Austen
(3, 3),   -- To Kill a Mockingbird by Harper Lee
(4, 4),   -- The Great Gatsby by F. Scott Fitzgerald
(5, 5),   -- The Old Man and the Sea by Ernest Hemingway
(6, 6),   -- The Adventures of Tom Sawyer by Mark Twain
(7, 7),   -- Murder on the Orient Express by Agatha Christie
(8, 8),   -- It by Stephen King
(9, 1),   -- Animal Farm by George Orwell
(10, 5);  -- A Farewell to Arms by Ernest Hemingway

-- ============================================================================
-- SAMPLE DATA: book_category (15 records - books can have multiple categories)
-- ============================================================================

INSERT INTO book_category (book_id, category_id) VALUES
(1, 1),   -- 1984: Fiction
(1, 2),   -- 1984: Classic
(1, 4),   -- 1984: Science Fiction
(2, 1),   -- Pride and Prejudice: Fiction
(2, 2),   -- Pride and Prejudice: Classic
(3, 1),   -- To Kill a Mockingbird: Fiction
(3, 2),   -- To Kill a Mockingbird: Classic
(4, 1),   -- The Great Gatsby: Fiction
(4, 2),   -- The Great Gatsby: Classic
(5, 1),   -- The Old Man and the Sea: Fiction
(5, 2),   -- The Old Man and the Sea: Classic
(6, 1),   -- Tom Sawyer: Fiction
(6, 2),   -- Tom Sawyer: Classic
(7, 1),   -- Murder on the Orient Express: Fiction
(7, 3),   -- Murder on the Orient Express: Mystery
(8, 1),   -- It: Fiction
(8, 6);   -- It: Horror

-- ============================================================================
-- SAMPLE DATA: loan (8 records)
-- ============================================================================

INSERT INTO loan (member_id, book_id, staff_id, loan_date, due_date, return_date, status) VALUES
(1, 1, 3, '2024-10-01', '2024-10-15', '2024-10-14', 'returned'),
(1, 3, 3, '2024-10-20', '2024-11-03', '2024-11-01', 'returned'),
(2, 2, 4, '2024-11-01', '2024-11-15', NULL, 'active'),
(2, 7, 3, '2024-11-05', '2024-11-19', NULL, 'active'),
(3, 4, 5, '2024-10-15', '2024-10-29', '2024-11-05', 'returned'),
(4, 8, 3, '2024-09-01', '2024-09-15', NULL, 'overdue'),
(6, 5, 4, '2024-11-10', '2024-11-24', NULL, 'active'),
(3, 1, 5, '2024-11-15', '2024-11-29', NULL, 'active');

-- ============================================================================
-- SAMPLE DATA: fine (5 records)
-- ============================================================================

INSERT INTO fine (loan_id, amount, issue_date, paid_status) VALUES
(5, 3.50, '2024-11-05', 'paid'),      -- Michael's late return of The Great Gatsby
(6, 15.00, '2024-09-16', 'unpaid'),   -- Emily's overdue book (still not returned)
(2, 1.50, '2024-11-03', 'paid'),      -- John's slightly late return
(4, 2.00, '2024-11-20', 'unpaid');    -- Sarah's fine for late return

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count records in each table
SELECT 'member' AS table_name, COUNT(*) AS record_count FROM member
UNION ALL
SELECT 'author', COUNT(*) FROM author
UNION ALL
SELECT 'category', COUNT(*) FROM category
UNION ALL
SELECT 'staff', COUNT(*) FROM staff
UNION ALL
SELECT 'book', COUNT(*) FROM book
UNION ALL
SELECT 'book_author', COUNT(*) FROM book_author
UNION ALL
SELECT 'book_category', COUNT(*) FROM book_category
UNION ALL
SELECT 'loan', COUNT(*) FROM loan
UNION ALL
SELECT 'fine', COUNT(*) FROM fine;

-- Sample query: Show books with their authors
SELECT
    b.title,
    CONCAT(a.first_name, ' ', a.last_name) AS author_name
FROM book b
JOIN book_author ba ON b.id = ba.book_id
JOIN author a ON ba.author_id = a.id
ORDER BY b.title;

-- Sample query: Show books with their categories
SELECT
    b.title,
    GROUP_CONCAT(c.name SEPARATOR ', ') AS categories
FROM book b
JOIN book_category bc ON b.id = bc.book_id
JOIN category c ON bc.category_id = c.id
GROUP BY b.id, b.title
ORDER BY b.title;

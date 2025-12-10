#!/usr/bin/env python3
"""
Library Management System - Large Sample Data Generator
Generates realistic sample data using Faker library.

Target volumes:
- 200 members
- 100 authors
- 500 books
- 15 categories
- 20 staff
- 2000 loans
- ~400 fines
"""

import random
from datetime import date, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)  # Reproducible results
random.seed(42)

# Configuration
NUM_MEMBERS = 200
NUM_AUTHORS = 100
NUM_BOOKS = 500
NUM_STAFF = 20
NUM_LOANS = 2000

# Categories (expanded list)
CATEGORIES = [
    ("Fiction", "Narrative literary works based on imagination"),
    ("Classic", "Enduring works of literary excellence"),
    ("Mystery", "Fiction dealing with puzzling crimes or situations"),
    ("Science Fiction", "Fiction based on scientific discoveries or advanced technology"),
    ("Fantasy", "Fiction featuring magical or supernatural elements"),
    ("Horror", "Fiction intended to frighten or disturb readers"),
    ("Romance", "Fiction focused on romantic relationships"),
    ("Thriller", "Fast-paced fiction with tension and suspense"),
    ("Biography", "Account of a person's life written by someone else"),
    ("History", "Non-fiction about historical events and periods"),
    ("Self-Help", "Books offering advice for personal improvement"),
    ("Philosophy", "Works exploring fundamental questions about existence"),
    ("Poetry", "Literary works written in verse"),
    ("Drama", "Works written for theatrical performance"),
    ("Children", "Books written for young readers"),
]

# Famous authors to include
FAMOUS_AUTHORS = [
    ("George", "Orwell"),
    ("Jane", "Austen"),
    ("Harper", "Lee"),
    ("F. Scott", "Fitzgerald"),
    ("Ernest", "Hemingway"),
    ("Mark", "Twain"),
    ("Agatha", "Christie"),
    ("Stephen", "King"),
    ("J.K.", "Rowling"),
    ("Charles", "Dickens"),
    ("William", "Shakespeare"),
    ("Leo", "Tolstoy"),
    ("Oscar", "Wilde"),
    ("Virginia", "Woolf"),
    ("Gabriel", "Garcia Marquez"),
    ("Toni", "Morrison"),
    ("Franz", "Kafka"),
    ("James", "Joyce"),
    ("Homer", ""),
    ("Edgar Allan", "Poe"),
]

# Sample book titles (will be combined with generated ones)
SAMPLE_BOOK_TITLES = [
    "1984", "Pride and Prejudice", "To Kill a Mockingbird", "The Great Gatsby",
    "The Old Man and the Sea", "The Adventures of Tom Sawyer", "Murder on the Orient Express",
    "It", "Animal Farm", "A Farewell to Arms", "Moby Dick", "War and Peace",
    "Crime and Punishment", "The Catcher in the Rye", "Lord of the Flies",
    "Brave New World", "The Hobbit", "Frankenstein", "Dracula", "Jane Eyre",
    "Wuthering Heights", "Great Expectations", "Oliver Twist", "The Odyssey",
    "The Iliad", "Don Quixote", "Les Miserables", "The Count of Monte Cristo",
    "Anna Karenina", "The Brothers Karamazov", "One Hundred Years of Solitude",
    "The Sound and the Fury", "Beloved", "The Color Purple", "Slaughterhouse-Five",
    "Cat's Cradle", "The Handmaid's Tale", "Dune", "Foundation", "Neuromancer",
    "Snow Crash", "The Martian", "Ready Player One", "Gone Girl", "The Girl with the Dragon Tattoo",
    "The Da Vinci Code", "Angels and Demons", "The Shining", "Carrie", "Misery",
]


def escape_sql(value):
    """Escape single quotes for SQL."""
    if value is None:
        return "NULL"
    return str(value).replace("'", "''")


def generate_isbn():
    """Generate a valid-looking ISBN-13."""
    prefix = random.choice(["978", "979"])
    group = str(random.randint(0, 9))
    publisher = str(random.randint(10000, 99999))
    title = str(random.randint(100, 999))
    return f"{prefix}-{group}{publisher}{title}"


def generate_phone():
    """Generate a US phone number."""
    return f"555-{random.randint(1000, 9999)}"


def generate_members():
    """Generate member records."""
    members = []
    used_emails = set()

    for i in range(NUM_MEMBERS):
        first_name = fake.first_name()
        last_name = fake.last_name()

        # Ensure unique email
        base_email = f"{first_name.lower()}.{last_name.lower()}@email.com"
        email = base_email
        counter = 1
        while email in used_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{counter}@email.com"
            counter += 1
        used_emails.add(email)

        # Membership date between 2020 and 2024
        membership_date = fake.date_between(start_date=date(2020, 1, 1), end_date=date(2024, 11, 30))

        # Status distribution: 70% active, 20% expired, 10% suspended
        rand = random.random()
        if rand < 0.70:
            status = "active"
        elif rand < 0.90:
            status = "expired"
        else:
            status = "suspended"

        members.append({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": generate_phone(),
            "membership_date": membership_date,
            "status": status,
        })

    return members


def generate_authors():
    """Generate author records."""
    authors = []

    # Add famous authors first
    for first, last in FAMOUS_AUTHORS:
        if last:  # Skip if no last name (like Homer)
            authors.append({"first_name": first, "last_name": last})
        else:
            authors.append({"first_name": first, "last_name": first})

    # Fill the rest with generated names
    while len(authors) < NUM_AUTHORS:
        authors.append({
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
        })

    return authors


def generate_books():
    """Generate book records."""
    books = []
    used_isbns = set()
    used_titles = set()

    # Add sample titles first
    for title in SAMPLE_BOOK_TITLES:
        if len(books) >= NUM_BOOKS:
            break

        isbn = generate_isbn()
        while isbn in used_isbns:
            isbn = generate_isbn()
        used_isbns.add(isbn)
        used_titles.add(title)

        books.append({
            "isbn": isbn,
            "title": title,
            "publication_year": random.randint(1800, 2024),
            "copies_available": random.randint(1, 10),
        })

    # Generate more books with fake titles
    title_patterns = [
        lambda: f"The {fake.word().title()} of {fake.word().title()}",
        lambda: f"A {fake.word().title()} in {fake.city()}",
        lambda: f"The {fake.word().title()}'s {fake.word().title()}",
        lambda: f"{fake.word().title()} and {fake.word().title()}",
        lambda: f"The Last {fake.word().title()}",
        lambda: f"Beyond the {fake.word().title()}",
        lambda: f"Secrets of the {fake.word().title()}",
        lambda: f"The {fake.color_name().title()} {fake.word().title()}",
        lambda: f"Journey to {fake.city()}",
        lambda: f"The {fake.last_name()} Legacy",
    ]

    while len(books) < NUM_BOOKS:
        title = random.choice(title_patterns)()
        if title in used_titles:
            continue
        used_titles.add(title)

        isbn = generate_isbn()
        while isbn in used_isbns:
            isbn = generate_isbn()
        used_isbns.add(isbn)

        books.append({
            "isbn": isbn,
            "title": title,
            "publication_year": random.randint(1900, 2024),
            "copies_available": random.randint(1, 10),
        })

    return books


def generate_staff():
    """Generate staff records."""
    staff = []
    used_emails = set()

    for i in range(NUM_STAFF):
        first_name = fake.first_name()
        last_name = fake.last_name()

        # Ensure unique email
        base_email = f"{first_name.lower()}.{last_name.lower()}@library.com"
        email = base_email
        counter = 1
        while email in used_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{counter}@library.com"
            counter += 1
        used_emails.add(email)

        # 30% librarians, 70% assistants
        role = "librarian" if random.random() < 0.30 else "assistant"

        # Hire date between 2018 and 2024
        hire_date = fake.date_between(start_date=date(2018, 1, 1), end_date=date(2024, 6, 30))

        staff.append({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role": role,
            "hire_date": hire_date,
        })

    return staff


def generate_book_authors(num_books, num_authors):
    """Generate book-author relationships."""
    book_authors = []

    for book_id in range(1, num_books + 1):
        # Each book has 1-3 authors (weighted toward 1)
        num_book_authors = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        author_ids = random.sample(range(1, num_authors + 1), num_book_authors)

        for author_id in author_ids:
            book_authors.append({
                "book_id": book_id,
                "author_id": author_id,
            })

    return book_authors


def generate_book_categories(num_books, num_categories):
    """Generate book-category relationships."""
    book_categories = []

    for book_id in range(1, num_books + 1):
        # Each book has 1-3 categories (weighted toward 1-2)
        num_book_categories = random.choices([1, 2, 3], weights=[0.4, 0.45, 0.15])[0]
        category_ids = random.sample(range(1, num_categories + 1), num_book_categories)

        for category_id in category_ids:
            book_categories.append({
                "book_id": book_id,
                "category_id": category_id,
            })

    return book_categories


def generate_loans(num_members, num_books, num_staff):
    """Generate loan records."""
    loans = []

    for i in range(NUM_LOANS):
        member_id = random.randint(1, num_members)
        book_id = random.randint(1, num_books)
        staff_id = random.randint(1, num_staff)

        # Loan date between 2022 and 2024 (weighted toward recent)
        days_ago = int(random.triangular(0, 900, 100))  # More recent loans
        loan_date = date.today() - timedelta(days=days_ago)
        if loan_date < date(2022, 1, 1):
            loan_date = date(2022, 1, 1) + timedelta(days=random.randint(0, 365))

        due_date = loan_date + timedelta(days=14)

        # 80% returned, 15% active, 5% overdue
        rand = random.random()
        if rand < 0.80:
            # Returned: return date is loan_date + 1 to 30 days
            return_days = random.randint(1, 30)
            return_date = loan_date + timedelta(days=return_days)
            if return_date > date.today():
                return_date = date.today()
            status = "returned"
        elif rand < 0.95:
            return_date = None
            if due_date < date.today():
                status = "overdue"
            else:
                status = "active"
        else:
            return_date = None
            status = "overdue"

        loans.append({
            "member_id": member_id,
            "book_id": book_id,
            "staff_id": staff_id,
            "loan_date": loan_date,
            "due_date": due_date,
            "return_date": return_date,
            "status": status,
        })

    return loans


def generate_fines(loans):
    """Generate fines for overdue loans."""
    fines = []

    for i, loan in enumerate(loans, 1):
        # Only create fines for returned loans that were late
        if loan["return_date"] and loan["return_date"] > loan["due_date"]:
            days_overdue = (loan["return_date"] - loan["due_date"]).days
            amount = min(days_overdue * 0.50, 25.00)  # $0.50/day, max $25

            # 60% paid, 40% unpaid
            paid_status = "paid" if random.random() < 0.60 else "unpaid"

            fines.append({
                "loan_id": i,
                "amount": round(amount, 2),
                "issue_date": loan["return_date"],
                "paid_status": paid_status,
            })
        # Also add fines for currently overdue loans
        elif loan["status"] == "overdue" and not loan["return_date"]:
            days_overdue = (date.today() - loan["due_date"]).days
            amount = min(days_overdue * 0.50, 25.00)

            fines.append({
                "loan_id": i,
                "amount": round(amount, 2),
                "issue_date": loan["due_date"] + timedelta(days=1),
                "paid_status": "unpaid",
            })

    return fines


def generate_sql():
    """Generate the complete SQL file."""
    print("Generating sample data...")

    members = generate_members()
    print(f"  Generated {len(members)} members")

    authors = generate_authors()
    print(f"  Generated {len(authors)} authors")

    books = generate_books()
    print(f"  Generated {len(books)} books")

    staff = generate_staff()
    print(f"  Generated {len(staff)} staff")

    book_authors = generate_book_authors(len(books), len(authors))
    print(f"  Generated {len(book_authors)} book-author relationships")

    book_categories = generate_book_categories(len(books), len(CATEGORIES))
    print(f"  Generated {len(book_categories)} book-category relationships")

    loans = generate_loans(len(members), len(books), len(staff))
    print(f"  Generated {len(loans)} loans")

    fines = generate_fines(loans)
    print(f"  Generated {len(fines)} fines")

    # Build SQL
    sql_lines = [
        "-- ============================================================================",
        "-- Library Management System - Large Sample Data",
        "-- Auto-generated with Faker",
        "-- ============================================================================",
        "",
        "USE library;",
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: member ({len(members)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO member (first_name, last_name, email, phone, membership_date, status) VALUES",
    ]

    member_values = []
    for m in members:
        member_values.append(
            f"('{escape_sql(m['first_name'])}', '{escape_sql(m['last_name'])}', "
            f"'{escape_sql(m['email'])}', '{m['phone']}', '{m['membership_date']}', '{m['status']}')"
        )
    sql_lines.append(",\n".join(member_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: author ({len(authors)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO author (first_name, last_name) VALUES",
    ])

    author_values = []
    for a in authors:
        author_values.append(f"('{escape_sql(a['first_name'])}', '{escape_sql(a['last_name'])}')")
    sql_lines.append(",\n".join(author_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: category ({len(CATEGORIES)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO category (name, description) VALUES",
    ])

    category_values = []
    for name, desc in CATEGORIES:
        category_values.append(f"('{escape_sql(name)}', '{escape_sql(desc)}')")
    sql_lines.append(",\n".join(category_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: staff ({len(staff)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO staff (first_name, last_name, email, role, hire_date) VALUES",
    ])

    staff_values = []
    for s in staff:
        staff_values.append(
            f"('{escape_sql(s['first_name'])}', '{escape_sql(s['last_name'])}', "
            f"'{escape_sql(s['email'])}', '{s['role']}', '{s['hire_date']}')"
        )
    sql_lines.append(",\n".join(staff_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: book ({len(books)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO book (isbn, title, publication_year, copies_available) VALUES",
    ])

    book_values = []
    for b in books:
        book_values.append(
            f"('{b['isbn']}', '{escape_sql(b['title'])}', {b['publication_year']}, {b['copies_available']})"
        )
    sql_lines.append(",\n".join(book_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: book_author ({len(book_authors)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO book_author (book_id, author_id) VALUES",
    ])

    ba_values = [f"({ba['book_id']}, {ba['author_id']})" for ba in book_authors]
    sql_lines.append(",\n".join(ba_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: book_category ({len(book_categories)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO book_category (book_id, category_id) VALUES",
    ])

    bc_values = [f"({bc['book_id']}, {bc['category_id']})" for bc in book_categories]
    sql_lines.append(",\n".join(bc_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: loan ({len(loans)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO loan (member_id, book_id, staff_id, loan_date, due_date, return_date, status) VALUES",
    ])

    loan_values = []
    for l in loans:
        return_date = f"'{l['return_date']}'" if l["return_date"] else "NULL"
        loan_values.append(
            f"({l['member_id']}, {l['book_id']}, {l['staff_id']}, "
            f"'{l['loan_date']}', '{l['due_date']}', {return_date}, '{l['status']}')"
        )
    sql_lines.append(",\n".join(loan_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        f"-- SAMPLE DATA: fine ({len(fines)} records)",
        "-- ============================================================================",
        "",
        "INSERT INTO fine (loan_id, amount, issue_date, paid_status) VALUES",
    ])

    fine_values = []
    for f in fines:
        fine_values.append(f"({f['loan_id']}, {f['amount']:.2f}, '{f['issue_date']}', '{f['paid_status']}')")
    sql_lines.append(",\n".join(fine_values) + ";")

    sql_lines.extend([
        "",
        "-- ============================================================================",
        "-- VERIFICATION QUERIES",
        "-- ============================================================================",
        "",
        "SELECT 'member' AS table_name, COUNT(*) AS record_count FROM member",
        "UNION ALL SELECT 'author', COUNT(*) FROM author",
        "UNION ALL SELECT 'category', COUNT(*) FROM category",
        "UNION ALL SELECT 'staff', COUNT(*) FROM staff",
        "UNION ALL SELECT 'book', COUNT(*) FROM book",
        "UNION ALL SELECT 'book_author', COUNT(*) FROM book_author",
        "UNION ALL SELECT 'book_category', COUNT(*) FROM book_category",
        "UNION ALL SELECT 'loan', COUNT(*) FROM loan",
        "UNION ALL SELECT 'fine', COUNT(*) FROM fine;",
        "",
    ])

    return "\n".join(sql_lines)


if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "02_insert_data_large.sql")

    sql_content = generate_sql()

    with open(output_file, "w") as f:
        f.write(sql_content)

    print(f"\nSQL file written to: {output_file}")
    print(f"File size: {len(sql_content):,} bytes")

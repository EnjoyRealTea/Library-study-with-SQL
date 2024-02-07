# ============================= Case Study 06 ================================
# ================== Library Management System with SQLite ===================
# ****************************** E. Thompson *********************************

"""
This version of the Library Management System case study uses SQLite3 to
manage a database containing the library's books, their members and records
of books borrowed and returned. To make it more realistic, the user can
opt to 'scan' in library cards and books when using the features.

Functions
---------
get_member:
    Obtains a valid member id from the user.
get_book:
    Obtains a valid ISBN from the user, and notes if the isbn is already used.
scan_all_books:
    Returns a random ISBN from all books in the library.
scan_from_shelf:
    Returns a random ISBN from all books in the library that are not on loan.
scan_from_user:
    Returns a random ISBN from books the member has on loan.
return_book:
    Records a book returning to the library.
borrow_book:
    Records a book being taken out of the library.
pay_fine:
    Allows a member's fines to be cleared.
reward:
    Records reward points, increases borrow limit when member has enough rewards.
fine:
    Records a fine and resets the member's rewards and borrow limit.
add_book:
    Adds a book to the library stock.
remove_book:
    Removes a book from the library stock.
add_member:
    Adds a new library member to the database.
user_id:
    Returns a random new or random existing member ID.
search_books:
    Allows the user to search for books by title or author.
print_book_record:
    Displays the record for a book.
print_all_books:
    Displays the records for all books.
print_loaned_books:
    Displays the records for books currently out on loan.
"""

import sqlite3
import random as rd


def get_member():
    """Function to get a valid member id from the user.

    Returns
    -------
    int
        A valid member ID that exists in the database.

    Notes
    -----
        Entering 0 'scans' a card (provides a random id)."""

    while True:
        try:
            member = int(input("Please enter the member id, "
                               "or 0 to scan their card: "))
            if member == 0:
                member = user_id(True)
                print(f"*Beep!* Card {member} accepted.")
                break
            else:
                cursor.execute('''SELECT * FROM users WHERE id = ?;'''
                               , (member,))
                id_list = cursor.fetchone()
                if id_list is None:
                    print("Error: ID not found.")
                else:
                    break
        except ValueError:
            print("Error: Invalid ID format.")
    return member


def get_book(scan_type, member_id=None):
    """Function to get a valid ISBN from the user.

    Parameters
    ----------
    scan_type :
        The scan function required (scan_all_books, scan_from_shelf or scan_from_user).
    member_id: int
        The id of the member, only required for scan_from_user.

    Returns
    -------
    book_isbn
        A valid ISBN.
    exists
        True if the ISBN is in the database.

    Notes
    -----
        Entering 0 'scans' a book (provides a random ISBN)."""

    while True:
        try:
            book_isbn = int(input("Please enter the book ISBN or "
                                  "0 to scan the book: "))
            if book_isbn > 0 and len(str(book_isbn)) == 13:
                break
            elif book_isbn == 0:
                book_isbn = scan_type(member_id)
                print(f"*Beep!* ISBN: {book_isbn}")
                break
            else:
                print("Error: ISBN must be 13 digits long")
        except ValueError:
            print("Error: ISBN must be a 13 digit number")

    cursor.execute('''
        SELECT EXISTS(
            SELECT 1 FROM books WHERE isbn = ?);''', (book_isbn,))
    exists = cursor.fetchone()[0]

    return book_isbn, exists


def scan_all_books(member_id=None):
    """Function to return a random ISBN from the library collection.

    Parameters
    ----------
    member_id
        Not required for this function.

    Returns
    -------
    int
        A valid ISBN from the database."""

    cursor.execute('''SELECT isbn FROM books;''')
    isbn_list = cursor.fetchall()
    isbn = rd.choice(isbn_list)[0]
    return isbn


def scan_from_shelf(member_id=None):
    """Function to return a random ISBN from the library collection,
    but only from copies that are not out on loan.

    Parameters
    ----------
    member_id
        Not required for this function.

    Returns
    -------
    int
        A valid ISBN from books held in the database that are not on loan."""

    cursor.execute('''
                    SELECT bk.isbn
                    FROM books AS bk
                    LEFT JOIN (
                        SELECT * FROM records 
                        WHERE returned = 'FALSE') AS rc
                    ON bk.isbn = rc.isbn
                    GROUP BY bk.isbn
                    HAVING  MAX(bk.stock) - COUNT(rc.returned) > 0;
                ''')
    isbn_list = cursor.fetchall()
    isbn = rd.choice(isbn_list)[0]
    return isbn


def scan_from_user(member_id):
    """Function to return a random ISBN from the books taken out by a user.

    Parameters
    ----------
    member_id: int
        The ID of the member.

    Returns
    -------
    int
        A valid ISBN from the books the member has on loan."""

    cursor.execute('''SELECT isbn FROM records
                        WHERE user_id = ? AND returned = 'FALSE';''',
                   (member_id,))
    isbn_list = cursor.fetchall()
    isbn = rd.choice(isbn_list)[0]
    return isbn


def return_book(ISBN, member_id):
    """Function to record a book returning to library.

    Parameters
    ----------
    ISBN: int
        The ISBN of the book being returned.
    member_id: int
        The id of the member who is attempting to return the book."""

    # Check user has checked the book out:
    cursor.execute('''SELECT * FROM records 
                WHERE user_id = ?
                AND isbn = ?
                AND returned = 'FALSE';''',
                   (member_id, ISBN))
    check_book = cursor.fetchall()
    # print(check_book)

    if not check_book:
        print(f"Error: Member {member_id} does not have this book on loan.")
        pass

    # Update the record
    cursor.execute('''
                UPDATE records
                SET date_checked_in = DATE(), returned = 'TRUE'
                WHERE isbn = ? AND user_id = ?;''',
                   (ISBN, member_id))
    db.commit()
    print("Book successfully returned.")


def borrow_book(ISBN, member_id):
    """Function to borrow a book from the library.
    Parameters
    ----------
    ISBN: int
        The ISBN of the book to be borrowed.
    member_id: int
        The id of the member wishing to borrow the book."""

    # Check that the book is in stock:
    cursor.execute('''
                SELECT bk.isbn
                FROM books AS bk
                LEFT JOIN (
                    SELECT * FROM records 
                    WHERE returned = 'FALSE') AS rc
                ON bk.isbn = rc.isbn
                WHERE bk.isbn = ?
                GROUP BY bk.isbn
                HAVING  MAX(bk.stock) - COUNT(rc.returned) > 0;
            ''', (ISBN,))
    check_stock = cursor.fetchone()

    # Check user has not already got a copy of the book out:
    cursor.execute('''
                SELECT * FROM records 
                WHERE isbn = ? AND  user_id = ? AND returned = 'FALSE';''',
                   (ISBN, member_id))
    check_user_copy = cursor.fetchone()

    # Check borrowing limit not reached and check user has no fines:
    cursor.execute('''
            SELECT u.name, MAX(fines), MAX(borrow_limit) - COUNT(rc.returned)
            FROM users as u
            LEFT JOIN (
                SELECT * FROM records
                WHERE returned = 'FALSE') AS rc
            ON u.id = rc.user_id
            where u.id = ?
            GROUP BY u.name;
        ''', (member_id,))
    check_user = cursor.fetchone()

    if not check_stock:
        # No copies left on the shelves
        print("Error: All copies are currently out on loan.")
    elif check_user_copy:
        # User has already taken the book out
        print(f"Error: {check_user[0]} has already got a copy on loan.")
    elif check_user[1] > 0:
        # User has fines
        print(f"Error: {check_user[0]} has outstanding "
              "fines to be paid before borrowing.")
    elif check_user[2] == 0:
        # User has reached borrowing limit
        print(f"Error: {check_user[0]} has reached their borrowing limit.")
    else:
        cursor.execute('''
                        INSERT INTO records(
                        isbn, user_id, date_checked_out, returned)
                        VALUES(?,?,DATE(),'FALSE');''',
                       (ISBN, member_id))
        db.commit()
        print(f"{check_user[0]} successfully checked out {ISBN}")


def pay_fine(member_id):
    """Function to record that a fine has been paid.

    Parameters
    ----------
    member_id: int
        The id of the member paying a fine."""

    # Check if a member has an outstanding fine:
    cursor.execute('''SELECT fines FROM users WHERE id = ?;''', (member_id,))
    fine_number = cursor.fetchone()[0]
    if fine_number == 0:
        print("No fines to pay.")
    else:
        fine_total = fine_number * 1.50
        print(f"Please pay £{fine_total:.2f}")
        print("*Beep!*")
        cursor.execute('''UPDATE users SET fines = 0 WHERE id = ?;''',
                       (member_id,))
        db.commit()
        print("Fines successfully paid.")


def reward(member_id):
    """Function to give a user a reward for returning books on time.

    Parameters
    ----------
    member_id: int
        The id of the member getting a reward point."""

    cursor.execute('''
            UPDATE users
            SET rewards = rewards + 1
            WHERE id = ?;''', (member_id,))
    db.commit()
    print("Reward point earned!")
    cursor.execute('''SELECT name, rewards, borrow_limit FROM users 
                    WHERE id = ?;''', (member_id,))
    reward_check = cursor.fetchone()
    if reward_check[1] > 9 and reward_check[2] < 6:
        print(f"Congratulations to {reward_check[0]}! "
              f"They have earned 10 rewards and can now borrow"
              f" {reward_check[2] + 1} books!")
        cursor.execute('''
                    UPDATE users
                    SET rewards = 0, borrow_limit = borrow_limit + 1
                    WHERE id = ?;''', (member_id,))
        db.commit()


def fine(member_id, fine_qty=1):
    """Function to give the user a fine for a late return / lost book.

    Parameters
    ----------
    member_id: int
        The id of the member being given a fine.
    fine_qty: int
        The number of fines. This can be used to charge a larger amount for a lost book."""

    cursor.execute('''
                UPDATE users
                SET fines = fines + ?, rewards = 0, borrow_limit = 3
                WHERE id = ?;''', (fine_qty, member_id))
    db.commit()
    print("Fine has been issued")


def add_book():
    """Function to add books to the library stock"""

    book = get_book(scan_all_books)
    if book[1] == 1:
        # Book already exists in library, user can add more copies:
        while True:
            try:
                add_stock = int(input("This book is already in stock. "
                                      "How many copies do you wish to "
                                      "add to the stock?: "))
                if add_stock >= 0:
                    cursor.execute('''
                            UPDATE books 
                            SET stock = stock + ?
                            WHERE isbn = ?;''', (add_stock, book[0]))
                    db.commit()
                    print("Stock updated.")
                    break
                else:
                    print("Error: Invalid number.")

            except ValueError:
                print("Error: Please enter a whole number.")

    # Book does not already exist:
    else:
        # Get book title from the user:
        book_title = input("Please enter the book title: ")

        # Get author name from the user:
        book_author = input("Please enter the book author: ")

        # Get stock from the user:
        while True:
            try:
                book_stock = int(input("Please enter the number of copies: "))
                if book_stock > 0:
                    break
                else:
                    print("Error: Invalid number of copies")
            except ValueError:
                print("Error: Book stock must be a whole number.")

        cursor.execute('''
                INSERT INTO books(isbn, title, author, stock)
                VALUES(?,?,?,?);
                ''', (book[0], book_title, book_author, book_stock))
        db.commit()
        print(f"{book_stock} copies of {book_title} added to database.")


def remove_book(ISBN):
    """Function to remove a book from stock, e.g. when lost.

    Parameters
    ----------
    ISBN: int
        The ISBN of the book being removed from stock."""

    # check stock is more than 0
    cursor.execute('''SELECT stock FROM books WHERE isbn = ?;''', (ISBN,))
    stock = cursor.fetchone()[0]
    if stock > 0:
        print("Book has stock")
        # need to know if the lost copy is on loan
        cursor.execute('''
                SELECT user_id from records 
                WHERE isbn = ? AND returned = 'FALSE';''', (ISBN,))
        users_list = cursor.fetchall()
        check_list = []
        if users_list:
            print("The following members currently have the book on loan:")
            for item in users_list:
                print(item[0])
                check_list.append(item[0])
            while True:
                try:
                    bad_member = int(
                        input("If a member lost / damaged the book, "
                              "please enter their number, "
                              "else enter 0: "))
                    if bad_member == 0:
                        if len(check_list) == stock:
                            print(
                                "Error: All stock is on loan, please enter a user")
                        else:
                            break
                    elif bad_member in check_list:
                        return_book(ISBN, bad_member)
                        fine(bad_member, 5)
                        break
                    else:
                        print("Error: Incorrect member number")
                except ValueError:
                    print("Error: Invalid member number")

        # reduce stock by 1
        cursor.execute(
            '''UPDATE books SET stock = stock - 1 WHERE isbn = ?;''',
            (ISBN,))
        db.commit()
        print("One copy successfully removed from the stock record.")
    else:
        print("Error: There are no copies of this book stocked.")


def add_member(user_name):
    """Function to add a new member to the database.

    Parameters
    ----------
    user_name: str
        The name of the member being added to the database."""

    new_id = user_id(False)
    cursor.execute('''
            INSERT INTO users(id, name, fines, rewards, borrow_limit)
            VALUES(?,?,0,0,3);
            ''', (new_id, user_name))
    db.commit()
    print(f"Membership number {new_id}, {user_name} added to database.")


def user_id(exists):
    """Function to return a random new id or a random existing id.

    Parameters
    ----------
    exists: bool
        True if an existing id is required.

    Returns
    -------
    int
        A new random id if exists=False, a random id from database if exists=True."""

    cursor.execute('''SELECT id FROM users;''')
    id_list = cursor.fetchall()
    _id_list = [i[0] for i in id_list]

    if exists:
        # Select from the existing ids:
        rand_id = rd.choice(_id_list)
    else:
        while True:
            # Select a random number, repeat if id is already in use:
            rand_id = rd.randint(1000, 9999)
            if rand_id not in _id_list:
                break
    return rand_id


def search_books(column_name, search_for):
    """Function to search for books in the library and display results.

    Parameters
    ----------
    column_name: str
        The column to be searched, either 'title' or 'author'.
    search_for: str
        The string the user wishes to look for."""

    search_for = '%' + search_for + '%'
    cursor.execute('''
            SELECT isbn, title, author
            FROM books
            WHERE (%s) LIKE ?;''' % (column_name), (search_for,))
    books_found = cursor.fetchall()
    if books_found:
        for row in books_found:
            print(f"ISBN: {row[0]}\tTitle: {row[1]}\tAuthor: {row[2]}")
    else:
        print("No books were found matching your search term.")


def print_book_record(ISBN):
    """Function to display a book record.

    Parameters
    ----------
    ISBN: int
        The ISBN to display records for."""

    cursor.execute('''
                SELECT bk.isbn, bk.title, bk.author, 
                MAX(stock) - COUNT(rc.returned)
                FROM books AS bk
                LEFT JOIN (
                    SELECT * FROM records 
                    WHERE returned = 'FALSE') AS rc
                ON bk.isbn = rc.isbn
                WHERE bk.isbn = ?
                GROUP BY bk.isbn''', (ISBN,))
    print("ISBN\t\t\tTitle\t\t\t\tAuthor\t\t\t\tCopies Available")
    for row in cursor:
        print(f"{row[0]}\t{row[1]}\t\t{row[2]}\t\t{row[3]}")


def print_all_books():
    """Function to display all books in library database."""
    cursor.execute('''
                SELECT bk.isbn, bk.title, bk.author, bk.stock,
                MAX(stock) - COUNT(rc.returned)
                FROM books AS bk
                LEFT JOIN (
                    SELECT * FROM records 
                    WHERE returned = 'FALSE') AS rc
                ON bk.isbn = rc.isbn
                GROUP BY bk.isbn''')
    print("ISBN\t\t\tStock\tOn Shelf\tTitle\t\t\t\t\tAuthor")
    for row in cursor:
        print(f"{row[0]}\t{row[3]}\t\t{row[4]}\t\t\t{row[1]}\t\t\t{row[2]}")


def print_loaned_books():
    """Function to display all books out on loan."""
    cursor.execute('''
                SELECT 
                 rc.isbn, 
                 bk.title, 
                 bk.author, 
                 rc.user_id,
                 u.name,
                 rc.date_checked_out
                FROM records AS rc
                INNER JOIN books AS bk
                ON rc.isbn = bk.isbn
                INNER JOIN users AS u
                ON rc.user_id = u.id
                WHERE rc.returned = 'FALSE'
                ORDER BY rc.isbn
                ''')
    print("ISBN\t\t\tTitle\t\t\t\tAuthor\t\t\tID\tName\tDate Borrowed")
    for row in cursor:
        print(
            f"{row[0]}\t{row[1]}\t\t{row[2]}\t\t\t{row[3]}\t{row[4]}\t{row[5]}")


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# Sets up database with 3 tables: books, users, records:
try:
    db = sqlite3.connect('library_db')
    cursor = db.cursor()

    # Check if books table exists, and create if not:
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS books(
            isbn INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT,
            stock INTEGER);
    ''')
    db.commit()

    # Check if users table exists, and create if not:
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            name TEXT,
            fines INTEGER,
            rewards INTEGER,
            borrow_limit INTEGER);
    ''')
    db.commit()

    # Check if records table exists, and create if not:
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS records(
            isbn INTEGER,
            user_id INTEGER,
            date_checked_out,
            date_checked_in,
            returned);
    ''')
    db.commit()
    # ---------------------------------------------------------------------
    print("Welcome to the Library Management System")

    # Provide the user with the list of options for the library system:
    while True:
        print("""
Please select from the following options:
    1. Search for a book
    2. Borrow a book
    3. Return a book
    4. Pay a fine
    5. Manage book stock
    6. Manage library members
    7. Exit
    """)
        user_choice = input("Please enter your choice (1-7): ")

        # -----------------------------------------------------------
        if user_choice == '7':
            # Exit system
            break
        # -----------------------------------------------------------
        elif user_choice == '1':
            # Book search feature
            while True:
                print("""
Please select the type of search:
    1. Search for an author
    2. Search for a book title
    3. Back
                """)
                user_sub_choice = input("Please enter your choice (1-3): ")
                if user_sub_choice == '3':
                    # Returns to main menu
                    break
                elif user_sub_choice == '1':
                    user_search_term = input("Please enter your search term: ")
                    search_books('author', user_search_term)

                elif user_sub_choice == '2':
                    user_search_term = input("Please enter your search term: ")
                    search_books('title', user_search_term)

                else:
                    print("Error: Please enter a number between 1 and 3.")
        # -----------------------------------------------------------
        elif user_choice == '2':
            # Borrow a book
            chosen_book = get_book(scan_from_shelf)
            # Check book is from the library:
            if not chosen_book[1]:
                print("Error: This is not a book from the library.")
            else:
                print_book_record(chosen_book[0])
                borrow_book(chosen_book[0], get_member())
        # -----------------------------------------------------------
        elif user_choice == '3':
            # Return a book
            memberid = get_member()
            # Check member has books on loan
            cursor.execute('''SELECT * FROM records
                            WHERE user_id = ?
                            AND returned = 'FALSE';''', (memberid,))
            check_loans = cursor.fetchone()
            if not check_loans:
                print(f"Error: Member {memberid} has no books on loan.")
            else:
                returned_book = get_book(scan_from_user, memberid)
                if returned_book[1]:
                    print_book_record(returned_book[0])
                    return_book(returned_book[0], memberid)
                    # Ask if the book was late, issue fine or reward:
                    while True:
                        on_time = input("Was the book returned on time? (Y/N)"
                                        ).upper()
                        if on_time == 'N':
                            fine(memberid)
                            break
                        elif on_time == 'Y':
                            reward(memberid)
                            break
                        else:
                            print("Error: Invalid input. Please enter Y or N.")
                else:
                    print("Error: This is not a book from the library.")
        # -----------------------------------------------------------
        elif user_choice == '4':
            # Pay a fine
            pay_fine(get_member())
        # -----------------------------------------------------------
        elif user_choice == '5':
            # Manage Book stock
            while True:
                print("""
Please select from the following options:
    1. View book stock
    2. Add book to stock
    3. Remove book
    4. View books on loan
    5. Back
                """)
                user_sub_choice = input("Please enter your choice (1-5): ")
                if user_sub_choice == '5':
                    # Returns to main menu
                    break

                elif user_sub_choice == '1':
                    # Display all book records
                    print_all_books()

                elif user_sub_choice == '2':
                    # Add a book to the stock
                    add_book()

                elif user_sub_choice == '3':
                    # Remove books from stock
                    book_to_remove = get_book(scan_all_books)
                    if book_to_remove[1]:
                        print_book_record(book_to_remove[0])
                        remove_book(book_to_remove[0])
                    else:
                        print("Error: This is not a book from the library.")

                elif user_sub_choice == '4':
                    # View books currently on loan
                    print_loaned_books()
                else:
                    print("Error: Please enter a number between 1 and 5.")

        # -----------------------------------------------------------
        elif user_choice == '6':
            # Manage Library Users
            while True:
                print("""
Please select from the following options:
    1. View library members
    2. Add a new member
    3. Back
                """)
                user_sub_choice = input("Please enter your choice (1-3): ")
                if user_sub_choice == '3':
                    # Returns to main menu
                    break

                elif user_sub_choice == '1':
                    # Display all member records
                    cursor.execute('''SELECT * FROM users;''')
                    print("ID\tUser Name\tFines\tRewards\tBorrow Limit")
                    for row in cursor:
                        print(
                            f"{row[0]}\t{row[1]}\t\t{row[2]}\t\t{row[3]}\t\t{row[4]}")

                elif user_sub_choice == '2':
                    # Add a member to the database
                    user = input("Please enter the new member's name: "
                                 ).capitalize()
                    add_member(user)

                else:
                    print("Error: Please enter a number between 1 and 3.")

        # -----------------------------------------------------------
        else:
            print("Error: Please enter a number between 1 and 7.")

except Exception as e:
    # Roll back any changes made before error
    db.rollback()
    raise e

finally:
    # Close the db connection
    db.close()

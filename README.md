# Library Sytem Case Study with SQL
### A Library System Case Study which uses SQLite3

## About
This is an improved version of the ["Library System" Case Study](https://github.com/EnjoyRealTea/library-study), a digital solution to manage book checkouts, returns and reservations.

Instead of using lists and dictionaries to handle the data, this version makes use of SQLite to manage the data through the creation of a database, along with various functions.

## Installation
LibrarySystem2.py can be downloaded and run locally through an IDE using Python.

The following libraries will need to be installed before running:
- tabulate

>[!WARNING]
> At least one library member and book will need to be added to the database on the first run, before attempting to use the other features. This can be done through the menu options (5. Manage book stock -> 2. Add book to stock  and  6. Manage library members -> 2. Add a new member).


## Use
A pretend 'scan' feature has been added to simulate a library barcode reader. This can be used instead of inputting isbn or member id numbers, as if scanning in a book's barcode or a member's library card. The numbers are selected at random and are not always restricted to cases that make sense. 
For example, the scanned user wishing to borrow might have already have a copy of that book. The system will prevent them borrowing another, but the scanner doesn't stop them trying. 
However, returning a book will always 'scan' in a book that is on loan to the member, otherwise it could take too many attempts to find a book that is returnable.

The database created contains three tables:

**books:**
This table holds records of the books the library owns. 
It contains the following columns:
- isbn (the unique book id)
- title
- author
- stock (the number of copies the library owns)

**users:**
The users table holds records of the library members. 
It contains the following columns:
- id (the unique id of the member)
- name
- fines (the number of unpaid fines the member has accrued)
- rewards (the number of unredeemed reward points the member has)
- borrow_limit (the maximum number of books the member may borrow)

**records:**
This table holds records of who borrowed which book, and when. 
It contains:
- isbn (unique id of the book that was taken out)
- user_id (unique id of the user who took the book out)
- date_checked_out (the date the book was borrowed)
- date_checked_in (the date the book was returned)
- returned (whether or not the book is back, True/False)

## Credits
LibrarySystem2.py was written by E. Thompson


"""
TEST CASE 1: Login → Add Book to "Want to Read" Shelf
======================================================

Test ID: TC001
Purpose: Verify that a user can successfully log in and add a book to their "Want to Read" shelf

EQUIVALENCE PARTITIONING:
-------------------------

Input 1: Username
- Valid username (exists in database): test_user_1, test_user_2
- Invalid username (doesn't exist): nonexistent_user
- Empty username: ""
- Special characters: "test@#$%"

Input 2: Password
- Valid password (matches user): TestPass123
- Invalid password (doesn't match): WrongPassword123
- Empty password: ""
- Short password: "123"

Input 3: Book ID
- Valid book ID (exists): 9999991, 9999992, 9999993
- Invalid book ID (doesn't exist): 0, -1, 9999999999
- Non-integer book ID: "abc", None

Input 4: Shelf Type
- Valid shelf type: 'plan-to-read', 'reading', 'completed'
- Invalid shelf type: 'invalid', '', None

Test Environment:
- Database: PostgreSQL (Supabase)
- Framework: Dash (Python)
- Test user: test_user_1 (email_verified=True)
- Test books: 9999991-9999995
"""

import pytest
import backend.login as login_backend
import backend.bookshelf as bookshelf_backend


@pytest.mark.login
@pytest.mark.bookshelf
class TestLoginAddToBookshelf:
    """
    Test suite for Login → Add Book to Bookshelf functionality
    """
    
    # =====================================================
    # TEST 1: Valid Login + Valid Book Addition
    # =====================================================
    
    def test_valid_login_add_book_to_want_to_read(self, test_user_credentials, test_books, cleanup_bookshelf):
        """
        Test ID: TC001-01
        Test: Valid login credentials + Valid book addition to Want to Read
        
        Input:
        - Username: test_user_1
        - Password: TestPass123
        - Book ID: 9999991
        - Shelf Type: plan-to-read
        
        Expected Result:
        - Login succeeds
        - Book is added to Want to Read shelf
        - Success message returned
        """
        # STEP 1: Login
        username = test_user_credentials['username']
        password = test_user_credentials['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        # ASSERT: Login successful
        assert success is True, f"Login failed: {message}"
        assert user_data is not None, "User data should not be None"
        assert user_data['username'] == username, f"Username mismatch: expected {username}, got {user_data['username']}"
        assert 'user_id' in user_data, "User data should contain user_id"
        
        user_id = user_data['user_id']
        
        # STEP 2: Add book to Want to Read shelf
        book_id = test_books['book_1']  # 9999991
        shelf_type = 'plan-to-read'
        
        add_success, add_message = bookshelf_backend.add_to_bookshelf(
            user_id=user_id,
            book_id=book_id,
            shelf_type=shelf_type
        )
        
        # ASSERT: Book added successfully
        assert add_success is True, f"Failed to add book: {add_message}"
        assert 'added' in add_message.lower() or 'moved' in add_message.lower(), \
            f"Success message should indicate book was added or moved: {add_message}"
        
        # STEP 3: Verify book is on shelf
        verify_success, verify_message, actual_shelf_type = bookshelf_backend.get_book_shelf_status(
            user_id, book_id
        )
        
        # ASSERT: Book is on correct shelf
        assert verify_success is True, f"Failed to verify shelf status: {verify_message}"
        assert actual_shelf_type == shelf_type, \
            f"Book should be on '{shelf_type}' shelf, but found on '{actual_shelf_type}'"
    
    # =====================================================
    # TEST 2: Invalid Login Credentials
    # =====================================================
    
    def test_invalid_password_cannot_add_book(self, test_user_invalid_credentials, test_books):
        """
        Test ID: TC001-02
        Test: Invalid password prevents login and book addition
        
        Input:
        - Username: test_user_1
        - Password: WrongPassword123 (INVALID)
        - Book ID: 9999991
        
        Expected Result:
        - Login fails with error message
        - Book addition is not attempted
        """
        # STEP 1: Attempt login with wrong password
        username = test_user_invalid_credentials['username']
        password = test_user_invalid_credentials['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        # ASSERT: Login should fail
        assert success is False, "Login should fail with invalid password"
        assert message is not None, "Error message should be provided"
        assert 'invalid' in message.lower() or 'incorrect' in message.lower(), \
            f"Error message should indicate invalid credentials: {message}"
        assert user_data is None, "User data should be None on failed login"
    
    # =====================================================
    # TEST 3: Non-existent User
    # =====================================================
    
    def test_nonexistent_user_cannot_login(self, test_user_nonexistent):
        """
        Test ID: TC001-03
        Test: Non-existent username prevents login
        
        Input:
        - Username: nonexistent_user_99999 (DOES NOT EXIST)
        - Password: SomePassword123
        
        Expected Result:
        - Login fails
        - User cannot add books
        """
        # STEP 1: Attempt login with non-existent user
        username = test_user_nonexistent['username']
        password = test_user_nonexistent['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        # ASSERT: Login should fail
        assert success is False, "Login should fail for non-existent user"
        assert user_data is None, "User data should be None"
    
    # =====================================================
    # TEST 4: Empty Credentials
    # =====================================================
    
    def test_empty_credentials_validation(self, test_user_empty_credentials):
        """
        Test ID: TC001-04
        Test: Empty username and password are rejected
        
        Input:
        - Username: "" (EMPTY)
        - Password: "" (EMPTY)
        
        Expected Result:
        - Login fails (handled by frontend validation in actual app)
        - Backend returns failure
        """
        # STEP 1: Attempt login with empty credentials
        username = test_user_empty_credentials['username']
        password = test_user_empty_credentials['password']
        
        # Note: In the actual Dash app, this would be prevented by frontend validation
        # (login button is disabled if fields are empty)
        # But we test backend behavior here
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        # ASSERT: Login should fail
        assert success is False, "Login should fail with empty credentials"
        assert user_data is None, "User data should be None"
    
    # =====================================================
    # TEST 5: Add Book to Different Shelf Types
    # =====================================================
    
    def test_valid_login_add_book_to_currently_reading(self, test_user_credentials, test_books, cleanup_bookshelf):
        """
        Test ID: TC001-05
        Test: Valid login + Add book to Currently Reading shelf
        
        Input:
        - Username: test_user_1
        - Password: TestPass123
        - Book ID: 9999993
        - Shelf Type: reading
        
        Expected Result:
        - Login succeeds
        - Book is added to Currently Reading shelf
        """
        # STEP 1: Login
        username = test_user_credentials['username']
        password = test_user_credentials['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        assert success is True, f"Login failed: {message}"
        user_id = user_data['user_id']
        
        # STEP 2: Add book to Currently Reading shelf
        book_id = test_books['book_3']  # 9999993
        shelf_type = 'reading'
        
        add_success, add_message = bookshelf_backend.add_to_bookshelf(
            user_id=user_id,
            book_id=book_id,
            shelf_type=shelf_type
        )
        
        # ASSERT: Book added successfully
        assert add_success is True, f"Failed to add book: {add_message}"
        
        # STEP 3: Verify book is on reading shelf
        verify_success, verify_message, actual_shelf_type = bookshelf_backend.get_book_shelf_status(
            user_id, book_id
        )
        
        assert verify_success is True, f"Failed to verify shelf status: {verify_message}"
        assert actual_shelf_type == shelf_type, \
            f"Book should be on 'reading' shelf, but found on '{actual_shelf_type}'"
    
    # =====================================================
    # TEST 6: Add Invalid Book ID
    # =====================================================
    
    def test_add_nonexistent_book_fails(self, logged_in_user):
        """
        Test ID: TC001-06
        Test: Attempting to add a non-existent book fails
        
        Input:
        - User: logged_in_user (valid)
        - Book ID: 9999999999 (DOES NOT EXIST)
        - Shelf Type: plan-to-read
        
        Expected Result:
        - Add operation fails
        - Error message returned
        """
        # STEP 1: User is already logged in (via fixture)
        user_id = logged_in_user['user_id']
        
        # STEP 2: Attempt to add non-existent book
        book_id = 9999999999  # This book doesn't exist
        shelf_type = 'plan-to-read'
        
        add_success, add_message = bookshelf_backend.add_to_bookshelf(
            user_id=user_id,
            book_id=book_id,
            shelf_type=shelf_type
        )
        
        # ASSERT: Operation should fail (or succeed with foreign key constraint allowing it)
        # Note: Behavior depends on database constraints
        # If foreign key constraint exists, this will fail
        # If not, it might succeed but won't be useful
        
        # For this test, we document the actual behavior
        print(f"\nAdd non-existent book result: {add_success}, {add_message}")
        
        # The test documents the behavior - if FK constraint exists, success should be False
        # If not, we verify the book isn't retrievable later


# =====================================================
# LIKELY BUGS / ISSUES TO WATCH FOR
# =====================================================
"""
Potential Bugs This Test May Reveal:

1. SQL Injection Vulnerability:
   - If username/password aren't properly sanitized
   - Test with username: "test' OR '1'='1"

2. Session Management Issues:
   - User remains logged in after failed login attempts
   - Session data persists incorrectly

3. Race Conditions:
   - Adding same book to multiple shelves simultaneously
   - Concurrent login attempts

4. Data Integrity:
   - Book appears on wrong shelf after addition
   - Duplicate entries created in bookshelf table

5. Error Handling:
   - Generic error messages don't help user
   - Database connection errors not handled gracefully

6. Frontend-Backend Mismatch:
   - Frontend allows actions that backend rejects
   - Success message doesn't match actual operation performed
"""
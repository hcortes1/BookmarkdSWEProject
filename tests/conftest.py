"""
pytest Configuration and Fixtures
Reading Tracker Application Testing

This file contains shared fixtures and utilities for all test files.
"""

import pytest
import os
import sys
from datetime import datetime
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import backend modules
import backend.login as login_backend
import backend.bookshelf as bookshelf_backend
import backend.reading_goals as reading_goals_backend
import backend.notifications as notifications_backend

# Load environment variables from .env.test or .env
if os.path.exists('.env.test'):
    load_dotenv('.env.test')
else:
    load_dotenv('.env')


# =====================================================
# DATABASE FIXTURES
# =====================================================

@pytest.fixture(scope="session")
def db_connection():
    """
    Create a database connection for the entire test session.
    This connection is shared across all tests.
    Note: Most backend functions use their own connections via get_conn(),
    so this fixture is mainly for direct database operations in tests.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            user=os.getenv("user"),
            password=os.getenv("password"),
            host=os.getenv("host"),
            port=os.getenv("port"),
            dbname=os.getenv("dbname")
        )
        print("\n✅ Database connection established for testing")
        yield connection
    except Error as e:
        pytest.fail(f"Failed to connect to test database: {e}")
    finally:
        if connection and not connection.closed:
            connection.close()
            print("\n✅ Database connection closed")


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """
    Provide a database cursor for each test function.
    Automatically rolls back changes after each test.
    """
    # Check if connection is closed and reconnect if needed
    if db_connection.closed:
        db_connection = psycopg2.connect(
            user=os.getenv("user"),
            password=os.getenv("password"),
            host=os.getenv("host"),
            port=os.getenv("port"),
            dbname=os.getenv("dbname")
        )
        print("\n⚠️ Database connection was closed, reconnected")
    
    cursor = db_connection.cursor()
    yield cursor
    
    # Rollback any changes made during the test
    try:
        if not db_connection.closed:
            db_connection.rollback()
    except Exception as e:
        print(f"\n⚠️ Warning during rollback: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass


# =====================================================
# TEST USER FIXTURES
# =====================================================

@pytest.fixture
def test_user_credentials():
    """
    Provide test user credentials.
    Password: TestPass123
    """
    return {
        'username': 'test_user_1',
        'password': 'TestPass123',
        'email': 'test_user_1@example.com'
    }


@pytest.fixture
def test_user_invalid_credentials():
    """
    Provide invalid test user credentials for negative testing.
    """
    return {
        'username': 'test_user_1',
        'password': 'WrongPassword123',
        'email': 'test_user_1@example.com'
    }


@pytest.fixture
def test_user_nonexistent():
    """
    Provide non-existent user credentials for negative testing.
    """
    return {
        'username': 'nonexistent_user_99999',
        'password': 'SomePassword123',
        'email': 'nonexistent@example.com'
    }


@pytest.fixture
def test_user_empty_credentials():
    """
    Provide empty credentials for validation testing.
    """
    return {
        'username': '',
        'password': '',
        'email': ''
    }


@pytest.fixture
def test_user_2_credentials():
    """
    Provide second test user credentials (unverified email).
    """
    return {
        'username': 'test_user_2',
        'password': 'TestPass123',
        'email': 'test_user_2@example.com'
    }


# =====================================================
# LOGGED IN USER FIXTURES
# =====================================================

@pytest.fixture
def logged_in_user(test_user_credentials):
    """
    Provide a logged-in user session.
    Returns user data and session information.
    """
    username = test_user_credentials['username']
    password = test_user_credentials['password']
    
    # Debug: Print what we're trying to log in with
    print(f"\n[DEBUG] Attempting login with:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    
    # Perform login
    success, message, user_data, remember_token = login_backend.login_user(
        username, password, remember_me=False
    )
    
    # Debug: Print result
    print(f"[DEBUG] Login result: success={success}, message={message}")
    if user_data:
        print(f"[DEBUG] User data: user_id={user_data.get('user_id')}, username={user_data.get('username')}")
    
    if not success:
        pytest.fail(f"Failed to log in test user: {message}")
    
    # Return comprehensive session data
    session_data = {
        "logged_in": True,
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "email": user_data["email"],
        "profile_image_url": user_data["profile_image_url"],
        "created_at": user_data["created_at"],
        "first_login": user_data["first_login"],
        "favorite_genres": user_data["favorite_genres"],
        "display_mode": user_data.get("display_mode", "light"),
        "email_verified": user_data.get("email_verified", False)
    }
    
    return session_data


# =====================================================
# TEST BOOK FIXTURES
# =====================================================

@pytest.fixture
def test_books():
    """
    Provide test book IDs for testing.
    """
    return {
        'book_1': 9999991,  # Test Book: The Great Adventure
        'book_2': 9999992,  # Test Book: Mystery Manor
        'book_3': 9999993,  # Test Book: Science Quest
        'book_4': 9999994,  # Test Book: Fantasy Realm
        'book_5': 9999995   # Test Book: Quick Read
    }


# =====================================================
# CLEANUP FIXTURES
# =====================================================

@pytest.fixture
def cleanup_bookshelf(logged_in_user, test_books):
    """
    Clean up bookshelf entries after test.
    """
    yield
    # Cleanup after test
    user_id = logged_in_user['user_id']
    for book_id in test_books.values():
        try:
            bookshelf_backend.remove_from_bookshelf(user_id, book_id)
        except:
            pass  # Ignore errors during cleanup


@pytest.fixture
def cleanup_reading_goals(logged_in_user):
    """
    Clean up reading goals created during test.
    """
    yield
    # Cleanup after test
    user_id = logged_in_user['user_id']
    try:
        from backend.db import get_conn
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM reading_goals WHERE user_id = %s AND goal_id > 1000000",
                    (user_id,)
                )
                conn.commit()
    except Exception as e:
        print(f"\n⚠️ Cleanup error: {e}")
        pass  # Ignore errors during cleanup


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def get_user_id_by_username(username):
    """
    Helper function to get user_id by username.
    """
    from backend.db import get_conn
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Error getting user_id: {e}")
        return None


def verify_book_on_shelf(user_id, book_id, expected_shelf_type):
    """
    Helper function to verify a book is on the correct shelf.
    """
    success, message, shelf_type = bookshelf_backend.get_book_shelf_status(user_id, book_id)
    if not success:
        return False
    return shelf_type == expected_shelf_type


def verify_reading_goal_exists(user_id, min_target=0):
    """
    Helper function to verify reading goal exists for user.
    """
    success, message, goals = reading_goals_backend.get_user_goals(user_id)
    if not success:
        return False
    
    # Check if any goal matches criteria
    for goal in goals:
        if goal.get('target_books', 0) >= min_target:
            return True
    return False


# =====================================================
# PYTEST CONFIGURATION
# =====================================================

def pytest_configure(config):
    """
    Custom pytest configuration.
    """
    print("\n" + "="*60)
    print("ðŸ§ª Reading Tracker Application - Test Suite")
    print("="*60)


def pytest_collection_finish(session):
    """
    Called after test collection is finished.
    """
    print(f"\nðŸ“‹ Collected {len(session.items)} test cases")


def pytest_runtest_logreport(report):
    """
    Called after each test phase (setup, call, teardown).
    """
    if report.when == 'call':
        if report.passed:
            print(f"âœ… PASSED: {report.nodeid}")
        elif report.failed:
            print(f"âŒ FAILED: {report.nodeid}")
        elif report.skipped:
            print(f"â­ï¸  SKIPPED: {report.nodeid}")
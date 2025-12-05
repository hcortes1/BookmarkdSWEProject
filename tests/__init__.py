"""
Tests Package for Reading Tracker Application
==============================================

This package contains pytest test cases for the Reading Tracker application.

Test Cases:
-----------
1. test_login_add_to_bookshelf.py - Login and add books to bookshelf
2. test_login_create_goal.py - Login and create reading goals
3. test_login_view_notifications.py - Login and view notifications
4. test_login_mark_finished.py - Login and mark books as finished with review
5. test_login_update_goal.py - Login and update reading goal progress

Running Tests:
-------------
# Run all tests
pytest

# Run specific test file
pytest tests/test_login_add_to_bookshelf.py

# Run tests with specific marker
pytest -m login

# Generate HTML report
pytest --html=tests/reports/test_report.html
"""

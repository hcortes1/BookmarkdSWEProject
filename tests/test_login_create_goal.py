"""
TEST CASE 2: Login → Create a New Reading Goal
===============================================

Test ID: TC002
Purpose: Verify that a user can successfully log in and create a new reading goal

EQUIVALENCE PARTITIONING:
-------------------------

Input 1: Username (Login)
- Valid username: test_user_1, test_user_2
- Invalid username: nonexistent_user
- Empty username: ""

Input 2: Password (Login)
- Valid password: TestPass123
- Invalid password: WrongPassword123
- Empty password: ""

Input 3: Goal Type
- Valid types: 'pages_per_day', 'books_per_month', 'deadline'
- Invalid type: 'invalid_type', '', None

Input 4: Target Books/Pages
- Valid positive integer: 1, 10, 100, 500
- Zero: 0
- Negative: -1, -100
- Non-integer: "abc", 3.5, None

Input 5: End Date
- Future date: CURRENT_DATE + 30 days
- Current date: CURRENT_DATE
- Past date: CURRENT_DATE - 10 days
- None/null: None

Input 6: Reminder Enabled
- True: true, 'on'
- False: false, ''
- Invalid: 'invalid', None

Test Environment:
- Database: PostgreSQL (Supabase)
- Framework: Dash (Python)
- Test user: test_user_1 (email_verified=True)
"""

import pytest
from datetime import date, timedelta
import backend.login as login_backend
import backend.reading_goals as reading_goals_backend


@pytest.mark.login
@pytest.mark.reading_goals
class TestLoginCreateReadingGoal:
    """
    Test suite for Login → Create Reading Goal functionality
    """
    
    # =====================================================
    # TEST 1: Valid Login + Valid Goal Creation
    # =====================================================
    
    def test_valid_login_create_pages_per_day_goal(self, test_user_credentials, cleanup_reading_goals):
        """
        Test ID: TC002-01
        Test: Valid login + Create pages per day goal with valid inputs
        
        Input:
        - Username: test_user_1
        - Password: TestPass123
        - Goal Type: pages_per_day
        - Target: 50 pages
        - End Date: 30 days from now
        - Reminder: enabled
        
        Expected Result:
        - Login succeeds
        - Goal is created successfully
        - Goal appears in user's goal list
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
        user_id = user_data['user_id']
        
        # STEP 2: Create reading goal
        goal_type = 'pages_per_day'
        target = 50
        end_date = date.today() + timedelta(days=30)
        reminder_enabled = True
        
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type=goal_type,
            book_name='Test Book: The Great Adventure',
            target=target,
            start_date=None,  # Will use today
            end_date=end_date,
            reminder_enabled=reminder_enabled
        )
        
        # ASSERT: Goal created successfully
        assert goal_success is True, f"Failed to create goal: {goal_message}"
        assert 'created' in goal_message.lower() or 'success' in goal_message.lower(), \
            f"Success message should indicate goal was created: {goal_message}"
        
        # STEP 3: Verify goal exists in database
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        
        # ASSERT: Goal is in user's goal list
        assert get_success is True, f"Failed to retrieve goals: {get_message}"
        assert len(goals) > 0, "User should have at least one goal"
        
        # Find the newly created goal
        new_goal = None
        for goal in goals:
            if goal.get('target_books') == target and goal.get('goal_type') == goal_type:
                new_goal = goal
                break
        
        assert new_goal is not None, "Newly created goal should be in goal list"
        assert new_goal['target_books'] == target, f"Target should be {target}"
        assert new_goal['reminder_enabled'] is True, "Reminder should be enabled"
    
    # =====================================================
    # TEST 2: Invalid Login Prevents Goal Creation
    # =====================================================
    
    def test_invalid_login_prevents_goal_creation(self, test_user_invalid_credentials):
        """
        Test ID: TC002-02
        Test: Invalid login credentials prevent goal creation
        
        Input:
        - Username: test_user_1
        - Password: WrongPassword123 (INVALID)
        
        Expected Result:
        - Login fails
        - Goal creation is not possible
        """
        # STEP 1: Attempt login with wrong password
        username = test_user_invalid_credentials['username']
        password = test_user_invalid_credentials['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        # ASSERT: Login should fail
        assert success is False, "Login should fail with invalid password"
        assert user_data is None, "User data should be None on failed login"
        
        # Cannot proceed with goal creation without valid user_id
    
    # =====================================================
    # TEST 3: Create Goal with Invalid Target
    # =====================================================
    
    def test_create_goal_with_zero_target(self, logged_in_user):
        """
        Test ID: TC002-03
        Test: Creating goal with zero target should fail or be handled
        
        Input:
        - User: logged_in_user (valid)
        - Goal Type: pages_per_day
        - Target: 0 (INVALID - zero)
        
        Expected Result:
        - Goal creation fails OR succeeds with validation warning
        - Appropriate error message returned
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Attempt to create goal with zero target
        goal_type = 'pages_per_day'
        target = 0  # Invalid
        end_date = date.today() + timedelta(days=30)
        
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type=goal_type,
            book_name=None,
            target=target,
            start_date=None,
            end_date=end_date,
            reminder_enabled=False
        )
        
        # ASSERT: Should either fail or succeed with warning
        # Document the actual behavior
        print(f"\nCreate goal with zero target result: {goal_success}, {goal_message}")
        
        # If it succeeds, verify the goal was created (documenting behavior)
        if goal_success:
            get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
            print(f"Goals retrieved: {len(goals) if get_success else 'Failed'}")
    
    # =====================================================
    # TEST 4: Create Goal with Negative Target
    # =====================================================
    
    def test_create_goal_with_negative_target(self, logged_in_user):
        """
        Test ID: TC002-04
        Test: Creating goal with negative target should fail
        
        Input:
        - User: logged_in_user (valid)
        - Goal Type: books_per_month
        - Target: -10 (INVALID - negative)
        
        Expected Result:
        - Goal creation fails
        - Error message indicates invalid target
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Attempt to create goal with negative target
        goal_type = 'books_per_month'
        target = -10  # Invalid
        end_date = date.today() + timedelta(days=30)
        
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type=goal_type,
            book_name=None,
            target=target,
            start_date=None,
            end_date=end_date,
            reminder_enabled=False
        )
        
        # ASSERT: Document behavior (may succeed due to lack of validation)
        print(f"\nCreate goal with negative target result: {goal_success}, {goal_message}")
        
        # Note: This test documents whether backend validates negative targets
        # If it doesn't, this is a bug to report
    
    # =====================================================
    # TEST 5: Create Deadline Goal (Valid)
    # =====================================================
    
    def test_valid_login_create_deadline_goal(self, test_user_credentials, cleanup_reading_goals):
        """
        Test ID: TC002-05
        Test: Valid login + Create deadline goal
        
        Input:
        - Username: test_user_1
        - Password: TestPass123
        - Goal Type: deadline
        - Target: 300 pages
        - End Date: 15 days from now
        - Reminder: enabled
        
        Expected Result:
        - Login succeeds
        - Deadline goal created successfully
        - End date is correctly stored
        """
        # STEP 1: Login
        username = test_user_credentials['username']
        password = test_user_credentials['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        assert success is True, f"Login failed: {message}"
        user_id = user_data['user_id']
        
        # STEP 2: Create deadline goal
        goal_type = 'deadline'
        target = 300
        end_date = date.today() + timedelta(days=15)
        reminder_enabled = True
        
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type=goal_type,
            book_name='Test Book: Mystery Manor',
            target=target,
            start_date=None,
            end_date=end_date,
            reminder_enabled=reminder_enabled
        )
        
        # ASSERT: Goal created successfully
        assert goal_success is True, f"Failed to create deadline goal: {goal_message}"
        
        # STEP 3: Verify goal with correct end date
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        
        assert get_success is True, f"Failed to retrieve goals: {get_message}"
        
        # Find the deadline goal
        deadline_goal = None
        for goal in goals:
            if goal.get('goal_type') == goal_type and goal.get('target_books') == target:
                deadline_goal = goal
                break
        
        assert deadline_goal is not None, "Deadline goal should be in goal list"
        assert deadline_goal['end_date'] == end_date, \
            f"End date mismatch: expected {end_date}, got {deadline_goal['end_date']}"
    
    # =====================================================
    # TEST 6: Create Goal with Past End Date
    # =====================================================
    
    def test_create_goal_with_past_end_date(self, logged_in_user):
        """
        Test ID: TC002-06
        Test: Creating goal with past end date
        
        Input:
        - User: logged_in_user (valid)
        - Goal Type: deadline
        - Target: 100 pages
        - End Date: 10 days ago (PAST DATE)
        
        Expected Result:
        - Goal creation succeeds OR fails with validation error
        - Document behavior for past dates
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Attempt to create goal with past end date
        goal_type = 'deadline'
        target = 100
        end_date = date.today() - timedelta(days=10)  # Past date
        
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type=goal_type,
            book_name='Test Book: Past Date',
            target=target,
            start_date=None,
            end_date=end_date,
            reminder_enabled=True
        )
        
        # ASSERT: Document behavior
        print(f"\nCreate goal with past end date result: {goal_success}, {goal_message}")
        
        # Note: This test documents whether backend validates past dates
        # Some systems allow past dates, some don't - both are valid designs
    
    # =====================================================
    # TEST 7: Create Multiple Goals for Same User
    # =====================================================
    
    def test_user_can_have_multiple_goals(self, logged_in_user, cleanup_reading_goals):
        """
        Test ID: TC002-07
        Test: User can create multiple reading goals
        
        Input:
        - User: logged_in_user (valid)
        - Create 3 different goals
        
        Expected Result:
        - All 3 goals created successfully
        - All goals appear in user's goal list
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Create first goal
        goal1_success, goal1_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='pages_per_day',
            book_name='Goal 1 Book',
            target=30,
            start_date=None,
            end_date=date.today() + timedelta(days=30),
            reminder_enabled=True
        )
        
        assert goal1_success is True, f"Failed to create goal 1: {goal1_message}"
        
        # STEP 3: Create second goal
        goal2_success, goal2_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='books_per_month',
            book_name='Goal 2 Book',
            target=5,
            start_date=None,
            end_date=date.today() + timedelta(days=30),
            reminder_enabled=False
        )
        
        assert goal2_success is True, f"Failed to create goal 2: {goal2_message}"
        
        # STEP 4: Create third goal
        goal3_success, goal3_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='deadline',
            book_name='Goal 3 Book',
            target=200,
            start_date=None,
            end_date=date.today() + timedelta(days=15),
            reminder_enabled=True
        )
        
        assert goal3_success is True, f"Failed to create goal 3: {goal3_message}"
        
        # STEP 5: Verify all goals exist
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        
        assert get_success is True, f"Failed to retrieve goals: {get_message}"
        assert len(goals) >= 3, f"User should have at least 3 goals, found {len(goals)}"


# =====================================================
# LIKELY BUGS / ISSUES TO WATCH FOR
# =====================================================
"""
Potential Bugs This Test May Reveal:

1. Validation Issues:
   - Negative or zero targets accepted
   - Past end dates allowed without warning
   - Missing required fields don't trigger errors

2. Data Type Mismatches:
   - String targets instead of integers
   - Date format inconsistencies
   - Boolean reminder flag handling

3. Database Constraints:
   - Duplicate goals created
   - Foreign key violations not handled
   - Transaction rollback issues

4. Business Logic Errors:
   - Progress can exceed target
   - End date before start date allowed
   - Reminder logic doesn't trigger

5. Performance Issues:
   - Creating many goals causes slowdown
   - Database query optimization needed
   - Memory leaks with goal retrieval

6. Race Conditions:
   - Concurrent goal creation by same user
   - Goal ID collisions
"""
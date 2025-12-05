"""
TEST CASE 5: Login → Update Reading Goal Progress
==================================================

Test ID: TC005
Purpose: Verify that a user can successfully log in and manually update their reading goal progress

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

Input 3: Goal ID
- Valid goal ID (user's own goal): Existing goal_id
- Invalid goal ID (doesn't exist): 9999999
- Invalid goal ID (belongs to another user): Another user's goal_id
- Non-integer: "abc", None

Input 4: New Progress Value
- Valid progress (less than target): 25 (target=100)
- Valid progress (equal to target): 100 (target=100)
- Valid progress (exceeds target): 150 (target=100)
- Zero progress: 0
- Negative progress: -10
- Non-integer: "abc", 50.5, None

Expected Behavior:
- Progress <= target: Goal still active
- Progress = target: Goal marked complete, feed entry created
- Progress > target: Goal marked complete (over-achieved)

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
class TestLoginUpdateReadingGoalProgress:
    """
    Test suite for Login → Update Reading Goal Progress functionality
    """
    
    # =====================================================
    # TEST 1: Valid Login + Update Progress (Partial Completion)
    # =====================================================
    
    def test_valid_login_update_progress_partial(self, test_user_credentials, cleanup_reading_goals):
        """
        Test ID: TC005-01
        Test: Valid login + Update goal progress to partial completion
        
        Input:
        - Username: test_user_1
        - Password: TestPass123
        - Create goal with target: 100 pages
        - Update progress to: 50 pages (50%)
        
        Expected Result:
        - Login succeeds
        - Goal progress updated to 50
        - Goal still marked as active (not complete)
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
        user_id = user_data['user_id']
        
        # STEP 2: Create a reading goal
        target = 100
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='pages_per_day',
            book_name='Test Progress Book',
            target=target,
            start_date=None,
            end_date=date.today() + timedelta(days=30),
            reminder_enabled=True
        )
        
        assert goal_success is True, f"Failed to create goal: {goal_message}"
        
        # STEP 3: Get the goal_id
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        assert get_success is True, f"Failed to retrieve goals: {get_message}"
        assert len(goals) > 0, "User should have at least one goal"
        
        # Find the newly created goal
        test_goal = None
        for goal in goals:
            if goal.get('target_books') == target and goal.get('book_name') == 'Test Progress Book':
                test_goal = goal
                break
        
        assert test_goal is not None, "Test goal should exist"
        goal_id = test_goal['goal_id']
        
        # STEP 4: Update progress to 50 (50% complete)
        new_progress = 50
        update_result = reading_goals_backend.update_progress_manual(goal_id, new_progress)
        
        # ASSERT: Progress updated successfully
        assert update_result.get('success') is True, \
            f"Failed to update progress: {update_result.get('message')}"
        assert 'updated' in update_result.get('message', '').lower(), \
            f"Message should indicate update: {update_result.get('message')}"
        
        # STEP 5: Verify progress was updated
        get_success, get_message, updated_goals = reading_goals_backend.get_user_goals(user_id)
        updated_goal = next((g for g in updated_goals if g['goal_id'] == goal_id), None)
        
        assert updated_goal is not None, "Goal should still exist"
        assert updated_goal['progress'] == new_progress, \
            f"Progress should be {new_progress}, got {updated_goal['progress']}"
        
        print(f"\n✓ Goal progress updated: {new_progress}/{target} ({new_progress/target*100}%)")
    
    # =====================================================
    # TEST 2: Invalid Login Prevents Progress Update
    # =====================================================
    
    def test_invalid_login_cannot_update_progress(self, test_user_invalid_credentials):
        """
        Test ID: TC005-02
        Test: Invalid login credentials prevent goal progress update
        
        Input:
        - Username: test_user_1
        - Password: WrongPassword123 (INVALID)
        
        Expected Result:
        - Login fails
        - Cannot update goal progress without valid user_id
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
        
        # Cannot update goals without valid user_id
    
    # =====================================================
    # TEST 3: Update Progress to Completion
    # =====================================================
    
    def test_update_progress_to_completion(self, logged_in_user, cleanup_reading_goals):
        """
        Test ID: TC005-03
        Test: Update goal progress to exactly meet target (100% completion)
        
        Input:
        - User: logged_in_user (valid)
        - Create goal with target: 200 pages
        - Update progress to: 200 pages (100%)
        
        Expected Result:
        - Progress updated to 200
        - Goal marked as complete
        - Success message indicates completion
        - Feed entry created (activity posted)
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Create a reading goal
        target = 200
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='deadline',
            book_name='Complete This Goal',
            target=target,
            start_date=None,
            end_date=date.today() + timedelta(days=10),
            reminder_enabled=False
        )
        
        assert goal_success is True, f"Failed to create goal: {goal_message}"
        
        # STEP 3: Get goal_id
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        test_goal = next((g for g in goals if g.get('target_books') == target 
                          and g.get('book_name') == 'Complete This Goal'), None)
        assert test_goal is not None, "Test goal should exist"
        goal_id = test_goal['goal_id']
        
        # STEP 4: Update progress to exactly meet target (completion)
        new_progress = target  # 200 = 200 (100%)
        update_result = reading_goals_backend.update_progress_manual(goal_id, new_progress)
        
        # ASSERT: Progress updated and goal marked complete
        assert update_result.get('success') is True, \
            f"Failed to update progress: {update_result.get('message')}"
        
        # Check if message indicates completion
        result_message = update_result.get('message', '').lower()
        assert 'completed' in result_message or 'complete' in result_message, \
            f"Message should indicate goal completion: {update_result.get('message')}"
        
        print(f"\n✓ Goal completed: {new_progress}/{target} (100%)")
    
    # =====================================================
    # TEST 4: Update Progress Beyond Target
    # =====================================================
    
    def test_update_progress_beyond_target(self, logged_in_user, cleanup_reading_goals):
        """
        Test ID: TC005-04
        Test: Update progress to exceed target (over-achievement)
        
        Input:
        - User: logged_in_user (valid)
        - Create goal with target: 100 pages
        - Update progress to: 150 pages (150% - exceeds target)
        
        Expected Result:
        - Progress updated to 150
        - Goal marked as complete (over-achieved)
        - System handles over-achievement gracefully
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Create a reading goal
        target = 100
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='books_per_month',
            book_name='Over-Achieve Goal',
            target=target,
            start_date=None,
            end_date=date.today() + timedelta(days=30),
            reminder_enabled=True
        )
        
        assert goal_success is True, f"Failed to create goal: {goal_message}"
        
        # STEP 3: Get goal_id
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        test_goal = next((g for g in goals if g.get('target_books') == target 
                          and g.get('book_name') == 'Over-Achieve Goal'), None)
        assert test_goal is not None, "Test goal should exist"
        goal_id = test_goal['goal_id']
        
        # STEP 4: Update progress beyond target
        new_progress = 150  # 150 > 100 (150%)
        update_result = reading_goals_backend.update_progress_manual(goal_id, new_progress)
        
        # ASSERT: Progress updated successfully (over-achievement)
        assert update_result.get('success') is True, \
            f"Failed to update progress: {update_result.get('message')}"
        
        # STEP 5: Verify progress stored correctly
        get_success, get_message, updated_goals = reading_goals_backend.get_user_goals(user_id)
        updated_goal = next((g for g in updated_goals if g['goal_id'] == goal_id), None)
        
        assert updated_goal is not None, "Goal should still exist"
        assert updated_goal['progress'] == new_progress, \
            f"Progress should be {new_progress}, got {updated_goal['progress']}"
        
        print(f"\n✓ Goal over-achieved: {new_progress}/{target} ({new_progress/target*100}%)")
    
    # =====================================================
    # TEST 5: Update Progress with Negative Value
    # =====================================================
    
    def test_update_progress_with_negative_value(self, logged_in_user, cleanup_reading_goals):
        """
        Test ID: TC005-05
        Test: Attempting to update progress with negative value
        
        Input:
        - User: logged_in_user (valid)
        - Create goal with target: 100
        - Update progress to: -10 (INVALID - negative)
        
        Expected Result:
        - Update fails OR succeeds with validation warning
        - Negative progress not allowed (business logic)
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Create a reading goal
        target = 100
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='pages_per_day',
            book_name='Negative Test Goal',
            target=target,
            start_date=None,
            end_date=date.today() + timedelta(days=20),
            reminder_enabled=False
        )
        
        assert goal_success is True, f"Failed to create goal: {goal_message}"
        
        # STEP 3: Get goal_id
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        test_goal = next((g for g in goals if g.get('target_books') == target 
                          and g.get('book_name') == 'Negative Test Goal'), None)
        assert test_goal is not None, "Test goal should exist"
        goal_id = test_goal['goal_id']
        
        # STEP 4: Attempt to update with negative value
        new_progress = -10  # Invalid
        update_result = reading_goals_backend.update_progress_manual(goal_id, new_progress)
        
        # ASSERT: Document behavior
        print(f"\nNegative progress result: {update_result.get('success')}, {update_result.get('message')}")
        
        # Note: This test documents whether backend validates negative progress
        # Expected: Should fail or reject negative values
    
    # =====================================================
    # TEST 6: Update Progress to Zero
    # =====================================================
    
    def test_update_progress_to_zero(self, logged_in_user, cleanup_reading_goals):
        """
        Test ID: TC005-06
        Test: Update progress to zero (reset progress)
        
        Input:
        - User: logged_in_user (valid)
        - Create goal and set initial progress: 50
        - Update progress to: 0 (reset)
        
        Expected Result:
        - Progress updated to 0
        - Goal remains active (not deleted)
        - User can reset their progress
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Create a reading goal
        target = 100
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='books_per_month',
            book_name='Zero Progress Goal',
            target=target,
            start_date=None,
            end_date=date.today() + timedelta(days=30),
            reminder_enabled=True
        )
        
        assert goal_success is True, f"Failed to create goal: {goal_message}"
        
        # STEP 3: Get goal_id and set initial progress
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        test_goal = next((g for g in goals if g.get('target_books') == target 
                          and g.get('book_name') == 'Zero Progress Goal'), None)
        assert test_goal is not None, "Test goal should exist"
        goal_id = test_goal['goal_id']
        
        # Set initial progress
        reading_goals_backend.update_progress_manual(goal_id, 50)
        
        # STEP 4: Reset progress to zero
        new_progress = 0
        update_result = reading_goals_backend.update_progress_manual(goal_id, new_progress)
        
        # ASSERT: Progress reset to zero
        assert update_result.get('success') is True, \
            f"Failed to reset progress: {update_result.get('message')}"
        
        # STEP 5: Verify progress is zero
        get_success, get_message, updated_goals = reading_goals_backend.get_user_goals(user_id)
        updated_goal = next((g for g in updated_goals if g['goal_id'] == goal_id), None)
        
        assert updated_goal is not None, "Goal should still exist"
        assert updated_goal['progress'] == 0, \
            f"Progress should be 0, got {updated_goal['progress']}"
        
        print(f"\n✓ Progress reset to zero: 0/{target}")
    
    # =====================================================
    # TEST 7: Update Non-Existent Goal
    # =====================================================
    
    def test_update_nonexistent_goal(self, logged_in_user):
        """
        Test ID: TC005-07
        Test: Attempting to update a non-existent goal
        
        Input:
        - User: logged_in_user (valid)
        - Goal ID: 9999999 (does not exist)
        - New Progress: 50
        
        Expected Result:
        - Update fails
        - Error message indicates goal not found
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Attempt to update non-existent goal
        fake_goal_id = 9999999
        new_progress = 50
        
        update_result = reading_goals_backend.update_progress_manual(fake_goal_id, new_progress)
        
        # ASSERT: Update should fail
        assert update_result.get('success') is False, \
            "Update should fail for non-existent goal"
        assert 'not found' in update_result.get('message', '').lower(), \
            f"Error message should indicate goal not found: {update_result.get('message')}"
        
        print(f"\n✓ Correctly rejected update for non-existent goal")
    
    # =====================================================
    # TEST 8: Multiple Progress Updates
    # =====================================================
    
    def test_multiple_progress_updates(self, logged_in_user, cleanup_reading_goals):
        """
        Test ID: TC005-08
        Test: User can update goal progress multiple times
        
        Input:
        - User: logged_in_user (valid)
        - Create goal with target: 500
        - Update 1: progress = 100
        - Update 2: progress = 250
        - Update 3: progress = 400
        
        Expected Result:
        - All updates succeed
        - Progress reflects latest value
        - Each update overwrites previous value
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Create a reading goal
        target = 500
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='deadline',
            book_name='Multiple Updates Goal',
            target=target,
            start_date=None,
            end_date=date.today() + timedelta(days=60),
            reminder_enabled=True
        )
        
        assert goal_success is True, f"Failed to create goal: {goal_message}"
        
        # STEP 3: Get goal_id
        get_success, get_message, goals = reading_goals_backend.get_user_goals(user_id)
        test_goal = next((g for g in goals if g.get('target_books') == target 
                          and g.get('book_name') == 'Multiple Updates Goal'), None)
        assert test_goal is not None, "Test goal should exist"
        goal_id = test_goal['goal_id']
        
        # STEP 4: Perform multiple updates
        updates = [100, 250, 400]
        
        for progress in updates:
            update_result = reading_goals_backend.update_progress_manual(goal_id, progress)
            assert update_result.get('success') is True, \
                f"Update to {progress} failed: {update_result.get('message')}"
            print(f"  Update {progress}/{target} successful")
        
        # STEP 5: Verify final progress
        get_success, get_message, final_goals = reading_goals_backend.get_user_goals(user_id)
        final_goal = next((g for g in final_goals if g['goal_id'] == goal_id), None)
        
        assert final_goal is not None, "Goal should still exist"
        assert final_goal['progress'] == updates[-1], \
            f"Final progress should be {updates[-1]}, got {final_goal['progress']}"
        
        print(f"\n✓ Multiple updates successful, final: {updates[-1]}/{target}")


# =====================================================
# LIKELY BUGS / ISSUES TO WATCH FOR
# =====================================================
"""
Potential Bugs This Test May Reveal:

1. Input Validation Issues:
   - Negative progress values accepted
   - Non-integer values cause errors
   - Progress > 2147483647 (int overflow)
   - NULL or None values not handled

2. Goal Completion Logic:
   - Progress = target doesn't trigger completion
   - Feed entry not created on completion
   - Completed goals still show reminders
   - Over-achievement not handled properly

3. Database Update Issues:
   - Progress update fails silently
   - Concurrent updates cause race conditions
   - Transaction rollback issues
   - Stale data returned after update

4. Permission/Security Issues:
   - User can update other users' goals
   - Goal_id validation insufficient
   - SQL injection in goal_id parameter

5. Business Logic Errors:
   - Progress can decrease below previous value (should this be allowed?)
   - Resetting to zero doesn't clear completion status
   - Reminder logic doesn't account for progress changes
   - Percentage calculations incorrect

6. Performance Issues:
   - Multiple rapid updates cause database locks
   - No rate limiting on update frequency
   - Goal list retrieval slow after many updates

7. Data Integrity:
   - Progress stored incorrectly (wrong data type)
   - Goal not found in database after update
   - Foreign key constraints violated
   - Orphaned feed entries if goal deleted

8. Edge Cases:
   - Very large progress values (>1000000)
   - Updating deleted goal succeeds
   - Progress update during concurrent goal deletion
   - Time zone issues with completion timestamps
"""
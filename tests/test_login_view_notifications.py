"""
TEST CASE 3: Login → View Reading Goal Notifications
=====================================================

Test ID: TC003
Purpose: Verify that a user can successfully log in and view their reading goal reminder notifications

EQUIVALENCE PARTITIONING:
-------------------------

Input 1: Username (Login)
- Valid username (verified email): test_user_1
- Valid username (unverified email): test_user_2
- Invalid username: nonexistent_user
- Empty username: ""

Input 2: Password (Login)
- Valid password: TestPass123
- Invalid password: WrongPassword123
- Empty password: ""

Input 3: Email Verified Status
- Verified: True (should NOT show email verification notification)
- Unverified: False (SHOULD show email verification notification)

Input 4: Reading Goals with Reminders
- Has goals with reminders enabled: Yes
- No goals with reminders: No
- Goals with reminders disabled: Mixed

Output Validation:
- Notification count: 0, 1, 2+
- Notification types: email_verification, reading_goal_reminder, friend_request, book_recommendation
- Notification structure: All required fields present

Test Environment:
- Database: PostgreSQL (Supabase)
- Framework: Dash (Python)
- Test users: test_user_1 (verified), test_user_2 (unverified)
"""

import pytest
import backend.login as login_backend
import backend.notifications as notifications_backend
import backend.reading_goals as reading_goals_backend
from datetime import date, timedelta


@pytest.mark.login
@pytest.mark.notifications
@pytest.mark.reading_goals
class TestLoginViewNotifications:
    """
    Test suite for Login → View Notifications functionality
    """
    
    # =====================================================
    # TEST 1: Valid Login + View Notifications (Verified User)
    # =====================================================
    
    def test_valid_login_view_notifications_verified_user(self, test_user_credentials):
        """
        Test ID: TC003-01
        Test: Valid login with verified user + View notifications
        
        Input:
        - Username: test_user_1 (email_verified=True)
        - Password: TestPass123
        
        Expected Result:
        - Login succeeds
        - Notifications are retrieved
        - NO email verification notification (email already verified)
        - Reading goal notifications present if goals exist
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
        assert user_data['email_verified'] is True, "Test user should have verified email"
        
        user_id = user_data['user_id']
        
        # STEP 2: Get notifications
        notifications_data = notifications_backend.get_user_notifications(
            str(user_id), 
            email_verified=user_data['email_verified']
        )
        
        # ASSERT: Notifications retrieved successfully
        assert 'count' in notifications_data, "Notifications should have count field"
        assert 'notifications' in notifications_data, "Notifications should have notifications list"
        assert isinstance(notifications_data['notifications'], list), "Notifications should be a list"
        
        # ASSERT: NO email verification notification (user is verified)
        email_verification_notifs = [n for n in notifications_data['notifications'] 
                                      if n.get('type') == 'email_verification']
        assert len(email_verification_notifs) == 0, \
            "Verified user should NOT have email verification notification"
        
        # Log notification types found
        notif_types = [n.get('type') for n in notifications_data['notifications']]
        print(f"\nNotifications for {username}: {notif_types}")
    
    # =====================================================
    # TEST 2: Valid Login + View Notifications (Unverified User)
    # =====================================================
    
    def test_valid_login_view_notifications_unverified_user(self, test_user_2_credentials):
        """
        Test ID: TC003-02
        Test: Valid login with unverified user + View notifications
        
        Input:
        - Username: test_user_2 (email_verified=False)
        - Password: TestPass123
        
        Expected Result:
        - Login succeeds (even though email not verified)
        - Notifications retrieved
        - Email verification notification present at top
        """
        # STEP 1: Login
        username = test_user_2_credentials['username']
        password = test_user_2_credentials['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        # ASSERT: Login successful (app allows login even if unverified)
        assert success is True, f"Login failed: {message}"
        assert user_data is not None, "User data should not be None"
        
        user_id = user_data['user_id']
        email_verified = user_data.get('email_verified', False)
        
        # STEP 2: Get notifications
        notifications_data = notifications_backend.get_user_notifications(
            str(user_id), 
            email_verified=email_verified
        )
        
        # ASSERT: Notifications retrieved
        assert 'count' in notifications_data, "Notifications should have count field"
        assert 'notifications' in notifications_data, "Notifications should have notifications list"
        
        # ASSERT: Email verification notification present if email not verified
        if not email_verified:
            email_verification_notifs = [n for n in notifications_data['notifications'] 
                                          if n.get('type') == 'email_verification']
            assert len(email_verification_notifs) >= 1, \
                "Unverified user SHOULD have email verification notification"
            
            # Check notification structure
            email_notif = email_verification_notifs[0]
            assert email_notif.get('id') == 'email_verification', "Email notif should have correct ID"
            assert email_notif.get('dismissible') is False, "Email notif should not be dismissible"
            assert 'verify' in email_notif.get('message', '').lower(), \
                "Email notif should mention verification"
    
    # =====================================================
    # TEST 3: Invalid Login Prevents Notification Access
    # =====================================================
    
    def test_invalid_login_cannot_view_notifications(self, test_user_invalid_credentials):
        """
        Test ID: TC003-03
        Test: Invalid login credentials prevent notification viewing
        
        Input:
        - Username: test_user_1
        - Password: WrongPassword123 (INVALID)
        
        Expected Result:
        - Login fails
        - Cannot retrieve notifications without valid user_id
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
        
        # Cannot get notifications without user_id
    
    # =====================================================
    # TEST 4: View Reading Goal Reminder Notifications
    # =====================================================
    
    def test_view_reading_goal_reminders(self, logged_in_user, cleanup_reading_goals):
        """
        Test ID: TC003-04
        Test: User can view reading goal reminder notifications
        
        Input:
        - User: logged_in_user (valid)
        - Create a reading goal with reminder enabled
        
        Expected Result:
        - Reading goal notification appears in notification list
        - Notification contains progress information
        - Notification contains days left information
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Create a reading goal with reminder
        goal_success, goal_message = reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='pages_per_day',
            book_name='Test Notification Goal',
            target=100,
            start_date=None,
            end_date=date.today() + timedelta(days=10),
            reminder_enabled=True
        )
        
        assert goal_success is True, f"Failed to create goal: {goal_message}"
        
        # STEP 3: Get notifications
        notifications_data = notifications_backend.get_user_notifications(
            str(user_id), 
            email_verified=logged_in_user.get('email_verified', True)
        )
        
        # ASSERT: Notifications retrieved
        assert 'notifications' in notifications_data, "Should have notifications field"
        
        # STEP 4: Find reading goal reminder notifications
        goal_notifs = [n for n in notifications_data['notifications'] 
                       if n.get('type') == 'reading_goal_reminder']
        
        # ASSERT: At least one reading goal reminder exists
        assert len(goal_notifs) >= 1, \
            f"Should have at least 1 reading goal notification, found {len(goal_notifs)}"
        
        # STEP 5: Validate notification structure
        goal_notif = goal_notifs[0]
        
        # Check required fields
        assert 'goal_id' in goal_notif, "Notification should have goal_id"
        assert 'progress' in goal_notif, "Notification should have progress"
        assert 'target' in goal_notif, "Notification should have target"
        assert 'percentage' in goal_notif, "Notification should have percentage"
        assert 'message' in goal_notif, "Notification should have message"
        
        # Check message format
        message = goal_notif['message']
        assert 'Reading goal' in message, "Message should mention 'Reading goal'"
        assert '%' in message or 'complete' in message.lower(), \
            "Message should show percentage or completion status"
        
        print(f"\nReading Goal Notification Message: {message}")
    
    # =====================================================
    # TEST 5: Empty Notifications List
    # =====================================================
    
    def test_user_with_no_notifications(self, logged_in_user):
        """
        Test ID: TC003-05
        Test: User with no goals/requests sees empty or minimal notifications
        
        Input:
        - User: logged_in_user (valid, verified, no active goals with reminders)
        
        Expected Result:
        - Notifications retrieved successfully
        - Count reflects actual notifications (may be 0 or minimal)
        - No errors occur with empty list
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        email_verified = logged_in_user.get('email_verified', True)
        
        # STEP 2: Get notifications
        notifications_data = notifications_backend.get_user_notifications(
            str(user_id), 
            email_verified=email_verified
        )
        
        # ASSERT: Notifications structure is valid even if empty
        assert 'count' in notifications_data, "Should have count field"
        assert 'notifications' in notifications_data, "Should have notifications field"
        assert isinstance(notifications_data['notifications'], list), "Notifications should be a list"
        assert notifications_data['count'] == len(notifications_data['notifications']), \
            "Count should match notifications list length"
        
        print(f"\nUser {user_id} has {notifications_data['count']} notification(s)")
    
    # =====================================================
    # TEST 6: Notification Count Accuracy
    # =====================================================
    
    def test_notification_count_matches_list_length(self, logged_in_user):
        """
        Test ID: TC003-06
        Test: Notification count field matches actual list length
        
        Input:
        - User: logged_in_user (valid)
        
        Expected Result:
        - 'count' field equals len(notifications list)
        - No discrepancy between count and actual notifications
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Get notifications
        notifications_data = notifications_backend.get_user_notifications(
            str(user_id), 
            email_verified=logged_in_user.get('email_verified', True)
        )
        
        # ASSERT: Count matches list length
        reported_count = notifications_data.get('count', 0)
        actual_count = len(notifications_data.get('notifications', []))
        
        assert reported_count == actual_count, \
            f"Count mismatch: reported {reported_count}, actual {actual_count}"
        
        print(f"\n✓ Count accuracy verified: {reported_count} notification(s)")
    
    # =====================================================
    # TEST 7: Multiple Notification Types
    # =====================================================
    
    def test_multiple_notification_types_display_correctly(self, logged_in_user, cleanup_reading_goals):
        """
        Test ID: TC003-07
        Test: Different notification types all display correctly
        
        Input:
        - User: logged_in_user (valid)
        - Create reading goal (creates reading_goal_reminder notification)
        
        Expected Result:
        - All notification types have required fields
        - Each type has correct structure
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        
        # STEP 2: Create a reading goal to generate notification
        reading_goals_backend.create_goal(
            user_id=user_id,
            goal_type='deadline',
            book_name='Multi-Type Test Goal',
            target=50,
            start_date=None,
            end_date=date.today() + timedelta(days=5),
            reminder_enabled=True
        )
        
        # STEP 3: Get notifications
        notifications_data = notifications_backend.get_user_notifications(
            str(user_id), 
            email_verified=logged_in_user.get('email_verified', True)
        )
        
        # STEP 4: Validate each notification type has required fields
        for notif in notifications_data['notifications']:
            # All notifications must have these fields
            assert 'type' in notif, "Every notification must have 'type'"
            assert 'id' in notif, "Every notification must have 'id'"
            assert 'message' in notif, "Every notification must have 'message'"
            
            notif_type = notif['type']
            print(f"\n✓ Validated notification type: {notif_type}")
            
            # Type-specific validation
            if notif_type == 'reading_goal_reminder':
                assert 'goal_id' in notif, "Goal reminder must have goal_id"
                assert 'progress' in notif, "Goal reminder must have progress"
                assert 'target' in notif, "Goal reminder must have target"
                assert 'percentage' in notif, "Goal reminder must have percentage"


# =====================================================
# LIKELY BUGS / ISSUES TO WATCH FOR
# =====================================================
"""
Potential Bugs This Test May Reveal:

1. Session Management Issues:
   - Notifications not refreshing after login
   - Stale notification data from previous session
   - User_id mismatch in notification retrieval

2. Email Verification Logic:
   - Verified users still see verification notification
   - Notification doesn't disappear after verification
   - Dismissible flag not respected

3. Reading Goal Reminder Issues:
   - Completed goals still showing reminders
   - Progress percentage calculated incorrectly
   - Days left calculation off by one
   - Reminders not showing when enabled

4. Notification Structure:
   - Missing required fields in notification objects
   - Inconsistent field names across notification types
   - Null/None values not handled properly

5. Count Discrepancies:
   - Count doesn't match actual notification list length
   - Count includes dismissed notifications
   - Duplicate notifications inflating count

6. Performance Issues:
   - Slow notification loading with many goals
   - Database query optimization needed
   - N+1 query problem with related data

7. Race Conditions:
   - Notifications retrieved before goals are created
   - Concurrent notification updates cause inconsistency
   - Caching issues with stale data

8. Data Integrity:
   - Notifications for deleted goals still appear
   - Orphaned notifications (user_id doesn't exist)
   - Foreign key constraint violations
"""
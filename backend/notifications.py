# backend/notifications.py
from typing import List, Dict, Any
import backend.friends as friends_backend
import backend.recommendations as recommendations_backend


def get_user_notifications(user_id: str, email_verified: bool = True) -> Dict[str, Any]:
    """
    Get all notifications for a user.
    Currently includes pending friend requests, book recommendations, email verification, and reading goal reminders.
    Returns a dict with notification count and details.
    """
    try:
        notifications = []

        # add email verification notification if not verified (always at top, cannot be dismissed)
        if not email_verified:
            notifications.append({
                'type': 'email_verification',
                'id': 'email_verification',
                'message': 'Please verify your email address to secure your account',
                'created_at': None,
                'dismissible': False  # cannot be dismissed
            })

        # Get pending friend requests
        pending_requests = friends_backend.get_pending_friend_requests(user_id)
        for request in pending_requests:
            notifications.append({
                'type': 'friend_request',
                'id': f"friend_request_{request['sender_id']}",
                'sender_id': request['sender_id'],
                'sender_username': request['username'],
                'sender_profile_image_url': request.get('profile_image_url'),
                'created_at': request['created_at'],
                'message': f"{request['username']} sent you a friend request"
            })

        # Get book recommendations
        book_recommendations = recommendations_backend.get_user_recommendations(int(user_id))
        for rec in book_recommendations:
            notifications.append({
                'type': 'book_recommendation',
                'id': f"book_recommendation_{rec['rec_id']}",
                'rec_id': rec['rec_id'],
                'sender_id': rec['user_id'],
                'sender_username': rec['sender_username'],
                'sender_profile_image_url': rec.get('sender_profile_image_url'),
                'book_id': rec['book_id'],
                'book_title': rec['book_title'],
                'book_cover_url': rec.get('cover_url'),
                'reason': rec['reason'],
                'created_at': rec['created_at'],
                'message': f"{rec['sender_username']} recommended '{rec['book_title']}' to you"
            })

        # Get reading goal reminders
        goal_reminders = get_reading_goal_reminders(int(user_id))
        for goal in goal_reminders:
            # Calculate progress percentage
            progress = goal.get('progress', 0) or 0
            target = goal.get('target_books', 1) or 1
            percentage = int((progress / target) * 100) if target else 0
            
            # Calculate days left
            end_date = goal.get('end_date')
            days_left_text = ""
            if end_date:
                from datetime import date
                if hasattr(end_date, 'date'):
                    end_date = end_date.date()
                days_left = (end_date - date.today()).days
                if days_left > 0:
                    days_left_text = f"{days_left} day{'s' if days_left != 1 else ''} left"
                elif days_left == 0:
                    days_left_text = "Due today!"
                else:
                    days_left_text = "Overdue"
            
            # Create message
            if goal.get('book_title'):
                message = f"Reading goal: {goal['book_title']} - {percentage}% complete"
            else:
                message = f" Reading goal: {percentage}% complete ({progress}/{target})"
            
            if days_left_text:
                message += f" • {days_left_text}"
            
            notifications.append({
                'type': 'reading_goal_reminder',
                'id': f"reading_goal_{goal['goal_id']}",
                'goal_id': goal['goal_id'],
                'book_id': goal.get('book_id'),
                'book_title': goal.get('book_title'),
                'book_cover_url': goal.get('book_cover_url'),
                'progress': progress,
                'target': target,
                'percentage': percentage,
                'end_date': goal.get('end_date'),
                'days_left_text': days_left_text,
                'created_at': goal.get('created_at'),
                'message': message
            })

        return {
            'count': len(notifications),
            'notifications': notifications
        }

    except Exception as e:
        return {
            'count': 0,
            'notifications': []
        }


def respond_to_friend_request_notification(user_id: str, notification_id: str, accept: bool) -> Dict[str, Any]:
    """
    Handle responding to a friend request notification.
    notification_id should be in format: friend_request_{sender_id}
    """
    try:
        if not notification_id.startswith('friend_request_'):
            return {'success': False, 'message': 'Invalid notification type'}

        sender_id = notification_id.replace('friend_request_', '')

        # Accept or reject the friend request
        result = friends_backend.respond_to_friend_request(
            user_id, sender_id, accept)

        if result['success']:
            return {'success': True, 'message': f'Friend request {"accepted" if accept else "declined"}'}
        else:
            return {'success': False, 'message': result.get('message', 'Failed to respond to friend request')}

    except Exception as e:
        return {'success': False, 'message': f'Error: {str(e)}'}


def respond_to_book_recommendation_notification(user_id: str, notification_id: str, dismiss: bool = True) -> Dict[str, Any]:
    """
    Handle responding to a book recommendation notification.
    Currently only supports dismissing (deleting) the recommendation.
    notification_id should be in format: book_recommendation_{rec_id}
    """
    try:
        if not notification_id.startswith('book_recommendation_'):
            return {'success': False, 'message': 'Invalid notification type'}

        rec_id = int(notification_id.replace('book_recommendation_', ''))

        if dismiss:
            result = recommendations_backend.delete_recommendation(
                rec_id, int(user_id))
            if result['success']:
                return {'success': True, 'message': 'Book recommendation dismissed'}
            else:
                return {'success': False, 'message': result.get('message', 'Failed to dismiss recommendation')}
        else:
            return {'success': False, 'message': 'Only dismiss action is supported for book recommendations'}

    except Exception as e:
        return {'success': False, 'message': f'Error: {str(e)}'}


def resend_verification_email(user_id: int) -> Dict[str, Any]:
    """Resend verification email to user"""
    try:
        import backend.email_utils as email_utils
        from backend.db import get_conn
        import psycopg2.extras

        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # get user info
            cur.execute(
                "SELECT email, username, email_verified FROM users WHERE user_id = %s", (user_id,))
            user = cur.fetchone()

            if not user:
                return {'success': False, 'message': 'User not found'}

            if user['email_verified']:
                return {'success': False, 'message': 'Email already verified'}

            # generate new token
            token = email_utils.generate_token()
            success, message = email_utils.store_verification_token(
                user_id, token)

            if not success:
                return {'success': False, 'message': 'Error generating token'}

            # send email
            success, message = email_utils.send_verification_email(
                user['email'], user['username'], token)

            if success:
                return {'success': True, 'message': 'Verification email sent'}
            else:
                return {'success': False, 'message': message}

    except Exception as e:
        return {'success': False, 'message': f'Error: {str(e)}'}
    

def get_reading_goal_reminders(user_id: int) -> List[Dict[str, Any]]:
    """
    Get active reading goal reminders for a user.
    These are shown in the notifications page.
    Reminders are dynamically generated from reading_goals table.
    """
    try:
        from backend.db import get_conn
        import psycopg2.extras
        
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get goals that have reminders enabled and are not completed
            cur.execute("""
                SELECT 
                    goal_id,
                    user_id,
                    target_books,
                    progress,
                    start_date,
                    end_date,
                    reminder_enabled,
                    goal_type,
                    book_name
                FROM reading_goals
                WHERE user_id = %s 
                  AND reminder_enabled = TRUE
                  AND progress < target_books
                  AND (end_date IS NULL OR end_date >= CURRENT_DATE)
                ORDER BY end_date ASC NULLS LAST
            """, (user_id,))
            
            goals = cur.fetchall()
            
            # Convert to list of dicts and add fields for compatibility with notification system
            result = []
            for g in goals:
                goal_dict = dict(g)
                # Map book_name to book_title for backward compatibility with notification display
                goal_dict['book_title'] = goal_dict.get('book_name')
                goal_dict['book_id'] = None
                goal_dict['book_cover_url'] = None
                goal_dict['created_at'] = goal_dict.get('start_date')  # Use start_date as timestamp
                result.append(goal_dict)
            return result
    except Exception as e:
        print(f"Error getting reading goal reminders: {e}")
        return []
    
    
def dismiss_reading_goal_reminder(user_id: str, goal_id: int) -> Dict[str, Any]:
    """
    Dismiss a reading goal reminder by disabling reminders for that goal.
    """
    try:
        from backend.db import get_conn
        
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                UPDATE reading_goals 
                SET reminder_enabled = FALSE 
                WHERE goal_id = %s AND user_id = %s
            """, (goal_id, int(user_id)))
            
            if cur.rowcount > 0:
                conn.commit()
                return {'success': True, 'message': 'Reminder dismissed'}
            else:
                return {'success': False, 'message': 'Goal not found'}
    
    except Exception as e:
        return {'success': False, 'message': str(e)}
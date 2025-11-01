# backend/notifications.py
from typing import List, Dict, Any
import backend.friends as friends_backend


def get_user_notifications(user_id: str) -> Dict[str, Any]:
    """
    Get all notifications for a user.
    Currently includes pending friend requests.
    Returns a dict with notification count and details.
    """
    try:
        # Get pending friend requests
        pending_requests = friends_backend.get_pending_friend_requests(user_id)

        notifications = []
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

        result = friends_backend.respond_to_friend_request(
            receiver_id=user_id,
            sender_id=sender_id,
            accept=accept
        )

        return {
            'success': True,
            'message': result['message']
        }

    except Exception as e:
        return {
            'success': False,
            'message': 'Error processing response'
        }

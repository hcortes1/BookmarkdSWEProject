# backend/notifications.py
from typing import List, Dict, Any
import backend.friends as friends_backend
import backend.recommendations as recommendations_backend


def get_user_notifications(user_id: str) -> Dict[str, Any]:
    """
    Get all notifications for a user.
    Currently includes pending friend requests and book recommendations.
    Returns a dict with notification count and details.
    """
    try:
        notifications = []

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
        book_recommendations = recommendations_backend.get_user_recommendations(
            int(user_id))
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

# backend/recommendations.py
from typing import List, Dict, Any
import backend.db as db
import psycopg2.extras
from datetime import datetime, timezone


def create_book_recommendation(sender_id: int, receiver_id: int, book_id: int, reason: str) -> Dict[str, Any]:
    """
    Create a book recommendation from sender to receiver.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Insert the recommendation
                cur.execute("""
                    INSERT INTO recommendations (user_id, receiver_id, book_id, reason, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING rec_id
                """, (sender_id, receiver_id, book_id, reason, datetime.now(timezone.utc)))

                result = cur.fetchone()
                conn.commit()

                return {
                    'success': True,
                    'rec_id': result['rec_id'],
                    'message': 'Book recommendation sent successfully'
                }

    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to create recommendation: {str(e)}'
        }


def get_user_recommendations(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all book recommendations for a user.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT r.*, b.title as book_title, b.cover_url,
                           u.username as sender_username, u.profile_image_url as sender_profile_image_url
                    FROM recommendations r
                    JOIN books b ON r.book_id = b.book_id
                    JOIN users u ON r.user_id = u.user_id
                    WHERE r.receiver_id = %s
                    ORDER BY r.created_at DESC
                """, (user_id,))

                recommendations = cur.fetchall()
                return [dict(rec) for rec in recommendations]

    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []


def get_sent_recommendations(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all book recommendations sent by a user.
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT r.*, b.title as book_title, b.cover_url,
                           u.username as receiver_username
                    FROM recommendations r
                    JOIN books b ON r.book_id = b.book_id
                    JOIN users u ON r.receiver_id = u.user_id
                    WHERE r.user_id = %s
                    ORDER BY r.created_at DESC
                """, (user_id,))

                recommendations = cur.fetchall()
                return [dict(rec) for rec in recommendations]

    except Exception as e:
        print(f"Error getting sent recommendations: {e}")
        return []


def delete_recommendation(rec_id: int, user_id: int) -> Dict[str, Any]:
    """
    Delete a recommendation (only if user is the receiver).
    """
    try:
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM recommendations
                    WHERE rec_id = %s AND receiver_id = %s
                """, (rec_id, user_id))

                if cur.rowcount > 0:
                    conn.commit()
                    return {'success': True, 'message': 'Recommendation dismissed'}
                else:
                    return {'success': False, 'message': 'Recommendation not found or not authorized'}

    except Exception as e:
        return {'success': False, 'message': f'Failed to delete recommendation: {str(e)}'}
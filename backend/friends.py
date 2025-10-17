# backend/friends.py
from typing import Optional, List, Dict, Any
import psycopg2
import psycopg2.extras
from .db import get_conn

# ---- FRIEND REQUESTS ----


def send_friend_request(sender_id: str, receiver_username: str) -> Dict[str, Any]:
    """
    Send a friend request to a user by username.
    Creates a record in friend_requests table.
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # First, find the receiver's user_id
        cur.execute(
            "SELECT user_id FROM public.users WHERE lower(username) = lower(%s)", (receiver_username,))
        receiver_row = cur.fetchone()

        if not receiver_row:
            raise ValueError("User not found")

        receiver_id = receiver_row['user_id']

        if int(sender_id) == int(receiver_id):
            raise ValueError("Cannot send friend request to yourself")

        # Check if they're already friends
        cur.execute("""
            SELECT 1 FROM public.friends 
            WHERE (user_id = %s AND friend_id = %s)
               OR (user_id = %s AND friend_id = %s)
        """, (int(sender_id), int(receiver_id), int(receiver_id), int(sender_id)))

        if cur.fetchone():
            raise ValueError("You are already friends with this user")

        # Check if request already exists
        cur.execute("""
            SELECT status FROM public.friend_requests 
            WHERE sender_id = %s AND receiver_id = %s
        """, (int(sender_id), int(receiver_id)))

        existing = cur.fetchone()
        if existing:
            if existing['status'] == 'pending':
                raise ValueError("Friend request already sent")
            elif existing['status'] == 'declined':
                # Update existing declined request to pending
                cur.execute("""
                    UPDATE public.friend_requests 
                    SET status = 'pending', created_at = CURRENT_TIMESTAMP
                    WHERE sender_id = %s AND receiver_id = %s
                """, (int(sender_id), int(receiver_id)))
            else:
                raise ValueError("Friend request already exists")
        else:
            # Create new friend request
            cur.execute("""
                INSERT INTO public.friend_requests (sender_id, receiver_id, status)
                VALUES (%s, %s, 'pending')
            """, (int(sender_id), int(receiver_id)))

        conn.commit()
        return {"success": True, "message": "Friend request sent"}


def get_pending_friend_requests(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all pending friend requests for a user.
    """
    sql = """
    SELECT fr.sender_id, fr.created_at, u.username, u.profile_image_url
      FROM public.friend_requests fr
      JOIN public.users u ON u.user_id = fr.sender_id
     WHERE fr.receiver_id = %s AND fr.status = 'pending'
     ORDER BY fr.created_at DESC
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # print(f"DEBUG: Looking for friend requests for user_id: {user_id}")
        cur.execute(sql, (int(user_id),))
        results = [dict(r) for r in cur.fetchall()]
        # print(f"DEBUG: Found {len(results)} friend requests")
        return results


def respond_to_friend_request(receiver_id: str, sender_id: str, accept: bool) -> Dict[str, Any]:
    """
    Accept or decline a friend request.
    If accepted, adds mutual friendship and removes the request.
    If declined, marks the request as declined.
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Check if the friend request exists and is pending
        cur.execute("""
            SELECT * FROM public.friend_requests 
            WHERE sender_id = %s AND receiver_id = %s AND status = 'pending'
        """, (int(sender_id), int(receiver_id)))

        request = cur.fetchone()
        if not request:
            raise ValueError("No pending friend request found")

        if accept:
            # Add mutual friendship
            cur.execute("""
                INSERT INTO public.friends (user_id, friend_id)
                VALUES (%s, %s)
            """, (int(receiver_id), int(sender_id)))

            cur.execute("""
                INSERT INTO public.friends (user_id, friend_id)
                VALUES (%s, %s)
            """, (int(sender_id), int(receiver_id)))

            # Remove the friend request
            cur.execute("""
                DELETE FROM public.friend_requests 
                WHERE sender_id = %s AND receiver_id = %s
            """, (int(sender_id), int(receiver_id)))

            conn.commit()
            return {"success": True, "message": "Friend request accepted"}
        else:
            # Mark as declined
            cur.execute("""
                UPDATE public.friend_requests 
                SET status = 'declined'
                WHERE sender_id = %s AND receiver_id = %s
            """, (int(sender_id), int(receiver_id)))

            conn.commit()
            return {"success": True, "message": "Friend request declined"}


def get_sent_friend_requests(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all friend requests sent by a user.
    """
    sql = """
    SELECT fr.receiver_id, fr.status, fr.created_at, u.username, u.profile_image_url
      FROM public.friend_requests fr
      JOIN public.users u ON u.user_id = fr.receiver_id
     WHERE fr.sender_id = %s
     ORDER BY fr.created_at DESC
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (int(user_id),))
        return [dict(r) for r in cur.fetchall()]


def cancel_friend_request(sender_id: str, receiver_id: str) -> Dict[str, Any]:
    """
    Cancel a sent friend request.
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            DELETE FROM public.friend_requests 
            WHERE sender_id = %s AND receiver_id = %s AND status = 'pending'
        """, (int(sender_id), int(receiver_id)))

        if cur.rowcount == 0:
            raise ValueError("No pending friend request found to cancel")

        conn.commit()
        return {"success": True, "message": "Friend request cancelled"}

# ---- FRIENDS ----


def remove_friend(user_id: str, friend_id: str) -> Dict[str, Any]:
    """
    Remove a friendship (mutual removal).
    """
    with get_conn() as conn, conn.cursor() as cur:
        # Remove both directions of the friendship
        cur.execute("""
            DELETE FROM public.friends 
            WHERE (user_id = %s AND friend_id = %s)
               OR (user_id = %s AND friend_id = %s)
        """, (int(user_id), int(friend_id), int(friend_id), int(user_id)))

        conn.commit()
        return {"success": True, "message": "Friend removed"}


def get_friends_list(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all friends for a user.
    """
    sql = """
    SELECT f.friend_id, u.username, u.profile_image_url
      FROM public.friends f
      JOIN public.users u ON u.user_id = f.friend_id
     WHERE f.user_id = %s
     ORDER BY u.username
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (int(user_id),))
        return [dict(r) for r in cur.fetchall()]


def get_friendship_status(user1_id: str, user2_username: str) -> Dict[str, Any]:
    """
    Check the friendship status between two users.
    Returns: 
    - 'friends': They are already friends
    - 'pending_sent': user1 sent a friend request to user2 (pending)
    - 'pending_received': user2 sent a friend request to user1 (pending) 
    - 'none': No relationship
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # First, get user2's ID from username
        cur.execute(
            "SELECT user_id FROM public.users WHERE lower(username) = lower(%s)", (user2_username,))
        user2_row = cur.fetchone()

        if not user2_row:
            return {'status': 'user_not_found'}

        user2_id = user2_row['user_id']

        # Check if they are friends
        cur.execute("""
            SELECT 1 FROM public.friends 
            WHERE (user_id = %s AND friend_id = %s)
               OR (user_id = %s AND friend_id = %s)
        """, (int(user1_id), int(user2_id), int(user2_id), int(user1_id)))

        if cur.fetchone():
            return {'status': 'friends', 'user2_id': user2_id}

        # Check for pending friend requests
        cur.execute("""
            SELECT sender_id, receiver_id FROM public.friend_requests 
            WHERE ((sender_id = %s AND receiver_id = %s) 
                   OR (sender_id = %s AND receiver_id = %s))
              AND status = 'pending'
        """, (int(user1_id), int(user2_id), int(user2_id), int(user1_id)))

        request = cur.fetchone()
        if request:
            if request['sender_id'] == int(user1_id):
                return {'status': 'pending_sent', 'user2_id': user2_id}
            else:
                return {'status': 'pending_received', 'user2_id': user2_id}

        return {'status': 'none', 'user2_id': user2_id}

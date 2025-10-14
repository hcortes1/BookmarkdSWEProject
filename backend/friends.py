import os
import pymysql
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Database config from .env
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = int(os.getenv("port"))
DBNAME = os.getenv("dbname")

def get_db_connection():
    """Create and return a new database connection."""
    try:
        connection = pymysql.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DBNAME,
            port=PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return None


# Search Users
def search_users_by_username(query, current_user_id):
    """
    Search for users by partial username match.
    Excludes the current user.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, email
                FROM users
                WHERE username LIKE %s AND user_id != %s
            """, (f"%{query}%", current_user_id))
            results = cur.fetchall()
        conn.close()
        return True, results
    except Exception as e:
        conn.close()
        return False, str(e)


# Send Friend Request
def send_friend_request(sender_id, receiver_id):
    """
    Create a friend request (friends table, status='pending').
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            # Check if a relationship already exists
            cur.execute("""
                SELECT status FROM friends
                WHERE user_id = %s AND friend_id = %s
            """, (sender_id, receiver_id))
            existing = cur.fetchone()

            if existing:
                if existing['status'] == 'pending':
                    return False, "Friend request already sent"
                elif existing['status'] == 'accepted':
                    return False, "You are already friends"
                elif existing['status'] == 'blocked':
                    return False, "User has blocked you"

            # Insert reciprocal pending records for clarity
            cur.execute("""
                INSERT INTO friends (user_id, friend_id, status)
                VALUES (%s, %s, 'pending')
                ON DUPLICATE KEY UPDATE status='pending'
            """, (sender_id, receiver_id))
            cur.execute("""
                INSERT INTO friends (user_id, friend_id, status)
                VALUES (%s, %s, 'pending')
                ON DUPLICATE KEY UPDATE status='pending'
            """, (receiver_id, sender_id))

            conn.commit()
        conn.close()
        return True, f"Friend request sent to user {receiver_id}"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)



# Get Pending Friend Requests
def get_pending_requests(user_id):
    """
    Retrieve all pending friend requests received by this user.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.user_id, u.username, u.email
                FROM friends f
                JOIN users u ON f.user_id = u.user_id
                WHERE f.friend_id = %s AND f.status = 'pending'
            """, (user_id,))
            results = cur.fetchall()
        conn.close()
        return True, results
    except Exception as e:
        conn.close()
        return False, str(e)


# Accept or Deny Friend Request
def respond_to_friend_request(receiver_id, sender_id, accept=True):
    """
    Accept or deny a pending friend request.
    Updates both directions in friends table.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        new_status = 'accepted' if accept else 'blocked'

        with conn.cursor() as cur:
            # Verify pending request exists
            cur.execute("""
                SELECT * FROM friends
                WHERE user_id = %s AND friend_id = %s AND status = 'pending'
            """, (sender_id, receiver_id))
            pending = cur.fetchone()
            if not pending:
                return False, "No pending friend request found"

            # Update both sides
            cur.execute("""
                UPDATE friends
                SET status = %s
                WHERE (user_id = %s AND friend_id = %s)
                   OR (user_id = %s AND friend_id = %s)
            """, (new_status, sender_id, receiver_id, receiver_id, sender_id))

            conn.commit()

        conn.close()

        if accept:
            # Notification-like response
            return True, f"Friend request accepted — you are now friends with user {sender_id}"
        else:
            return True, f"Friend request denied/blocked for user {sender_id}"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)


# Get Friend List
def get_friend_list(user_id):
    """
    Return a list of all accepted friends for this user.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.user_id, u.username, u.email
                FROM friends f
                JOIN users u ON f.friend_id = u.user_id
                WHERE f.user_id = %s AND f.status = 'accepted'
            """, (user_id,))
            results = cur.fetchall()
        conn.close()
        return True, results
    except Exception as e:
        conn.close()
        return False, str(e)

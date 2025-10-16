# backend/profile.py
from typing import Optional, List, Dict, Any
import json
import psycopg2
import psycopg2.extras
from .db import get_conn

# ---- READ ----


def list_friends(user_id: str) -> List[Dict[str, Any]]:
    # Handle type mismatch: users.user_id is integer, friends.user_id/friend_id are uuid
    sql = """
    select u.user_id, u.username, u.profile_image_url
      from public.friends f
      join public.users u on u.user_id::text = f.friend_id::text
     where f.user_id::text = %s::text
     order by u.username
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (str(user_id),))
        return [dict(r) for r in cur.fetchall()]

# ---- UPDATE ----
# Profile updates should be done directly on the users table if needed

# ---- SEARCH ----


def search_users(query: str) -> List[Dict[str, Any]]:
    """
    Search for users by username, returns matching users
    """
    sql = """
    select user_id, username, profile_image_url
      from public.users
     where lower(username) like lower(%s)
     order by username
     limit 10
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (f"%{query}%",))
        return [dict(r) for r in cur.fetchall()]


def get_user_profile_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Get complete user profile information by username for public viewing
    """
    sql = """
    select u.user_id, u.username, u.email, u.profile_image_url, u.created_at
      from public.users u
     where lower(u.username) = lower(%s)
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (username,))
        user_row = cur.fetchone()
        if not user_row:
            return None

        user_data = dict(user_row)

        # Get user's friends - handle type mismatch between tables
        friends_sql = """
        select u.user_id, u.username, u.profile_image_url
          from public.friends f
          join public.users u on u.user_id::text = f.friend_id::text
         where f.user_id::text = %s::text
         order by u.username
        """
        cur.execute(friends_sql, (str(user_data['user_id']),))
        friends = [dict(r) for r in cur.fetchall()]

        user_data['friends'] = friends
        return user_data

# ---- FRIENDS ----


def add_friend_by_username(user_id: str, friend_username: str) -> Dict[str, Any]:
    # find friend id from users table
    sql = """
    select user_id from public.users where lower(username) = lower(%s)
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (friend_username,))
        friend_row = cur.fetchone()

        if not friend_row:
            raise ValueError("friend username not found")

        friend_id = friend_row["user_id"]
        if str(friend_id) == str(user_id):
            raise ValueError("cannot friend yourself")

        # insert directed edge; add second row too if you want mutual
        # Cast to UUID since friends table expects UUID types
        insert_sql = """
        insert into public.friends(user_id, friend_id)
        values (%s::uuid, %s::uuid)
        on conflict do nothing
        """
        cur.execute(insert_sql, (str(user_id), str(friend_id)))
        # (optional) mutual
        cur.execute(insert_sql, (str(friend_id), str(user_id)))
        conn.commit()

    return {"added": True, "friend_id": friend_id}


def remove_friend(user_id: str, friend_id: str) -> Dict[str, Any]:
    sql = "delete from public.friends where user_id = %s and friend_id = %s"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (user_id, friend_id))
        # (optional) mutual
        cur.execute(sql, (friend_id, user_id))
        conn.commit()
    return {"removed": True}

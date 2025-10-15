# backend/profile.py
from typing import Optional, List, Dict, Any
import json
import psycopg2
import psycopg2.extras
from .db import get_conn

# ---- READ ----

def get_profile_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    select id, username, profile_image, bio,
           coalesce(favorite_books, '[]'::jsonb)  as favorite_books,
           coalesce(favorite_authors, '[]'::jsonb) as favorite_authors
      from public.profiles
     where id = %s
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_profile_by_username(username: str) -> Optional[Dict[str, Any]]:
    sql = """
    select id, username, profile_image, bio,
           coalesce(favorite_books, '[]'::jsonb)  as favorite_books,
           coalesce(favorite_authors, '[]'::jsonb) as favorite_authors
      from public.profiles
     where lower(username) = lower(%s)
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (username,))
        row = cur.fetchone()
        return dict(row) if row else None

def list_friends(user_id: str) -> List[Dict[str, Any]]:
    # Adjust if your friendship is stored differently; this expects a directed table `friends(user_id, friend_id)`
    sql = """
    select p.id, p.username, p.profile_image
      from public.friends f
      join public.profiles p on p.id = f.friend_id
     where f.user_id = %s
     order by p.username
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (user_id,))
        return [dict(r) for r in cur.fetchall()]

# ---- UPDATE ----

def update_profile(
    user_id: str,
    *,
    bio: Optional[str] = None,
    profile_image: Optional[str] = None,
    favorite_books: Optional[List[str]] = None,
    favorite_authors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Partial update: only fields not None are updated.
    """
    sets = []
    vals: List[Any] = []

    if bio is not None:
        sets.append("bio = %s")
        vals.append(bio)
    if profile_image is not None:
        sets.append("profile_image = %s")
        vals.append(profile_image)
    if favorite_books is not None:
        sets.append("favorite_books = %s::jsonb")
        vals.append(json.dumps(favorite_books))
    if favorite_authors is not None:
        sets.append("favorite_authors = %s::jsonb")
        vals.append(json.dumps(favorite_authors))

    if not sets:
        # nothing to update -> return current row
        prof = get_profile_by_id(user_id)
        if prof is None:
            raise ValueError("profile not found")
        return prof

    sql = f"""
    update public.profiles
       set {", ".join(sets)}
     where id = %s
     returning id, username, profile_image, bio,
               coalesce(favorite_books, '[]'::jsonb)  as favorite_books,
               coalesce(favorite_authors, '[]'::jsonb) as favorite_authors
    """
    vals.append(user_id)

    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, tuple(vals))
        conn.commit()
        row = cur.fetchone()
        if not row:
            raise ValueError("profile not found")
        return dict(row)

# ---- FRIENDS ----

def add_friend_by_username(user_id: str, friend_username: str) -> Dict[str, Any]:
    # find friend id
    friend = get_profile_by_username(friend_username)
    if not friend:
        raise ValueError("friend username not found")
    friend_id = friend["id"]
    if friend_id == user_id:
        raise ValueError("cannot friend yourself")

    # insert directed edge; add second row too if you want mutual
    sql = """
    insert into public.friends(user_id, friend_id)
    values (%s, %s)
    on conflict do nothing
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (user_id, friend_id))
        # (optional) mutual
        cur.execute(sql, (friend_id, user_id))
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

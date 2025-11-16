# backend/profile.py
from typing import Optional, List, Dict, Any
import json
import psycopg2
import psycopg2.extras
from .db import get_conn
from backend.moderation import moderate_review
# ---- READ ----


def list_friends(user_id: str) -> List[Dict[str, Any]]:
    # Handle type mismatch: users.user_id is integer, friends.user_id/friend_id are uuid
    sql = """
    select u.user_id, u.username, u.profile_image_url, f.created_at
      from public.friends f
      join public.users u on u.user_id::text = f.friend_id::text
     where f.user_id::text = %s::text
     order by f.created_at ASC
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (str(user_id),))
        return [dict(r) for r in cur.fetchall()]

# ---- UPDATE ----
# Profile updates should be done directly on the users table if needed


def update_user_profile(user_id: str, display_name: str = None, bio: str = None) -> Dict[str, Any]:
    """
    Update user profile information
    """
    try:
        if display_name is not None:
            is_approved, reason, layer = moderate_review(display_name, context="profile")
            if not is_approved:
                return {"success": False, "message": "Display name contains inappropriate content"}
        if bio is not None:
                is_approved, reason, layer = moderate_review(bio, context="profile")
                if not is_approved:
                    return {"success": False, "message": "Bio contains inappropriate content."}


        updates = []
        params = []

        if display_name is not None:
            updates.append("display_name = %s")
            params.append(display_name)

        if bio is not None:
            updates.append("bio = %s")
            params.append(bio)

        if not updates:
            return {"success": False, "message": "No updates provided"}

        params.append(int(user_id))
        sql = f"UPDATE public.users SET {', '.join(updates)} WHERE user_id = %s"

        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.rowcount == 0:
                return {"success": False, "message": "User not found"}
            conn.commit()

        return {"success": True, "message": "Profile updated successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def add_favorite_author(user_id: str, author_id: int) -> Dict[str, Any]:
    """
    Add an author to user's favorites
    """
    sql = """
    UPDATE public.users 
    SET favorite_authors = array_append(
        COALESCE(favorite_authors, '{}'), %s
    )
    WHERE user_id = %s 
      AND NOT (%s = ANY(COALESCE(favorite_authors, '{}')))
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (author_id, int(user_id), author_id))
        if cur.rowcount > 0:
            conn.commit()
            return {"success": True, "message": "Author added to favorites"}
        else:
            return {"success": False, "message": "Author already in favorites"}


def remove_favorite_author(user_id: str, author_id: int) -> Dict[str, Any]:
    """
    Remove an author from user's favorites
    """
    sql = """
    UPDATE public.users 
    SET favorite_authors = array_remove(favorite_authors, %s)
    WHERE user_id = %s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (author_id, int(user_id)))
        conn.commit()
        return {"success": True, "message": "Author removed from favorites"}


def add_favorite_book(user_id: str, book_id: int) -> Dict[str, Any]:
    """
    Add a book to user's favorites
    """
    sql = """
    UPDATE public.users 
    SET favorite_books = array_append(
        COALESCE(favorite_books, '{}'), %s
    )
    WHERE user_id = %s 
      AND NOT (%s = ANY(COALESCE(favorite_books, '{}')))
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (book_id, int(user_id), book_id))
        if cur.rowcount > 0:
            conn.commit()
            return {"success": True, "message": "Book added to favorites"}
        else:
            return {"success": False, "message": "Book already in favorites"}


def remove_favorite_book(user_id: str, book_id: int) -> Dict[str, Any]:
    """
    Remove a book from user's favorites
    """
    sql = """
    UPDATE public.users 
    SET favorite_books = array_remove(favorite_books, %s)
    WHERE user_id = %s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (book_id, int(user_id)))
        conn.commit()
        return {"success": True, "message": "Book removed from favorites"}

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


def search_all(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Combined search function that searches users, books, and authors
    """
    from .openlibrary import search_books_and_authors

    # Get users from existing function
    users = search_users(query)

    # Get books and authors from Open Library integration
    book_author_results = search_books_and_authors(query)

    return {
        'users': users,
        'books': book_author_results['books'],
        'authors': book_author_results['authors']
    }


def get_user_profile_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Get complete user profile information by username for public viewing
    """
    sql = """
    select u.user_id, u.username, u.email, u.profile_image_url, u.created_at,
           u.display_name, u.bio, u.favorite_authors, u.favorite_books
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
        select u.user_id, u.username, u.profile_image_url, f.created_at
          from public.friends f
          join public.users u on u.user_id = f.friend_id
         where f.user_id = %s
         order by f.created_at ASC
        """
        cur.execute(friends_sql, (user_data['user_id'],))
        friends = [dict(r) for r in cur.fetchall()]

        user_data['friends'] = friends

        # Get favorite authors details
        if user_data.get('favorite_authors'):
            authors_sql = """
            select author_id, name, author_image_url
              from public.authors
             where author_id = ANY(%s)
             order by array_position(%s, author_id)
            """
            cur.execute(
                authors_sql, (user_data['favorite_authors'], user_data['favorite_authors']))
            user_data['favorite_authors_details'] = [
                dict(r) for r in cur.fetchall()]
        else:
            user_data['favorite_authors_details'] = []

        # Get favorite books details
        if user_data.get('favorite_books'):
            books_sql = """
            select b.book_id, b.title, b.cover_url, a.name as author_name
              from public.books b
              left join public.authors a on b.author_id = a.author_id
             where b.book_id = ANY(%s)
             order by array_position(%s, b.book_id)
            """
            cur.execute(
                books_sql, (user_data['favorite_books'], user_data['favorite_books']))
            user_data['favorite_books_details'] = [
                dict(r) for r in cur.fetchall()]
        else:
            user_data['favorite_books_details'] = []

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

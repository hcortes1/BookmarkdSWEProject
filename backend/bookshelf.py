import psycopg2
import psycopg2.extras
from backend.db import get_conn
from psycopg2 import Error
from datetime import datetime


def add_to_bookshelf(user_id, book_id, shelf_type):
    """Add a book to user's bookshelf or update existing entry"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                # Check if book already exists on any shelf for this user
                check_query = """
                    SELECT shelf_id, shelf_type FROM bookshelf 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(check_query, (user_id, book_id))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing entry
                    update_query = """
                        UPDATE bookshelf 
                        SET shelf_type = %s, added_at = CURRENT_TIMESTAMP 
                        WHERE shelf_id = %s
                    """
                    cursor.execute(update_query, (shelf_type, existing[0]))
                    conn.commit()
                    return True, f"Book moved to {shelf_type} shelf"
                else:
                    # Insert new entry
                    insert_query = """
                        INSERT INTO bookshelf (user_id, book_id, shelf_type, added_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """
                    cursor.execute(insert_query, (user_id, book_id, shelf_type))
                    conn.commit()
                    return True, f"Book added to {shelf_type} shelf"
                
    except Error as e:
        print(f"Error adding to bookshelf: {e}")
        return False, f"Error adding to bookshelf: {e}"


def get_user_bookshelf(user_id):
    """Get user's complete bookshelf organized by shelf type"""
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = """
                    SELECT 
                        bs.shelf_id, bs.shelf_type, bs.added_at,
                        b.book_id, b.title, b.author_id, b.cover_url, b.genre,
                        b.average_rating, b.rating_count,
                        EXTRACT(YEAR FROM b.release_date) as release_year,
                        a.name as author_name,
                        r.rating as user_rating, r.review_text, r.created_at as review_date
                    FROM bookshelf bs
                    JOIN books b ON bs.book_id = b.book_id
                    LEFT JOIN authors a ON b.author_id = a.author_id
                    LEFT JOIN reviews r ON bs.user_id = r.user_id AND bs.book_id = r.book_id
                    WHERE bs.user_id = %s
                    ORDER BY bs.shelf_type, bs.added_at DESC
                """
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()
                
                # Organize by shelf type (map database values to frontend keys)
                bookshelf = {
                    'to_read': [],
                    'reading': [],
                    'finished': []
                }
                
                # Mapping from database values to frontend keys
                db_to_frontend = {
                    'plan-to-read': 'to_read',
                    'reading': 'reading',
                    'completed': 'finished'
                }
                
                for row in results:
                    book_data = dict(row)
                    db_shelf_type = book_data['shelf_type']
                    frontend_key = db_to_frontend.get(db_shelf_type)
                    if frontend_key and frontend_key in bookshelf:
                        bookshelf[frontend_key].append(book_data)
                
                return True, "Bookshelf retrieved successfully", bookshelf
                
    except Error as e:
        print(f"Error getting bookshelf: {e}")
        return False, f"Error getting bookshelf: {e}", None


def get_book_shelf_status(user_id, book_id):
    """Check if a book is on user's bookshelf and return status"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT shelf_type FROM bookshelf 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(query, (user_id, book_id))
                result = cursor.fetchone()
                
                if result:
                    return True, "Found", result[0]
                else:
                    return True, "Not on bookshelf", None
                    
    except Error as e:
        print(f"Error checking shelf status: {e}")
        return False, f"Error checking shelf status: {e}", None


def remove_from_bookshelf(user_id, book_id):
    """Remove a book from user's bookshelf"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                delete_query = """
                    DELETE FROM bookshelf 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(delete_query, (user_id, book_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return True, "Book removed from bookshelf"
                else:
                    return False, "Book not found on bookshelf"
                    
    except Error as e:
        print(f"Error removing from bookshelf: {e}")
        return False, f"Error removing from bookshelf: {e}"


def update_shelf_status(user_id, book_id, new_status):
    """Update the shelf status of a book"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                # Check if book exists on shelf
                check_query = """
                    SELECT shelf_id FROM bookshelf 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(check_query, (user_id, book_id))
                
                if not cursor.fetchone():
                    return False, "Book not found on bookshelf"
                
                # Update status
                update_query = """
                    UPDATE bookshelf 
                    SET shelf_type = %s, added_at = CURRENT_TIMESTAMP 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(update_query, (new_status, user_id, book_id))
                conn.commit()
                
                return True, f"Book status updated to {new_status}"
                
    except Error as e:
        print(f"Error updating shelf status: {e}")
        return False, f"Error updating shelf status: {e}"
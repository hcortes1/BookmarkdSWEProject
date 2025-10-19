# backend/books.py
from backend.db import get_conn
import psycopg2.extras


def get_book_details(book_id: int):
    """Get book details from database including core enhanced fields"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT b.book_id, b.title, b.isbn, b.genre,
                       EXTRACT(YEAR FROM b.release_date) as release_year,
                       b.description, b.cover_url, b.author_id,
                       COALESCE(b.language, 'en') as language,
                       b.page_count, b.average_rating, b.rating_count,
                       a.name as author_name, a.bio as author_bio
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                WHERE b.book_id = %s
            """
            cur.execute(sql, (book_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    except Exception as e:
        print(f"Error getting book details: {e}")
        return None


def get_books_with_same_title(book_id: int, title: str):
    """Get all books with the same title as the current book including core enhanced fields"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT b.book_id, b.title, b.isbn, b.genre,
                       EXTRACT(YEAR FROM b.release_date) as release_year,
                       b.description, b.cover_url, b.author_id,
                       COALESCE(b.language, 'en') as language,
                       b.page_count,
                       a.name as author_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                WHERE LOWER(b.title) = LOWER(%s) AND b.book_id != %s
                ORDER BY b.release_date, a.name
            """
            cur.execute(sql, (title, book_id))
            results = cur.fetchall()
            return [dict(result) for result in results]
    except Exception as e:
        print(f"Error getting books with same title: {e}")
        return []

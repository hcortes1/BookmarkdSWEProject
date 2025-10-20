from backend.db import get_conn
import psycopg2.extras


def get_author_details(author_id: int):
    """Get author details from database"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT author_id, name, bio, birth_date, death_date, nationality, author_image_url, created_at
                FROM authors
                WHERE author_id = %s
            """
            cur.execute(sql, (author_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    except Exception as e:
        print(f"Error getting author details: {e}")
        return None


def get_author_books(author_id: int):
    """Get books by this author, sorted by average rating then release date"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT book_id, title, isbn, genre, release_date,
                       EXTRACT(YEAR FROM release_date) as release_year,
                       description, cover_url,
                       COALESCE(language, 'en') as language,
                       page_count, average_rating, rating_count
                FROM books
                WHERE author_id = %s
                ORDER BY
                    CASE
                        WHEN average_rating IS NULL OR average_rating = 0 THEN 0
                        ELSE average_rating
                    END DESC,
                    COALESCE(release_date, '1900-01-01') DESC,
                    title ASC
            """
            cur.execute(sql, (author_id,))
            results = cur.fetchall()
            return [dict(result) for result in results]
    except Exception as e:
        print(f"Error getting author books: {e}")
        return []

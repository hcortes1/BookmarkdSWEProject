import psycopg2.extras
from backend.db import get_conn


def get_showcase_books(limit=30):
    """
    Return currently active sponsored (showcase) books based on date range.
    """
    sql = """
        SELECT 
            b.book_id,
            b.title,
            b.cover_url,
            a.name AS author_name,
            s.sponsor_name,
            s.start_date,
            s.end_date
        FROM public.sponsored_books s
        JOIN public.books b ON s.book_id = b.book_id
        LEFT JOIN public.authors a ON b.author_id = a.author_id
        WHERE s.start_date <= CURRENT_DATE
          AND (s.end_date IS NULL OR s.end_date >= CURRENT_DATE)
        ORDER BY s.start_date DESC
        LIMIT %s;
    """

    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]

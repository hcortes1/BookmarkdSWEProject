import psycopg2.extras
from backend.db import get_conn


def get_trending_books(limit=30):
    sql = """
        SELECT 
            b.book_id,
            b.title,
            b.cover_url,
            a.name AS author_name,
            COUNT(bs.book_id) AS activity_count
        FROM public.bookshelf bs
        JOIN public.books b ON bs.book_id = b.book_id
        LEFT JOIN public.authors a ON b.author_id = a.author_id
        WHERE 
            bs.added_at >= NOW() - INTERVAL '30 days'
            AND bs.shelf_type IN ('reading', 'completed')
        GROUP BY b.book_id, b.title, b.cover_url, a.name
        ORDER BY activity_count DESC
        LIMIT %s;
    """

    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]

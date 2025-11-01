import psycopg2.extras
from backend.db import get_conn


def get_friend_leaderboard(user_id, time_window='month'):
    """Return leaderboard data for a user and their friends within a rolling time window."""
    if time_window not in ['week', 'month', 'year']:
        time_window = 'month'

    if time_window == 'week':
        time_sql = "now() - interval '7 days'"
    elif time_window == 'month':
        time_sql = "now() - interval '30 days'"
    elif time_window == 'year':
        time_sql = "now() - interval '365 days'"
    else:
        time_sql = "now() - interval '30 days'"

    sql = f"""
        SELECT 
            u.user_id,
            u.username,
            COALESCE(u.profile_image_url, '/assets/svg/default-profile.svg') AS profile_image_url,
            COUNT(b.book_id) AS books_completed
        FROM public.bookshelf b
        JOIN public.users u ON b.user_id = u.user_id
        WHERE 
            b.shelf_type = 'completed'
            AND b.added_at >= {time_sql}
            AND b.user_id IN (
                SELECT friend_id FROM public.friends WHERE user_id = %s
                UNION
                SELECT %s
            )
        GROUP BY u.user_id, u.username, u.profile_image_url
        ORDER BY books_completed DESC, u.username ASC;
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (user_id, user_id))
        return [dict(r) for r in cur.fetchall()]


def get_global_leaderboard(time_window='month'):
    """Return global leaderboard data for all users within a rolling time window."""
    if time_window not in ['week', 'month', 'year']:
        time_window = 'month'

    if time_window == 'week':
        time_sql = "now() - interval '7 days'"
    elif time_window == 'month':
        time_sql = "now() - interval '30 days'"
    elif time_window == 'year':
        time_sql = "now() - interval '365 days'"
    else:
        time_sql = "now() - interval '30 days'"

    sql = f"""
        SELECT 
            u.user_id,
            u.username,
            COALESCE(u.profile_image_url, '/assets/svg/default-profile.svg') AS profile_image_url,
            COUNT(b.book_id) AS books_completed
        FROM public.bookshelf b
        JOIN public.users u ON b.user_id = u.user_id
        WHERE 
            b.shelf_type = 'completed'
            AND b.added_at >= {time_sql}
        GROUP BY u.user_id, u.username, u.profile_image_url
        ORDER BY books_completed DESC, u.username ASC
        LIMIT 100;
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]

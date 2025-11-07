import psycopg2.extras
from datetime import datetime, timezone
from backend.db import get_conn
from datetime import datetime, timezone
from backend.gemini_helper import get_book_recommendation_chat
import difflib

def format_timestamp(dt):
    if not dt:
        return ""

    # Ensure both datetimes are timezone-aware (UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - dt

    if diff.days >= 1:
        return dt.strftime("%b %d, %Y")

    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    else:
        return f"{int(seconds // 3600)}h ago"

def get_friend_activity(user_id, limit=10):
    sql = """
        SELECT 
            u.username,
            COALESCE(u.profile_image_url, '/assets/svg/default-profile.svg') AS profile_image_url,
            b.book_id,
            b.title AS book_title,
            b.cover_url,
            bs.shelf_type,
            bs.added_at
        FROM public.bookshelf bs
        JOIN public.books b ON bs.book_id = b.book_id
        JOIN public.users u ON bs.user_id = u.user_id
        WHERE bs.user_id IN (
            SELECT friend_id FROM public.friends WHERE user_id = %s
        )
        ORDER BY bs.added_at DESC
        LIMIT %s;
    """

    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (user_id, limit))
        records = [dict(r) for r in cur.fetchall()]

    # Add readable action + formatted timestamps
    for r in records:
        shelf = (r.get("shelf_type") or "").lower()
        if shelf == "completed":
            r["action"] = "finished"
        elif shelf in ("reading", "currently reading"):
            r["action"] = "started reading"
        elif shelf in ("planned", "plan to read", "wishlist"):
            r["action"] = "added to their 'Plan to Read' list"
        else:
            r["action"] = "updated their bookshelf with"

        # Add relative time
        added_at = r.get("added_at")
        if isinstance(added_at, datetime):
            r["display_time"] = format_timestamp(added_at)
        else:
            r["display_time"] = ""

    return records


def get_recent_reviews(limit=10):
    sql = """
        SELECT 
            r.review_id,
            r.book_id,
            r.rating,
            r.review_text,
            r.created_at,
            u.username,
            COALESCE(u.profile_image_url, '/assets/svg/default-profile.svg') AS profile_image_url,
            b.title AS book_title,
            b.cover_url
        FROM public.reviews r
        JOIN public.users u ON r.user_id = u.user_id
        JOIN public.books b ON r.book_id = b.book_id
        ORDER BY r.created_at DESC
        LIMIT %s;
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (limit,))
        records = [dict(r) for r in cur.fetchall()]

    # Add readable action and formatted timestamps
    for r in records:
        text = (r.get("review_text") or "").strip()
        r["is_review"] = bool(text)
        r["snippet"] = (text[:120] + "...") if len(text) > 120 else text
        created_at = r.get("created_at")
        if isinstance(created_at, datetime):
            r["display_time"] = format_timestamp(created_at)
        else:
            r["display_time"] = ""

    return records

def get_ai_recommendations(user_genres, limit=10):
    if not user_genres:
        return []

    prompt = (
        f"Recommend {limit} popular and well-reviewed books across these genres: {', '.join(user_genres)}.\n"
        "Output strictly as plain text, no markdown or bullet points. Each line should be in the format:\n"
        "Title by Author\n\n"
        "Do not include quotes, asterisks, numbering, or any special characters — only the raw title and author."
    )

    success, response_text = get_book_recommendation_chat(prompt, user_genres, [])
    if not success or not response_text:
        return []

    recs = []
    for line in response_text.split("\n"):
        if " by " in line:
            title, author = line.split(" by ", 1)
            recs.append({"title": title.strip(), "author": author.strip()})
        if len(recs) >= limit:
            break

    if not recs:
        return []

    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                b.book_id, 
                b.title, 
                COALESCE(b.cover_url, '/assets/svg/default-book.svg') AS cover_url,
                COALESCE(a.name, '') AS author_name
            FROM public.books b
            LEFT JOIN public.authors a ON b.author_id = a.author_id;
        """)
        all_books = cur.fetchall()

    if not all_books:
        return []

    all_titles = [b["title"].lower() for b in all_books]

    matched = []
    for r in recs:
        title_lower = r["title"].lower()

        best_match = difflib.get_close_matches(title_lower, all_titles, n=1, cutoff=0.55)

        if best_match:
            match_title = best_match[0]
            db_book = next(b for b in all_books if b["title"].lower() == match_title)
            matched.append({
                "book_id": db_book["book_id"],
                "title": db_book["title"],
                "author": db_book["author_name"] or r["author"],
                "cover_url": db_book["cover_url"] or "/assets/svg/default-book.svg"
            })
        else:
            matched.append({
                "book_id": None,
                "title": r["title"],
                "author": r["author"],
                "cover_url": "/assets/svg/default-book.svg"
            })

    return matched
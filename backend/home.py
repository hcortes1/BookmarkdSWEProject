import psycopg2.extras
from datetime import datetime, timezone
from backend.db import get_conn
from datetime import datetime, timezone

def format_timestamp(dt):
    """
    - If < 24 hours: 'x hours/minutes ago'
    - Else: formatted date (e.g. 'Nov 3, 2025')
    """
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
    """
    Return recent bookshelf activity for a user's friends.
    Includes actions such as marking a book as completed,
    currently reading, or planning to read.
    """
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
    """
    Return the most recent user reviews site-wide,
    including whether it's just a rating or a full review.
    """
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

#  AI Recommendations Helper
from backend.gemini_helper import get_book_recommendation_chat

def get_ai_recommendations(user_genres, limit=12):
    """
    Generate AI-powered book recommendations based on user's favorite genres.
    Cross-references with your books table to fetch covers and IDs.
    """
    if not user_genres:
        return []

    prompt = (
        f"Recommend {limit} popular and well-reviewed books across these genres: {', '.join(user_genres)}.\n"
        "Output strictly as plain text, no markdown or bullet points. Each line should be in the format:\n"
        "Title by Author\n\n"
        "Do not include quotes, asterisks, numbering, or any special characters — only the raw title and author."
    )

    success, response_text = get_book_recommendation_chat(prompt, user_genres, [])
    if not success:
        return []

    # Parse Gemini’s response
    recs = []
    for line in response_text.split("\n"):
        if " by " in line:
            title, author = line.split(" by ", 1)
            recs.append({"title": title.strip(), "author": author.strip()})
        if len(recs) >= limit:
            break

    # --- Cross-reference with database ---
    matched = []
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for r in recs:
            cur.execute("""
                SELECT book_id, title, cover_url, a.name AS author_name
                FROM public.books b
                LEFT JOIN public.authors a ON b.author_id = a.author_id
                WHERE LOWER(b.title) ILIKE LOWER(%s)
                ORDER BY LENGTH(b.title) ASC
                LIMIT 1;
            """, (f"%{r['title'].strip('*\"')}%",))
            db_book = cur.fetchone()

            if db_book:
                matched.append({
                    "book_id": db_book["book_id"],
                    "title": db_book["title"],
                    "author": db_book["author_name"] or r["author"],
                    "cover_url": db_book["cover_url"]
                })
            else:
                # Fallback: AI-only result
                matched.append({
                    "book_id": None,
                    "title": r["title"],
                    "author": r["author"],
                    "cover_url": None
                })

    return matched
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
            u.user_id,
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
            u.user_id,
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

def get_ai_recommendations(user_id, user_genres, limit=10):
    if not user_genres:
        return []

    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

        cur.execute("""
            SELECT book_id FROM public.bookshelf
            WHERE user_id = %s AND shelf_type IN ('completed', 'reading', 'currently reading');
        """, (user_id,))
        excluded_ids = {row["book_id"] for row in cur.fetchall()}

        cur.execute("""
            SELECT 
                b.book_id,
                b.title,
                COALESCE(b.cover_url, '') AS cover_url,
                COALESCE(a.name, '') AS author
            FROM public.books b
            LEFT JOIN public.authors a ON b.author_id = a.author_id
        """)
        all_books = cur.fetchall()

    if not all_books:
        return []

    # Filter out completed/currently-reading books
    available_books = [
        b for b in all_books
        if b["book_id"] not in excluded_ids
    ]

    if not available_books:
        return []

    # Split books into two categories
    books_with_covers = [b for b in available_books if b["cover_url"] not in (None, "", " ")]
    books_without_covers = [b for b in available_books if b["cover_url"] in (None, "", " ")]

    # AI selects books from DB titles
    ai_prompt = (
        f"From this list of books, pick {limit} titles that best match "
        f"these genres: {', '.join(user_genres)}.\n"
        f"Output only exact titles, one per line:\n\n" +
        "\n".join([b["title"] for b in available_books])
    )

    success, ai_output = get_book_recommendation_chat(ai_prompt, user_genres, [])
    ai_titles = ai_output.split("\n") if success else []

    ai_titles_clean = {t.strip().lower() for t in ai_titles if t.strip()}

    matched_recs = []
    used_ids = set()

    for title_lower in ai_titles_clean:
        best = difflib.get_close_matches(
            title_lower,
            [b["title"].lower() for b in available_books],
            n=1,
            cutoff=0.7
        )

        if not best:
            continue

        match_title = best[0]
        book = next(b for b in available_books if b["title"].lower() == match_title)

        if book["book_id"] not in used_ids:
            matched_recs.append(book)
            used_ids.add(book["book_id"])

        if len(matched_recs) >= limit:
            break

    if len(matched_recs) < limit:
        for b in books_with_covers:
            if b["book_id"] not in used_ids:
                matched_recs.append(b)
                used_ids.add(b["book_id"])
                if len(matched_recs) >= limit:
                    break

    if len(matched_recs) < limit:
        for b in books_without_covers:
            if b["book_id"] not in used_ids:
                b["cover_url"] = "/assets/svg/default-book.svg"
                matched_recs.append(b)
                used_ids.add(b["book_id"])
                if len(matched_recs) >= limit:
                    break

    return matched_recs[:limit]

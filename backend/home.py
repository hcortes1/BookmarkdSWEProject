import psycopg2.extras
from datetime import datetime, timezone, timedelta
from backend.db import get_conn
from backend.gemini_helper import get_book_recommendation_chat, select_books_from_list
from backend.gutenberg import get_gutenberg_description
import difflib
import json
import pytz

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
            bs.added_at,
            (SELECT COUNT(*) FROM public.reviews WHERE book_id = b.book_id) AS total_ratings,
            (SELECT ROUND(AVG(rating)::numeric, 1) FROM public.reviews WHERE book_id = b.book_id) AS avg_rating
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
            b.cover_url,
            (SELECT COUNT(*) FROM public.reviews WHERE book_id = r.book_id) AS total_ratings,
            (SELECT ROUND(AVG(rating)::numeric, 1) FROM public.reviews WHERE book_id = r.book_id) AS avg_rating
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
                COALESCE(a.name, '') AS author,
                b.description AS description,
                (SELECT COUNT(*) FROM public.reviews WHERE book_id = b.book_id) AS total_ratings,
                (SELECT ROUND(AVG(rating)::numeric, 1) FROM public.reviews WHERE book_id = b.book_id) AS avg_rating
            FROM public.books b
            LEFT JOIN public.authors a ON b.author_id = a.author_id
        """)
        all_books = cur.fetchall()
        print(f"DEBUG: Fetched {len(all_books)} books from database")
        for book in all_books[:3]:  # Print first 3 books
            print(f"  Book: {book['title']}, Description exists: {bool(book.get('description'))}, Length: {len(book.get('description', '') or '')}")

    if not all_books:
        return []

    # Filter out completed/currently-reading books
    available_books = [
        b for b in all_books
        if b["book_id"] not in excluded_ids
    ]

    if not available_books:
        return []

    # Prioritize books by quality: cover + description > cover only > neither
    books_with_both = [b for b in available_books 
                       if b["cover_url"] not in (None, "", " ") 
                       and b.get("description") and b["description"].strip()]
    books_with_cover_only = [b for b in available_books 
                             if b["cover_url"] not in (None, "", " ") 
                             and (not b.get("description") or not b["description"].strip())]
    books_with_neither = [b for b in available_books 
                          if b["cover_url"] in (None, "", " ")]

    # AI selects books from DB titles using dedicated function
    book_titles_list = [b["title"] for b in available_books]
    success, ai_output = select_books_from_list(book_titles_list, user_genres, limit)
    
    matched_recs = []
    used_ids = set()
    
    # Try to match AI-selected titles if successful, prioritizing complete books
    if success and ai_output:
        ai_titles = [t.strip() for t in ai_output.split("\n") if t.strip()]
        ai_titles_clean = {t.lower() for t in ai_titles}

        # First pass: match books with both cover and description
        for title_lower in ai_titles_clean:
            best = difflib.get_close_matches(
                title_lower,
                [b["title"].lower() for b in books_with_both],
                n=1,
                cutoff=0.7
            )
            if best:
                match_title = best[0]
                book = next(b for b in books_with_both if b["title"].lower() == match_title)
                if book["book_id"] not in used_ids:
                    matched_recs.append(book)
                    used_ids.add(book["book_id"])
                    if len(matched_recs) >= limit:
                        break

        # Second pass: match remaining AI titles from books with cover only
        if len(matched_recs) < limit:
            for title_lower in ai_titles_clean:
                best = difflib.get_close_matches(
                    title_lower,
                    [b["title"].lower() for b in books_with_cover_only],
                    n=1,
                    cutoff=0.7
                )
                if best:
                    match_title = best[0]
                    book = next(b for b in books_with_cover_only if b["title"].lower() == match_title)
                    if book["book_id"] not in used_ids:
                        matched_recs.append(book)
                        used_ids.add(book["book_id"])
                        if len(matched_recs) >= limit:
                            break

    # Fill remaining slots with books that have both cover and description
    if len(matched_recs) < limit:
        for b in books_with_both:
            if b["book_id"] not in used_ids:
                matched_recs.append(b)
                used_ids.add(b["book_id"])
                if len(matched_recs) >= limit:
                    break

    # Then fill with books that have cover only
    if len(matched_recs) < limit:
        for b in books_with_cover_only:
            if b["book_id"] not in used_ids:
                matched_recs.append(b)
                used_ids.add(b["book_id"])
                if len(matched_recs) >= limit:
                    break

    # Finally add books without covers as last resort
    if len(matched_recs) < limit:
        for b in books_with_neither:
            if b["book_id"] not in used_ids:
                b["cover_url"] = "/assets/svg/default-book.svg"
                matched_recs.append(b)
                used_ids.add(b["book_id"])
                if len(matched_recs) >= limit:
                    break

    # Debug: print what descriptions we have
    for rec in matched_recs:
        print(f"Book: {rec['title']}, Has description: {bool(rec.get('description'))}, Description: {rec.get('description', '')[:50] if rec.get('description') else 'None'}")

    return matched_recs[:limit]


def get_next_refresh_time():
    """Calculate next 7 PM ET refresh time"""
    eastern = pytz.timezone('US/Eastern')
    now_et = datetime.now(eastern)
    
    # Set to today at 7 PM ET
    refresh_time = now_et.replace(hour=19, minute=0, second=0, microsecond=0)
    
    # If it's already past 7 PM, move to tomorrow
    if now_et >= refresh_time:
        refresh_time += timedelta(days=1)
    
    return refresh_time


def should_refresh_cache(created_at):
    """Check if cache should be refreshed (past 7 PM ET)"""
    if not created_at:
        return True
    
    eastern = pytz.timezone('US/Eastern')
    now_et = datetime.now(eastern)
    
    # Convert created_at to Eastern time
    if created_at.tzinfo is None:
        created_at = pytz.utc.localize(created_at)
    created_at_et = created_at.astimezone(eastern)
    
    # Get last 7 PM ET
    last_refresh = now_et.replace(hour=19, minute=0, second=0, microsecond=0)
    if now_et < last_refresh:
        # Haven't hit today's 7 PM yet, so last refresh was yesterday
        last_refresh -= timedelta(days=1)
    
    # Cache should refresh if it was created before the last 7 PM ET
    return created_at_et < last_refresh


def get_cached_recommendations(user_id):
    """Get cached recommendations for user, or None if cache invalid"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT rec_data, created_at
                FROM public.ai_recommendation_cache
                WHERE user_id = %s
            """, (user_id,))
            
            result = cur.fetchone()
            if not result:
                return None
            
            # Check if cache should be refreshed
            if should_refresh_cache(result['created_at']):
                return None
            
            return result['rec_data']
    except Exception as e:
        print(f"Error getting cached recommendations: {e}")
        return None


def cache_recommendations(user_id, recommendations):
    """Store recommendations in cache"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Use upsert to insert or update
            cur.execute("""
                INSERT INTO public.ai_recommendation_cache (user_id, rec_data, created_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET rec_data = EXCLUDED.rec_data, created_at = CURRENT_TIMESTAMP
            """, (user_id, json.dumps(recommendations)))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error caching recommendations: {e}")
        return False


def get_ai_recommendations_with_cache(user_id, user_genres, limit=10):
    """Get AI recommendations with caching - refreshes daily at 7 PM ET"""
    if not user_genres:
        return []
    
    # Try to get from cache first
    cached = get_cached_recommendations(user_id)
    if cached is not None:
        print(f"Returning cached recommendations for user {user_id}")
        # Re-sort cached results to prioritize books with cover + description
        sorted_cached = sorted(cached, key=lambda b: (
            bool(b.get("cover_url") and b["cover_url"] not in ("", " ", "/assets/svg/default-book.svg") and b.get("description") and b["description"].strip()),
            bool(b.get("cover_url") and b["cover_url"] not in ("", " ", "/assets/svg/default-book.svg"))
        ), reverse=True)
        return sorted_cached
    
    # Generate fresh recommendations
    print(f"Generating fresh recommendations for user {user_id}")
    recommendations = get_ai_recommendations(user_id, user_genres, limit)
    
    # Cache the results
    if recommendations:
        cache_recommendations(user_id, recommendations)
    
    return recommendations

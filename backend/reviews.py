import psycopg2
import psycopg2.extras
from backend.db import get_conn
from psycopg2 import Error
from datetime import datetime


def create_or_update_review(user_id, book_id, rating, review_text=None):
    """Create a new review or update existing review"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                # Check if review already exists
                check_query = """
                    SELECT review_id FROM reviews 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(check_query, (user_id, book_id))
                existing_review = cursor.fetchone()
                
                if existing_review:
                    # Update existing review
                    update_query = """
                        UPDATE reviews 
                        SET rating = %s, review_text = %s, created_at = CURRENT_TIMESTAMP 
                        WHERE review_id = %s
                    """
                    cursor.execute(update_query, (rating, review_text, existing_review[0]))
                    message = "Review updated successfully"
                else:
                    # Create new review
                    insert_query = """
                        INSERT INTO reviews (user_id, book_id, rating, review_text, ai_filtered, created_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """
                    cursor.execute(insert_query, (user_id, book_id, rating, review_text, False))
                    message = "Review created successfully"
                
                # Update book's average rating and rating count
                success, update_message = update_book_rating_stats(book_id, conn)
                if not success:
                    conn.rollback()
                    return False, f"Review saved but failed to update book stats: {update_message}"
                
                conn.commit()
                return True, message
                
    except Error as e:
        print(f"Error creating/updating review: {e}")
        return False, f"Error saving review: {e}"


def get_user_review(user_id, book_id):
    """Get user's review for a specific book"""
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = """
                    SELECT review_id, rating, review_text, created_at
                    FROM reviews 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(query, (user_id, book_id))
                result = cursor.fetchone()
                
                if result:
                    return True, "Review found", dict(result)
                else:
                    return True, "No review found", None
                    
    except Error as e:
        print(f"Error getting user review: {e}")
        return False, f"Error getting review: {e}", None


def get_book_reviews(book_id, limit=10, offset=0):
    """Get all reviews for a book with pagination"""
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = """
                    SELECT 
                        r.review_id, r.rating, r.review_text, r.created_at,
                        u.username, u.profile_image_url
                    FROM reviews r
                    JOIN users u ON r.user_id = u.user_id
                    WHERE r.book_id = %s AND r.ai_filtered = false
                    ORDER BY r.created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, (book_id, limit, offset))
                results = cursor.fetchall()
                
                # Get total count
                count_query = """
                    SELECT COUNT(*) FROM reviews 
                    WHERE book_id = %s AND ai_filtered = false
                """
                cursor.execute(count_query, (book_id,))
                total_count = cursor.fetchone()[0]
                
                return True, "Reviews retrieved", {
                    'reviews': [dict(row) for row in results],
                    'total_count': total_count
                }
                
    except Error as e:
        print(f"Error getting book reviews: {e}")
        return False, f"Error getting reviews: {e}", None


def update_book_rating_stats(book_id, connection=None):
    """Update book's average rating and rating count based on all reviews"""
    try:
        conn = connection or get_conn()
        close_conn = connection is None
        
        with conn.cursor() as cursor:
            # Calculate new average rating and count
            stats_query = """
                SELECT 
                    COALESCE(AVG(rating::numeric), 0) as avg_rating,
                    COUNT(*) as rating_count
                FROM reviews 
                WHERE book_id = %s AND ai_filtered = false
            """
            cursor.execute(stats_query, (book_id,))
            result = cursor.fetchone()
            
            avg_rating = float(result[0])
            rating_count = result[1]
            
            # Update book table
            update_query = """
                UPDATE books 
                SET average_rating = %s, rating_count = %s
                WHERE book_id = %s
            """
            cursor.execute(update_query, (avg_rating, rating_count, book_id))
            
            if close_conn:
                conn.commit()
                conn.close()
            
            return True, f"Updated book stats: avg={avg_rating:.2f}, count={rating_count}"
            
    except Error as e:
        print(f"Error updating book rating stats: {e}")
        return False, f"Error updating book stats: {e}"


def delete_review(user_id, book_id):
    """Delete user's review for a book"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                # Delete the review
                delete_query = """
                    DELETE FROM reviews 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(delete_query, (user_id, book_id))
                
                if cursor.rowcount == 0:
                    return False, "No review found to delete"
                
                # Update book rating stats
                success, update_message = update_book_rating_stats(book_id, conn)
                if not success:
                    conn.rollback()
                    return False, f"Review deleted but failed to update book stats: {update_message}"
                
                conn.commit()
                return True, "Review deleted successfully"
                
    except Error as e:
        print(f"Error deleting review: {e}")
        return False, f"Error deleting review: {e}"


def has_user_reviewed(user_id, book_id):
    """Check if user has already reviewed this book"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT review_id FROM reviews 
                    WHERE user_id = %s AND book_id = %s
                """
                cursor.execute(query, (user_id, book_id))
                result = cursor.fetchone()
                
                return result is not None
                
    except Error as e:
        print(f"Error checking if user reviewed: {e}")
        return False
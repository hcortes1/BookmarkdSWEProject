# backend/rentals.py
from backend.db import get_conn
import psycopg2.extras
from datetime import datetime, timedelta
from backend.rewards import get_user_rewards, add_points
from backend.bookshelf import add_to_bookshelf


def check_book_rental_status(user_id, book_id):
    """Check if user has an active rental for the book"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT rental_id, rental_date, due_date, return_date
                FROM rentals
                WHERE user_id = %s AND book_id = %s AND return_date IS NULL
                ORDER BY rental_date DESC
                LIMIT 1
            """, (user_id, book_id))
            result = cur.fetchone()
            return dict(result) if result else None
    except Exception as e:
        print(f"Error checking rental status: {e}")
        return None


def get_rental_cost():
    """Get the cost in points for renting a book"""
    return 10  # 10 points to rent a book


def get_rental_duration_days():
    """Get the rental duration in days"""
    return 30  # 30 days (1 month) rental period


def rent_book(user_id, book_id):
    """Rent a book for the user, deducting points and creating rental record"""
    try:
        # Get rental cost and duration
        cost = get_rental_cost()
        duration_days = get_rental_duration_days()

        # Check if user has enough points
        user_rewards = get_user_rewards(user_id)
        if user_rewards['points'] < cost:
            return False, "Insufficient points to rent this book"

        # Check if user already has an active rental for this book
        existing_rental = check_book_rental_status(user_id, book_id)
        if existing_rental:
            return False, "You already have this book rented"

        # Calculate dates
        rental_date = datetime.now().date()
        due_date = rental_date + timedelta(days=duration_days)

        with get_conn() as conn, conn.cursor() as cur:
            # Deduct points from user
            new_points = user_rewards['points'] - cost
            cur.execute("""
                UPDATE rewards
                SET points = %s
                WHERE user_id = %s
            """, (new_points, user_id))

            # Create rental record
            cur.execute("""
                INSERT INTO rentals (user_id, book_id, rental_date, due_date)
                VALUES (%s, %s, %s, %s)
                RETURNING rental_id
            """, (user_id, book_id, rental_date, due_date))

            # Add book to user's bookshelf as "currently reading"
            add_to_bookshelf(user_id, book_id, 'reading')

            conn.commit()
            return True, f"Book rented successfully! Due date: {due_date.strftime('%Y-%m-%d')}"

    except Exception as e:
        print(f"Error renting book: {e}")
        return False, "Failed to rent book"


def get_rental_info_for_confirmation(user_id, book_id):
    """Get information needed for rental confirmation modal"""
    cost = get_rental_cost()
    duration = get_rental_duration_days()
    user_rewards = get_user_rewards(user_id)
    current_points = user_rewards['points']
    points_after = current_points - cost

    return {
        'cost': cost,
        'duration_days': duration,
        'current_points': current_points,
        'points_after': points_after,
        'can_afford': current_points >= cost
    }

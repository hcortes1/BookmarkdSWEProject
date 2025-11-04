import os
import pymysql
from dotenv import load_dotenv
from datetime import datetime, date, timedelta

load_dotenv()

# Database config from .env
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = int(os.getenv("port"))
DBNAME = os.getenv("dbname")


# Database Connection
def get_db_connection():
    try:
        connection = pymysql.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DBNAME,
            port=PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"DB connection error: {e}")
        return None

# Create a New Reading Goal
def create_reading_goal(user_id, book_id, target_books=1, start_date=None, end_date=None, reminder_enabled=True):
    """
    Create a reading goal for a specific book or time period.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        start_date = start_date or date.today()
        if not end_date:
            # Default goal = 30 days
            end_date = start_date + timedelta(days=30)

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO reading_goals (user_id, target_books, progress, start_date, end_date, reminder_enabled)
                VALUES (%s, %s, 0, %s, %s, %s)
            """, (user_id, target_books, start_date, end_date, reminder_enabled))
            conn.commit()
        conn.close()
        return True, f"Reading goal created successfully for user {user_id}"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Update Progress
def update_progress(user_id, books_completed=1):
    """
    Increment the user's progress in their reading goal.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            # Fetch current goal
            cur.execute("""
                SELECT goal_id, target_books, progress FROM reading_goals
                WHERE user_id = %s ORDER BY goal_id DESC LIMIT 1
            """, (user_id,))
            goal = cur.fetchone()
            if not goal:
                return False, "No active goal found"

            new_progress = goal["progress"] + books_completed
            cur.execute("""
                UPDATE reading_goals
                SET progress = %s
                WHERE goal_id = %s
            """, (new_progress, goal["goal_id"]))
            conn.commit()

        conn.close()

        if new_progress >= goal["target_books"]:
            # Goal completed
            return True, "🎉 Congratulations! You reached your reading goal!"
        else:
            return True, f"Progress updated: {new_progress}/{goal['target_books']} books read"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Get Active Goals
def get_active_goals(user_id):
    """
    Retrieve all active (incomplete and not expired) goals for a user.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        today = date.today()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM reading_goals
                WHERE user_id = %s AND progress < target_books AND end_date >= %s
            """, (user_id, today))
            goals = cur.fetchall()
        conn.close()
        return True, goals
    except Exception as e:
        conn.close()
        return False, str(e)

# Modify or Delete Goal
def modify_goal(goal_id, target_books=None, end_date=None, reminder_enabled=None):
    """
    Allow user to adjust their reading goal.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        updates = []
        params = []

        if target_books is not None:
            updates.append("target_books = %s")
            params.append(target_books)
        if end_date is not None:
            updates.append("end_date = %s")
            params.append(end_date)
        if reminder_enabled is not None:
            updates.append("reminder_enabled = %s")
            params.append(reminder_enabled)

        if not updates:
            return False, "No fields to update"

        params.append(goal_id)
        query = f"UPDATE reading_goals SET {', '.join(updates)} WHERE goal_id = %s"

        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            conn.commit()
        conn.close()
        return True, "Goal updated successfully"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)


def delete_goal(goal_id):
    """
    Delete a reading goal.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM reading_goals WHERE goal_id = %s", (goal_id,))
            conn.commit()
        conn.close()
        return True, "Reading goal deleted"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Reminder System 
def get_due_reminders():
    """
    Fetch users who should receive a reminder today.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        today = date.today()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT g.goal_id, g.user_id, u.username, g.target_books, g.progress, g.end_date
                FROM reading_goals g
                JOIN users u ON g.user_id = u.user_id
                WHERE g.reminder_enabled = TRUE AND g.end_date >= %s
            """, (today,))
            reminders = cur.fetchall()
        conn.close()

        messages = []
        for r in reminders:
            progress_percent = round((r['progress'] / r['target_books']) * 100, 1)
            days_left = (r['end_date'] - today).days
            msg = (
                f"Hi {r['username']}! You're {progress_percent}% through your reading goal. "
                f"{days_left} days left to finish!"
            )
            messages.append(msg)

        return True, messages
    except Exception as e:
        conn.close()
        return False, str(e)

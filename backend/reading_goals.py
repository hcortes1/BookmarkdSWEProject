# backend/reading_goals.py
from typing import List, Dict, Any, Optional, Tuple
import psycopg2.extras
from datetime import date
from .db import get_conn


# Create a new reading goal for a user and return success status and message
def create_goal(
    user_id,
    book_id=None,
    target=1,
    start_date=None,
    end_date=None,
    reminder_enabled=False
) -> Tuple[bool, str]:

    # Prevent Ellipsis from Dash being sent to DB
    if start_date is Ellipsis:
        start_date = None
    if end_date is Ellipsis:
        end_date = None

    # Ensure start_date always has a valid value
    start_date = start_date or date.today()

    # Boolean Reminder
    reminder_enabled = bool(reminder_enabled)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO reading_goals(user_id, target_books, start_date, end_date, reminder_enabled)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING goal_id
                """, (user_id, target, start_date, end_date, reminder_enabled))

                goal_id = cur.fetchone()[0]
                conn.commit()

        return True, "Goal created successfully"

    except Exception as e:
        return False, str(e)

# Retrieve all reading goals for a specific user, newest first
def get_user_goals(user_id: int) -> Tuple[bool, str, List[Dict[str, Any]]]:
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT goal_id, user_id, target_books, progress, start_date, end_date, reminder_enabled
                    FROM reading_goals
                    WHERE user_id = %s
                    ORDER BY goal_id DESC
                """, (int(user_id),))
                rows = cur.fetchall()

        return True, "OK", [dict(r) for r in rows]

    except Exception as e:
        return False, str(e), []

# Retrieve a single reading goal by its ID
def get_goal(goal_id: int) -> Optional[Dict[str, Any]]:
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT goal_id, user_id, target_books, progress, start_date, end_date, reminder_enabled
                    FROM reading_goals
                    WHERE goal_id = %s
                """, (int(goal_id),))
                row = cur.fetchone()

        return dict(row) if row else None

    except Exception:
        return None

# Manually update the progress of a goal and optionally create a feed item if completed
def update_progress_manual(goal_id: int, new_progress: int) -> Dict[str, Any]:
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

                cur.execute("SELECT * FROM reading_goals WHERE goal_id = %s", (int(goal_id),))
                goal = cur.fetchone()

                if not goal:
                    return {"success": False, "message": "Goal not found"}

                cur.execute("""
                    UPDATE reading_goals
                    SET progress = %s
                    WHERE goal_id = %s
                """, (int(new_progress), int(goal_id)))

                completed = int(new_progress) >= int(goal["target_books"])

                if completed:
                    try:
                        cur.execute("""
                            INSERT INTO feed (user_id, activity_type, activity_text)
                            VALUES (%s, 'goal', %s)
                        """, (int(goal["user_id"]), f"Completed reading goal (goal_id={goal_id})"))
                    except Exception:
                        pass

            conn.commit()

        msg = "Progress updated"
        if completed:
            msg += " — goal completed!"

        return {"success": True, "message": msg}

    except Exception as e:
        return {"success": False, "message": str(e)}

# Wrapper to set goal progress
def set_progress(goal_id: int, new_progress: int) -> Tuple[bool, str]:
    res = update_progress_manual(goal_id, int(new_progress))

    if res.get("success"):
        return True, res.get("message", "Progress updated")

    return False, res.get("message", "Error updating progress")

# Modify an existing goal
def modify_goal(
    goal_id: int,
    target_books: Optional[int] = None,
    end_date: Optional[date] = None,
    reminder_enabled: Optional[bool] = None
) -> Dict[str, Any]:

    updates = []
    params = []

    if target_books is not None:
        updates.append("target_books = %s")
        params.append(int(target_books))

    if end_date is not None:
        updates.append("end_date = %s")
        params.append(end_date)

    if reminder_enabled is not None:
        updates.append("reminder_enabled = %s")
        params.append(bool(reminder_enabled))

    if not updates:
        return {"success": False, "message": "No fields to update"}

    params.append(int(goal_id))

    sql = f"UPDATE reading_goals SET {', '.join(updates)} WHERE goal_id = %s"

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
            conn.commit()

        return {"success": True, "message": "Goal updated"}

    except Exception as e:
        return {"success": False, "message": str(e)}

# Delete a goal
def delete_goal(goal_id: int) -> Dict[str, Any]:
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM reading_goals WHERE goal_id = %s", (int(goal_id),))

            conn.commit()

        return {"success": True, "message": "Goal deleted"}

    except Exception as e:
        return {"success": False, "message": str(e)}

# Reminders due today or later
def get_due_reminders(today: Optional[date] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
    today = today or date.today()
    msgs = []

    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT g.goal_id, g.user_id, g.target_books, g.progress, g.end_date, u.username
                    FROM reading_goals g
                    JOIN users u ON u.user_id = g.user_id
                    WHERE g.reminder_enabled = TRUE AND g.end_date >= %s
                """, (today,))
                rows = cur.fetchall()

        for r in rows:
            percent = 0.0
            try:
                percent = round((r["progress"] / float(r["target_books"])) * 100, 1) if r["target_books"] else 0.0
            except Exception:
                percent = 0.0

            days_left = (r["end_date"] - today).days if r["end_date"] else None

            msgs.append({
                "user_id": r["user_id"],
                "username": r.get("username"),
                "goal_id": r["goal_id"],
                "progress_percent": percent,
                "days_left": days_left,
                "message": f"Hi {r.get('username')}, you're {percent}% through your goal. {days_left} days left."
            })

        return True, "OK", msgs

    except Exception as e:
        return False, str(e), []

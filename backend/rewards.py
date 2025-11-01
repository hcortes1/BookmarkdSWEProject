# backend/rewards.py
from backend.db import get_conn
import psycopg2.extras


def get_user_rewards(user_id):
    """Get user's rewards data"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT points, level, COALESCE(xp, 0) as xp
                FROM rewards
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()
            if result:
                return dict(result)
            else:
                # Create entry if not exists
                create_user_rewards(user_id)
                return {'points': 0, 'level': 1, 'xp': 0}
    except Exception as e:
        print(f"Error getting user rewards: {e}")
        return {'points': 0, 'level': 1, 'xp': 0}


def create_user_rewards(user_id):
    """Create rewards entry for new user"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO rewards (user_id, points, level, xp)
                VALUES (%s, 0, 1, 0)
            """, (user_id,))
            conn.commit()
    except Exception as e:
        print(f"Error creating user rewards: {e}")


def add_points(user_id, points_increment, xp_increment):
    """Add points and XP to user, update level"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Get current values
            cur.execute("""
                SELECT points, COALESCE(xp, 0) as xp
                FROM rewards
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()
            if not result:
                create_user_rewards(user_id)
                current_points = 0
                current_xp = 0
            else:
                current_points = result[0] or 0
                current_xp = result[1] or 0

            new_points = current_points + points_increment
            new_xp = current_xp + xp_increment
            new_level = calculate_level(new_xp)

            cur.execute("""
                UPDATE rewards
                SET points = %s, level = %s, xp = %s
                WHERE user_id = %s
            """, (new_points, new_level, new_xp, user_id))
            conn.commit()
    except Exception as e:
        print(f"Error adding points: {e}")


def calculate_level(xp):
    """Calculate level from XP with progressive requirements"""
    # XP requirements for each level (cumulative)
    level_requirements = [
        0,      # Level 1
        50,     # Level 2 (50 XP needed)
        150,    # Level 3 (100 XP more)
        300,    # Level 4 (150 XP more)
        500,    # Level 5 (200 XP more)
        750,    # Level 6 (250 XP more)
        1050,   # Level 7 (300 XP more)
        1400,   # Level 8 (350 XP more)
        1800,   # Level 9 (400 XP more)
        2250,   # Level 10 (450 XP more)
    ]
    
    for level, required_xp in enumerate(level_requirements, 1):
        if xp < required_xp:
            return level - 1 if level > 1 else 1
    
    # For levels beyond 10, each level requires 50 more than the previous increment
    # Level 10 requires 450 XP, so level 11 would require 500 XP, etc.
    base_level = 10
    base_xp = 2250
    increment = 450  # Starting increment for level 10->11
    
    while True:
        next_xp = base_xp + increment
        if xp < next_xp:
            return base_level
        base_level += 1
        base_xp = next_xp
        increment += 50  # Each subsequent level requires 50 more XP


def get_level_progress(xp):
    """Get current level, XP in current level, and XP needed for next level"""
    level = calculate_level(xp)
    
    # XP requirements for each level (cumulative)
    level_requirements = [
        0,      # Level 1
        50,     # Level 2
        150,    # Level 3
        300,    # Level 4
        500,    # Level 5
        750,    # Level 6
        1050,   # Level 7
        1400,   # Level 8
        1800,   # Level 9
        2250,   # Level 10
    ]
    
    if level <= len(level_requirements):
        current_level_xp = level_requirements[level - 1]
        next_level_xp = level_requirements[level] if level < len(level_requirements) else level_requirements[-1] + 450 + (level - 10) * 50
    else:
        # For levels beyond 10
        base_xp = 2250
        increment = 450
        for i in range(11, level + 1):
            base_xp += increment
            increment += 50
        current_level_xp = base_xp - increment + 50  # Previous level's requirement
        next_level_xp = base_xp + increment
    
    xp_in_level = xp - current_level_xp
    xp_to_next = next_level_xp - current_level_xp
    
    return level, xp_in_level, xp_to_next


def award_completion_rating(user_id):
    """Award points for completing book with rating"""
    add_points(user_id, 10, 10)


def award_review(user_id):
    """Award points for writing a review"""
    add_points(user_id, 15, 15)


def award_recommendation(user_id):
    """Award points for sending a recommendation"""
    add_points(user_id, 5, 5)
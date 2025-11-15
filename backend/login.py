import os
import hashlib
import psycopg2
import json
from dotenv import load_dotenv
from psycopg2 import Error
import backend.email_utils as email_utils

# load environment variables from .env file
load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")


# create the database connection and return it
def get_db_connection():
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

# hash the password for security


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def signup_user(username, email, password):
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"

    cursor = connection.cursor()

    # if username already exists
    cursor.execute(
        "SELECT user_id FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        cursor.close()
        connection.close()
        return False, "Username already exists"

    # if email already exists
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        connection.close()
        return False, "Email already exists"

    hashed_password = hash_password(password)

    # insert new user with email_verified = false
    insert_query = """
        INSERT INTO users (username, email, password, display_mode, email_verified) 
        VALUES (%s, %s, %s, 'light', false)
        RETURNING user_id
    """
    cursor.execute(insert_query, (username, email, hashed_password))
    user_id = cursor.fetchone()[0]

    connection.commit()

    # generate and store verification token
    token = email_utils.generate_token()
    success, message = email_utils.store_verification_token(user_id, token)

    if not success:
        cursor.close()
        connection.close()
        return False, "Error generating verification token"

    # send verification email
    success, message = email_utils.send_verification_email(
        email, username, token)

    cursor.close()
    connection.close()

    if success:
        return True, "Account created! Please check your email to verify your account."
    else:
        return True, "Account created! However, verification email could not be sent."


def login_user(username, password):
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed", None

    cursor = connection.cursor()

    hashed_password = hash_password(password)

    # check login credentials and get all user data including email_verified
    login_query = """
        SELECT user_id, username, email, profile_image_url, created_at, first_login, favorite_genres, display_mode, email_verified
        FROM users 
        WHERE username = %s AND password = %s
    """
    cursor.execute(login_query, (username, hashed_password))
    user_record = cursor.fetchone()

    cursor.close()
    connection.close()

    if user_record:
        # Return all user data as a dictionary (allow login even if email not verified)
        user_data = {
            "user_id": user_record[0],
            "username": user_record[1],
            "email": user_record[2],
            "profile_image_url": user_record[3],
            "created_at": user_record[4].isoformat() if user_record[4] else None,
            "first_login": user_record[5],
            "favorite_genres": user_record[6],
            "display_mode": user_record[7],
            "email_verified": user_record[8]  # include email_verified status
        }
        return True, "Login successful", user_data
    else:
        return False, "Invalid username or password", None


def refresh_user_session_data(user_id):
    """Refresh user session data from database"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed", None

    cursor = connection.cursor()

    try:
        # Get all user data
        query = """
            SELECT user_id, username, email, profile_image_url, created_at, first_login, favorite_genres, display_mode, email_verified
            FROM users 
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        user_record = cursor.fetchone()

        cursor.close()
        connection.close()

        if user_record:
            # Return updated session data
            session_data = {
                "logged_in": True,
                "user_id": user_record[0],
                "username": user_record[1],
                "email": user_record[2],
                "profile_image_url": user_record[3],
                "created_at": user_record[4].isoformat() if user_record[4] else None,
                "first_login": user_record[5],
                "favorite_genres": user_record[6],
                "display_mode": user_record[7],
                "email_verified": user_record[8]
            }
            return True, "Session data refreshed successfully", session_data
        else:
            return False, "User not found", None

    except Error as e:
        cursor.close()
        connection.close()
        return False, f"Error refreshing session data: {e}", None

# Update User Genre backend


def update_user_genres(user_id, favorite_genres):
    """Update user's favorite genres and mark first login as complete"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"

    cursor = connection.cursor()

    try:
        update_preference_query = """
            UPDATE users 
            SET favorite_genres = %s, first_login = %s 
            WHERE user_id = %s
        """
        cursor.execute(update_preference_query,
                       (json.dumps(favorite_genres), False, user_id))
        connection.commit()

        cursor.close()
        connection.close()

        return True, "User's favorite genres have been updated!"

    except Error as e:
        cursor.close()
        connection.close()
        return False, f"Error updating genres: {e}"


def request_password_reset(email):
    """Request password reset - send reset email if email exists"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"

    cursor = connection.cursor()

    try:
        # check if email exists
        cursor.execute(
            "SELECT user_id, username FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if not user:
            # don't reveal if email exists or not for security
            return True, "If that email is registered, you will receive a password reset link shortly."

        user_id, username = user

        # generate and store reset token
        token = email_utils.generate_token()
        success, message = email_utils.store_reset_token(user_id, token)

        if not success:
            return False, "Error generating reset token"

        # send reset email
        success, message = email_utils.send_password_reset_email(
            email, username, token)

        if success:
            return True, "If that email is registered, you will receive a password reset link shortly."
        else:
            return False, "Error sending reset email"

    except Error as e:
        return False, f"Error requesting password reset: {e}"


def reset_password(token, new_password):
    """Reset password using valid token"""
    # verify token
    success, message, user_id = email_utils.verify_reset_token(token)

    if not success:
        return False, message

    # hash new password
    hashed_password = hash_password(new_password)

    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"

    cursor = connection.cursor()

    try:
        # update password
        cursor.execute(
            "UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, user_id))
        connection.commit()

        cursor.close()
        connection.close()

        # clear reset token
        email_utils.clear_reset_token(user_id)

        return True, "Password reset successfully"

    except Error as e:
        cursor.close()
        connection.close()
        return False, f"Error resetting password: {e}"


def change_password(user_id, old_password, new_password):
    """Change password for authenticated user"""
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"

    cursor = connection.cursor()

    try:
        # verify old password
        hashed_old = hash_password(old_password)
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = %s AND password = %s", (user_id, hashed_old))

        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return False, "Current password is incorrect"

        # update to new password
        hashed_new = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password = %s WHERE user_id = %s", (hashed_new, user_id))
        connection.commit()

        cursor.close()
        connection.close()

        return True, "Password changed successfully"

    except Error as e:
        cursor.close()
        connection.close()
        return False, f"Error changing password: {e}"

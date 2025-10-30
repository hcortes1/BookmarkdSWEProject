import os
import hashlib
import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error

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

    # insert new user
    insert_query = """
        INSERT INTO users (username, email, password) 
        VALUES (%s, %s, %s)
    """
    cursor.execute(insert_query, (username, email, hashed_password))

    connection.commit()

    cursor.close()
    connection.close()

    return True, "User created successfully"


def login_user(username, password):
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed", None

    cursor = connection.cursor()

    hashed_password = hash_password(password)

    # check login credentials and get all user data
    login_query = """
        SELECT user_id, username, email, profile_image_url, created_at, favorite_genres, first_login
        FROM users 
        WHERE username = %s AND password = %s
    """
    cursor.execute(login_query, (username, hashed_password))
    user_record = cursor.fetchone()

    cursor.close()
    connection.close()

    if user_record:
        # Return all user data as a dictionary
        user_data = {
            "user_id": user_record[0],
            "username": user_record[1],
            "email": user_record[2],
            "profile_image_url": user_record[3],
            "created_at": user_record[4].isoformat() if user_record[4] else None,
            "first_login":user_record[5],
            "favorite_genres": user_record[6]
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
            SELECT user_id, username, email, profile_image_url, created_at, first_login, favorite_genres
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
                "first_login":user_record[5],
                "favorite_genres": user_record[6]
            }
            return True, "Session data refreshed successfully", session_data
        else:
            return False, "User not found", None

    except Error as e:
        cursor.close()
        connection.close()
        return False, f"Error refreshing session data: {e}", None
    
# stopped here, need to save users genre preference and mark first_login as false upon completion 
def genre_preference(user_id,favorite_genres):
    pass
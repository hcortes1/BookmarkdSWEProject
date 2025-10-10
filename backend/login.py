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

    # check login credentials
    login_query = """
        SELECT user_id
        FROM users 
        WHERE username = %s AND password = %s
    """
    cursor.execute(login_query, (username, hashed_password))
    user_record = cursor.fetchone()

    cursor.close()
    connection.close()

    if user_record:
        user_id = user_record[0]
        return True, "Login successful", user_id
    else:
        return False, "Invalid username or password", None

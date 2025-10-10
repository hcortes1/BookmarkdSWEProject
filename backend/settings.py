import os
import hashlib
import psycopg2
import base64
import uuid
from dotenv import load_dotenv
from psycopg2 import Error
from supabase import create_client, Client

# load environment variables from .env file
load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
# This should be your service_role key for server operations
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(
    SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


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


def delete_user_account(user_id):
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"

    cursor = connection.cursor()

    try:
        # Check if user exists
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return False, "User not found"

        # Delete the user account
        delete_query = "DELETE FROM users WHERE user_id = %s"
        cursor.execute(delete_query, (user_id,))

        # Check if deletion was successful
        if cursor.rowcount == 0:
            connection.rollback()
            cursor.close()
            connection.close()
            return False, "Failed to delete user account"

        connection.commit()
        cursor.close()
        connection.close()

        return True, "User account deleted successfully"

    except Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        return False, f"Error deleting user account: {e}"


def upload_profile_image(user_id, image_content, filename):
    if not supabase:
        return False, "Supabase client not configured", None

    try:
        # Generate a unique filename to avoid conflicts
        file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
        unique_filename = f"{user_id}_{uuid.uuid4()}.{file_extension}"

        # Upload image to Supabase storage
        storage_response = supabase.storage.from_("profile_image").upload(
            path=unique_filename,
            file=image_content,
            file_options={"content-type": f"image/{file_extension}"}
        )

        # Check if upload was successful
        if hasattr(storage_response, 'error') and storage_response.error:
            return False, f"Failed to upload image: {storage_response.error}", None

        # Get the public URL for the uploaded image
        image_url = supabase.storage.from_(
            "profile_image").get_public_url(unique_filename)

        # Update the user's profile_image_url in the database
        connection = get_db_connection()
        if not connection:
            return False, "Database connection failed", None

        cursor = connection.cursor()

        # Delete old profile image if exists
        cursor.execute(
            "SELECT profile_image_url FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        old_image_url = result[0] if result else None

        # Update profile_image_url
        update_query = "UPDATE users SET profile_image_url = %s WHERE user_id = %s"
        cursor.execute(update_query, (image_url, user_id))

        connection.commit()
        cursor.close()
        connection.close()

        # Delete old image from storage if it exists
        if old_image_url and "profile_image" in old_image_url:
            try:
                # Extract filename from old URL
                old_filename = old_image_url.split('/')[-1]
                supabase.storage.from_("profile_image").remove([old_filename])
            except:
                pass  # Don't fail if old image deletion fails

        return True, "Profile image updated successfully", image_url

    except Exception as e:
        return False, f"Error uploading profile image: {str(e)}", None


def get_user_profile_image_url(user_id):
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed", None

    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT profile_image_url FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            profile_url = result[0]
            # print(f"Debug: Retrieved profile URL for user {user_id}: {profile_url}")
            # Return None if profile_url is NULL in database
            if profile_url is None:
                return True, "No profile image set", None
            return True, "Profile image URL retrieved", profile_url
        else:
            print(f"Debug: No user found with ID {user_id}")
            return False, "User not found", None

    except Error as e:
        cursor.close()
        connection.close()
        return False, f"Error retrieving profile image: {e}", None


def delete_profile_image(user_id):
    if not supabase:
        return False, "Supabase client not configured"

    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"

    cursor = connection.cursor()

    try:
        # Get current profile image URL
        cursor.execute(
            "SELECT profile_image_url FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if not result or not result[0]:
            cursor.close()
            connection.close()
            return True, "No profile image to delete"

        image_url = result[0]

        # Remove profile_image_url from database
        cursor.execute(
            "UPDATE users SET profile_image_url = NULL WHERE user_id = %s", (user_id,))
        connection.commit()

        cursor.close()
        connection.close()

        # Delete from Supabase storage
        if "profile_image" in image_url:
            try:
                filename = image_url.split('/')[-1]
                delete_response = supabase.storage.from_(
                    "profile_image").remove([filename])
            except Exception as delete_error:
                # Don't fail if storage deletion fails, just log it
                print(
                    f"Warning: Could not delete old image from storage: {delete_error}")

        return True, "Profile image deleted successfully"

    except Error as e:
        cursor.close()
        connection.close()
        return False, f"Error deleting profile image: {e}"

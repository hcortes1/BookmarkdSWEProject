import os
import secrets
import yagmail
from datetime import datetime, timedelta
from dotenv import load_dotenv
from backend.db import get_conn
import psycopg2.extras

# load environment variables
load_dotenv()

# email configuration from environment
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
APP_URL = os.getenv("APP_URL", "http://127.0.0.1:8080")


def generate_token():
    """Generate a secure random token for email verification or password reset"""
    return secrets.token_urlsafe(32)


def send_verification_email(email, username, token):
    """Send email verification link to user"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            print("Email credentials not configured")
            return False, "Email service not configured"

        # initialize yagmail
        yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASSWORD)

        # create verification link
        verification_link = f"{APP_URL}/verify-email/{token}"

        # email content
        subject = "Verify your Bookmarkd email"
        body = f"""
        <html>
        <body>
            <h2>Welcome to Bookmarkd, {username}!</h2>
            <p>Thanks for signing up. Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}">Verify Email</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account with Bookmarkd, you can safely ignore this email.</p>
        </body>
        </html>
        """

        # send email
        yag.send(to=email, subject=subject, contents=body)
        return True, "Verification email sent successfully"

    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False, f"Error sending email: {e}"


def send_password_reset_email(email, username, token):
    """Send password reset link to user"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            print("Email credentials not configured")
            return False, "Email service not configured"

        # initialize yagmail
        yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASSWORD)

        # create reset link
        reset_link = f"{APP_URL}/change-password?token={token}"

        # email content
        subject = "Reset your Bookmarkd password"
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi {username},</p>
            <p>We received a request to reset your password. Click the link below to create a new password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_link}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, you can safely ignore this email.</p>
        </body>
        </html>
        """

        # send email
        yag.send(to=email, subject=subject, contents=body)
        return True, "Password reset email sent successfully"

    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False, f"Error sending email: {e}"


def store_verification_token(user_id, token):
    """Store verification token in database with 24 hour expiry"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            expires_at = datetime.now() + timedelta(hours=24)
            sql = """
                UPDATE users 
                SET verification_token = %s, token_expires_at = %s 
                WHERE user_id = %s
            """
            cur.execute(sql, (token, expires_at, user_id))
            conn.commit()
            return True, "Token stored successfully"
    except Exception as e:
        print(f"Error storing verification token: {e}")
        return False, f"Error: {e}"


def store_reset_token(user_id, token):
    """Store password reset token in database with 1 hour expiry"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            expires_at = datetime.now() + timedelta(hours=1)
            sql = """
                UPDATE users 
                SET reset_password_token = %s, reset_token_expires_at = %s 
                WHERE user_id = %s
            """
            cur.execute(sql, (token, expires_at, user_id))
            conn.commit()
            return True, "Reset token stored successfully"
    except Exception as e:
        print(f"Error storing reset token: {e}")
        return False, f"Error: {e}"


def verify_email_token(token):
    """Verify email token and mark email as verified"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # check if token exists and hasn't expired
            sql = """
                SELECT user_id, username, token_expires_at 
                FROM users 
                WHERE verification_token = %s
            """
            cur.execute(sql, (token,))
            result = cur.fetchone()

            if not result:
                return False, "Invalid verification token"

            # check if token expired
            if result['token_expires_at'] < datetime.now():
                return False, "Verification link has expired"

            # mark email as verified and clear token
            update_sql = """
                UPDATE users 
                SET email_verified = true, 
                    verification_token = NULL, 
                    token_expires_at = NULL 
                WHERE user_id = %s
            """
            cur.execute(update_sql, (result['user_id'],))
            conn.commit()

            return True, f"Email verified successfully for {result['username']}"

    except Exception as e:
        print(f"Error verifying email token: {e}")
        return False, f"Error: {e}"


def verify_reset_token(token):
    """Verify password reset token and return user_id if valid"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # check if token exists and hasn't expired
            sql = """
                SELECT user_id, reset_token_expires_at 
                FROM users 
                WHERE reset_password_token = %s
            """
            cur.execute(sql, (token,))
            result = cur.fetchone()

            if not result:
                return False, "Invalid reset token", None

            # check if token expired
            if result['reset_token_expires_at'] < datetime.now():
                return False, "Reset link has expired", None

            return True, "Token valid", result['user_id']

    except Exception as e:
        print(f"Error verifying reset token: {e}")
        return False, f"Error: {e}", None


def clear_reset_token(user_id):
    """Clear password reset token after successful password change"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            sql = """
                UPDATE users 
                SET reset_password_token = NULL, 
                    reset_token_expires_at = NULL 
                WHERE user_id = %s
            """
            cur.execute(sql, (user_id,))
            conn.commit()
            return True, "Reset token cleared"
    except Exception as e:
        print(f"Error clearing reset token: {e}")
        return False, f"Error: {e}"

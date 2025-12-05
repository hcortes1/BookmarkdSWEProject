"""
Debug Login Test
================
Simple test to verify login works outside of fixtures
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backend.login as login_backend


def test_direct_login_simple():
    """
    Test login directly without any fixtures
    """
    print("\n" + "="*60)
    print("DIRECT LOGIN TEST")
    print("="*60)
    
    username = "test_user_1"
    password = "TestPass123"
    
    print(f"\nAttempting login:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    
    # Call login directly
    success, message, user_data, remember_token = login_backend.login_user(
        username, password, remember_me=False
    )
    
    print(f"\nResult:")
    print(f"  Success: {success}")
    print(f"  Message: {message}")
    
    if user_data:
        print(f"  User ID: {user_data.get('user_id')}")
        print(f"  Username: {user_data.get('username')}")
        print(f"  Email: {user_data.get('email')}")
        print(f"  Email Verified: {user_data.get('email_verified')}")
    
    # Assertions
    assert success is True, f"Login should succeed but got: {message}"
    assert user_data is not None, "User data should not be None"
    assert user_data.get('username') == username, f"Username mismatch"
    
    print("\n✅ DIRECT LOGIN TEST PASSED!")
    print("="*60)


def test_check_password_hash():
    """
    Verify the password hashing works correctly
    """
    import hashlib
    
    print("\n" + "="*60)
    print("PASSWORD HASH TEST")
    print("="*60)
    
    password = "TestPass123"
    expected_hash = "c1b8b58c3e7ac442b525e87709d5c1aef49a5d5acb70551be645887a978e238a"
    
    # Use the same hash function as backend
    actual_hash = hashlib.sha256(password.encode()).hexdigest()
    
    print(f"\nPassword: {password}")
    print(f"Expected hash: {expected_hash}")
    print(f"Actual hash:   {actual_hash}")
    
    assert actual_hash == expected_hash, "Password hash mismatch!"
    
    print("\n✅ PASSWORD HASH TEST PASSED!")
    print("="*60)


def test_database_query_direct():
    """
    Test direct database query to verify user exists
    """
    from backend.db import get_conn
    import hashlib
    
    print("\n" + "="*60)
    print("DATABASE QUERY TEST")
    print("="*60)
    
    username = "test_user_1"
    password = "TestPass123"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    print(f"\nQuerying database for:")
    print(f"  Username: {username}")
    print(f"  Password hash: {password_hash[:20]}...")
    
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, username, email, password
                    FROM users
                    WHERE username = %s
                """, (username,))
                
                user = cursor.fetchone()
                
                if user:
                    print(f"\n✓ User found!")
                    print(f"  User ID: {user[0]}")
                    print(f"  Username: {user[1]}")
                    print(f"  Email: {user[2]}")
                    print(f"  Password hash in DB: {user[3][:20]}...")
                    
                    # Check if password matches
                    if user[3] == password_hash:
                        print(f"\n✅ PASSWORD MATCHES!")
                    else:
                        print(f"\n❌ PASSWORD DOES NOT MATCH!")
                        print(f"  Expected: {password_hash}")
                        print(f"  Got:      {user[3]}")
                        assert False, "Password hash mismatch in database!"
                else:
                    print(f"\n❌ USER NOT FOUND!")
                    assert False, "test_user_1 not found in database!"
                    
    except Exception as e:
        print(f"\n❌ DATABASE ERROR: {e}")
        raise
    
    print("\n✅ DATABASE QUERY TEST PASSED!")
    print("="*60)


if __name__ == "__main__":
    # Run tests manually
    test_check_password_hash()
    test_database_query_direct()
    test_direct_login_simple()
    print("\n🎉 ALL DEBUG TESTS PASSED!")

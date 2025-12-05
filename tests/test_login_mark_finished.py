"""
TEST CASE 4: Login → Mark Book as Finished (with Review)
=========================================================

Test ID: TC004
Purpose: Verify that a user can successfully log in, add a book to bookshelf, 
         mark it as finished, and submit a review

EQUIVALENCE PARTITIONING:
-------------------------

Input 1: Username (Login)
- Valid username: test_user_1, test_user_2
- Invalid username: nonexistent_user
- Empty username: ""

Input 2: Password (Login)
- Valid password: TestPass123
- Invalid password: WrongPassword123
- Empty password: ""

Input 3: Book ID
- Valid book ID: 9999991-9999995
- Invalid book ID: 0, -1, 9999999999
- Non-integer: "abc", None

Input 4: Rating (Required for finished books)
- Valid ratings: 1, 2, 3, 4, 5
- Invalid ratings: 0, 6, 10, -1
- Non-integer: 3.5, "abc", None

Input 5: Review Text (Optional)
- Valid review: "Great book!", "Long review...", ""
- Empty review: ""
- Very long review: >1000 characters
- Special characters: HTML tags, SQL injection attempts

Input 6: Shelf Status
- Initial: 'plan-to-read' or 'reading'
- Final: 'completed'

Test Environment:
- Database: PostgreSQL (Supabase)
- Framework: Dash (Python)
- Test user: test_user_1 (email_verified=True)
- Test books: 9999991-9999995
"""

import pytest
import backend.login as login_backend
import backend.bookshelf as bookshelf_backend
import backend.reviews as reviews_backend


@pytest.mark.login
@pytest.mark.bookshelf
class TestLoginMarkBookFinished:
    """
    Test suite for Login → Mark Book as Finished with Review functionality
    """
    
    # =====================================================
    # TEST 1: Valid Login + Mark Book as Finished with Review
    # =====================================================
    
    def test_valid_login_mark_book_finished_with_review(self, test_user_credentials, test_books, cleanup_bookshelf):
        """
        Test ID: TC004-01
        Test: Complete workflow - Login, add book, mark as finished with review
        
        Input:
        - Username: test_user_1
        - Password: TestPass123
        - Book ID: 9999994
        - Rating: 5
        - Review: "This is an excellent test book!"
        
        Expected Result:
        - Login succeeds
        - Book added to bookshelf
        - Book marked as completed
        - Review saved successfully
        - Review appears when viewing book
        """
        # STEP 1: Login
        username = test_user_credentials['username']
        password = test_user_credentials['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        # ASSERT: Login successful
        assert success is True, f"Login failed: {message}"
        assert user_data is not None, "User data should not be None"
        user_id = user_data['user_id']
        
        # STEP 2: Add book to reading shelf first (realistic workflow)
        book_id = test_books['book_4']  # 9999994 - Test Book: Fantasy Realm
        
        add_success, add_message = bookshelf_backend.add_to_bookshelf(
            user_id=user_id,
            book_id=book_id,
            shelf_type='reading'
        )
        
        assert add_success is True, f"Failed to add book: {add_message}"
        
        # STEP 3: Mark book as completed (move to finished shelf)
        complete_success, complete_message = bookshelf_backend.update_shelf_status(
            user_id=user_id,
            book_id=book_id,
            new_status='completed'
        )
        
        assert complete_success is True, f"Failed to mark book as completed: {complete_message}"
        
        # STEP 4: Verify book is on completed shelf
        verify_success, verify_message, shelf_type = bookshelf_backend.get_book_shelf_status(
            user_id, book_id
        )
        
        assert verify_success is True, f"Failed to verify shelf: {verify_message}"
        assert shelf_type == 'completed', f"Book should be on 'completed' shelf, found '{shelf_type}'"
        
        # STEP 5: Submit review for the book
        rating = 5
        review_text = "This is an excellent test book! Highly recommend."
        
        review_success, review_message = reviews_backend.create_or_update_review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            review_text=review_text
        )
        
        # ASSERT: Review submitted successfully
        assert review_success is True, f"Failed to submit review: {review_message}"
        assert 'created' in review_message.lower() or 'updated' in review_message.lower(), \
            f"Success message should confirm review creation: {review_message}"
        
        print(f"\n✓ Book {book_id} marked as finished with {rating}-star review")
    
    # =====================================================
    # TEST 2: Invalid Login Prevents Book Completion
    # =====================================================
    
    def test_invalid_login_cannot_mark_finished(self, test_user_invalid_credentials):
        """
        Test ID: TC004-02
        Test: Invalid login credentials prevent marking book as finished
        
        Input:
        - Username: test_user_1
        - Password: WrongPassword123 (INVALID)
        
        Expected Result:
        - Login fails
        - Cannot mark books as finished without valid user_id
        """
        # STEP 1: Attempt login with wrong password
        username = test_user_invalid_credentials['username']
        password = test_user_invalid_credentials['password']
        
        success, message, user_data, remember_token = login_backend.login_user(
            username, password, remember_me=False
        )
        
        # ASSERT: Login should fail
        assert success is False, "Login should fail with invalid password"
        assert user_data is None, "User data should be None on failed login"
        
        # Cannot proceed with book operations without valid user_id
    
    # =====================================================
    # TEST 3: Mark Book Finished with Minimum Rating
    # =====================================================
    
    def test_mark_finished_with_minimum_rating(self, logged_in_user, test_books, cleanup_bookshelf):
        """
        Test ID: TC004-03
        Test: Mark book as finished with minimum valid rating (1 star)
        
        Input:
        - User: logged_in_user (valid)
        - Book ID: 9999995
        - Rating: 1 (minimum)
        - Review: "Not my favorite."
        
        Expected Result:
        - Book marked as completed
        - 1-star review accepted
        - Review saved correctly
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        book_id = test_books['book_5']  # 9999995
        
        # STEP 2: Add book and mark as completed
        bookshelf_backend.add_to_bookshelf(user_id, book_id, 'reading')
        bookshelf_backend.update_shelf_status(user_id, book_id, 'completed')
        
        # STEP 3: Submit 1-star review
        rating = 1
        review_text = "Not my favorite book."
        
        review_success, review_message = reviews_backend.create_or_update_review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            review_text=review_text
        )
        
        # ASSERT: 1-star review accepted
        assert review_success is True, f"Failed to submit 1-star review: {review_message}"
        
        print(f"\n✓ Book marked finished with minimum rating (1 star)")
    
    # =====================================================
    # TEST 4: Mark Book Finished with Maximum Rating
    # =====================================================
    
    def test_mark_finished_with_maximum_rating(self, logged_in_user, test_books, cleanup_bookshelf):
        """
        Test ID: TC004-04
        Test: Mark book as finished with maximum valid rating (5 stars)
        
        Input:
        - User: logged_in_user (valid)
        - Book ID: 9999991
        - Rating: 5 (maximum)
        - Review: "Absolutely amazing!"
        
        Expected Result:
        - Book marked as completed
        - 5-star review accepted
        - Review saved correctly
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        book_id = test_books['book_1']  # 9999991
        
        # STEP 2: Add book and mark as completed
        bookshelf_backend.add_to_bookshelf(user_id, book_id, 'reading')
        bookshelf_backend.update_shelf_status(user_id, book_id, 'completed')
        
        # STEP 3: Submit 5-star review
        rating = 5
        review_text = "Absolutely amazing! Best book ever!"
        
        review_success, review_message = reviews_backend.create_or_update_review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            review_text=review_text
        )
        
        # ASSERT: 5-star review accepted
        assert review_success is True, f"Failed to submit 5-star review: {review_message}"
        
        print(f"\n✓ Book marked finished with maximum rating (5 stars)")
    
    # =====================================================
    # TEST 5: Mark Finished with Invalid Rating
    # =====================================================
    
    def test_mark_finished_with_invalid_rating(self, logged_in_user, test_books, cleanup_bookshelf):
        """
        Test ID: TC004-05
        Test: Attempting to submit review with invalid rating (out of range)
        
        Input:
        - User: logged_in_user (valid)
        - Book ID: 9999992
        - Rating: 6 (INVALID - out of range)
        - Review: "Good book"
        
        Expected Result:
        - Review submission fails OR succeeds with validation
        - Error message indicates invalid rating
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        book_id = test_books['book_2']  # 9999992
        
        # STEP 2: Add book and mark as completed
        bookshelf_backend.add_to_bookshelf(user_id, book_id, 'reading')
        bookshelf_backend.update_shelf_status(user_id, book_id, 'completed')
        
        # STEP 3: Attempt to submit review with invalid rating
        rating = 6  # Invalid - should be 1-5
        review_text = "Good book"
        
        review_success, review_message = reviews_backend.create_or_update_review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            review_text=review_text
        )
        
        # ASSERT: Document behavior - should fail validation
        print(f"\nInvalid rating (6) result: {review_success}, {review_message}")
        
        # Note: This test documents whether backend validates rating range
        # Expected: review_success should be False with validation error
    
    # =====================================================
    # TEST 6: Mark Finished with Empty Review
    # =====================================================
    
    def test_mark_finished_with_empty_review(self, logged_in_user, test_books, cleanup_bookshelf):
        """
        Test ID: TC004-06
        Test: Mark book as finished with rating only (no review text)
        
        Input:
        - User: logged_in_user (valid)
        - Book ID: 9999993
        - Rating: 4
        - Review: "" (EMPTY)
        
        Expected Result:
        - Book marked as completed
        - Review with rating only is accepted (review text is optional)
        - Database stores empty string or NULL for review text
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        book_id = test_books['book_3']  # 9999993
        
        # STEP 2: Add book and mark as completed
        bookshelf_backend.add_to_bookshelf(user_id, book_id, 'reading')
        bookshelf_backend.update_shelf_status(user_id, book_id, 'completed')
        
        # STEP 3: Submit review with empty text
        rating = 4
        review_text = ""  # Empty review text
        
        review_success, review_message = reviews_backend.create_or_update_review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            review_text=review_text
        )
        
        # ASSERT: Review accepted with empty text (rating only)
        assert review_success is True, f"Failed to submit review with empty text: {review_message}"
        
        print(f"\n✓ Book marked finished with rating only (no review text)")
    
    # =====================================================
    # TEST 7: Update Existing Review
    # =====================================================
    
    def test_update_existing_review(self, logged_in_user, test_books, cleanup_bookshelf):
        """
        Test ID: TC004-07
        Test: User can update their existing review for a completed book
        
        Input:
        - User: logged_in_user (valid)
        - Book ID: 9999991
        - Initial Rating: 3, Review: "It was okay"
        - Updated Rating: 5, Review: "Actually, it was amazing!"
        
        Expected Result:
        - Initial review created successfully
        - Updated review replaces old review
        - Only one review exists per user per book
        """
        # STEP 1: User is already logged in
        user_id = logged_in_user['user_id']
        book_id = test_books['book_1']  # 9999991
        
        # STEP 2: Add book and mark as completed
        bookshelf_backend.add_to_bookshelf(user_id, book_id, 'reading')
        bookshelf_backend.update_shelf_status(user_id, book_id, 'completed')
        
        # STEP 3: Submit initial review
        initial_rating = 3
        initial_review = "It was okay, nothing special."
        
        initial_success, initial_message = reviews_backend.create_or_update_review(
            user_id=user_id,
            book_id=book_id,
            rating=initial_rating,
            review_text=initial_review
        )
        
        assert initial_success is True, f"Failed to create initial review: {initial_message}"
        
        # STEP 4: Update review (change of heart!)
        updated_rating = 5
        updated_review = "Actually, after thinking about it, this book was amazing!"
        
        update_success, update_message = reviews_backend.create_or_update_review(
            user_id=user_id,
            book_id=book_id,
            rating=updated_rating,
            review_text=updated_review
        )
        
        # ASSERT: Review updated successfully
        assert update_success is True, f"Failed to update review: {update_message}"
        assert 'updated' in update_message.lower(), \
            f"Message should indicate review was updated: {update_message}"
        
        print(f"\n✓ Review updated from {initial_rating} stars to {updated_rating} stars")


# =====================================================
# LIKELY BUGS / ISSUES TO WATCH FOR
# =====================================================
"""
Potential Bugs This Test May Reveal:

1. Rating Validation Issues:
   - Ratings outside 1-5 range accepted
   - Negative ratings allowed
   - Non-integer ratings (3.5) cause errors
   - Zero rating accepted

2. Review Text Validation:
   - Very long reviews cause database overflow
   - HTML/script tags not sanitized (XSS vulnerability)
   - SQL injection in review text
   - Emoji or special characters break database

3. Workflow Logic Errors:
   - Can submit review without marking book as completed
   - Can mark book as completed without review (if required)
   - Book remains in "reading" status after review
   - Duplicate reviews created instead of updating

4. Database Integrity:
   - Multiple reviews for same user/book combination
   - Orphaned reviews (book_id doesn't exist)
   - Foreign key constraint violations
   - Transaction rollback issues

5. Book Average Rating Update:
   - Book's average_rating not recalculated after review
   - Rating_count not incremented
   - Update review doesn't adjust average correctly
   - Deletion doesn't update averages

6. Permission Issues:
   - User can review books they haven't finished
   - User can review books not on their bookshelf
   - User can edit other users' reviews

7. Data Type Mismatches:
   - Rating stored as string instead of integer
   - Date fields in wrong format
   - NULL handling inconsistencies

8. Edge Cases:
   - Removing book from bookshelf orphans review
   - Re-adding book doesn't restore review
   - Concurrent review submissions create duplicates
"""
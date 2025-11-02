#!/usr/bin/env python3
"""
Backfill OpenLibrary keys for existing books in the database.

This script searches OpenLibrary for existing books that don't have openlibrary_key
populated and updates them with the correct keys for future duplicate prevention.
"""

import psycopg2.extras
from backend.openlibrary import OpenLibraryAPI
from backend.db import get_conn
import sys
import os
import re
import time
from typing import List, Dict, Any, Optional

# Add the backend directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def normalize_title(title: str) -> str:
    """Normalize title for comparison (remove punctuation, lowercase)"""
    return re.sub(r'[^a-zA-Z0-9]', '', title.lower())


def find_best_match(book_title: str, author_name: str, search_results: List[Dict[str, Any]]) -> Optional[str]:
    """
    Find the best matching work from search results.
    Returns the OpenLibrary key if a good match is found.
    """
    normalized_book_title = normalize_title(book_title)

    best_match = None
    best_score = 0

    for result in search_results:
        result_title = result.get('title', '')
        normalized_result_title = normalize_title(result_title)

        # Exact title match gets highest score
        if normalized_book_title == normalized_result_title:
            score = 100
        # Partial match gets lower score
        elif normalized_book_title in normalized_result_title or normalized_result_title in normalized_book_title:
            score = 50
        else:
            continue

        # Boost score if author matches
        result_authors = result.get('author_names', [])
        if author_name and any(author_name.lower() in author.lower() for author in result_authors):
            score += 25

        if score > best_score:
            best_score = score
            best_match = result.get('key')

    # Only return a match if we're reasonably confident (score > 50)
    return best_match if best_score > 50 else None


def backfill_book_keys():
    """Main function to backfill OpenLibrary keys for existing books."""
    print("Starting OpenLibrary key backfill for existing books...")

    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get all books that don't have an openlibrary_key
            cur.execute("""
                SELECT b.book_id, b.title, a.name as author_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                WHERE b.openlibrary_key IS NULL OR b.openlibrary_key = ''
                ORDER BY b.book_id
            """)

            books_to_update = cur.fetchall()
            print(
                f"Found {len(books_to_update)} books that need OpenLibrary keys")

            if not books_to_update:
                print(
                    "No books need backfilling. All books already have OpenLibrary keys.")
                return

            updated_count = 0
            error_count = 0

            for book in books_to_update:
                book_id = book['book_id']
                title = book['title']
                author_name = book['author_name'] or ''

                print(f"Processing book {book_id}: '{title}' by {author_name}")

                try:
                    # Construct search query
                    if author_name:
                        search_query = f'"{title}" author:"{author_name}"'
                    else:
                        search_query = f'"{title}"'

                    # Search OpenLibrary
                    search_results = OpenLibraryAPI.search_books(
                        search_query, limit=5)

                    if not search_results:
                        print(f"  No search results found for: {search_query}")
                        error_count += 1
                        continue

                    # Find best match
                    best_key = find_best_match(
                        title, author_name, search_results)

                    if best_key:
                        # Update the book with the OpenLibrary key (strip /works/ prefix)
                        clean_key = best_key.replace('/works/', '')
                        cur.execute("""
                            UPDATE books
                            SET openlibrary_key = %s
                            WHERE book_id = %s
                        """, (clean_key, book_id))

                        conn.commit()
                        updated_count += 1
                        print(f"  ✓ Updated with key: {clean_key}")
                    else:
                        print(
                            f"  ✗ No good match found among {len(search_results)} results")
                        error_count += 1

                except Exception as e:
                    print(f"  ✗ Error processing book {book_id}: {e}")
                    error_count += 1

                except Exception as e:
                    print(f"  ✗ Error processing book {book_id}: {e}")
                    error_count += 1

                # Small delay to be respectful to the API
                time.sleep(0.5)

            print("\nBackfill completed!")
            print(f"Updated: {updated_count} books")
            print(f"Errors: {error_count} books")
            print(f"Total processed: {len(books_to_update)} books")

    except Exception as e:
        print(f"Error during backfill: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    backfill_book_keys()

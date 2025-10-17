# backend/openlibrary.py
import requests
import json
import re
from typing import List, Dict, Any, Optional
import psycopg2
import psycopg2.extras
from .db import get_conn
import logging
import concurrent.futures
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenLibraryAPI:
    BASE_URL = "https://openlibrary.org"
    COVERS_URL = "https://covers.openlibrary.org"

    @staticmethod
    def search_books(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for books using Open Library API"""
        try:
            url = f"{OpenLibraryAPI.BASE_URL}/search.json"
            params = {
                'q': query,
                'limit': limit,
                'fields': 'key,title,author_name,author_key,first_publish_year,cover_i,isbn,subject,publisher'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            books = []

            for doc in data.get('docs', []):
                book = {
                    'key': doc.get('key'),
                    'title': doc.get('title', 'Unknown Title'),
                    'author_names': doc.get('author_name', []),
                    'author_keys': doc.get('author_key', []),
                    'first_publish_year': doc.get('first_publish_year'),
                    'cover_id': doc.get('cover_i'),
                    'isbn': doc.get('isbn', []),
                    'subjects': doc.get('subject', []),
                    'publishers': doc.get('publisher', []),
                    'source': 'openlibrary'
                }

                # Generate cover URL if available
                if book['cover_id']:
                    book['cover_url'] = f"{OpenLibraryAPI.COVERS_URL}/b/id/{book['cover_id']}-M.jpg"
                else:
                    book['cover_url'] = None

                books.append(book)

            return books

        except Exception as e:
            logger.error(f"Error searching books: {e}")
            return []

    @staticmethod
    def search_authors(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for authors using Open Library API"""
        try:
            url = f"{OpenLibraryAPI.BASE_URL}/search/authors.json"
            params = {
                'q': query,
                'limit': limit
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            authors = []

            for doc in data.get('docs', []):
                author = {
                    'key': doc.get('key'),
                    'name': doc.get('name', 'Unknown Author'),
                    'birth_date': doc.get('birth_date'),
                    'death_date': doc.get('death_date'),
                    'bio': doc.get('bio'),
                    'work_count': doc.get('work_count', 0),
                    'top_work': doc.get('top_work'),
                    'source': 'openlibrary'
                }

                # Generate author image URL if available
                if doc.get('key'):
                    olid = doc['key'].replace('/authors/', '')
                    author['image_url'] = f"{OpenLibraryAPI.COVERS_URL}/a/olid/{olid}-M.jpg"
                else:
                    author['image_url'] = None

                authors.append(author)

            return authors

        except Exception as e:
            logger.error(f"Error searching authors: {e}")
            return []

    @staticmethod
    @staticmethod
    def get_enhanced_book_details(book_key: str) -> Optional[Dict[str, Any]]:
        """Get enhanced book information focusing on series detection and core metadata"""
        try:
            # book_key comes in format like "/works/OL123W" - use it directly
            url = f"{OpenLibraryAPI.BASE_URL}{book_key}.json"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            work_data = response.json()

            # Get basic work info
            book_info = {
                'key': work_data.get('key'),
                'title': work_data.get('title', 'Unknown Title'),
                'subjects': work_data.get('subjects', []),
                'authors': work_data.get('authors', [])
            }

            # Get description
            description = ""
            if isinstance(work_data.get('description'), dict):
                description = work_data['description'].get('value', '')
            elif isinstance(work_data.get('description'), str):
                description = work_data['description']
            book_info['description'] = description

            # Check for cover from work data first
            if work_data.get('covers') and work_data['covers']:
                cover_id = work_data['covers'][0]
                book_info['cover_url'] = f"{OpenLibraryAPI.COVERS_URL}/b/id/{cover_id}-L.jpg"
                book_info['cover_id'] = cover_id

            # Get editions data for additional metadata
            editions_url = f"{OpenLibraryAPI.BASE_URL}{book_key}/editions.json"
            try:
                editions_response = requests.get(editions_url, timeout=10)
                if editions_response.status_code == 200:
                    editions_data = editions_response.json()

                    # Extract basic data from editions
                    original_language = None
                    earliest_date = None

                    for edition in editions_data.get('entries', []):
                        # Cover images - prioritize covers from editions
                        if not book_info.get('cover_url'):
                            # Check for cover in edition
                            if edition.get('covers') and edition['covers']:
                                cover_id = edition['covers'][0]
                                book_info['cover_url'] = f"{OpenLibraryAPI.COVERS_URL}/b/id/{cover_id}-L.jpg"
                                book_info['cover_id'] = cover_id

                        # Track language from earliest edition (likely original language)
                        if edition.get('languages') and edition.get('publish_date'):
                            try:
                                pub_date = edition['publish_date']
                                if not earliest_date or pub_date < earliest_date:
                                    earliest_date = pub_date
                                    languages = edition['languages']
                                    if isinstance(languages, list) and languages:
                                        lang_key = languages[0].get(
                                            'key', '/languages/en')
                                        original_language = lang_key.replace(
                                            '/languages/', '')
                            except:
                                pass

                        # Page count
                        if not book_info.get('page_count') and edition.get('number_of_pages'):
                            book_info['page_count'] = edition['number_of_pages']

                        # ISBNs
                        if not book_info.get('isbn_10') and edition.get('isbn_10'):
                            book_info['isbn_10'] = edition['isbn_10']
                        if not book_info.get('isbn_13') and edition.get('isbn_13'):
                            book_info['isbn_13'] = edition['isbn_13']

                        # Publication date
                        if not book_info.get('publish_date') and edition.get('publish_date'):
                            book_info['publish_date'] = edition['publish_date']

                    # Set language to original language if found, otherwise fallback logic
                    if original_language:
                        book_info['language'] = original_language
                    elif not book_info.get('language'):
                        # Fallback: look for any language in any edition
                        for edition in editions_data.get('entries', [])[:5]:
                            if edition.get('languages'):
                                languages = edition['languages']
                                if isinstance(languages, list) and languages:
                                    lang_key = languages[0].get(
                                        'key', '/languages/en')
                                    book_info['language'] = lang_key.replace(
                                        '/languages/', '')
                                    break

                    # Set defaults
                    book_info.setdefault('language', 'en')
                    book_info.setdefault('page_count', None)

            except Exception as e:
                logger.warning(f"Could not fetch editions for {book_key}: {e}")

            return book_info

        except Exception as e:
            logger.error(f"Error getting enhanced book details: {e}")
            return None

    @staticmethod
    def get_book_details(book_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed book information from Open Library"""
        try:
            # book_key comes in format like "/works/OL123W" - use it directly
            url = f"{OpenLibraryAPI.BASE_URL}{book_key}.json"
            print(f"DEBUG: Requesting book details from URL: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Get additional details like description
            description = ""
            if isinstance(data.get('description'), dict):
                description = data['description'].get('value', '')
            elif isinstance(data.get('description'), str):
                description = data['description']

            # Try to get more detailed publication info from editions
            isbn_10 = data.get('isbn_10', [])
            isbn_13 = data.get('isbn_13', [])
            publish_date = data.get('publish_date')
            first_publish_date = data.get('first_publish_date')

            # If no ISBNs or dates found in work, try to get from editions
            if not isbn_10 and not isbn_13 and not publish_date:
                try:
                    # Get editions to find ISBN and publication details
                    editions_url = f"{OpenLibraryAPI.BASE_URL}{book_key}/editions.json"
                    editions_response = requests.get(editions_url, timeout=10)
                    if editions_response.status_code == 200:
                        editions_data = editions_response.json()

                        # Extract ISBNs and dates from first few editions
                        for edition in editions_data.get('entries', [])[:5]:
                            if not isbn_10 and edition.get('isbn_10'):
                                isbn_10 = edition['isbn_10']
                            if not isbn_13 and edition.get('isbn_13'):
                                isbn_13 = edition['isbn_13']
                            if not publish_date and edition.get('publish_date'):
                                publish_date = edition['publish_date']

                            # Stop if we have what we need
                            if isbn_10 and isbn_13 and publish_date:
                                break
                except Exception as e:
                    print(
                        f"DEBUG: Could not fetch editions for {book_key}: {e}")

            return {
                'key': data.get('key'),
                'title': data.get('title', 'Unknown Title'),
                'description': description,
                'subjects': data.get('subjects', []),
                'publish_date': publish_date,
                'first_publish_date': first_publish_date,
                'publishers': data.get('publishers', []),
                'isbn_10': isbn_10,
                'isbn_13': isbn_13,
                'number_of_pages': data.get('number_of_pages'),
                'authors': data.get('authors', [])
            }

        except Exception as e:
            logger.error(f"Error getting book details: {e}")
            return None

    @staticmethod
    def get_author_details(author_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed author information from Open Library"""
        try:
            # author_key comes in format like "OL108452A" or "/authors/OL108452A"
            # Clean it to just get the ID
            if author_key.startswith('/authors/'):
                author_id = author_key.replace('/authors/', '')
            else:
                author_id = author_key

            url = f"{OpenLibraryAPI.BASE_URL}/authors/{author_id}.json"
            print(f"DEBUG: Requesting author details from URL: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Handle bio field which can be a string or dict
            bio = ""
            if isinstance(data.get('bio'), dict):
                bio = data['bio'].get('value', '')
            elif isinstance(data.get('bio'), str):
                bio = data['bio']

            # Generate author image URL using OLID (more reliable than photo ID)
            image_url = None
            if data.get('key'):
                olid = data['key'].replace('/authors/', '')
                image_url = f"{OpenLibraryAPI.COVERS_URL}/a/olid/{olid}-M.jpg"
            elif author_id:
                # Fallback to using the cleaned author_id
                image_url = f"{OpenLibraryAPI.COVERS_URL}/a/olid/{author_id}-M.jpg"

            return {
                'key': data.get('key'),
                'name': data.get('name', 'Unknown Author'),
                'bio': bio,
                'birth_date': data.get('birth_date'),
                'death_date': data.get('death_date'),
                'wikipedia': data.get('wikipedia'),
                'website': data.get('website'),
                'image_url': image_url  # Add image URL
            }

        except Exception as e:
            logger.error(f"Error getting author details: {e}")
            return None


def save_author_to_db(author_data: Dict[str, Any]) -> Optional[int]:
    """Save author to database if not already exists"""
    print(f"DEBUG: save_author_to_db called with: {author_data}")

    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check if author already exists by name
            cur.execute(
                "SELECT author_id FROM authors WHERE LOWER(name) = LOWER(%s)",
                (author_data['name'],)
            )
            existing = cur.fetchone()

            if existing:
                print(
                    f"DEBUG: Author already exists with ID: {existing['author_id']}")
                return existing['author_id']

            # Parse dates
            birth_date = None
            death_date = None

            if author_data.get('birth_date'):
                try:
                    # Handle various date formats from Open Library
                    birth_str = str(author_data['birth_date']).strip()
                    if birth_str:
                        # Try to extract year from various formats
                        import re
                        year_match = re.search(r'\b(\d{4})\b', birth_str)
                        if year_match:
                            year = year_match.group(1)
                            birth_date = f"{year}-01-01"  # Default to Jan 1
                except Exception as e:
                    logger.error(
                        f"Error parsing birth date '{author_data.get('birth_date')}': {e}")
                    pass

            if author_data.get('death_date'):
                try:
                    death_str = str(author_data['death_date']).strip()
                    if death_str:
                        # Try to extract year from various formats
                        import re
                        year_match = re.search(r'\b(\d{4})\b', death_str)
                        if year_match:
                            year = year_match.group(1)
                            death_date = f"{year}-01-01"
                except Exception as e:
                    logger.error(
                        f"Error parsing death date '{author_data.get('death_date')}': {e}")
                    pass

            # Insert new author
            insert_sql = """
                INSERT INTO authors (name, bio, birth_date, death_date, nationality, author_image_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING author_id
            """

            print(
                f"DEBUG: Inserting author with data: name={author_data['name']}, bio={author_data.get('bio', '')[:50]}..., birth_date={birth_date}, death_date={death_date}, image_url={author_data.get('image_url')}")

            cur.execute(insert_sql, (
                author_data['name'],
                author_data.get('bio', ''),
                birth_date,
                death_date,
                None,  # nationality not available from Open Library
                author_data.get('image_url')  # author image URL
            ))

            result = cur.fetchone()
            conn.commit()

            print(
                f"DEBUG: Author saved successfully with ID: {result['author_id'] if result else None}")

            return result['author_id'] if result else None

    except Exception as e:
        logger.error(f"Error saving author to database: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_enhanced_book_to_db(book_data: Dict[str, Any], author_id: int = None) -> Optional[int]:
    """Save book with enhanced data to database, ensuring ISBN uniqueness and filtering duplicates"""
    try:
        # Filter out unwanted books first
        title = book_data.get('title', '').strip()

        # Skip books with problematic titles
        skip_keywords = [
            'untitled', 'series collection', 'box set', 'book set',
            'complete series', 'omnibus', 'anthology'
        ]

        if any(keyword in title.lower() for keyword in skip_keywords):
            print(
                f"DEBUG: Skipping book '{title}' - contains unwanted keywords")
            return None

        # Skip very short or empty titles
        if len(title) < 3:
            print(f"DEBUG: Skipping book '{title}' - title too short")
            return None

        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check for similar titles by normalizing them
            # Remove spaces, punctuation, and convert to lowercase for comparison
            normalized_current = re.sub(r'[^a-zA-Z0-9]', '', title.lower())

            print(
                f"DEBUG: Checking for duplicates of '{title}' (normalized: '{normalized_current}')")

            if author_id:
                # For same author, look for titles that normalize to the same string
                cur.execute("""
                    SELECT book_id, title, description, release_date, genre
                    FROM books 
                    WHERE author_id = %s AND 
                          REGEXP_REPLACE(LOWER(title), '[^a-zA-Z0-9]', '', 'g') = %s
                """, (author_id, normalized_current))
            else:
                # For different/unknown authors, be more strict
                cur.execute("""
                    SELECT book_id, title, description, release_date, genre
                    FROM books 
                    WHERE REGEXP_REPLACE(LOWER(title), '[^a-zA-Z0-9]', '', 'g') = %s
                """, (normalized_current,))

            similar_books = cur.fetchall()

            print(
                f"DEBUG: Found {len(similar_books)} similar books for '{title}'")
            for book in similar_books:
                print(f"DEBUG: Similar book: '{book['title']}'")

            # If we found similar books, apply deduplication logic
            if similar_books:
                current_description = book_data.get('description', '').strip()
                current_release_date = book_data.get('release_date')
                current_subjects = book_data.get('subjects', [])
                current_genre_count = len(
                    [s for s in current_subjects if s]) if current_subjects else 0

                print(
                    f"DEBUG: Current book - description: {bool(current_description)}, release_date: {current_release_date}, genres: {current_genre_count}")

                for similar_book in similar_books:
                    existing_description = similar_book.get(
                        'description', '').strip()
                    existing_release_date = similar_book.get('release_date')
                    existing_genres = similar_book.get('genre', '').split(
                        ',') if similar_book.get('genre') else []
                    existing_genre_count = len(
                        [g for g in existing_genres if g.strip()]) if existing_genres else 0

                    print(
                        f"DEBUG: Existing book '{similar_book['title']}' - description: {bool(existing_description)}, release_date: {existing_release_date}, genres: {existing_genre_count}")

                    # Rule 1: Keep the one with description if only one has it
                    if current_description and not existing_description:
                        print(
                            f"DEBUG: Current book '{title}' has description, existing doesn't - deleting existing book")
                        # Delete the existing book and continue with saving current
                        cur.execute(
                            "DELETE FROM books WHERE book_id = %s", (similar_book['book_id'],))
                        continue
                    elif existing_description and not current_description:
                        print(
                            f"DEBUG: Existing book '{similar_book['title']}' has description, current doesn't - skipping current")
                        return None

                    # Rule 2: If both or neither have descriptions, keep the older one
                    if current_release_date and existing_release_date:
                        if current_release_date > existing_release_date:
                            print(
                                f"DEBUG: Existing book '{similar_book['title']}' is older ({existing_release_date} vs {current_release_date}) - skipping current")
                            return None
                        elif current_release_date < existing_release_date:
                            print(
                                f"DEBUG: Current book '{title}' is older ({current_release_date} vs {existing_release_date}) - deleting existing")
                            cur.execute(
                                "DELETE FROM books WHERE book_id = %s", (similar_book['book_id'],))
                            continue
                        elif current_release_date == existing_release_date:
                            # Rule 3: Same release date, keep the one with more genres
                            if current_genre_count <= existing_genre_count:
                                print(
                                    f"DEBUG: Existing book '{similar_book['title']}' has more/same genres ({existing_genre_count} vs {current_genre_count}) - skipping current")
                                return None
                            else:
                                print(
                                    f"DEBUG: Current book '{title}' has more genres ({current_genre_count} vs {existing_genre_count}) - deleting existing")
                                cur.execute(
                                    "DELETE FROM books WHERE book_id = %s", (similar_book['book_id'],))
                                continue
                    elif existing_release_date and not current_release_date:
                        print(
                            f"DEBUG: Existing book '{similar_book['title']}' has release date, current doesn't - skipping current")
                        return None
                    elif current_release_date and not existing_release_date:
                        print(
                            f"DEBUG: Current book '{title}' has release date, existing doesn't - deleting existing")
                        cur.execute(
                            "DELETE FROM books WHERE book_id = %s", (similar_book['book_id'],))
                        continue
                    else:
                        # Neither has release date, compare genres
                        if current_genre_count <= existing_genre_count:
                            print(
                                f"DEBUG: Existing book '{similar_book['title']}' has more/same genres ({existing_genre_count} vs {current_genre_count}) - skipping current")
                            return None
                        else:
                            print(
                                f"DEBUG: Current book '{title}' has more genres ({current_genre_count} vs {existing_genre_count}) - deleting existing")
                            cur.execute(
                                "DELETE FROM books WHERE book_id = %s", (similar_book['book_id'],))
                            continue

            # Prepare ISBN for uniqueness check
            isbn = None
            if book_data.get('isbn_13'):
                isbn = book_data['isbn_13'][0] if isinstance(
                    book_data['isbn_13'], list) else book_data['isbn_13']
            elif book_data.get('isbn_10'):
                isbn = book_data['isbn_10'][0] if isinstance(
                    book_data['isbn_10'], list) else book_data['isbn_10']
            elif book_data.get('isbn'):
                isbn = book_data['isbn'][0] if isinstance(
                    book_data['isbn'], list) else book_data['isbn']

            # Check if book already exists by ISBN first (if available)
            existing = None
            if isbn:
                cur.execute(
                    "SELECT book_id FROM books WHERE isbn = %s", (isbn,))
                existing = cur.fetchone()

            # If no ISBN match, check by title and author
            if not existing:
                if author_id:
                    cur.execute(
                        "SELECT book_id FROM books WHERE LOWER(title) = LOWER(%s) AND author_id = %s",
                        (book_data['title'], author_id)
                    )
                else:
                    cur.execute(
                        "SELECT book_id FROM books WHERE LOWER(title) = LOWER(%s)",
                        (book_data['title'],)
                    )
                existing = cur.fetchone()

            subjects = book_data.get('subjects', [])
            # Store all genres as a comma-separated string for database compatibility
            # Filter out non-genre subjects like "Open Library Staff Picks", nyt: prefixes, etc.
            filtered_genres = []
            for subject in subjects:
                # Skip technical subjects and library-specific tags
                if any(skip in subject.lower() for skip in [
                    'nyt:', 'collection', 'open library', 'staff picks', 'protected daisy',
                    'accessible book', 'lending library', 'in library', 'internet archive',
                    'overdrive', 'library', 'ebook', 'kindle', 'epub'
                ]):
                    continue
                filtered_genres.append(subject)

            # Take the first 5 genres to avoid overwhelming the database
            genre = ', '.join(filtered_genres[:5]) if filtered_genres else None

            # Parse release date
            release_date = None
            date_fields = ['publish_date',
                           'first_publish_year', 'first_publish_date']
            for field in date_fields:
                if book_data.get(field) and not release_date:
                    try:
                        date_str = str(book_data[field]).strip()
                        if date_str:
                            year_match = re.search(r'\b(\d{4})\b', date_str)
                            if year_match:
                                year = year_match.group(1)
                                release_date = f"{year}-01-01"
                                break
                    except Exception as e:
                        logger.warning(
                            f"Error parsing date field {field}: {e}")

            # Generate cover URL
            cover_url = None
            if book_data.get('cover_id'):
                cover_url = f"{OpenLibraryAPI.COVERS_URL}/b/id/{book_data['cover_id']}-L.jpg"

            # Prepare core fields only (no ratings, external IDs, or classifications)
            language = book_data.get('language', 'en')
            page_count = book_data.get('page_count')

            if existing:
                print(
                    f"DEBUG: Updating existing book {existing['book_id']} with enhanced data")
                update_sql = """
                    UPDATE books 
                    SET isbn = COALESCE(NULLIF(%s, ''), isbn),
                        genre = COALESCE(NULLIF(%s, ''), genre),
                        release_date = COALESCE(%s, release_date),
                        description = COALESCE(NULLIF(%s, ''), description),
                        cover_url = COALESCE(NULLIF(%s, ''), cover_url),
                        language = COALESCE(NULLIF(%s, ''), language),
                        page_count = COALESCE(%s, page_count)
                    WHERE book_id = %s
                """

                cur.execute(update_sql, (
                    isbn, genre, release_date, book_data.get(
                        'description', ''), cover_url,
                    language, page_count, existing['book_id']
                ))
                conn.commit()
                return existing['book_id']
            else:
                print(f"DEBUG: Inserting new book with enhanced data")
                insert_sql = """
                    INSERT INTO books (title, isbn, genre, release_date, description, cover_url, author_id,
                                     language, page_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING book_id
                """

                cur.execute(insert_sql, (
                    book_data['title'], isbn, genre, release_date,
                    book_data.get('description', ''), cover_url, author_id,
                    language, page_count
                ))

                result = cur.fetchone()
                conn.commit()
                return result['book_id'] if result else None

    except Exception as e:
        logger.error(f"Error saving enhanced book to database: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_book_to_db(book_data: Dict[str, Any], author_id: int = None) -> Optional[int]:
    """Save book to database if not already exists"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check if book already exists by title and author
            if author_id:
                cur.execute(
                    "SELECT book_id FROM books WHERE LOWER(title) = LOWER(%s) AND author_id = %s",
                    (book_data['title'], author_id)
                )
            else:
                cur.execute(
                    "SELECT book_id FROM books WHERE LOWER(title) = LOWER(%s)",
                    (book_data['title'],)
                )
            existing = cur.fetchone()

            if existing:
                print(
                    f"DEBUG: Book already exists with ID: {existing['book_id']}")
                # If this is an API book with additional data, update the existing record
                if book_data.get('source') == 'openlibrary':
                    print(f"DEBUG: Updating existing book with new API data")
                    update_sql = """
                        UPDATE books 
                        SET isbn = COALESCE(NULLIF(%s, ''), isbn),
                            genre = COALESCE(NULLIF(%s, ''), genre),
                            release_date = COALESCE(%s, release_date),
                            description = COALESCE(NULLIF(%s, ''), description),
                            cover_url = COALESCE(NULLIF(%s, ''), cover_url)
                        WHERE book_id = %s
                    """

                    # Prepare data for update
                    isbn = None
                    if book_data.get('isbn_13'):
                        isbn = book_data['isbn_13'][0] if book_data['isbn_13'] else None
                    elif book_data.get('isbn_10'):
                        isbn = book_data['isbn_10'][0] if book_data['isbn_10'] else None
                    elif book_data.get('isbn'):
                        isbn = book_data['isbn'][0] if book_data['isbn'] else None

                    subjects = book_data.get('subjects', [])
                    genre = subjects[0] if subjects else None

                    # Parse release date
                    release_date = None
                    date_fields = ['publish_date',
                                   'first_publish_year', 'first_publish_date']
                    for field in date_fields:
                        if book_data.get(field) and not release_date:
                            try:
                                date_str = str(book_data[field]).strip()
                                if date_str:
                                    import re
                                    year_match = re.search(
                                        r'\b(\d{4})\b', date_str)
                                    if year_match:
                                        year = year_match.group(1)
                                        release_date = f"{year}-01-01"
                                        break
                            except Exception:
                                continue

                    cur.execute(update_sql, (
                        isbn,
                        genre,
                        release_date,
                        book_data.get('description', ''),
                        book_data.get('cover_url'),
                        existing['book_id']
                    ))
                    conn.commit()
                    print(
                        f"DEBUG: Updated existing book {existing['book_id']} with API data")

                return existing['book_id']

            # Prepare data for insertion
            title = book_data.get('title', 'Unknown Title')

            # Handle ISBN - prefer ISBN-13, then ISBN-10, then from isbn array
            isbn = None
            if book_data.get('isbn_13'):
                isbn = book_data['isbn_13'][0] if book_data['isbn_13'] else None
            elif book_data.get('isbn_10'):
                isbn = book_data['isbn_10'][0] if book_data['isbn_10'] else None
            elif book_data.get('isbn'):
                isbn = book_data['isbn'][0] if book_data['isbn'] else None

            # Get genre from subjects
            subjects = book_data.get('subjects', [])
            genre = subjects[0] if subjects else None

            # Parse release date - try multiple date fields
            release_date = None

            # Try different date fields from Open Library
            date_fields = ['publish_date',
                           'first_publish_year', 'first_publish_date']
            for field in date_fields:
                if book_data.get(field) and not release_date:
                    try:
                        date_str = str(book_data[field]).strip()
                        if date_str:
                            # Extract year from various formats
                            import re
                            year_match = re.search(r'\b(\d{4})\b', date_str)
                            if year_match:
                                year = year_match.group(1)
                                # Default to Jan 1
                                release_date = f"{year}-01-01"
                                break
                    except Exception as e:
                        logger.error(
                            f"Error parsing date field {field} '{book_data.get(field)}': {e}")
                        continue

            description = book_data.get('description', '')
            cover_url = book_data.get('cover_url')

            print(
                f"DEBUG: Inserting book: title={title}, isbn={isbn}, release_date={release_date}, author_id={author_id}")

            # Insert new book
            insert_sql = """
                INSERT INTO books (title, isbn, genre, release_date, description, cover_url, author_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING book_id
            """

            cur.execute(insert_sql, (
                title,
                isbn,
                genre,
                release_date,
                description,
                cover_url,
                author_id
            ))

            result = cur.fetchone()
            conn.commit()

            print(
                f"DEBUG: Book saved successfully with ID: {result['book_id'] if result else None}")

            return result['book_id'] if result else None

    except Exception as e:
        logger.error(f"Error saving book to database: {e}")
        import traceback
        traceback.print_exc()
        return None


def search_books_and_authors(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Combined search function that searches both local database and Open Library API
    Returns both books and authors from both sources
    Excludes API authors that are already in the database
    """
    results = {
        'books': [],
        'authors': [],
        'users': []
    }

    existing_author_names = set()

    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Search local database for books
            cur.execute("""
                SELECT b.book_id, b.title, b.isbn, b.genre, b.release_date, 
                       b.description, b.cover_url, b.author_id,
                       a.name as author_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                WHERE LOWER(b.title) LIKE LOWER(%s)
                ORDER BY b.title
                LIMIT 5
            """, (f"%{query}%",))

            local_books = cur.fetchall()
            for book in local_books:
                book_dict = dict(book)
                book_dict['source'] = 'local'
                results['books'].append(book_dict)

            # Search local database for authors
            cur.execute("""
                SELECT a.author_id, a.name, a.bio, a.birth_date, a.death_date, a.nationality, 
                       a.author_image_url, a.created_at,
                       COUNT(b.book_id) as work_count
                FROM authors a
                LEFT JOIN books b ON a.author_id = b.author_id
                WHERE LOWER(a.name) LIKE LOWER(%s)
                GROUP BY a.author_id, a.name, a.bio, a.birth_date, a.death_date, 
                         a.nationality, a.author_image_url, a.created_at
                ORDER BY a.name
                LIMIT 5
            """, (f"%{query}%",))

            local_authors = cur.fetchall()
            for author in local_authors:
                author_dict = dict(author)
                author_dict['source'] = 'local'
                # Map author_image_url to image_url for consistency
                author_dict['image_url'] = author_dict.get('author_image_url')
                results['authors'].append(author_dict)
                existing_author_names.add(author_dict['name'].lower())

            # Get all author names from database to filter API results
            cur.execute("SELECT LOWER(name) as name FROM authors")
            all_existing = cur.fetchall()
            for row in all_existing:
                existing_author_names.add(row['name'])

    except Exception as e:
        logger.error(f"Error searching local database: {e}")

    # Search Open Library API for books
    api_books = OpenLibraryAPI.search_books(query, limit=5)
    results['books'].extend(api_books)

    # Search Open Library API for authors and filter out existing ones
    api_authors = OpenLibraryAPI.search_authors(
        query, limit=10)  # Get more to account for filtering

    filtered_api_authors = []
    for author in api_authors:
        author_name_lower = author.get('name', '').lower()
        if author_name_lower not in existing_author_names:
            filtered_api_authors.append(author)
            if len(filtered_api_authors) >= 5:  # Limit API authors
                break

    results['authors'].extend(filtered_api_authors)

    return results


def search_books_only(query: str) -> List[Dict[str, Any]]:
    """
    Search for books only from both local database and Open Library API
    """
    books = []

    try:
        # Search local database
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT b.book_id, b.title, b.isbn, b.genre, b.release_date, 
                       b.description, b.cover_url, b.author_id,
                       a.name as author_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                WHERE LOWER(b.title) LIKE LOWER(%s)
                ORDER BY b.title
                LIMIT 5
            """, (f"%{query}%",))

            local_books = cur.fetchall()
            for book in local_books:
                book_dict = dict(book)
                book_dict['source'] = 'local'
                books.append(book_dict)

    except Exception as e:
        logger.error(f"Error searching local books: {e}")

    # Search Open Library API
    api_books = OpenLibraryAPI.search_books(query, limit=8)
    books.extend(api_books)

    return books


def search_authors_only(query: str) -> List[Dict[str, Any]]:
    """
    Search for authors only from both local database and Open Library API
    Excludes API authors that are already in the database
    """
    authors = []
    existing_author_names = set()

    try:
        # Search local database
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT a.author_id, a.name, a.bio, a.birth_date, a.death_date, a.nationality, 
                       a.author_image_url, a.created_at,
                       COUNT(b.book_id) as work_count
                FROM authors a
                LEFT JOIN books b ON a.author_id = b.author_id
                WHERE LOWER(a.name) LIKE LOWER(%s)
                GROUP BY a.author_id, a.name, a.bio, a.birth_date, a.death_date, 
                         a.nationality, a.author_image_url, a.created_at
                ORDER BY a.name
                LIMIT 5
            """, (f"%{query}%",))

            local_authors = cur.fetchall()
            for author in local_authors:
                author_dict = dict(author)
                author_dict['source'] = 'local'
                # Map author_image_url to image_url for consistency
                author_dict['image_url'] = author_dict.get('author_image_url')
                authors.append(author_dict)
                # Track existing author names (case-insensitive)
                existing_author_names.add(author_dict['name'].lower())

            # Also get all author names from database to filter API results
            cur.execute("SELECT LOWER(name) as name FROM authors")
            all_existing = cur.fetchall()
            for row in all_existing:
                existing_author_names.add(row['name'])

    except Exception as e:
        logger.error(f"Error searching local authors: {e}")

    # Search Open Library API and filter out existing authors
    api_authors = OpenLibraryAPI.search_authors(
        query, limit=15)  # Get more to account for filtering

    filtered_api_authors = []
    for author in api_authors:
        author_name_lower = author.get('name', '').lower()
        if author_name_lower not in existing_author_names:
            filtered_api_authors.append(author)
            # Limit to 8 total results after filtering
            if len(filtered_api_authors) >= 8:
                break

    authors.extend(filtered_api_authors)

    return authors


def fetch_work_details_with_retry(work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fetch enhanced work details with retry logic for concurrent processing
    Returns book_data dict with ratings, language, and other enhanced fields
    """
    work_key = work.get('key')
    if not work_key:
        return None

    # Get enhanced work details with ratings and metadata
    try:
        enhanced_details = OpenLibraryAPI.get_enhanced_book_details(work_key)
        if enhanced_details:
            # Add any missing fields and ensure proper structure
            enhanced_details['source'] = 'openlibrary'
            enhanced_details['key'] = work_key

            # Set default cover URL if not present
            if not enhanced_details.get('cover_url') and enhanced_details.get('cover_id'):
                enhanced_details['cover_url'] = f"{OpenLibraryAPI.COVERS_URL}/b/id/{enhanced_details['cover_id']}-L.jpg"

            return enhanced_details
        else:
            # Fallback to basic work details if enhanced fetch fails
            return fetch_basic_work_details(work_key)

    except Exception as e:
        logger.warning(f"Error fetching enhanced details for {work_key}: {e}")
        # Fallback to basic work details
        return fetch_basic_work_details(work_key)


def fetch_basic_work_details(work_key: str) -> Optional[Dict[str, Any]]:
    """
    Fallback function to fetch basic work details without enhancements
    """
    # Get work details with retry - optimized for speed
    work_details = None
    for attempt in range(2):  # Reduced to 2 attempts for speed
        try:
            work_url = f"{OpenLibraryAPI.BASE_URL}{work_key}.json"
            work_response = requests.get(
                work_url, timeout=10)  # Reduced timeout
            work_response.raise_for_status()
            work_details = work_response.json()
            break
        except Exception as e:
            if attempt < 1:
                time.sleep(0.2)  # Very short delay
            else:
                return None

    if not work_details:
        return None

    # Create book data from work
    book_data = {
        'title': work_details.get('title', 'Unknown Title'),
        'key': work_key,
        'description': '',
        'subjects': work_details.get('subjects', []),
        'first_publish_year': work_details.get('first_publish_date'),
        'first_publish_date': work_details.get('first_publish_date'),
        'publish_date': work_details.get('publish_date'),
        'isbn_10': work_details.get('isbn_10', []),
        'isbn_13': work_details.get('isbn_13', []),
        'cover_url': None,
        'source': 'openlibrary',
        # Default enhanced fields
        'average_rating': 0.0,
        'rating_count': 0,
        'language': 'en',
        'page_count': None
    }

    # Handle description
    if isinstance(work_details.get('description'), dict):
        book_data['description'] = work_details['description'].get('value', '')
    elif isinstance(work_details.get('description'), str):
        book_data['description'] = work_details['description']

    # Try to get cover from work
    if work_details.get('covers'):
        cover_id = work_details['covers'][0]
        book_data['cover_url'] = f"{OpenLibraryAPI.COVERS_URL}/b/id/{cover_id}-M.jpg"

    # Simplified editions check - for publication info and cover if missing
    if (not book_data['isbn_10'] and not book_data['isbn_13'] and
            not book_data['publish_date'] and not book_data['first_publish_date']) or not book_data['cover_url']:
        try:
            editions_url = f"{OpenLibraryAPI.BASE_URL}{work_key}/editions.json"
            editions_response = requests.get(
                editions_url, timeout=5)  # Very short timeout
            if editions_response.status_code == 200:
                editions_data = editions_response.json()
                # Only check first edition for speed
                if editions_data.get('entries'):
                    edition = editions_data['entries'][0]
                    if edition.get('isbn_10'):
                        book_data['isbn_10'] = edition['isbn_10']
                    if edition.get('isbn_13'):
                        book_data['isbn_13'] = edition['isbn_13']
                    if edition.get('publish_date'):
                        book_data['publish_date'] = edition['publish_date']
                    # Try to get cover from edition if work cover not found
                    if not book_data['cover_url'] and edition.get('covers'):
                        cover_id = edition['covers'][0]
                        book_data['cover_url'] = f"{OpenLibraryAPI.COVERS_URL}/b/id/{cover_id}-M.jpg"
        except Exception:
            pass  # Skip editions if it fails - speed is priority

    return book_data


def get_or_create_author_from_api(author_data: Dict[str, Any]) -> Optional[int]:
    """
    Get detailed author info from API and save to database
    Returns author_id
    """
    if not author_data.get('key'):
        return None

    # Get detailed author information
    detailed_author = OpenLibraryAPI.get_author_details(author_data['key'])
    if not detailed_author:
        return None

    # Merge the data
    merged_data = {**author_data, **detailed_author}

    return save_author_to_db(merged_data)


def get_or_create_author_with_books(author_data: Dict[str, Any]) -> Optional[int]:
    """
    Get detailed author info from API, save to database with all their books
    Uses bulk inserts and checks for existing authors by name and birth year
    Returns author_id
    """
    import time
    import re

    print(f"DEBUG: get_or_create_author_with_books called with: {author_data}")

    if not author_data.get('key'):
        print("DEBUG: No key found in author_data")
        return None

    # Get detailed author information
    detailed_author = OpenLibraryAPI.get_author_details(author_data['key'])
    if not detailed_author:
        print("DEBUG: Failed to get detailed author info")
        return None

    print(f"DEBUG: Got detailed author: {detailed_author}")

    # Merge the data
    merged_author_data = {**author_data, **detailed_author}

    # Extract birth year for matching
    birth_year = None
    if merged_author_data.get('birth_date'):
        try:
            birth_str = str(merged_author_data['birth_date']).strip()
            year_match = re.search(r'\b(\d{4})\b', birth_str)
            if year_match:
                birth_year = int(year_match.group(1))
        except Exception as e:
            logger.error(f"Error parsing birth date: {e}")

    # Check if author already exists by name and birth year
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if birth_year:
                cur.execute("""
                    SELECT author_id FROM authors 
                    WHERE LOWER(name) = LOWER(%s) 
                    AND EXTRACT(YEAR FROM birth_date) = %s
                """, (merged_author_data['name'], birth_year))
            else:
                cur.execute("""
                    SELECT author_id FROM authors 
                    WHERE LOWER(name) = LOWER(%s)
                """, (merged_author_data['name'],))

            existing = cur.fetchone()
            if existing:
                author_id = existing['author_id']
                print(f"DEBUG: Found existing author with ID: {author_id}")
            else:
                # Save new author
                author_id = save_author_to_db(merged_author_data)
                if not author_id:
                    print("DEBUG: Failed to save author to database")
                    return None
                print(f"DEBUG: Saved new author with ID: {author_id}")

    except Exception as e:
        logger.error(f"Error checking/saving author: {e}")
        return None

    # Get the author's works/books from Open Library with retry logic and pagination
    try:
        author_key = author_data['key']
        if author_key.startswith('/authors/'):
            author_id_clean = author_key.replace('/authors/', '')
        else:
            author_id_clean = author_key

        works_url = f"{OpenLibraryAPI.BASE_URL}/authors/{author_id_clean}/works.json"
        print(f"DEBUG: Requesting author works from URL: {works_url}")

        # Collect all works using pagination
        all_works = []
        offset = 0
        limit = 50  # Max per request

        while True:
            # Get works list with retry
            works_data = None
            for attempt in range(3):
                try:
                    params = {'limit': limit, 'offset': offset}
                    response = requests.get(
                        works_url, params=params, timeout=15)
                    response.raise_for_status()
                    works_data = response.json()
                    break
                except Exception as e:
                    print(
                        f"DEBUG: Attempt {attempt + 1} failed for offset {offset}: {e}")
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        raise

            if not works_data or not works_data.get('entries'):
                print(f"DEBUG: No more works found at offset {offset}")
                break

            current_works = works_data.get('entries', [])
            all_works.extend(current_works)

            print(
                f"DEBUG: Fetched {len(current_works)} works at offset {offset}, total so far: {len(all_works)}")

            # If we got fewer works than the limit, we've reached the end
            if len(current_works) < limit:
                print(
                    f"DEBUG: Reached end of works list, got {len(current_works)} < {limit}")
                break

            offset += limit
            # Small delay between requests to be respectful to the API
            time.sleep(0.5)

        print(f"DEBUG: Total works found: {len(all_works)}")

        if not all_works:
            print("DEBUG: No works data received")
            return author_id

        # Collect all book data before inserting using concurrent processing
        books_to_insert = []

        print(f"DEBUG: Processing {len(all_works)} works concurrently...")

        # Adaptive batch sizing based on total number of works - optimized for API limits
        if len(all_works) <= 100:
            batch_size = 30
            max_workers = 12
        elif len(all_works) <= 500:
            batch_size = 35
            max_workers = 15
        elif len(all_works) <= 1000:
            batch_size = 40
            max_workers = 18
        else:  # 1000+ works
            batch_size = 45
            max_workers = 20

        print(
            f"DEBUG: Using batch_size={batch_size}, max_workers={max_workers} for {len(all_works)} works (optimized for API limits)")

        # Process works in batches with concurrent requests
        for i in range(0, len(all_works), batch_size):
            batch = all_works[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(all_works) + batch_size - 1)//batch_size

            print(
                f"DEBUG: Processing batch {batch_num}/{total_batches} ({len(batch)} works) - {len(books_to_insert)} books collected so far")

            # Process this batch concurrently with retry for failed works
            batch_results = []
            failed_works = []

            # First attempt
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_work = {
                    executor.submit(fetch_work_details_with_retry, work): work
                    for work in batch
                }

                for future in as_completed(future_to_work):
                    work = future_to_work[future]
                    try:
                        book_data = future.result()
                        if book_data:
                            batch_results.append(book_data)
                        else:
                            failed_works.append(work)
                    except Exception as e:
                        print(
                            f"DEBUG: Failed to process work {work.get('key', 'unknown')}: {e}")
                        failed_works.append(work)

            # Retry failed works with smaller concurrency
            if failed_works:
                print(
                    f"DEBUG: Retrying {len(failed_works)} failed works from batch {batch_num}")
                retry_results = []

                with ThreadPoolExecutor(max_workers=min(10, max_workers//2)) as executor:
                    future_to_work = {
                        executor.submit(fetch_work_details_with_retry, work): work
                        for work in failed_works
                    }

                    for future in as_completed(future_to_work):
                        work = future_to_work[future]
                        try:
                            book_data = future.result()
                            if book_data:
                                retry_results.append(book_data)
                        except Exception as e:
                            print(
                                f"DEBUG: Final failure for work {work.get('key', 'unknown')}: {e}")

                batch_results.extend(retry_results)
                print(
                    f"DEBUG: Recovered {len(retry_results)} books from {len(failed_works)} failed works")

            books_to_insert.extend(batch_results)
            success_rate = len(batch_results) / len(batch) * 100
            print(
                f"DEBUG: Batch {batch_num} completed: +{len(batch_results)} books (total: {len(books_to_insert)}, success rate: {success_rate:.1f}%)")

            # Longer delay between batches to respect API limits
            if batch_num < total_batches:  # Don't delay after the last batch
                time.sleep(1.0)  # Increased delay to be more respectful to API

        # Bulk insert books
        if books_to_insert:
            print(f"DEBUG: Bulk inserting {len(books_to_insert)} books")
            bulk_insert_books(books_to_insert, author_id)

    except Exception as e:
        logger.error(f"Error fetching author's works: {e}")

    return author_id


def bulk_insert_books(books_data: List[Dict[str, Any]], author_id: int):
    """Bulk insert books with enhanced data into database, skipping duplicates with individual transactions"""
    try:
        successful_inserts = 0
        failed_inserts = 0

        for book_data in books_data:
            # Try to insert each book individually with retries
            for attempt in range(3):
                try:
                    # Use the enhanced save function
                    book_id = save_enhanced_book_to_db(book_data, author_id)

                    if book_id:
                        successful_inserts += 1
                        print(
                            f"DEBUG: Successfully saved book '{book_data['title'][:50]}...' with ID {book_id}")
                        break
                    else:
                        print(
                            f"DEBUG: Failed to save book '{book_data['title'][:50]}...' (attempt {attempt + 1})")
                        if attempt == 2:  # Last attempt
                            failed_inserts += 1
                        else:
                            time.sleep(0.5)  # Brief pause before retry

                except Exception as e:
                    print(
                        f"DEBUG: Error saving book '{book_data['title'][:50]}...' (attempt {attempt + 1}): {e}")
                    if attempt == 2:  # Last attempt
                        failed_inserts += 1
                    else:
                        time.sleep(0.5)  # Brief pause before retry

        print(
            f"DEBUG: Bulk insert completed. Successful: {successful_inserts}, Failed: {failed_inserts}")
        return successful_inserts, failed_inserts

    except Exception as e:
        logger.error(f"Error in bulk insert: {e}")
        return 0, len(books_data)


def get_or_create_book_from_api(book_data: Dict[str, Any]) -> Optional[int]:
    """
    Get detailed book info from API and save to database
    Returns book_id
    """
    if not book_data.get('key'):
        return None

    # Get detailed book information
    detailed_book = OpenLibraryAPI.get_book_details(book_data['key'])
    if detailed_book:
        # Merge the data
        book_data = {**book_data, **detailed_book}

    # Handle authors
    author_id = None
    if book_data.get('author_names') and book_data.get('author_keys'):
        # Use the first author
        first_author_name = book_data['author_names'][0]
        first_author_key = book_data['author_keys'][0]

        author_data = {
            'name': first_author_name,
            'key': first_author_key
        }

        author_id = get_or_create_author_from_api(author_data)

    return save_book_to_db(book_data, author_id)


def get_or_create_book_with_author_books(book_data: Dict[str, Any]) -> Optional[int]:
    """
    When a book is clicked from API results, import the author and all their books
    Similar to get_or_create_author_with_books but triggered from book click
    Returns book_id of the clicked book
    """
    print(
        f"DEBUG: get_or_create_book_with_author_books called with: {book_data}")

    # Extract author information from the book data
    author_keys = book_data.get('author_keys', [])
    author_names = book_data.get('author_names', [])

    if not author_keys or not author_names:
        print("DEBUG: No author keys or names found in book data")
        # Fall back to just saving the book
        return get_or_create_book_from_api(book_data)

    # Use the first author
    author_data = {
        'key': f"/authors/{author_keys[0]}" if not author_keys[0].startswith('/authors/') else author_keys[0],
        'name': author_names[0]
    }

    print(f"DEBUG: Importing author and all their books: {author_data}")

    # This will fetch the author and all their books from the API and store them
    author_id = get_or_create_author_with_books(author_data)

    if not author_id:
        print("DEBUG: Failed to import author, falling back to single book save")
        return get_or_create_book_from_api(book_data)

    # Now find the book we originally clicked on in the database
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT book_id FROM books 
                WHERE LOWER(title) = LOWER(%s) AND author_id = %s
                LIMIT 1
            """, (book_data['title'], author_id))

            result = cur.fetchone()
            if result:
                print(
                    f"DEBUG: Found clicked book in database with ID: {result['book_id']}")
                return result['book_id']
            else:
                print(
                    "DEBUG: Clicked book not found in database after import, falling back to single book save")
                return get_or_create_book_from_api(book_data)

    except Exception as e:
        logger.error(f"Error finding clicked book after author import: {e}")
        return get_or_create_book_from_api(book_data)

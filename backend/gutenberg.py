import requests
from bs4 import BeautifulSoup
from backend.settings import supabase
from backend.db import get_conn
from typing import List, Dict, Any


def search_gutenberg_books_by_author(author_name: str) -> List[Dict[str, Any]]:
    """
    Search Gutenberg for books by a specific author.
    Returns a list of book data dictionaries compatible with OpenLibrary format.
    """
    books = []

    try:
        # Search Gutenberg with author name
        search_query = author_name.replace(' ', '+')
        search_url = f"https://www.gutenberg.org/ebooks/search/?query={search_query}"

        response = requests.get(search_url, timeout=15)
        if response.status_code != 200:
            return books

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all ebook links
        ebook_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/ebooks/' in href:
                ebook_links.append((link, href))

        print(
            f"DEBUG GUTENBERG_search_gutenberg_books_by_author: Found {len(ebook_links)} potential Gutenberg books for {author_name}")

        # Process up to 20 books to get more results
        for link, href in ebook_links[:20]:
            try:
                # Get the surrounding text to extract title and author
                parent = link.parent
                if parent:
                    full_text = parent.get_text().strip()
                else:
                    full_text = link.get_text().strip()

                # Parse title and author from text
                # Gutenberg format is typically: "Title\nAuthor"
                lines = full_text.split('\n')
                title = lines[0].strip() if lines else link.get_text().strip()
                author = lines[1].strip() if len(lines) > 1 else ""

                # Check if this author matches - be more flexible
                author_lower = author.lower()
                author_name_lower = author_name.lower()

                # Check if author name components match (e.g., "William Shakespeare" should match "Shakespeare, William")
                author_parts = set(author_lower.replace(',', '').split())
                search_parts = set(author_name_lower.split())

                # If we have significant overlap in name parts, consider it a match
                overlap = len(author_parts.intersection(search_parts))
                name_match = overlap >= 1  # At least one name part matches

                # Also check if the full author name is contained in the search name or vice versa
                if not name_match:
                    name_match = (author_name_lower in author_lower or
                                  author_lower in author_name_lower or
                                  author_name_lower in full_text.lower())

                if not name_match:
                    continue

                # Get book details page
                book_url = "https://www.gutenberg.org" + href
                book_response = requests.get(book_url, timeout=10)
                if book_response.status_code != 200:
                    continue

                book_soup = BeautifulSoup(book_response.text, 'html.parser')

                # Extract metadata from the page
                book_data = {
                    'title': title,
                    # Use the searched author name
                    'author_names': [author_name],
                    'author_keys': [],  # Gutenberg doesn't have OL keys
                    'source': 'gutenberg',
                    'key': href  # Use the Gutenberg URL as key
                }

                # Try to extract additional metadata
                # Look for publication year, etc.
                page_text = book_soup.get_text()

                # Look for year patterns
                import re
                year_match = re.search(r'\b(18|19|20)\d{2}\b', page_text)
                if year_match:
                    book_data['first_publish_year'] = int(year_match.group())

                books.append(book_data)

            except Exception as e:
                print(f"Error processing Gutenberg book {href}: {e}")
                continue

    except Exception as e:
        print(f"Error searching Gutenberg for author {author_name}: {e}")

    print(
        f"DEBUG GUTENBERG_search_gutenberg_books_by_author: Found {len(books)} Gutenberg books for {author_name}")
    return books


def search_and_download_gutenberg_html(book_title, author_name, book_id):
    """
    Search for a book on Project Gutenberg by title, download its HTML version if available,
    upload to Supabase storage, and update the database with the path.
    """
    try:
        # Try different search queries
        search_queries = [
            book_title.replace(' ', '+'),  # Just title
            # Title + last name
            f"{book_title} {author_name.split()[-1]}".replace(' ', '+'),
            book_title.replace('The ', '').replace(
                ' ', '+'),  # Title without 'The'
            # Title without 'The' + last name
            f"{book_title.replace('The ', '')} {author_name.split()[-1]}".replace(
                ' ', '+'),
        ]

        book_url = None

        for search_query in search_queries:
            print(
                f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Trying search query: {search_query}")
            search_url = f"https://www.gutenberg.org/ebooks/search/?query={search_query}"

            response = requests.get(search_url, timeout=15)
            if response.status_code != 200:
                print(f"Failed to search Gutenberg with query {search_query}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Debug: print some links
            all_links = soup.find_all('a', href=True)
            ebook_links = [
                link for link in all_links if '/ebooks/' in link['href']]
            print(
                f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Found {len(ebook_links)} ebook links for query {search_query}")
            for i, link in enumerate(ebook_links[:3]):  # Show first 3
                print(
                    f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Link {i+1}: {link.get_text().strip()} -> {link['href']}")

            # Look for book links in the search results
            # Gutenberg search results might be in various formats
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if '/ebooks/' in href:
                    link_text = link.get_text().strip()
                    # Get surrounding text in case title is split
                    parent = link.parent
                    if parent:
                        full_text = parent.get_text().strip()
                    else:
                        full_text = link_text

                    # Check if book title matches (case insensitive, partial match)
                    if book_title.lower() in full_text.lower() or any(word in full_text.lower() for word in book_title.lower().split()):
                        book_url = "https://www.gutenberg.org" + href
                        print(
                            f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Found potential book link: {link_text} -> {book_url}")
                        # Additional check: look for author in nearby text
                        author_found = False
                        if author_name.lower() in full_text.lower():
                            author_found = True
                        else:
                            # Check sibling elements
                            for sibling in link.parent.find_next_siblings() if link.parent else []:
                                sib_text = sibling.get_text().strip().lower()
                                if author_name.lower() in sib_text:
                                    author_found = True
                                    break

                        if author_found or not author_name:  # If no author to check, accept
                            print(
                                f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Matched book: {full_text}")
                            break

            if book_url:
                break

        if not book_url:
            print(
                f"No matching book found on Gutenberg for {book_title} by {author_name}")
            return None

        print(
            f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Accessing book page: {book_url}")

        # Get the book page
        book_response = requests.get(book_url, timeout=15)
        if book_response.status_code != 200:
            print(f"Failed to access book page {book_url}")
            return None

        soup = BeautifulSoup(book_response.text, 'html.parser')

        # Find the HTML download link
        # Prefer plain HTML (-h.htm) over "Read now!" which might be images version
        html_link = None

        # First, look for plain HTML links (-h.htm)
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '-h.htm' in href or '-h.html' in href:
                html_link = "https://www.gutenberg.org" + href
                print(
                    f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Found plain HTML link: {html_link}")
                break

        # If not found, look for "Read now!" link
        if not html_link:
            read_now_link = soup.find(
                'a', string=lambda text: text and 'read now' in text.lower())
            if read_now_link and read_now_link.get('href'):
                href = read_now_link['href']
                if href.startswith('/'):
                    html_link = "https://www.gutenberg.org" + href
                    print(
                        f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Found 'Read now!' HTML link: {html_link}")

        # If still not found, look for the download table
        if not html_link:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        format_cell = cells[0].get_text().strip().lower()
                        link_cell = cells[1]

                        if 'html' in format_cell and 'image' not in format_cell:
                            link = link_cell.find('a')
                            if link and link.get('href'):
                                href = link['href']
                                if href.startswith('/'):
                                    html_link = "https://www.gutenberg.org" + href
                                    print(
                                        f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Found HTML link in table: {html_link}")
                                    break
                if html_link:
                    break

        if not html_link:
            print(f"No HTML version available for {book_title}")
            return None

        # Download the HTML content
        html_response = requests.get(html_link, timeout=30)
        if html_response.status_code != 200:
            print(f"Failed to download HTML for {book_title}")
            return None

        html_content = html_response.text

        # Prepare storage path
        author_folder = author_name.replace(
            ' ', '_').replace('/', '_').replace('\\', '_')
        safe_title = book_title.replace(
            ' ', '_').replace('/', '_').replace('\\', '_')
        safe_author = author_name.replace(
            ' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"bookmarkd_{book_id}_{safe_title}_{safe_author}.html"
        file_path = f"{author_folder}/{filename}"

        # Upload to Supabase storage
        bucket = supabase.storage.from_("book_html")
        try:
            upload_response = bucket.upload(
                file_path,
                html_content.encode('utf-8'),
                {"content-type": "text/html"}
            )

            # Check if upload was successful (Supabase returns different response format)
            if hasattr(upload_response, 'status_code'):
                if upload_response.status_code not in [200, 201]:
                    if upload_response.status_code == 409 and 'already exists' in str(upload_response.json()).lower():
                        print(
                            f"DEBUG GUTENBERG_search_and_download_gutenberg_html: File already exists in storage: {file_path}")
                    else:
                        print(
                            f"Failed to upload to Supabase: {upload_response.json()}")
                        return None
            else:
                # Handle UploadResponse object
                print(
                    f"DEBUG GUTENBERG_search_and_download_gutenberg_html: Upload response: {upload_response}")
                if 'already exists' in str(upload_response).lower():
                    print(
                        f"DEBUG GUTENBERG_search_and_download_gutenberg_html: File already exists in storage: {file_path}")
                elif 'error' in str(upload_response).lower():
                    print(f"Failed to upload to Supabase: {upload_response}")
                    return None
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(
                    f"DEBUG GUTENBERG_search_and_download_gutenberg_html: File already exists in storage: {file_path}")
            else:
                print(f"Exception during upload: {e}")
                return None

        # Get public URL
        public_url = bucket.get_public_url(file_path)

        # Update database
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE books SET html_path = %s WHERE book_id = %s",
                    (public_url, book_id)
                )
                conn.commit()

        print(f"Successfully stored HTML for book {book_id} at {public_url}")
        return public_url

    except Exception as e:
        print(f"Error processing Gutenberg HTML for book {book_id}: {e}")
        return None

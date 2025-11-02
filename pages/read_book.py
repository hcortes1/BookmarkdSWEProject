# pages/read_book.py
import dash
from dash import html, dcc
from backend.books import get_book_details
import requests
import re
from bs4 import BeautifulSoup

dash.register_page(__name__, path_template="/read/<book_id>")


def extract_headers_from_html(html_content):
    """Extract headers (h1-h6) from HTML content and create navigation structure"""
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = []
    
    # First, try to find table of contents and extract proper ID mappings
    toc_mappings = {}
    toc_section = None
    for element in soup.find_all(['div', 'section', 'nav']):
        if element.get_text().strip().startswith('Contents') or 'CONTENTS' in element.get_text().upper():
            toc_section = element
            break
    
    if toc_section:
        toc_links = toc_section.find_all('a', href=lambda x: x and x.startswith('#'))
        for link in toc_links:
            link_text = link.get_text().strip()
            href = link.get('href')
            if href and href.startswith('#'):
                toc_mappings[link_text] = href[1:]  # Remove the # prefix
    
    # Now process headers and assign correct IDs
    toc_header_ids = set()  # Track which headers have TOC mappings
    
    for header_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        header_text = header_tag.get_text().strip()
        
        # Check if this header has a mapping in the TOC (case-insensitive, normalized)
        header_id = None
        normalized_header = re.sub(r'\s+', ' ', header_text.lower().strip())
        normalized_header = normalized_header.rstrip('.,!?')  # Remove trailing punctuation
        
        for toc_text, toc_id in toc_mappings.items():
            normalized_toc = re.sub(r'\s+', ' ', toc_text.lower().strip())
            normalized_toc = normalized_toc.rstrip('.,!?')  # Remove trailing punctuation
            if normalized_header == normalized_toc:
                header_id = toc_id
                toc_header_ids.add(id(header_tag))  # Mark this header as having TOC mapping
                break
        
        if header_id:
            # Use the ID from TOC
            header_tag['id'] = header_id
        elif not header_tag.get('id'):
            # Create ID only if no existing ID
            header_id = re.sub(r'[^a-zA-Z0-9]', '_', header_text.lower())
            header_id = re.sub(r'_+', '_', header_id).strip('_')
            if not header_id:
                header_id = f"header_{len(headers)}"
            header_tag['id'] = header_id
        else:
            header_id = header_tag.get('id')

        headers.append({
            'id': header_id,
            'text': header_text,
            'level': int(header_tag.name[1]),  # h1 -> 1, h2 -> 2, etc.
            'tag': header_tag.name
        })
    
    # Filter headers to only include ACT headers and headers with TOC mappings
    filtered_headers = []
    for header in headers:
        header_text = header['text']
        # Include ACT headers
        if header_text.upper().startswith('ACT '):
            filtered_headers.append(header)
        # Include headers that have TOC mappings (check by ID)
        elif any(toc_id == header['id'] for toc_id in toc_mappings.values()):
            filtered_headers.append(header)
    
    return filtered_headers, str(soup)


def create_navigation_panel(headers):
    """Create the navigation panel with headers"""
    if not headers:
        return html.Div("No headers found", className="nav-panel")

    nav_items = []
    for i, header in enumerate(headers):
        indent_class = f"nav-indent-{header['level']}"
        nav_items.append(
            html.A(
                header['text'][:50] + ('...' if len(header['text']) > 50 else ''),
                href=f"#{header['id']}",
                className=f"nav-link {indent_class}",
                id=f"nav-{i}",
                style={
                    'display': 'block',
                    'padding': '5px 10px',
                    'textDecoration': 'none',
                    'color': '#333',
                    'borderLeft': f"{header['level'] * 2}px solid #ddd",
                    'marginLeft': f"{(header['level'] - 1) * 10}px",
                    'cursor': 'pointer'
                }
            )
        )

    # Add JavaScript to handle navigation clicks
    nav_script = '''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        console.log("Navigation script loaded");

        // Function to send message to iframe
        function sendMessageToIframe(targetId) {
            var iframe = document.querySelector('.book-content-iframe');
            if (iframe && iframe.contentWindow) {
                console.log("Sending postMessage to iframe. Target ID:", targetId);
                iframe.contentWindow.postMessage({
                    type: 'scrollToElement',
                    elementId: targetId
                }, '*');
                return true;
            } else {
                console.error("Iframe not found or contentWindow unavailable");
                return false;
            }
        }

        // Handle navigation link clicks
        document.querySelectorAll('.nav-link').forEach(function(link) {
            console.log("Found nav link:", link.getAttribute('href'));
            link.addEventListener('click', function(e) {
                console.log("Nav link clicked, preventing default");
                e.preventDefault();
                var targetId = this.getAttribute('href').substring(1);

                console.log("Navigation link clicked. Target ID:", targetId);

                // Function to attempt scrolling
                function attemptScroll() {
                    var iframe = document.querySelector('.book-content-iframe');
                    if (iframe && iframe.contentWindow && iframe.contentDocument) {
                        try {
                            console.log("Trying direct access to iframe document");
                            var targetElement = iframe.contentDocument.getElementById(targetId);
                            if (targetElement) {
                                console.log("Found target element in iframe, scrolling");
                                targetElement.scrollIntoView({ behavior: 'smooth' });
                                return true;
                            } else {
                                console.error("Target element not found in iframe document");
                                // Try postMessage as fallback
                                console.log("Trying postMessage as fallback");
                                iframe.contentWindow.postMessage({
                                    type: 'scrollToElement',
                                    elementId: targetId
                                }, '*');
                                return true;
                            }
                        } catch (e) {
                            console.error("Error accessing iframe document:", e);
                            return false;
                        }
                    } else {
                        console.error("Iframe not ready for direct access");
                        return false;
                    }
                }

                // Try immediately
                if (!attemptScroll()) {
                    // If not ready, wait and try again
                    setTimeout(attemptScroll, 100);
                    setTimeout(attemptScroll, 500);
                    setTimeout(attemptScroll, 1000);
                }

                return false;
            });
        });

        // Also listen for iframe load events
        var iframe = document.querySelector('.book-content-iframe');
        if (iframe) {
            iframe.addEventListener('load', function() {
                console.log("Iframe loaded, navigation should now work");
            });
        }
    });
    </script>
    '''

    return html.Div([
        html.H3("Table of Contents", style={'padding': '10px', 'margin': '0', 'borderBottom': '1px solid #ddd'}),
        html.Div(nav_items, className="nav-links"),
        html.Script(nav_script)
    ], className="nav-panel", style={
        'width': '250px',
        'height': '70vh',
        'overflowY': 'auto',
        'borderRight': '1px solid #ddd',
        'backgroundColor': '#f9f9f9'
    })


def layout(book_id=None, **kwargs):
    if not book_id:
        return html.Div("Book not found", className="error-message")

    try:
        book_id = int(book_id)
        book_data = get_book_details(book_id)

        if not book_data or not book_data.get('html_path'):
            return html.Div("Book not available for reading", className="error-message")

        # Fetch the HTML content from Supabase
        try:
            response = requests.get(book_data['html_path'])
            response.raise_for_status()
            html_content = response.text

            # Extract headers for navigation BEFORE modifying HTML
            headers, html_content = extract_headers_from_html(html_content)
            
            # Remove Project Gutenberg header information
            import re
            # Find and remove everything between "The Project Gutenberg eBook of " and "*** START OF THE PROJECT GUTENBERG"
            pattern = r'The Project Gutenberg eBook of .*?\*\*\* START OF THE PROJECT GUTENBERG .*?\*\*\*'
            html_content = re.sub(pattern, '', html_content, flags=re.DOTALL)            # Add JavaScript to handle anchor links properly within the iframe
            anchor_script = '''
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Handle all anchor links
                document.querySelectorAll('a[href^="#"]').forEach(function(link) {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        var targetId = this.getAttribute('href').substring(1);
                        var targetElement = document.getElementById(targetId);
                        if (targetElement) {
                            targetElement.scrollIntoView({ behavior: 'smooth' });
                        }
                        return false;
                    });
                });

                // Listen for messages from parent window (navigation panel)
                window.addEventListener('message', function(event) {
                    console.log("Message received in iframe:", event.data);
                    console.log("Event origin:", event.origin);
                    if (event.data && event.data.type === 'scrollToElement') {
                        console.log("Looking for element with ID:", event.data.elementId);
                        var targetElement = document.getElementById(event.data.elementId);
                        console.log("Target element found:", !!targetElement);
                        if (targetElement) {
                            console.log("Scrolling to element");
                            targetElement.scrollIntoView({ behavior: 'smooth' });
                        } else {
                            console.error("Target element not found:", event.data.elementId);
                            // List all elements with IDs for debugging
                            var allElementsWithIds = document.querySelectorAll('[id]');
                            console.log("All elements with IDs:", Array.from(allElementsWithIds).map(el => el.id));
                        }
                    }
                });
            });
            </script>
            '''

            # Add the script and base tag to ensure proper link handling
            if '<head>' in html_content:
                html_content = html_content.replace(
                    '<head>', f'<head><base target="_self"><style>html {{ scroll-behavior: smooth; }}</style>{anchor_script}', 1)
            elif '<html>' in html_content:
                html_content = html_content.replace(
                    '<html>', f'<html><head><base target="_self"><style>html {{ scroll-behavior: smooth; }}</style>{anchor_script}</head>', 1)
            else:
                # If no head tag, add one at the beginning
                html_content = f'<head><base target="_self"><style>html {{ scroll-behavior: smooth; }}</style>{anchor_script}</head>{html_content}'

            # Fix navigation links - only external links should open in new tabs
            # Internal anchor links (starting with #) should work within the iframe
            # Add target="_blank" to external links (http, https, ftp, etc.)
            html_content = re.sub(
                r'<a([^>]+href="(?:https?|ftp)://[^"]*")>', r'<a\1 target="_blank">', html_content)

        except Exception as e:
            return html.Div(f"Error loading book content: {str(e)}", className="error-message")

        # Create navigation panel
        nav_panel = create_navigation_panel(headers)

        return html.Div([
            # Header with back button
            html.Div([
                html.Div([
                    dcc.Link("← Back to Book Details",
                             href=f"/book/{book_id}",
                             className="back-btn"),
                    html.H1(
                        f"Reading: {book_data['title']}", className="reading-title"),
                    html.H2(
                        f"by {book_data.get('author_name', 'Unknown Author')}", className="reading-author")
                ], className="reading-header")
            ], className="reading-header-container"),

            # Main content area with navigation and book
            html.Div([
                # Navigation panel (left side)
                nav_panel,

                # Book content (right side)
                html.Iframe(
                    srcDoc=html_content,
                    style={'flex': '1', 'height': '70vh', 'border': 'none'},
                    className="book-content-iframe"
                )
            ], style={
                'display': 'flex',
                'width': '100%',
                'marginBottom': '0'
            })
        ], className="reading-page")

    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="error-message")

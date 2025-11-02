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
        return ""

    nav_items = []
    for i, header in enumerate(headers):
        indent_class = f"nav-indent-{header['level']}"
        nav_items.append(
            '<a href="#{id}" class="nav-link {indent_class}" style="display:block;padding:5px 10px;text-decoration:none;color:#333;border-left:{border_left}px solid #ddd;margin-left:{margin_left}px;cursor:pointer;">{text}</a>'.format(
                id=header["id"],
                indent_class=indent_class,
                border_left=header["level"]*2,
                margin_left=(header["level"]-1)*10,
                text=header["text"][:50] + ("..." if len(header["text"]) > 50 else "")
            )
        )

    # Fixed sidebar TOC, always visible on the left
    nav_html = '''
    <style>
    .nav-panel-fixed {{
        position: fixed;
        top: 0;
        left: 0;
        width: 250px;
        height: 100vh;
        overflow-y: auto;
        border-right: 1px solid #ddd;
        background: #f9f9f9;
        z-index: 1000;
    }}
    .toc-book-content-fixed {{margin-left: 270px; padding: 20px 20px 20px 0; min-width: 0; box-sizing: border-box;}}
    /* Fallback: if book content is not moved, offset body */
    body:not(:has(.toc-book-content-fixed > *)) {{margin-left: 270px !important;}}
    </style>
    <div class="nav-panel-fixed">
      <h3 style="padding:10px;margin:0;border-bottom:1px solid #ddd;">Table of Contents</h3>
      <div class="nav-links">{nav_items}</div>
    </div>
    <div class="toc-book-content-fixed" id="toc-book-content-fixed">
      <!-- BOOK CONTENT WILL BE MOVED HERE BY JS -->
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Move all book content except the nav-panel into the .toc-book-content-fixed
        var wrapper = document.getElementById('toc-book-content-fixed');
        var navPanel = document.querySelector('.nav-panel-fixed');
        if (wrapper && navPanel) {{
            // Move all siblings after navPanel into wrapper
            var next = navPanel.nextSibling;
            var nodesToMove = [];
            while (next) {{
                // Only move elements that are not the wrapper itself
                if (next !== wrapper) nodesToMove.push(next);
                next = next.nextSibling;
            }}
            nodesToMove.forEach(function(node) {{
                wrapper.appendChild(node);
            }});
        }}
        document.querySelectorAll('.nav-link').forEach(function(link) {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                var targetId = this.getAttribute('href').substring(1);
                var targetElement = document.getElementById(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth' }});
                }}
                return false;
            }});
        }});
    }});
    </script>
    '''.format(nav_items=''.join(nav_items))
    return nav_html


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

        # Create navigation panel HTML
        nav_panel_html = create_navigation_panel(headers)

        # Inject the navigation panel at the top of the book HTML content
        if '<body' in html_content:
            html_content = re.sub(r'(<body[^>]*>)', r'\1' + nav_panel_html, html_content, count=1)
        else:
            html_content = nav_panel_html + html_content

        return html.Div([
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
            html.Iframe(
                srcDoc=html_content,
                style={'width': '100%', 'height': '70vh', 'border': 'none'},
                className="book-content-iframe",
                sandbox="allow-scripts allow-same-origin",
                key=str(hash(html_content))
            )
        ], className="reading-page")

    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="error-message")

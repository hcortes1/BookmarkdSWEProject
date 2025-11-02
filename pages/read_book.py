# pages/read_book.py
import dash
from dash import html, dcc
from backend.books import get_book_details
import requests

dash.register_page(__name__, path_template="/read/<book_id>")


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
            
            # Remove Project Gutenberg header information
            import re
            # Find and remove everything between "The Project Gutenberg eBook of " and "*** START OF THE PROJECT GUTENBERG"
            pattern = r'The Project Gutenberg eBook of .*?\*\*\* START OF THE PROJECT GUTENBERG .*?\*\*\*'
            html_content = re.sub(pattern, '', html_content, flags=re.DOTALL)
            
            # Add JavaScript to handle anchor links properly within the iframe
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
            });
            </script>
            '''
            
            # Add the script and base tag to ensure proper link handling
            if '<head>' in html_content:
                html_content = html_content.replace('<head>', f'<head><base target="_self"><style>html {{ scroll-behavior: smooth; }}</style>{anchor_script}', 1)
            elif '<html>' in html_content:
                html_content = html_content.replace('<html>', f'<html><head><base target="_self"><style>html {{ scroll-behavior: smooth; }}</style>{anchor_script}</head>', 1)
            else:
                # If no head tag, add one at the beginning
                html_content = f'<head><base target="_self"><style>html {{ scroll-behavior: smooth; }}</style>{anchor_script}</head>{html_content}'
            
            # Fix navigation links - only external links should open in new tabs
            # Internal anchor links (starting with #) should work within the iframe
            # Add target="_blank" to external links (http, https, ftp, etc.)
            html_content = re.sub(r'<a([^>]+href="(?:https?|ftp)://[^"]*")>', r'<a\1 target="_blank">', html_content)
            
        except Exception as e:
            return html.Div(f"Error loading book content: {str(e)}", className="error-message")

        return html.Div([
            # Header with back button
            html.Div([
                html.Div([
                    dcc.Link("← Back to Book Details",
                            href=f"/book/{book_id}",
                            className="back-btn"),
                    html.H1(f"Reading: {book_data['title']}", className="reading-title"),
                    html.H2(f"by {book_data.get('author_name', 'Unknown Author')}", className="reading-author")
                ], className="reading-header")
            ], className="reading-header-container"),

            # Book content
            html.Iframe(
                srcDoc=html_content,
                style={'width': '100%', 'height': '80vh', 'border': 'none'},
                className="book-content-iframe"
            )
        ], className="reading-page")

    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="error-message")
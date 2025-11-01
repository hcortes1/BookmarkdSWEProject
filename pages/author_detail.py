# pages/author_detail.py
import dash
from dash import html, dcc, Input, Output, State, callback
import psycopg2.extras
from backend.db import get_conn
from backend.favorites import is_author_favorited, toggle_author_favorite
from backend.authors import get_author_details, get_author_books
from urllib.parse import unquote, parse_qs
from typing import Dict, Any
import time

dash.register_page(__name__, path_template="/author/<author_id>")


def create_pagination_controls(current_page, total_pages, total_books, author_id):
    """Create pagination controls for author books"""
    # Defensive programming - ensure we have valid numbers
    current_page = max(1, int(current_page or 1))
    total_pages = max(1, int(total_pages or 1))
    total_books = max(0, int(total_books or 0))

    controls = []

    # Show page info (always show this, even for single page)
    start_book = (current_page - 1) * 80 + 1
    end_book = min(current_page * 80, total_books)

    controls.append(
        html.Div(f"Showing {start_book}-{end_book} of {total_books} books",
                 className="pagination-info")
    )

    # Only show pagination buttons if there are multiple pages
    if total_pages <= 1:
        return controls

    # Pagination buttons
    buttons = []

    # Previous button
    if current_page > 1:
        buttons.append(
            html.Button("← Previous",
                        id={'type': 'pagination-btn',
                            'author_id': author_id, 'page': current_page - 1},
                        className="pagination-btn")
        )

    # Page number buttons (show up to 7 pages around current)
    start_page = max(1, current_page - 3)
    end_page = min(total_pages, current_page + 3)

    if start_page > 1:
        buttons.append(
            html.Button("1",
                        id={'type': 'pagination-btn',
                            'author_id': author_id, 'page': 1},
                        className="pagination-btn")
        )
        if start_page > 2:
            buttons.append(html.Span("...", style={'margin': '0 5px'}))

    for page_num in range(start_page, end_page + 1):
        is_current = page_num == current_page
        buttons.append(
            html.Button(str(page_num),
                        id={'type': 'pagination-btn',
                            'author_id': author_id, 'page': page_num},
                        className=f"pagination-btn{' active' if is_current else ''}")
        )

    if end_page < total_pages:
        if end_page < total_pages - 1:
            buttons.append(html.Span("...", style={'margin': '0 5px'}))
        buttons.append(
            html.Button(str(total_pages),
                        id={'type': 'pagination-btn',
                            'author_id': author_id, 'page': total_pages},
                        className="pagination-btn")
        )

    # Next button
    if current_page < total_pages:
        buttons.append(
            html.Button("Next →",
                        id={'type': 'pagination-btn',
                            'author_id': author_id, 'page': current_page + 1},
                        className="pagination-btn")
        )

    controls.append(
        html.Div(buttons,
                 style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'flex-wrap': 'wrap'})
    )

    return controls


def layout(author_id=None, **kwargs):
    if not author_id:
        return html.Div("Author not found", className="error-message")

    try:
        author_id = int(author_id)
        author_data = get_author_details(author_id)

        if not author_data:
            return html.Div("Author not found", className="error-message")

        # Get author's books with error handling
        try:
            books = get_author_books(author_id)
            time.sleep(0.6)
        except Exception as e:
            print(f"Error getting author books: {e}")
            books = []

        return html.Div([
            # Store for favorite status feedback
            dcc.Store(id={'type': 'author-favorite-store',
                      'author_id': author_id}),
            dcc.Store(id='author-navigation-store',
                      data={'author_id': author_id}),

            html.Div([
                html.Div([
                    # Favorite button (top right corner of author card)
                    html.Button(
                        id={'type': 'author-favorite-btn',
                            'author_id': author_id},
                        className="favorite-btn-author-detail",
                        style={
                            'position': 'absolute',
                            'top': '20px',
                            'right': '20px',
                            'background': 'none',
                            'border': 'none',
                            'font-size': '2rem',
                            'cursor': 'pointer',
                            'zIndex': 2
                        }
                    ),

                    # Author image
                    html.Div([
                        html.Img(
                            src=author_data.get(
                                'author_image_url') or '/assets/svg/default-author.svg',
                            className="author-image-large"
                        )
                    ], className="author-image-container"),

                    # Author details
                    html.Div([
                        html.H1(author_data['name'], className="author-name"),

                        html.Div([
                            html.Strong("Born: "),
                            html.Span(str(author_data.get('birth_date')).split(
                                '-')[0] if author_data.get('birth_date') else 'Unknown')
                        ], className="author-info") if author_data.get('birth_date') else None,

                        html.Div([
                            html.Strong("Died: "),
                            html.Span(str(author_data.get('death_date')).split(
                                '-')[0] if author_data.get('death_date') else 'Unknown')
                        ], className="author-info") if author_data.get('death_date') else None,

                        html.Div([
                            html.Strong("Nationality: "),
                            html.Span(author_data.get(
                                'nationality') or 'Unknown')
                        ], className="author-info") if author_data.get('nationality') else None,

                        html.Div([
                            html.Strong("Biography: "),
                            dcc.Markdown(
                                author_data.get(
                                    'bio') or 'No biography available.',
                                className="author-bio"
                            )
                        ], className="author-info-block"),

                        html.Div(
                            id={'type': 'author-favorite-feedback',
                                'author_id': author_id},
                            className="favorite-feedback"
                        )

                    ], className="author-details")

                ], className="author-detail-container secondary-bg", style={'position': 'relative'}),

                # Author's books section with pagination
                html.Div([
                    html.H3("Books by this Author", className="section-title"),
                    html.Div(id={'type': 'author-books-pagination-top', 'author_id': author_id}, children=[
                        # Initial pagination controls
                        html.Div([
                            html.Div(create_pagination_controls(1, max(1, (len(books) + 79) // 80), len(
                                books), author_id) if len(books) > 0 else [html.P("No books to display.")])
                        ])
                    ], style={'margin-bottom': '20px'}),
                    dcc.Loading(
                        id={'type': 'author-books-loading',
                            'author_id': author_id},
                        children=[html.Div(
                            id={'type': 'author-books-grid',
                                'author_id': author_id},
                            children=[
                                # Show first 80 books initially
                                create_book_card(book, author_id) for book in books[:80]
                            ] if books else [html.P("No books found in our database.", className="no-books-message")],
                            className="books-grid"
                        )],
                        type="default"
                    ),
                    html.Div(id={'type': 'author-books-pagination-bottom', 'author_id': author_id}, children=[
                        # Initial pagination controls
                        html.Div(create_pagination_controls(1, max(1, (len(books) + 79) // 80), len(
                            books), author_id) if len(books) > 0 else [html.P("No books to display.")])
                    ], style={'margin-top': '20px'}),
                    # Store for pagination state
                    dcc.Store(id={'type': 'author-books-page-store', 'author_id': author_id}, data={
                              'current_page': 1, 'books_per_page': 80, 'total_books': len(books)})
                ], className="author-books-section secondary-bg", style={
                    'max-width': '1600px',  # Increased width for better space utilization
                    'margin': '30px auto 0',
                    'padding': '20px',  # Reduced padding to give more space to books
                    'border-radius': '12px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.1)'
                })

            ], className="page-container", style={
                'padding': '30px',
                'min-height': '100vh'
            })
        ])

    except Exception as e:
        print(f"Error loading author: {e}")
        return html.Div("Error loading author details", className="error-message")


def create_book_card(book: Dict[str, Any], author_id: int):
    """Create a book card for author page display"""

    # Create href for book details
    href = f"/book/{book['book_id']}"

    # Format rating information
    rating_info = []
    average_rating = book.get('average_rating')
    rating_count = book.get('rating_count', 0)

    if average_rating and average_rating > 0 and rating_count > 0:
        # Create clickable rating display in format: average/5.0 (count)
        rating_info.append(
            html.Div([
                dcc.Link(
                    f"{average_rating:.1f}/5.0 ({rating_count})",
                    href=f"/reviews/{book['book_id']}",
                    style={
                        'font-weight': 'bold',
                        'text-decoration': 'none'
                    },
                    className='rating-color'
                )
            ], className="book-rating")
        )

    # Format release year
    release_year = book.get('release_year')
    year_info = None
    if release_year:
        year_info = html.Div(
            str(int(release_year)),
            className="book-year"
        )

    return html.Div([
        dcc.Link([
            html.Img(
                src=book.get('cover_url') or '/assets/svg/default-book.svg',
                className="book-card-image"
            ),
            html.Div([
                html.H4(book['title'], className="book-card-title"),
                # Rating information
                *rating_info,
                # Release year
                year_info
            ])
        ], href=href, style={'text-decoration': 'none', 'color': 'inherit'})
    ], className="book-card lighter-bg")


# Callback to set initial favorite button state
@callback(
    [Output({'type': 'author-favorite-btn', 'author_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'author-favorite-btn', 'author_id': dash.dependencies.MATCH}, 'className')],
    [Input({'type': 'author-favorite-store',
           'author_id': dash.dependencies.MATCH}, 'id')],
    [State('user-session', 'data')],
    prevent_initial_call=False
)
def set_initial_author_favorite_state(store_id, session_data):
    """Set the initial state of the favorite button"""
    author_id = store_id['author_id']

    if not session_data or not session_data.get('logged_in'):
        return "❤️", "favorite-btn-author-detail"

    user_id = session_data.get('user_id')
    is_favorited = is_author_favorited(user_id, author_id)

    if is_favorited:
        return "💔", "favorite-btn-author-detail remove"
    else:
        return "❤️", "favorite-btn-author-detail add"


# Callback to handle favorite button clicks
@callback(
    [Output({'type': 'author-favorite-btn', 'author_id': dash.dependencies.MATCH}, 'children', allow_duplicate=True),
     Output({'type': 'author-favorite-btn',
            'author_id': dash.dependencies.MATCH}, 'className', allow_duplicate=True),
     Output({'type': 'author-favorite-feedback', 'author_id': dash.dependencies.MATCH}, 'children')],
    [Input({'type': 'author-favorite-btn',
           'author_id': dash.dependencies.MATCH}, 'n_clicks')],
    [State('user-session', 'data')],
    prevent_initial_call=True
)
def handle_author_favorite_click(n_clicks, session_data):
    """Handle author favorite button click"""
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    # Check if user is logged in
    if not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, html.Div(
            "Please log in to add favorites",
            className="error-message"
        )

    # Get author_id from callback context
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    author_id = eval(trigger_id)['author_id']  # Convert string back to dict
    user_id = session_data.get('user_id')

    # Toggle favorite
    result = toggle_author_favorite(user_id, author_id)

    if result['success']:
        if result['is_favorited']:
            return "💔", "favorite-btn-author-detail remove", html.Div(result['message'], className="success-message")
        else:
            return "❤️", "favorite-btn-author-detail add", html.Div(result['message'], className="success-message")
    else:
        return dash.no_update, dash.no_update, html.Div(
            result['message'],
            className="error-message"
        )


# Callback to handle pagination clicks
@callback(
    [Output({'type': 'author-books-page-store', 'author_id': dash.dependencies.MATCH}, 'data'),
     Output({'type': 'author-books-grid',
            'author_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'author-books-pagination-top',
            'author_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'author-books-pagination-bottom', 'author_id': dash.dependencies.MATCH}, 'children')],
    [Input({'type': 'pagination-btn', 'author_id': dash.dependencies.MATCH,
           'page': dash.dependencies.ALL}, 'n_clicks')],
    [State({'type': 'author-books-page-store',
           'author_id': dash.dependencies.MATCH}, 'data')],
    prevent_initial_call=True
)
def handle_pagination_click(clicks_list, page_data):
    """Handle pagination button clicks"""
    if not dash.callback_context.triggered or not any(clicks_list):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Find which button was clicked
    triggered = dash.callback_context.triggered[0]
    button_id = triggered['prop_id'].split('.')[0]
    button_info = eval(button_id)  # Convert string back to dict

    # Ensure valid page number
    new_page = max(1, int(button_info.get('page', 1)))
    author_id = int(button_info.get('author_id', 0))

    # Ensure page_data is valid
    if not page_data:
        page_data = {'current_page': 1, 'books_per_page': 80, 'total_books': 0}

    # Update page data
    updated_page_data = {**page_data, 'current_page': new_page}

    # Get author's books
    books = get_author_books(author_id)
    books_per_page = int(page_data.get('books_per_page', 80))
    total_books = len(books)
    total_pages = max(1, (total_books + books_per_page - 1) // books_per_page)

    # Ensure new_page is within valid range
    new_page = max(1, min(new_page, total_pages))
    updated_page_data['current_page'] = new_page

    # Calculate start and end indices for new page
    start_idx = (new_page - 1) * books_per_page
    end_idx = min(start_idx + books_per_page, total_books)

    # Get books for new page
    page_books = books[start_idx:end_idx]

    # Create book cards
    book_cards = [create_book_card(book, author_id) for book in page_books]

    # Create updated pagination controls
    pagination_controls = create_pagination_controls(
        new_page, total_pages, total_books, author_id)

    time.sleep(0.6)
    return updated_page_data, book_cards, pagination_controls, pagination_controls

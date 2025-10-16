# pages/book_detail.py
import dash
from dash import html, dcc, Input, Output, State, callback
import psycopg2.extras
from backend.db import get_conn
from backend.favorites import is_book_favorited, toggle_book_favorite
from urllib.parse import unquote, parse_qs

dash.register_page(__name__, path_template="/book/<book_id>")


def layout(book_id=None, **kwargs):
    if not book_id:
        return html.Div("Book not found", className="error-message")

    try:
        book_id = int(book_id)
        book_data = get_book_details(book_id)

        if not book_data:
            return html.Div("Book not found", className="error-message")

        return html.Div([
            # Store for favorite status feedback
            dcc.Store(id={'type': 'book-favorite-store', 'book_id': book_id}),
            dcc.Store(id='book-navigation-store', data={'book_id': book_id}),

            html.Div([
                html.Div([
                    # Book cover
                    html.Div([
                        html.Img(
                            src=book_data.get(
                                'cover_url') or '/assets/svg/default-book.svg',
                            className="book-cover-large",
                            style={
                                'width': '200px',
                                'height': '300px',
                                'object-fit': 'cover',
                                'border-radius': '8px',
                                'box-shadow': '0 4px 12px rgba(0,0,0,0.15)'
                            }
                        )
                    ], className="book-cover-container"),

                    # Book details
                    html.Div([
                        html.H1(book_data['title'], className="book-title"),
                        html.H2([
                            "by ",
                            dcc.Link(
                                book_data.get('author_name', 'Unknown Author'),
                                href=f"/author/{book_data.get('author_id')}?from_book={book_id}" if book_data.get(
                                    'author_id') else "#",
                                className="author-link",
                                style={
                                    'color': '#007bff',
                                    'text-decoration': 'none'
                                }
                            ) if book_data.get('author_id') else book_data.get('author_name', 'Unknown Author')
                        ], className="book-author"),

                        html.Div([
                            html.Strong("Genre: "),
                            html.Span(book_data.get('genre')
                                      or 'Not specified')
                        ], className="book-info"),

                        html.Div([
                            html.Strong("Published: "),
                            html.Span(str(int(book_data.get('release_year'))) if book_data.get(
                                'release_year') else 'Unknown')
                        ], className="book-info"),

                        html.Div([
                            html.Strong("ISBN: "),
                            html.Span(book_data.get('isbn') or 'Not available')
                        ], className="book-info"),

                        html.Div([
                            html.Strong("Description: "),
                            html.P(book_data.get('description') or 'No description available.',
                                   className="book-description")
                        ], className="book-info-block"),

                        # Favorite button
                        html.Div([
                            html.Button(
                                id={'type': 'book-favorite-btn',
                                    'book_id': book_id},
                                className="favorite-btn",
                                style={
                                    'margin-top': '20px',
                                    'padding': '10px 20px',
                                    'border': 'none',
                                    'border-radius': '5px',
                                    'cursor': 'pointer',
                                    'font-size': '14px',
                                    'font-weight': 'bold'
                                }
                            ),
                            html.Div(
                                id={'type': 'book-favorite-feedback',
                                    'book_id': book_id},
                                style={'margin-top': '10px',
                                       'font-size': '12px'}
                            )
                        ], className="favorite-section")

                    ], className="book-details", style={'flex': '1', 'margin-left': '30px'})

                ], className="book-detail-container", style={
                    'display': 'flex',
                    'max-width': '800px',
                    'margin': '0 auto',
                    'background': 'white',
                    'padding': '30px',
                    'border-radius': '12px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.1)'
                }),

                # Other editions/versions section
                html.Div(id='other-editions-section', children=[
                    # This will be populated by a callback
                ], style={
                    'max-width': '800px',
                    'margin': '20px auto 0',
                })

            ], className="page-container", style={
                'padding': '30px',
                'background': '#f5f5f5',
                'min-height': '100vh'
            })
        ])

    except Exception as e:
        print(f"Error loading book: {e}")
        return html.Div("Error loading book details", className="error-message")


def get_book_details(book_id: int):
    """Get book details from database"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT b.book_id, b.title, b.isbn, b.genre, 
                       EXTRACT(YEAR FROM b.release_date) as release_year,
                       b.description, b.cover_url, b.author_id,
                       a.name as author_name, a.bio as author_bio
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                WHERE b.book_id = %s
            """
            cur.execute(sql, (book_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    except Exception as e:
        print(f"Error getting book details: {e}")
        return None


def get_books_with_same_title(book_id: int, title: str):
    """Get all books with the same title as the current book"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT b.book_id, b.title, b.isbn, b.genre, 
                       EXTRACT(YEAR FROM b.release_date) as release_year,
                       b.description, b.cover_url, b.author_id,
                       a.name as author_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                WHERE LOWER(b.title) = LOWER(%s) AND b.book_id != %s
                ORDER BY b.release_date, a.name
            """
            cur.execute(sql, (title, book_id))
            results = cur.fetchall()
            return [dict(result) for result in results]
    except Exception as e:
        print(f"Error getting books with same title: {e}")
        return []


# Callback to populate other editions section
@callback(
    Output('other-editions-section', 'children'),
    [Input('book-navigation-store', 'data')],
    prevent_initial_call=False
)
def populate_other_editions(nav_data):
    """Populate the other editions section if there are books with the same title"""
    if not nav_data or not nav_data.get('book_id'):
        return []

    book_id = nav_data['book_id']
    current_book = get_book_details(book_id)

    if not current_book or not current_book.get('title'):
        return []

    other_books = get_books_with_same_title(book_id, current_book['title'])

    if not other_books:
        return []

    return html.Div([
        html.H3("Other Editions", style={
            'color': '#333',
            'margin-bottom': '15px',
            'font-size': '18px'
        }),
        html.Div([
            html.Div([
                dcc.Link([
                    html.Div([
                        html.Img(
                            src=book.get(
                                'cover_url') or '/assets/svg/default-book.svg',
                            style={
                                'width': '60px',
                                'height': '90px',
                                'object-fit': 'cover',
                                'border-radius': '4px',
                                'margin-right': '15px'
                            }
                        ),
                        html.Div([
                            html.H4(book['title'], style={
                                'margin': '0 0 5px 0',
                                'font-size': '16px',
                                'color': '#333'
                            }),
                            html.P(f"by {book.get('author_name', 'Unknown Author')}", style={
                                'margin': '0 0 5px 0',
                                'font-size': '14px',
                                'color': '#666'
                            }),
                            html.P(f"Published: {str(int(book.get('release_year'))) if book.get('release_year') else 'Unknown'}", style={
                                'margin': '0 0 5px 0',
                                'font-size': '12px',
                                'color': '#888'
                            }),
                            html.P(f"ISBN: {book.get('isbn', 'N/A')}", style={
                                'margin': '0',
                                'font-size': '12px',
                                'color': '#888'
                            }) if book.get('isbn') else None
                        ], style={'flex': '1'})
                    ], style={
                        'display': 'flex',
                        'align-items': 'flex-start',
                        'padding': '15px',
                        'background': '#f8f9fa',
                        'border-radius': '8px',
                        'margin-bottom': '10px',
                        'transition': 'background-color 0.2s'
                    })
                ], href=f"/book/{book['book_id']}", style={
                    'text-decoration': 'none',
                    'color': 'inherit'
                })
            ], style={
                'cursor': 'pointer'
            }) for book in other_books
        ])
    ], style={
        'background': 'white',
        'padding': '20px',
        'border-radius': '12px',
        'box-shadow': '0 4px 12px rgba(0,0,0,0.1)'
    })


# Callback to set initial favorite button state
@callback(
    [Output({'type': 'book-favorite-btn', 'book_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'book-favorite-btn', 'book_id': dash.dependencies.MATCH}, 'style')],
    [Input({'type': 'book-favorite-store', 'book_id': dash.dependencies.MATCH}, 'id')],
    [State('user-session', 'data')],
    prevent_initial_call=False
)
def set_initial_book_favorite_state(store_id, session_data):
    """Set the initial state of the favorite button"""
    book_id = store_id['book_id']

    # Default styles
    base_style = {
        'margin-top': '20px',
        'padding': '10px 20px',
        'border': 'none',
        'border-radius': '5px',
        'cursor': 'pointer',
        'font-size': '14px',
        'font-weight': 'bold'
    }

    if not session_data or not session_data.get('logged_in'):
        return "❤️ Add to Favorites (Login Required)", {
            **base_style,
            'background-color': '#ddd',
            'color': '#666',
            'cursor': 'not-allowed'
        }

    user_id = session_data.get('user_id')
    is_favorited = is_book_favorited(user_id, book_id)

    if is_favorited:
        return "💔 Remove from Favorites", {
            **base_style,
            'background-color': '#dc3545',
            'color': 'white'
        }
    else:
        return "❤️ Add to Favorites", {
            **base_style,
            'background-color': '#28a745',
            'color': 'white'
        }


# Callback to handle favorite button clicks
@callback(
    [Output({'type': 'book-favorite-btn', 'book_id': dash.dependencies.MATCH}, 'children', allow_duplicate=True),
     Output({'type': 'book-favorite-btn', 'book_id': dash.dependencies.MATCH},
            'style', allow_duplicate=True),
     Output({'type': 'book-favorite-feedback', 'book_id': dash.dependencies.MATCH}, 'children')],
    [Input({'type': 'book-favorite-btn', 'book_id': dash.dependencies.MATCH}, 'n_clicks')],
    [State('user-session', 'data')],
    prevent_initial_call=True
)
def handle_book_favorite_click(n_clicks, session_data):
    """Handle book favorite button click"""
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    # Check if user is logged in
    if not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, html.Div(
            "Please log in to add favorites",
            style={'color': 'red'}
        )

    # Get book_id from callback context
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    book_id = eval(trigger_id)['book_id']  # Convert string back to dict
    user_id = session_data.get('user_id')

    # Toggle favorite
    result = toggle_book_favorite(user_id, book_id)

    # Base styles
    base_style = {
        'margin-top': '20px',
        'padding': '10px 20px',
        'border': 'none',
        'border-radius': '5px',
        'cursor': 'pointer',
        'font-size': '14px',
        'font-weight': 'bold'
    }

    if result['success']:
        if result['is_favorited']:
            return "💔 Remove from Favorites", {
                **base_style,
                'background-color': '#dc3545',
                'color': 'white'
            }, html.Div(result['message'], style={'color': 'green'})
        else:
            return "❤️ Add to Favorites", {
                **base_style,
                'background-color': '#28a745',
                'color': 'white'
            }, html.Div(result['message'], style={'color': 'green'})
    else:
        return dash.no_update, dash.no_update, html.Div(
            result['message'],
            style={'color': 'red'}
        )

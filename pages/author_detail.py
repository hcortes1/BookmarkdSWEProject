# pages/author_detail.py
import dash
from dash import html, dcc, Input, Output, State, callback
import psycopg2.extras
from backend.db import get_conn
from backend.favorites import is_author_favorited, toggle_author_favorite
from urllib.parse import unquote, parse_qs

dash.register_page(__name__, path_template="/author/<author_id>")


def layout(author_id=None, **kwargs):
    if not author_id:
        return html.Div("Author not found", className="error-message")

    try:
        author_id = int(author_id)
        author_data = get_author_details(author_id)

        if not author_data:
            return html.Div("Author not found", className="error-message")

        # Get author's books
        books = get_author_books(author_id)

        return html.Div([
            # Store for favorite status feedback
            dcc.Store(id={'type': 'author-favorite-store',
                      'author_id': author_id}),
            dcc.Store(id='author-navigation-store',
                      data={'author_id': author_id}),

            html.Div([
                html.Div([
                    # Author image
                    html.Div([
                        html.Img(
                            src=author_data.get(
                                'author_image_url') or '/assets/svg/default-author.svg',
                            className="author-image-large",
                            style={
                                'width': '200px',
                                'height': '200px',
                                'object-fit': 'cover',
                                'border-radius': '50%',
                                'box-shadow': '0 4px 12px rgba(0,0,0,0.15)'
                            }
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
                            html.P(author_data.get('bio') or 'No biography available.',
                                   className="author-bio")
                        ], className="author-info-block"),

                        # Favorite button
                        html.Div([
                            html.Button(
                                id={'type': 'author-favorite-btn',
                                    'author_id': author_id},
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
                                id={'type': 'author-favorite-feedback',
                                    'author_id': author_id},
                                style={'margin-top': '10px',
                                       'font-size': '12px'}
                            )
                        ], className="favorite-section")

                    ], className="author-details", style={'flex': '1', 'margin-left': '30px'})

                ], className="author-detail-container", style={
                    'display': 'flex',
                    'max-width': '800px',
                    'margin': '0 auto',
                    'background': 'white',
                    'padding': '30px',
                    'border-radius': '12px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.1)'
                }),

                # Author's books section
                html.Div([
                    html.H3("Books by this Author", className="section-title"),
                    html.Div([
                        create_book_card(book, author_id) for book in books
                    ] if books else [html.P("No books found in our database.",
                                            className="no-books-message")],
                        className="books-grid", style={
                        'display': 'grid',
                        'grid-template-columns': 'repeat(auto-fill, minmax(150px, 1fr))',
                        'gap': '20px',
                        'margin-top': '20px'
                    })
                ], className="author-books-section", style={
                    'max-width': '800px',
                    'margin': '30px auto 0',
                    'background': 'white',
                    'padding': '30px',
                    'border-radius': '12px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.1)'
                })

            ], className="page-container", style={
                'padding': '30px',
                'background': '#f5f5f5',
                'min-height': '100vh'
            })
        ])

    except Exception as e:
        print(f"Error loading author: {e}")
        return html.Div("Error loading author details", className="error-message")


def create_book_card(book, author_id=None):
    """Create a book card component"""
    # Create link with author reference if author_id is provided
    href = f"/book/{book['book_id']}"
    if author_id:
        href += f"?from_author={author_id}"

    return html.Div([
        dcc.Link([
            html.Img(
                src=book.get('cover_url') or '/assets/svg/default-book.svg',
                style={
                    'width': '100%',
                    'height': '180px',
                    'object-fit': 'cover',
                    'border-radius': '4px'
                }
            ),
            html.Div([
                html.H4(book['title'], className="book-card-title", style={
                    'font-size': '14px',
                    'margin': '10px 0 5px',
                    'line-height': '1.3'
                }),
                html.P(book.get('genre', ''), className="book-card-genre", style={
                    'font-size': '12px',
                    'color': '#666',
                    'margin': '0'
                })
            ])
        ], href=href, style={'text-decoration': 'none', 'color': 'inherit'})
    ], className="book-card", style={
        'background': '#f8f9fa',
        'border-radius': '8px',
        'padding': '10px',
        'transition': 'transform 0.2s',
        'cursor': 'pointer'
    })


def get_author_details(author_id: int):
    """Get author details from database"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT author_id, name, bio, birth_date, death_date, nationality, author_image_url, created_at
                FROM authors
                WHERE author_id = %s
            """
            cur.execute(sql, (author_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    except Exception as e:
        print(f"Error getting author details: {e}")
        return None


def get_author_books(author_id: int):
    """Get books by this author"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT book_id, title, isbn, genre, release_date, description, cover_url
                FROM books
                WHERE author_id = %s
                ORDER BY release_date DESC, title
            """
            cur.execute(sql, (author_id,))
            results = cur.fetchall()
            return [dict(result) for result in results]
    except Exception as e:
        print(f"Error getting author books: {e}")
        return []


# Callback to set initial favorite button state
@callback(
    [Output({'type': 'author-favorite-btn', 'author_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'author-favorite-btn', 'author_id': dash.dependencies.MATCH}, 'style')],
    [Input({'type': 'author-favorite-store',
           'author_id': dash.dependencies.MATCH}, 'id')],
    [State('user-session', 'data')],
    prevent_initial_call=False
)
def set_initial_author_favorite_state(store_id, session_data):
    """Set the initial state of the favorite button"""
    author_id = store_id['author_id']

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
    is_favorited = is_author_favorited(user_id, author_id)

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
    [Output({'type': 'author-favorite-btn', 'author_id': dash.dependencies.MATCH}, 'children', allow_duplicate=True),
     Output({'type': 'author-favorite-btn',
            'author_id': dash.dependencies.MATCH}, 'style', allow_duplicate=True),
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
            style={'color': 'red'}
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

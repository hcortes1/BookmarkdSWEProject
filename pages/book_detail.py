# pages/book_detail.py
import dash
from dash import html, dcc, Input, Output, State, callback
import psycopg2.extras
from backend.db import get_conn
from backend.favorites import is_book_favorited, toggle_book_favorite
from backend.bookshelf import get_book_shelf_status, add_to_bookshelf
from backend.reviews import get_user_review, create_or_update_review
from urllib.parse import unquote, parse_qs

dash.register_page(__name__, path_template="/book/<book_id>")


# Mapping between frontend shelf types and database values
SHELF_TYPE_MAPPING = {
    'to_read': 'plan-to-read',
    'reading': 'reading',
    'finished': 'completed'
}

# Reverse mapping for display
DISPLAY_SHELF_MAPPING = {
    'plan-to-read': 'Want to Read',
    'reading': 'Currently Reading',
    'completed': 'Finished'
}


def _format_language(language_code):
    """Format language code into readable language name"""
    language_map = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'zh': 'Chinese',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'ko': 'Korean',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish'
    }
    return language_map.get(language_code, language_code.upper() if language_code else 'Unknown')


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
                                'object-fit': 'contain',
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

                        # Rating information (clickable)
                        html.Div([
                            html.Strong("Rating: "),
                            dcc.Link(
                                f"{book_data.get('average_rating', 0):.1f}/5.0 ({book_data.get('rating_count', 0)})",
                                href=f"/reviews/{book_id}",
                                style={
                                    'font-weight': 'bold',
                                    'text-decoration': 'none'
                                },
                                className='rating-color'
                            ) if book_data.get('average_rating') and book_data.get('average_rating') > 0 and book_data.get('rating_count', 0) > 0 else html.Span(
                                "No ratings yet",
                                style={'color': '#666'}
                            )
                        ], className="book-info"),

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

                        # Language
                        html.Div([
                            html.Strong("Language: "),
                            html.Span(_format_language(
                                book_data.get('language', 'en')))
                        ], className="book-info") if book_data.get('language') else html.Div(),

                        # Page count
                        html.Div([
                            html.Strong("Pages: "),
                            html.Span(f"{book_data['page_count']} pages")
                        ], className="book-info") if book_data.get('page_count') else html.Div(),

                        html.Div([
                            html.Strong("ISBN: "),
                            html.Span(book_data.get('isbn') or 'Not available')
                        ], className="book-info"),

                        html.Div([
                            html.Strong("Description: "),
                            dcc.Markdown(
                                book_data.get('description') or 'No description available.',
                                className="book-description"
                            )
                        ], className="book-info-block"),

                        # Action buttons section
                        html.Div([
                            # Favorite button
                            html.Button(
                                id={'type': 'book-favorite-btn',
                                    'book_id': book_id},
                                className="favorite-btn",
                                style={
                                    'margin-top': '20px',
                                    'margin-right': '10px',
                                    'padding': '10px 20px',
                                    'border': 'none',
                                    'border-radius': '5px',
                                    'cursor': 'pointer',
                                    'font-size': '14px',
                                    'font-weight': 'bold'
                                }
                            ),
                            # Bookshelf button
                            html.Button(
                                id={'type': 'book-bookshelf-btn',
                                    'book_id': book_id},
                                className="bookshelf-btn",
                                style={
                                    'margin-top': '20px',
                                    'padding': '10px 20px',
                                    'border': 'none',
                                    'border-radius': '5px',
                                    'cursor': 'pointer',
                                    'font-size': '14px',
                                    'font-weight': 'bold',
                                    'background-color': '#6c757d',
                                    'color': 'white'
                                }
                            ),
                            html.Div([
                                html.Div(
                                    id={'type': 'book-favorite-feedback',
                                        'book_id': book_id},
                                    style={'margin-top': '10px',
                                           'font-size': '12px'}
                                ),
                                html.Div(
                                    id={'type': 'book-bookshelf-feedback',
                                        'book_id': book_id},
                                    style={'margin-top': '10px',
                                           'font-size': '12px'}
                                )
                            ])
                        ], className="action-buttons-section")

                    ], className="book-details", style={'flex': '1', 'margin-left': '30px'})

                ], className="book-detail-container secondary-bg", style={
                    'display': 'flex',
                    'max-width': '800px',
                    'margin': '0 auto',
                    'padding': '30px',
                    'border-radius': '12px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.1)'
                }),

                # Store for modal visibility
                dcc.Store(id={'type': 'modal-visible',
                          'book_id': book_id}, data=False),

                # Store for review removal confirmation
                dcc.Store(id={'type': 'review-removal-confirmation-visible',
                          'book_id': book_id}, data=False),
                dcc.Store(id={'type': 'pending-status-change',
                          'book_id': book_id}, data=None),

                # Bookshelf overlay modal
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Add to Bookshelf", style={
                                'margin': '0 0 20px 0',
                                'color': '#333'
                            }),
                            html.Button("×", id={'type': 'close-bookshelf-modal', 'book_id': book_id},
                                        style={
                                'position': 'absolute',
                                'top': '15px',
                                'right': '15px',
                                'background': 'none',
                                'border': 'none',
                                          'font-size': '24px',
                                          'cursor': 'pointer',
                                          'color': '#666'
                            }),

                            # Status selection
                            html.Div([
                                html.H4("Choose status:", style={
                                        'margin-bottom': '15px'}),
                                html.Div([
                                    html.Button("Want to Read",
                                                id={'type': 'select-status',
                                                    'book_id': book_id, 'status': 'to_read'},
                                                className="status-btn",
                                                style={
                                                    'display': 'block',
                                                    'width': '100%',
                                                    'margin-bottom': '10px',
                                                    'padding': '12px',
                                                    'background': '#17a2b8',
                                                    'color': 'white',
                                                    'border': 'none',
                                                    'border-radius': '5px',
                                                    'cursor': 'pointer',
                                                    'font-size': '14px'
                                                }),
                                    html.Button("Currently Reading",
                                                id={'type': 'select-status',
                                                    'book_id': book_id, 'status': 'reading'},
                                                className="status-btn",
                                                style={
                                                    'display': 'block',
                                                    'width': '100%',
                                                    'margin-bottom': '10px',
                                                    'padding': '12px',
                                                    'background': '#ffc107',
                                                    'color': 'black',
                                                    'border': 'none',
                                                    'border-radius': '5px',
                                                    'cursor': 'pointer',
                                                    'font-size': '14px'
                                                }),
                                    html.Button("Mark as Finished",
                                                id={'type': 'select-status',
                                                    'book_id': book_id, 'status': 'finished'},
                                                className="status-btn",
                                                style={
                                                    'display': 'block',
                                                    'width': '100%',
                                                    'margin-bottom': '15px',
                                                    'padding': '12px',
                                                    'background': '#28a745',
                                                    'color': 'white',
                                                    'border': 'none',
                                                    'border-radius': '5px',
                                                    'cursor': 'pointer',
                                                    'font-size': '14px'
                                                })
                                ])
                            ], id={'type': 'status-selection', 'book_id': book_id}),

                            # Review form (shown when marking as finished)
                            html.Div([
                                html.H4("Write a Review", style={
                                        'margin-bottom': '15px'}),
                                html.Div([
                                    html.Label("Rating (required):", style={
                                               'display': 'block', 'margin-bottom': '5px'}),
                                    dcc.Dropdown(
                                        id={'type': 'rating-dropdown',
                                            'book_id': book_id},
                                        options=[
                                            {'label': '⭐ 1 - Poor', 'value': 1},
                                            {'label': '⭐⭐ 2 - Fair', 'value': 2},
                                            {'label': '⭐⭐⭐ 3 - Good', 'value': 3},
                                            {'label': '⭐⭐⭐⭐ 4 - Very Good',
                                                'value': 4},
                                            {'label': '⭐⭐⭐⭐⭐ 5 - Excellent',
                                                'value': 5}
                                        ],
                                        placeholder="Select a rating",
                                        style={'margin-bottom': '15px'}
                                    ),
                                    html.Label("Review (optional):", style={
                                               'display': 'block', 'margin-bottom': '5px'}),
                                    dcc.Textarea(
                                        id={'type': 'review-text',
                                            'book_id': book_id},
                                        placeholder="Write your review here...",
                                        style={
                                            'width': '100%',
                                            'height': '100px',
                                            'margin-bottom': '15px',
                                            'padding': '10px',
                                            'border': '1px solid #ddd',
                                            'border-radius': '5px',
                                            'resize': 'vertical'
                                        }
                                    ),
                                    html.Button("Save Review & Mark as Finished",
                                                id={'type': 'save-review',
                                                    'book_id': book_id},
                                                style={
                                                    'width': '100%',
                                                    'padding': '12px',
                                                    'background': '#28a745',
                                                    'color': 'white',
                                                    'border': 'none',
                                                    'border-radius': '5px',
                                                    'cursor': 'pointer',
                                                    'font-size': '14px'
                                                })
                                ])
                            ], id={'type': 'review-form', 'book_id': book_id},
                                style={'display': 'none'}),

                            html.Div(id={'type': 'modal-feedback', 'book_id': book_id},
                                     style={'margin-top': '15px'})
                        ], style={
                            'position': 'relative',
                            'padding': '25px',
                            'border-radius': '10px',
                            'box-shadow': '0 4px 20px rgba(0,0,0,0.3)',
                            'max-width': '400px',
                            'width': '90%',
                            'max-height': '80vh',
                            'overflow-y': 'auto'
                        }, className='secondary-bg')
                    ], id={'type': 'modal-overlay', 'book_id': book_id})
                ], id={'type': 'bookshelf-modal', 'book_id': book_id}, style={'display': 'none'}),

                # Review removal confirmation modal
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Remove Review?", style={
                                'margin': '0 0 20px 0',
                                'color': '#dc3545'
                            }),
                            html.P("Changing from 'Finished' to another status will remove your rating and review for this book. Are you sure you want to continue?",
                                   style={
                                       'margin-bottom': '20px',
                                       'line-height': '1.5'
                                   }),
                            html.Div([
                                html.Button("Cancel",
                                            id={'type': 'cancel-review-removal',
                                                'book_id': book_id},
                                            style={
                                                'padding': '10px 20px',
                                                'margin-right': '10px',
                                                'background': '#6c757d',
                                                'color': 'white',
                                                'border': 'none',
                                                'border-radius': '4px',
                                                'cursor': 'pointer'
                                            }),
                                html.Button("Continue & Remove Review",
                                            id={'type': 'confirm-review-removal',
                                                'book_id': book_id},
                                            style={
                                                'padding': '10px 20px',
                                                'background': '#dc3545',
                                                'color': 'white',
                                                'border': 'none',
                                                'border-radius': '4px',
                                                'cursor': 'pointer'
                                            })
                            ], style={'text-align': 'right'})
                        ], style={
                            'position': 'relative',
                            'padding': '25px',
                            'border-radius': '10px',
                            'box-shadow': '0 4px 20px rgba(0,0,0,0.3)',
                            'max-width': '400px',
                            'width': '90%'
                        }, className='secondary-bg')
                    ], style={
                        'position': 'fixed',
                        'top': '0',
                        'left': '0',
                        'width': '100%',
                        'height': '100%',
                        'background': 'rgba(0,0,0,0.5)',
                        'display': 'flex',
                        'justify-content': 'center',
                        'align-items': 'center',
                        'z-index': '1001'  # Higher than bookshelf modal
                    })
                ], id={'type': 'review-removal-modal', 'book_id': book_id}, style={'display': 'none'}),

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
    """Get book details from database including core enhanced fields"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT b.book_id, b.title, b.isbn, b.genre, 
                       EXTRACT(YEAR FROM b.release_date) as release_year,
                       b.description, b.cover_url, b.author_id,
                       COALESCE(b.language, 'en') as language, 
                       b.page_count, b.average_rating, b.rating_count,
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
    """Get all books with the same title as the current book including core enhanced fields"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT b.book_id, b.title, b.isbn, b.genre, 
                       EXTRACT(YEAR FROM b.release_date) as release_year,
                       b.description, b.cover_url, b.author_id,
                       COALESCE(b.language, 'en') as language, 
                       b.page_count,
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
                                'object-fit': 'contain',
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
        'padding': '20px',
        'border-radius': '12px',
        'box-shadow': '0 4px 12px rgba(0,0,0,0.1)'
    }, className='secondary-bg')


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


# Callback to set initial bookshelf button state
@callback(
    [Output({'type': 'book-bookshelf-btn',
            'book_id': dash.dependencies.MATCH}, 'children')],
    [Input({'type': 'book-favorite-store', 'book_id': dash.dependencies.MATCH}, 'id')],
    [State('user-session', 'data')],
    prevent_initial_call=False
)
def set_initial_bookshelf_button_state(store_id, session_data):
    """Set the initial state of the bookshelf button"""
    book_id = store_id['book_id']

    if not session_data or not session_data.get('logged_in'):
        return ["📚 Add to Bookshelf (Login Required)"]

    user_id = session_data.get('user_id')
    success, message, shelf_type = get_book_shelf_status(user_id, book_id)

    if success and shelf_type:
        status_text = DISPLAY_SHELF_MAPPING.get(shelf_type, shelf_type)
        return [f"📚 Manage: {status_text}"]
    else:
        return ["📚 Add to Bookshelf"]


# Callback to handle bookshelf button clicks (open modal)
@callback(
    Output({'type': 'modal-visible', 'book_id': dash.dependencies.MATCH}, 'data'),
    Input({'type': 'book-bookshelf-btn',
          'book_id': dash.dependencies.MATCH}, 'n_clicks'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def open_bookshelf_modal(n_clicks, session_data):
    """Open bookshelf modal when button is clicked"""
    if not n_clicks:
        return dash.no_update

    if not session_data or not session_data.get('logged_in'):
        return dash.no_update

    return True


# Callback to update modal visibility based on store
@callback(
    [Output({'type': 'bookshelf-modal', 'book_id': dash.dependencies.MATCH}, 'style'),
     Output({'type': 'modal-overlay', 'book_id': dash.dependencies.MATCH}, 'style')],
    Input({'type': 'modal-visible', 'book_id': dash.dependencies.MATCH}, 'data'),
    prevent_initial_call=False
)
def update_modal_visibility(is_visible):
    """Update modal style based on visibility state"""
    if is_visible:
        modal_style = {'display': 'block'}
        overlay_style = {
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'background': 'rgba(0,0,0,0.5)',
            'display': 'flex',
            'justify-content': 'center',
            'align-items': 'center',
            'z-index': '1000'
        }
        return modal_style, overlay_style
    else:
        return {'display': 'none'}, {'display': 'none'}


# Callback to close bookshelf modal
@callback(
    [Output({'type': 'modal-visible', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'status-selection',
            'book_id': dash.dependencies.MATCH}, 'style'),
     Output({'type': 'review-form', 'book_id': dash.dependencies.MATCH}, 'style')],
    Input({'type': 'close-bookshelf-modal',
          'book_id': dash.dependencies.MATCH}, 'n_clicks'),
    prevent_initial_call=True
)
def close_bookshelf_modal(n_clicks):
    """Close bookshelf modal and reset forms"""
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    return (
        False,                # Hide modal
        {'display': 'block'},  # Show status selection
        {'display': 'none'}   # Hide review form
    )


# Callback to handle status selection
@callback(
    [Output({'type': 'status-selection', 'book_id': dash.dependencies.MATCH}, 'style', allow_duplicate=True),
     Output({'type': 'review-form', 'book_id': dash.dependencies.MATCH},
            'style', allow_duplicate=True),
     Output({'type': 'modal-feedback',
            'book_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'book-bookshelf-btn', 'book_id': dash.dependencies.MATCH},
            'children', allow_duplicate=True),
     Output({'type': 'modal-visible', 'book_id': dash.dependencies.MATCH},
            'data', allow_duplicate=True),
     Output({'type': 'review-removal-modal',
            'book_id': dash.dependencies.MATCH}, 'style', allow_duplicate=True),
     Output({'type': 'review-removal-confirmation-visible',
            'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'pending-status-change', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True)],
    [Input({'type': 'select-status', 'book_id': dash.dependencies.MATCH, 'status': 'to_read'}, 'n_clicks'),
     Input({'type': 'select-status', 'book_id': dash.dependencies.MATCH,
           'status': 'reading'}, 'n_clicks'),
     Input({'type': 'select-status', 'book_id': dash.dependencies.MATCH, 'status': 'finished'}, 'n_clicks')],
    [State('user-session', 'data')],
    prevent_initial_call=True
)
def handle_status_selection(to_read_clicks, reading_clicks, finished_clicks, session_data):
    """Handle status selection - add to shelf or show review form"""
    ctx = dash.callback_context
    if not ctx.triggered or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Determine which button was clicked
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_data = eval(trigger_id)
    book_id = button_data['book_id']
    status = button_data['status']
    user_id = session_data.get('user_id')

    # Check current bookshelf status
    success, message, current_status = get_book_shelf_status(user_id, book_id)

    # If user currently has book as "completed" (finished) and wants to change to something else, show confirmation
    if success and current_status == 'completed' and status != 'finished':
        # Store the pending status change and show confirmation modal
        return (
            dash.no_update,  # Status selection modal stays
            dash.no_update,  # Review form stays
            dash.no_update,  # Feedback stays
            dash.no_update,  # Button stays
            dash.no_update,  # Modal visibility stays
            {'display': 'block'},  # Show confirmation modal
            True,  # Mark confirmation as visible
            {'book_id': book_id, 'new_status': status}  # Store pending change
        )

    if status == 'finished':
        # Show review form for finished books
        return (
            {'display': 'none'},  # Hide status selection
            {'display': 'block'},  # Show review form
            html.Div("Please provide a rating to mark as finished.",
                     style={'color': '#666'}),
            dash.no_update,
            dash.no_update,
            dash.no_update,  # Keep confirmation modal hidden
            dash.no_update,  # Don't change confirmation state
            dash.no_update   # No pending change
        )
    else:
        # Add to bookshelf with selected status (convert to database format)
        db_status = SHELF_TYPE_MAPPING.get(status, status)
        success, message = add_to_bookshelf(user_id, book_id, db_status)

        if success:
            status_text = {
                'to_read': 'Want to Read',
                'reading': 'Currently Reading'
            }.get(status, status)

            return (
                dash.no_update,
                dash.no_update,
                html.Div(message, style={'color': 'green'}),
                f"📚 Manage: {status_text}",
                False,  # Close modal
                dash.no_update,  # Keep confirmation modal hidden
                dash.no_update,  # Don't change confirmation state
                dash.no_update   # No pending change
            )
        else:
            return (
                dash.no_update,
                dash.no_update,
                html.Div(message, style={'color': 'red'}),
                dash.no_update,
                dash.no_update,
                dash.no_update,  # Keep confirmation modal hidden
                dash.no_update,  # Don't change confirmation state
                dash.no_update   # No pending change
            )


# Callback to handle review submission
@callback(
    [Output({'type': 'modal-feedback', 'book_id': dash.dependencies.MATCH}, 'children', allow_duplicate=True),
     Output({'type': 'book-bookshelf-btn', 'book_id': dash.dependencies.MATCH},
            'children', allow_duplicate=True),
     Output({'type': 'modal-visible', 'book_id': dash.dependencies.MATCH},
            'data', allow_duplicate=True),
     Output({'type': 'rating-dropdown',
            'book_id': dash.dependencies.MATCH}, 'value'),
     Output({'type': 'review-text', 'book_id': dash.dependencies.MATCH}, 'value')],
    Input({'type': 'save-review', 'book_id': dash.dependencies.MATCH}, 'n_clicks'),
    [State({'type': 'rating-dropdown', 'book_id': dash.dependencies.MATCH}, 'value'),
     State({'type': 'review-text', 'book_id': dash.dependencies.MATCH}, 'value'),
     State('user-session', 'data')],
    prevent_initial_call=True
)
def handle_review_submission(n_clicks, rating, review_text, session_data):
    """Handle review submission and mark book as finished"""
    if not n_clicks or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if not rating:
        return (
            html.Div("Please select a rating before submitting.",
                     style={'color': 'red'}),
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update
        )

    # Get book_id from callback context
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    book_id = eval(trigger_id)['book_id']
    user_id = session_data.get('user_id')

    # Save review and add to bookshelf in single operation
    try:
        # First add to bookshelf
        shelf_success, shelf_message = add_to_bookshelf(
            user_id, book_id, 'completed')

        if not shelf_success:
            return (
                html.Div(f"Error updating bookshelf: {shelf_message}", style={
                         'color': 'red'}),
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update
            )

        # Then save review
        review_success, review_message = create_or_update_review(
            user_id, book_id, rating, review_text)

        if not review_success:
            return (
                html.Div(f"Bookshelf updated but error saving review: {review_message}", style={
                         'color': 'orange'}),
                "📚 Manage: Finished",
                dash.no_update,
                dash.no_update,
                dash.no_update
            )

        return (
            html.Div("Review saved and book marked as finished!",
                     style={'color': 'green'}),
            "📚 Manage: Finished",
            False,  # Close modal
            None,  # Clear rating
            ""     # Clear review text
        )
    except Exception as e:
        return (
            html.Div(f"Unexpected error: {str(e)}", style={'color': 'red'}),
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update
        )


# Callback to handle remove from bookshelf
@callback(
    [Output({'type': 'book-bookshelf-feedback', 'book_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'book-bookshelf-btn', 'book_id': dash.dependencies.MATCH},
            'children', allow_duplicate=True),
     Output({'type': 'modal-visible', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True)],
    Input({'type': 'remove-from-shelf',
          'book_id': dash.dependencies.ALL}, 'n_clicks'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_remove_from_bookshelf(remove_clicks, session_data):
    """Handle removing book from bookshelf and associated review"""
    ctx = dash.callback_context
    if not ctx.triggered or not any(remove_clicks or []) or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update

    # Get book_id from callback context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    book_id = eval(trigger_id)['book_id']
    user_id = session_data.get('user_id')

    # Remove from bookshelf (this will also remove the review if it exists)
    from backend.bookshelf import remove_from_bookshelf
    from backend.reviews import delete_review

    # First remove the review (which will update book ratings)
    review_success, review_message = delete_review(user_id, book_id)

    # Then remove from bookshelf
    shelf_success, shelf_message = remove_from_bookshelf(user_id, book_id)

    if shelf_success:
        return (
            html.Div("Book removed from bookshelf and review deleted!",
                     style={'color': 'green'}),
            "📚 Add to Bookshelf",
            False  # Close modal
        )
    else:
        return (
            html.Div(f"Error removing from bookshelf: {shelf_message}", style={
                     'color': 'red'}),
            dash.no_update,
            dash.no_update
        )


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


# Callback to handle confirmation modal cancellation
@callback(
    [Output({'type': 'review-removal-modal', 'book_id': dash.dependencies.MATCH}, 'style'),
     Output({'type': 'review-removal-confirmation-visible',
            'book_id': dash.dependencies.MATCH}, 'data'),
     Output({'type': 'pending-status-change', 'book_id': dash.dependencies.MATCH}, 'data')],
    [Input({'type': 'cancel-review-removal',
           'book_id': dash.dependencies.MATCH}, 'n_clicks')],
    prevent_initial_call=True
)
def cancel_review_removal(n_clicks):
    """Cancel the review removal confirmation"""
    if n_clicks:
        return (
            {'display': 'none'},  # Hide confirmation modal
            False,  # Mark as not visible
            {}  # Clear pending change
        )
    return dash.no_update, dash.no_update, dash.no_update


# Callback to handle confirmation modal confirmation
@callback(
    [Output({'type': 'review-removal-modal', 'book_id': dash.dependencies.MATCH}, 'style', allow_duplicate=True),
     Output({'type': 'modal-feedback', 'book_id': dash.dependencies.MATCH},
            'children', allow_duplicate=True),
     Output({'type': 'book-bookshelf-btn', 'book_id': dash.dependencies.MATCH},
            'children', allow_duplicate=True),
     Output({'type': 'modal-visible', 'book_id': dash.dependencies.MATCH},
            'data', allow_duplicate=True),
     Output({'type': 'review-removal-confirmation-visible',
            'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'pending-status-change', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True)],
    [Input({'type': 'confirm-review-removal',
           'book_id': dash.dependencies.MATCH}, 'n_clicks')],
    [State({'type': 'pending-status-change', 'book_id': dash.dependencies.MATCH}, 'data'),
     State('user-session', 'data')],
    prevent_initial_call=True
)
def confirm_review_removal(n_clicks, pending_change, session_data):
    """Confirm the review removal and proceed with status change"""
    if not n_clicks or not pending_change or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    book_id = pending_change.get('book_id')
    new_status = pending_change.get('new_status')
    user_id = session_data.get('user_id')

    if not book_id or not new_status:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Import needed functions
    from backend.bookshelf import update_shelf_status
    from backend.reviews import delete_review

    # Remove the review first
    review_success, review_message = delete_review(user_id, book_id)

    # Update the shelf status
    db_status = SHELF_TYPE_MAPPING.get(new_status, new_status)
    status_success, status_message = update_shelf_status(
        user_id, book_id, db_status)

    if review_success and status_success:
        status_text = {
            'to_read': 'Want to Read',
            'reading': 'Currently Reading'
        }.get(new_status, new_status)

        return (
            {'display': 'none'},  # Hide confirmation modal
            html.Div("Review removed and status updated successfully.",
                     style={'color': 'green'}),
            f"📚 Manage: {status_text}",
            False,  # Close main modal
            False,  # Mark confirmation as not visible
            {}  # Clear pending change
        )
    else:
        error_msg = f"Error: {review_message if not review_success else status_message}"
        return (
            {'display': 'none'},  # Hide confirmation modal
            html.Div(error_msg, style={'color': 'red'}),
            dash.no_update,
            dash.no_update,
            False,  # Mark confirmation as not visible
            {}  # Clear pending change
        )

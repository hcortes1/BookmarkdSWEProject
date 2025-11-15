# pages/book_detail.py
import dash
from dash import html, dcc, Input, Output, State, callback
from backend.books import get_book_details, get_books_with_same_title
from backend.favorites import is_book_favorited, toggle_book_favorite
from backend.bookshelf import get_book_shelf_status, add_to_bookshelf
from backend.reviews import get_user_review, create_or_update_review
from backend.friends import get_friends_list
from backend.recommendations import create_book_recommendation
from backend.rewards import award_completion_rating, award_review, award_recommendation
from backend.gutenberg import search_and_download_gutenberg_html
from backend.rentals import check_book_rental_status, rent_book, get_rental_info_for_confirmation
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

        # Check if HTML is available from Gutenberg
        if not book_data.get('html_path'):
            search_and_download_gutenberg_html(
                book_data['title'], book_data['author_name'], book_id)
            # Refresh book data after potential update
            book_data = get_book_details(book_id)

        # Check rental status (will be updated by callback)
        rental_status = None  # Will be set by callback

        return html.Div([
            # Store for favorite status feedback
            dcc.Store(id={'type': 'book-favorite-store', 'book_id': book_id}),
            dcc.Store(id='book-navigation-store', data={'book_id': book_id}),
            dcc.Store(id={'type': 'error-modal-visible',
                      'book_id': book_id}, data=False),
            dcc.Store(id={'type': 'rental-modal-visible',
                      'book_id': book_id}, data=False),
            dcc.Store(id={'type': 'rental-status-store',
                      'book_id': book_id}, data=None),

            html.Div([
                html.Div([
                    # Book cover
                    html.Div([
                        html.Img(
                            src=book_data.get(
                                'cover_url') or '/assets/svg/default-book.svg',
                            className="book-cover-large"
                        )
                    ], className="book-cover-container"),

                    # Book details
                    html.Div([
                        # Favorite button (top right corner of book details)
                        html.Button(
                            id={'type': 'book-favorite-btn',
                                'book_id': book_id},
                            className="favorite-btn-book-detail",
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

                        html.H1(book_data['title'], className="book-title"),
                        html.H2([
                            "by ",
                            dcc.Link(
                                book_data.get('author_name', 'Unknown Author'),
                                href=f"/author/{book_data.get('author_id')}?from_book={book_id}" if book_data.get(
                                    'author_id') else "#",
                                className="author-link"
                            ) if book_data.get('author_id') else book_data.get('author_name', 'Unknown Author')
                        ], className="book-author"),

                        # Rating information (clickable)
                        html.Div([
                            html.Strong("Rating: "),
                            dcc.Link(
                                f"{book_data.get('average_rating', 0):.1f}/5.0 ({book_data.get('rating_count', 0)})",
                                href=f"/reviews/{book_id}",
                                className='rating-color rating-link'
                            ) if book_data.get('average_rating') and book_data.get('average_rating') > 0 and book_data.get('rating_count', 0) > 0 else html.Span(
                                "No ratings yet",
                                style={'color': 'var(--text-color-secondary)'}
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
                                book_data.get(
                                    'description') or 'No description available.',
                                className="book-description"
                            )
                        ], className="book-info-block"),

                        # Action buttons section
                        html.Div([
                            # Bookshelf button
                            html.Button(
                                id={'type': 'book-bookshelf-btn',
                                    'book_id': book_id},
                                className="bookshelf-btn",
                                style={
                                    'background': 'var(--link-color)',
                                    'color': 'white',
                                    'fontSize': '1rem',
                                    'padding': '10px 24px',
                                    'borderRadius': '6px',
                                    'border': 'none',
                                    'fontWeight': 'bold',
                                    'marginRight': '12px',
                                    'cursor': 'pointer',
                                    'boxShadow': '0 2px 4px rgba(25, 118, 210, 0.08)'
                                }
                            ),
                            html.Button(
                                "Recommend",
                                id={'type': 'book-recommend-btn',
                                    'book_id': book_id},
                                className="recommend-btn blue-btn",
                                style={
                                    'background': 'var(--link-color)',
                                    'color': 'white',
                                    'fontSize': '1rem',
                                    'padding': '10px 24px',
                                    'borderRadius': '6px',
                                    'border': 'none',
                                    'fontWeight': 'bold',
                                    'marginRight': '12px',
                                    'cursor': 'pointer',
                                    'boxShadow': '0 2px 4px rgba(25, 118, 210, 0.08)'
                                }
                            ),
                            # Read/Rent button - will be updated by callback
                            html.Div(
                                id={'type': 'read-rent-button-container',
                                    'book_id': book_id},
                                children=[],  # Will be populated by callback
                                style={'display': 'inline-flex', 'alignItems': 'center',
                                       'marginRight': '12px', 'verticalAlign': 'middle'}
                            ),
                            html.Div([
                                html.Div(
                                    id={'type': 'book-favorite-feedback',
                                        'book_id': book_id},
                                    className="feedback-text"
                                ),
                                html.Div(
                                    id={'type': 'book-bookshelf-feedback',
                                        'book_id': book_id},
                                    className="feedback-text"
                                ),
                                html.Div(
                                    id={'type': 'book-recommend-feedback',
                                        'book_id': book_id},
                                    className="feedback-text"
                                )
                            ])
                        ], className="action-buttons-section", style={'display': 'flex', 'alignItems': 'center'})

                    ], className="book-details", style={'position': 'relative'})

                ], className="book-detail-container secondary-bg"),

                # Store for modal visibility
                dcc.Store(id={'type': 'modal-visible',
                              'book_id': book_id}, data=False),

                # Store for review removal confirmation
                dcc.Store(id={'type': 'review-removal-confirmation-visible',
                              'book_id': book_id}, data=False),
                dcc.Store(id={'type': 'pending-status-change',
                              'book_id': book_id}, data=None),
                dcc.Store(id={'type': 'modal-mode',
                              'book_id': book_id}, data='add'),

                # Store for recommendation modal visibility
                dcc.Store(id={'type': 'recommend-modal-visible',
                              'book_id': book_id}, data=False),

                # Bookshelf overlay modal
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Add to Bookshelf",
                                    className="modal-header"),
                            html.Button("×", id={'type': 'close-bookshelf-modal', 'book_id': book_id},
                                        className="close-modal-btn"),

                            # Status selection
                            html.Div([
                                html.H4("Choose status:",
                                        className="modal-subheader"),
                                html.Div([
                                    html.Button("Want to Read",
                                                id={'type': 'select-status',
                                                    'book_id': book_id, 'status': 'to_read'},
                                                className="status-btn"),
                                    html.Button("Currently Reading",
                                                id={'type': 'select-status',
                                                    'book_id': book_id, 'status': 'reading'},
                                                className="status-btn reading"),
                                    html.Button("Mark as Finished",
                                                id={'type': 'select-status',
                                                    'book_id': book_id, 'status': 'finished'},
                                                className="status-btn finished"),
                                ])
                            ], id={'type': 'status-selection', 'book_id': book_id}),

                            # Review form (shown when marking as finished)
                            html.Div([
                                html.H4("Write a Review",
                                        className="modal-subheader"),
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
                                        className="review-textarea"
                                    ),
                                    html.Button("Save Review & Mark as Finished",
                                                id={'type': 'save-review',
                                                    'book_id': book_id},
                                                className="save-review-btn"),
                                    html.Button("Change Status",
                                                id={'type': 'change-status',
                                                    'book_id': book_id},
                                                className="change-status-btn")
                                ])
                            ], id={'type': 'review-form', 'book_id': book_id},
                                style={'display': 'none'}),

                            html.Div(id={'type': 'modal-feedback', 'book_id': book_id},
                                     className="modal-feedback")
                        ], className='secondary-bg modal-content')
                    ], id={'type': 'modal-overlay', 'book_id': book_id}, className="modal-overlay")
                ], id={'type': 'bookshelf-modal', 'book_id': book_id}, style={'display': 'none'}),

                # Review removal confirmation modal
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3(
                                "Remove Review?", className="modal-header review-removal-header"),
                            html.P("Changing from 'Finished' to another status will remove your rating and review for this book. Are you sure you want to continue?",
                                   className="modal-description"),
                            html.Div([
                                html.Button("Cancel",
                                            id={'type': 'cancel-review-removal',
                                                'book_id': book_id},
                                            className="modal-action-btn"),
                                html.Button("Continue & Remove Review",
                                            id={'type': 'confirm-review-removal',
                                                'book_id': book_id},
                                            className="confirm-btn")
                            ], className="modal-buttons-right")
                        ], className='secondary-bg modal-content')
                    ], className="review-removal-modal")
                ], id={'type': 'review-removal-modal', 'book_id': book_id}, style={'display': 'none'}),

                # Recommendation modal
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Recommend Book",
                                    className="modal-header"),
                            html.Button("×", id={'type': 'close-recommend-modal', 'book_id': book_id},
                                        className="close-modal-btn"),

                            # Friend selection
                            html.Div([
                                html.H4("Select friends to recommend to:",
                                        className="modal-subheader"),
                                html.Div(
                                    id={'type': 'friends-list-container',
                                        'book_id': book_id},
                                    children=[
                                        dcc.Checklist(
                                            id={'type': 'friends-checklist',
                                                'book_id': book_id},
                                            options=[],
                                            value=[],
                                            labelStyle={
                                                'display': 'flex', 'align-items': 'center', 'margin-bottom': '8px'}
                                        )
                                    ]
                                )
                            ]),

                            # Reason input
                            html.Div([
                                html.H4("Reason for recommendation (optional):",
                                        className="modal-subheader"),
                                dcc.Textarea(
                                    id={'type': 'recommend-reason',
                                        'book_id': book_id},
                                    placeholder="Tell your friends why you recommend this book...",
                                    className="recommend-reason-textarea",
                                    style={'width': '100%', 'height': '80px',
                                           'resize': 'vertical', 'margin-bottom': '15px'}
                                )
                            ], id={'type': 'recommend-reason-section', 'book_id': book_id}),

                            # Action buttons
                            html.Div([
                                html.Button("Send Recommendation",
                                            id={'type': 'send-recommendations',
                                                'book_id': book_id},
                                            className="send-recommendations")
                            ], id={'type': 'recommend-buttons-section', 'book_id': book_id}, className="modal-buttons-right"),

                            html.Div(id={'type': 'recommend-modal-feedback', 'book_id': book_id},
                                     className="modal-feedback")
                        ], className='secondary-bg modal-content')
                    ], id={'type': 'recommend-modal-overlay', 'book_id': book_id}, className="modal-overlay")
                ], id={'type': 'recommend-modal', 'book_id': book_id}, style={'display': 'none'}),

                # Rental confirmation modal
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3("Rent Book", className="modal-header"),
                            html.Button("×", id={'type': 'close-rental-modal', 'book_id': book_id},
                                        className="close-modal-btn"),
                            html.Div([
                                html.H4("Rental Confirmation",
                                        className="modal-subheader"),
                                html.Div(id={'type': 'rental-confirmation-content', 'book_id': book_id},
                                         className="rental-confirmation-content"),
                                html.Div([
                                    html.Button("Confirm Rental",
                                                id={'type': 'confirm-rental',
                                                    'book_id': book_id},
                                                className="confirm-btn",
                                                style={'background': 'var(--link-color)'})
                                ], className="modal-buttons-right")
                            ]),
                            html.Div(id={'type': 'rental-modal-feedback', 'book_id': book_id},
                                     className="modal-feedback")
                        ], className='secondary-bg modal-content', style={'width': '500px'})
                    ], className="rental-modal-overlay")
                ], id={'type': 'rental-modal', 'book_id': book_id}, style={'display': 'none'}),

                # Error modal
                html.Div([
                    html.Div([
                        html.Div([
                            html.H3(
                                "Error", className="modal-header error-modal-header"),
                            html.Button("×", id={'type': 'close-error-modal', 'book_id': book_id},
                                        className="close-modal-btn"),
                            html.Div(id={'type': 'error-modal-content', 'book_id': book_id},
                                     className="error-modal-content")
                        ], className='secondary-bg modal-content error-modal-content')
                    ], className="error-modal-overlay")
                ], id={'type': 'error-modal', 'book_id': book_id}, style={'display': 'none'}),

                # Other editions/versions section
                html.Div(id='other-editions-section', children=[
                    # This will be populated by a callback
                ], className="other-editions-section")

            ], className="page-container")
        ])

    except Exception as e:
        print(f"Error loading book: {e}")
        return html.Div("Error loading book details", className="error-message")


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
        html.H3("Other Editions", className="other-editions-header"),
        html.Div([
            html.Div([
                dcc.Link([
                    html.Div([
                        html.Img(
                            src=book.get(
                                'cover_url') or '/assets/svg/default-book.svg',
                            className="other-editions-image"
                        ),
                        html.Div([
                            html.H4(book['title'],
                                    className="other-editions-title"),
                            html.P(
                                f"by {book.get('author_name', 'Unknown Author')}", className="other-editions-author"),
                            html.P(
                                f"Published: {str(int(book.get('release_year'))) if book.get('release_year') else 'Unknown'}", className="other-editions-year"),
                            html.P(f"ISBN: {book.get('isbn', 'N/A')}",
                                   className="other-editions-isbn") if book.get('isbn') else None
                        ], style={'flex': '1'})
                    ], className="other-editions-item")
                ], href=f"/book/{book['book_id']}", className="other-editions-item-link")
            ], style={
                'cursor': 'pointer'
            }) for book in other_books
        ])
    ], className='secondary-bg other-editions-container')


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

    # New absolute top-right style for favorite button
    abs_style = {
        'position': 'absolute',
        'top': '20px',
        'right': '20px',
        'background': 'none',
        'border': 'none',
        'font-size': '2rem',
        'cursor': 'pointer',
        'zIndex': 2
    }

    if not session_data or not session_data.get('logged_in'):
        return "❤️", abs_style

    user_id = session_data.get('user_id')
    is_favorited = is_book_favorited(user_id, book_id)

    if is_favorited:
        return "💔", abs_style
    else:
        return "❤️", abs_style


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
        return [f"Manage: {status_text}"]
    else:
        return ["Add to Bookshelf"]


# Callback to handle bookshelf button clicks (open modal)
@callback(
    [Output({'type': 'modal-visible', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'status-selection', 'book_id': dash.dependencies.MATCH},
            'style', allow_duplicate=True),
     Output({'type': 'review-form', 'book_id': dash.dependencies.MATCH},
            'style', allow_duplicate=True),
     Output({'type': 'modal-mode', 'book_id': dash.dependencies.MATCH}, 'data'),
     Output({'type': 'rating-dropdown', 'book_id': dash.dependencies.MATCH},
            'value', allow_duplicate=True),
     Output({'type': 'review-text', 'book_id': dash.dependencies.MATCH}, 'value', allow_duplicate=True)],
    Input({'type': 'book-bookshelf-btn',
          'book_id': dash.dependencies.MATCH}, 'n_clicks'),
    [State('user-session', 'data'),
     State({'type': 'book-favorite-store', 'book_id': dash.dependencies.MATCH}, 'id')],
    prevent_initial_call=True
)
def open_bookshelf_modal(n_clicks, session_data, store_id):
    """Open bookshelf modal when button is clicked"""
    if not n_clicks or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    user_id = session_data.get('user_id')
    book_id = store_id['book_id']

    success, message, shelf_type = get_book_shelf_status(user_id, book_id)

    if success and shelf_type == 'completed':
        review_success, message, review = get_user_review(user_id, book_id)
        rating = review.get('rating') if review_success and review else None
        review_text = review.get(
            'review_text') if review_success and review else ''
        return True, {'display': 'none'}, {'display': 'block'}, 'edit', rating, review_text
    else:
        return True, {'display': 'block'}, {'display': 'none'}, 'add', None, ''


@callback(
    Output({'type': 'save-review', 'book_id': dash.dependencies.MATCH}, 'children'),
    Input({'type': 'modal-mode', 'book_id': dash.dependencies.MATCH}, 'data')
)
def update_save_button_text(mode):
    if mode == 'edit':
        return "Update Review"
    return "Save Review & Mark as Finished"


@callback(
    [Output({'type': 'review-removal-confirmation-visible', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'pending-status-change',
            'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'review-removal-modal', 'book_id': dash.dependencies.MATCH}, 'style', allow_duplicate=True)],
    Input({'type': 'change-status', 'book_id': dash.dependencies.MATCH}, 'n_clicks'),
    State({'type': 'book-favorite-store', 'book_id': dash.dependencies.MATCH}, 'id'),
    prevent_initial_call=True
)
def handle_change_status_click(n_clicks, store_id):
    if n_clicks:
        book_id = store_id['book_id']
        return True, {'action': 'change_status', 'book_id': book_id}, {'display': 'block'}
    return dash.no_update, dash.no_update, dash.no_update


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
            'book_id': dash.dependencies.MATCH}, 'style', allow_duplicate=True),
     Output({'type': 'review-form', 'book_id': dash.dependencies.MATCH}, 'style', allow_duplicate=True)],
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
                f"Manage: {status_text}",
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
            'book_id': dash.dependencies.MATCH}, 'value', allow_duplicate=True),
     Output({'type': 'review-text', 'book_id': dash.dependencies.MATCH},
            'value', allow_duplicate=True),
     Output({'type': 'error-modal-visible',
            'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'error-modal-content', 'book_id': dash.dependencies.MATCH}, 'children', allow_duplicate=True)],
    Input({'type': 'save-review', 'book_id': dash.dependencies.MATCH}, 'n_clicks'),
    [State({'type': 'rating-dropdown', 'book_id': dash.dependencies.MATCH}, 'value'),
     State({'type': 'review-text', 'book_id': dash.dependencies.MATCH}, 'value'),
     State('user-session', 'data'),
     State({'type': 'modal-mode', 'book_id': dash.dependencies.MATCH}, 'data')],
    prevent_initial_call=True
)
def handle_review_submission(n_clicks, rating, review_text, session_data, mode):
    """Handle review submission and mark book as finished"""
    if not n_clicks or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if not rating:
        return (
            dash.no_update,  # modal-feedback
            dash.no_update,  # book-bookshelf-btn
            dash.no_update,  # modal-visible
            dash.no_update,  # rating-dropdown
            dash.no_update,  # review-text
            True,  # error-modal-visible
            "Please select a rating before submitting."  # error-modal-content
        )

    # Get book_id from callback context
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    book_id = eval(trigger_id)['book_id']
    user_id = session_data.get('user_id')

    feedback_text = "Review updated successfully!" if mode == 'edit' else "Review saved and book marked as finished!"

    # Save review and add to bookshelf in single operation
    try:
        if mode == 'add':
            # First add to bookshelf
            shelf_success, shelf_message = add_to_bookshelf(
                user_id, book_id, 'completed')

            if not shelf_success:
                return (
                    dash.no_update,  # modal-feedback
                    dash.no_update,  # book-bookshelf-btn
                    dash.no_update,  # modal-visible
                    dash.no_update,  # rating-dropdown
                    dash.no_update,  # review-text
                    True,  # error-modal-visible
                    # error-modal-content
                    f"Error updating bookshelf: {shelf_message}"
                )

        # Then save review
        review_success, review_message = create_or_update_review(
            user_id, book_id, rating, review_text)

        if not review_success:
            return (
                dash.no_update,  # modal-feedback
                dash.no_update,  # book-bookshelf-btn
                dash.no_update,  # modal-visible
                dash.no_update,  # rating-dropdown
                dash.no_update,  # review-text
                True,  # error-modal-visible
                # error-modal-content
                f"Bookshelf updated but error saving review: {review_message}"
            )

        # Award points
        if mode == 'add':
            award_completion_rating(user_id)
        if review_text and review_text.strip():
            award_review(user_id)

        return (
            html.Div(feedback_text, style={'color': 'green'}),
            "Manage: Finished",
            False,  # Close modal
            None,  # Clear rating
            "",    # Clear review text
            False,  # error-modal-visible
            ""      # error-modal-content
        )
    except Exception as e:
        return (
            dash.no_update,  # modal-feedback
            dash.no_update,  # book-bookshelf-btn
            dash.no_update,  # modal-visible
            dash.no_update,  # rating-dropdown
            dash.no_update,  # review-text
            True,  # error-modal-visible
            f"Unexpected error: {str(e)}"  # error-modal-content
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

    # New absolute top-right style for favorite button
    abs_style = {
        'position': 'absolute',
        'top': '20px',
        'right': '20px',
        'background': 'none',
        'border': 'none',
        'font-size': '2rem',
        'cursor': 'pointer',
        'zIndex': 2
    }

    if result['success']:
        if result['is_favorited']:
            return "💔", abs_style, html.Div(result['message'], style={'color': 'green'})
        else:
            return "❤️", abs_style, html.Div(result['message'], style={'color': 'green'})
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
     Output({'type': 'pending-status-change',
            'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'status-selection', 'book_id': dash.dependencies.MATCH},
            'style', allow_duplicate=True),
     Output({'type': 'review-form', 'book_id': dash.dependencies.MATCH},
            'style', allow_duplicate=True),
     Output({'type': 'error-modal-visible',
            'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'error-modal-content', 'book_id': dash.dependencies.MATCH}, 'children', allow_duplicate=True)],
    [Input({'type': 'confirm-review-removal',
           'book_id': dash.dependencies.MATCH}, 'n_clicks')],
    [State({'type': 'pending-status-change', 'book_id': dash.dependencies.MATCH}, 'data'),
     State('user-session', 'data')],
    prevent_initial_call=True
)
def confirm_review_removal(n_clicks, pending_change, session_data):
    """Confirm the review removal and proceed with status change"""
    if not n_clicks or not pending_change or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    book_id = pending_change.get('book_id')
    new_status = pending_change.get('new_status')
    user_id = session_data.get('user_id')

    # Import needed functions
    from backend.bookshelf import update_shelf_status
    from backend.reviews import delete_review

    if pending_change.get('action') == 'change_status':
        # Remove the review and set status to plan-to-read, then show status selection
        review_success, review_message = delete_review(user_id, book_id)
        if review_success:
            status_success, status_message = update_shelf_status(
                user_id, book_id, 'plan-to-read')
            if status_success:
                return (
                    {'display': 'none'},  # confirmation modal
                    html.Div("Review removed. You can now select a new status.", style={
                             'color': 'blue'}),
                    dash.no_update,  # button
                    dash.no_update,  # modal visible
                    False,
                    {},
                    {'display': 'block'},  # status selection
                    {'display': 'none'}   # review form
                )
            else:
                return (
                    {'display': 'none'},
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    False,
                    {},
                    {'display': 'block'},  # status selection
                    {'display': 'none'},   # review form
                    True,  # error-modal-visible
                    # error-modal-content
                    f"Error updating status: {status_message}"
                )
        else:
            return (
                {'display': 'none'},
                dash.no_update,
                dash.no_update,
                dash.no_update,
                False,
                {},
                dash.no_update,
                dash.no_update,
                True,  # error-modal-visible
                # error-modal-content
                f"Error removing review: {review_message}"
            )

    if not book_id or not new_status:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

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
            f"Manage: {status_text}",
            False,  # Close main modal
            False,  # Mark confirmation as not visible
            {},  # Clear pending change
            dash.no_update,  # status selection
            dash.no_update,  # review form
            False,  # error-modal-visible
            ""      # error-modal-content
        )
    else:
        error_msg = f"Error: {review_message if not review_success else status_message}"
        return (
            {'display': 'none'},  # Hide confirmation modal
            dash.no_update,
            dash.no_update,
            dash.no_update,
            False,  # Mark confirmation as not visible
            {},  # Clear pending change
            dash.no_update,
            dash.no_update,
            True,  # error-modal-visible
            error_msg  # error-modal-content
        )


# Recommendation modal callbacks
@callback(
    [Output({'type': 'recommend-modal', 'book_id': dash.dependencies.MATCH}, 'style'),
     Output({'type': 'recommend-modal-visible', 'book_id': dash.dependencies.MATCH}, 'data')],
    [Input({'type': 'book-recommend-btn', 'book_id': dash.dependencies.MATCH}, 'n_clicks'),
     Input({'type': 'close-recommend-modal', 'book_id': dash.dependencies.MATCH}, 'n_clicks')],
    [State({'type': 'recommend-modal-visible',
           'book_id': dash.dependencies.MATCH}, 'data')],
    prevent_initial_call=True
)
def toggle_recommend_modal(open_clicks, close_clicks, is_visible):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, is_visible

    triggered_prop = ctx.triggered[0]['prop_id']

    # Check if it's a close action
    if 'close-recommend-modal' in triggered_prop:
        return {'display': 'none'}, False
    elif 'book-recommend-btn' in triggered_prop:
        return {'display': 'block'}, True
    else:
        return dash.no_update, is_visible


@callback(
    [Output({'type': 'friends-checklist', 'book_id': dash.dependencies.MATCH}, 'options'),
     Output({'type': 'friends-checklist',
            'book_id': dash.dependencies.MATCH}, 'value'),
     Output({'type': 'recommend-reason-section',
            'book_id': dash.dependencies.MATCH}, 'style'),
     Output({'type': 'recommend-buttons-section', 'book_id': dash.dependencies.MATCH}, 'style')],
    [Input({'type': 'recommend-modal-visible',
           'book_id': dash.dependencies.MATCH}, 'data')],
    [State('user-session', 'data'),
     State('book-navigation-store', 'data')],
    prevent_initial_call=True
)
def populate_friends_list(is_visible, user_session, book_data):
    if not is_visible or not user_session or not user_session.get('logged_in'):
        return [], [], {'display': 'none'}, {'display': 'none'}

    user_id = user_session['user_id']
    friends = get_friends_list(user_id)
    book_id = book_data.get('book_id')

    if not friends:
        return [], [], {'display': 'none'}, {'display': 'none'}

    # Create options for checklist
    options = []
    for friend in friends:
        # Check if friend has already completed this book
        has_completed = False
        if book_id:
            success, message, shelf_type = get_book_shelf_status(
                friend['friend_id'], book_id)
            has_completed = success and shelf_type == 'completed'

        # Create label with completion status
        username_display = friend['username']
        if has_completed:
            username_display += ' (completed)'

        options.append({
            'label': [
                html.Img(
                    src=friend.get(
                        'profile_image_url') or '/assets/svg/default-profile.svg',
                    style={'width': '30px', 'height': '30px', 'border-radius': '50%',
                           'margin-left': '20px', 'margin-right': '10px', 'vertical-align': 'middle'}
                ),
                html.Span(username_display, style={'vertical-align': 'middle'})
            ],
            'value': str(friend['friend_id']),
            'disabled': has_completed  # Disable if already completed
        })

    return options, [], {'display': 'block'}, {'display': 'block'}


@callback(
    [Output({'type': 'recommend-modal', 'book_id': dash.dependencies.MATCH}, 'style', allow_duplicate=True),
     Output({'type': 'recommend-modal-visible',
            'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'book-recommend-feedback',
            'book_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'recommend-reason',
            'book_id': dash.dependencies.MATCH}, 'value'),
     Output({'type': 'error-modal-visible',
            'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'error-modal-content', 'book_id': dash.dependencies.MATCH}, 'children', allow_duplicate=True),
     Output({'type': 'recommend-modal-feedback', 'book_id': dash.dependencies.MATCH}, 'children')],  # Add this output
    [Input({'type': 'send-recommendations',
           'book_id': dash.dependencies.MATCH}, 'n_clicks')],
    [State({'type': 'friends-checklist', 'book_id': dash.dependencies.MATCH}, 'value'),
     State({'type': 'recommend-reason', 'book_id': dash.dependencies.MATCH}, 'value'),
     State('user-session', 'data'),
     State('book-navigation-store', 'data')],
    prevent_initial_call=True
)
def send_recommendations(send_clicks, selected_friend_ids, reason, user_session, book_data):
    if not send_clicks or not user_session or not user_session.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Get selected friends
    selected_friends = [
        int(fid) for fid in selected_friend_ids] if selected_friend_ids else []

    if not selected_friends:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, "", html.Div("Please select at least one friend.", style={'color': 'red'})

    book_id = book_data['book_id']
    sender_id = user_session['user_id']
    reason = reason.strip() if reason else ""

    # Send recommendations to selected friends
    success_count = 0
    failed_message = None
    
    for friend_id in selected_friends:
        result = create_book_recommendation(
            sender_id, friend_id, book_id, reason)
        
        if result['success']:
            success_count += 1
            award_recommendation(sender_id)
        else:
            # Capture the failure message (likely moderation rejection)
            failed_message = result.get('message', 'Failed to send recommendation')
            break  # Stop trying if moderation fails

    # If moderation failed, show error and keep modal open
    if failed_message and success_count == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, "", html.Div(failed_message, style={'color': 'red', 'marginTop': '10px'})

    # If some or all succeeded
    if success_count == len(selected_friends):
        message = f"Book recommendation sent to {success_count} friend{'s' if success_count != 1 else ''}!"
        return {'display': 'none'}, False, html.Div(message, style={'color': 'green'}), "", False, "", ""
    elif success_count > 0:
        message = f"Book recommendation sent to {success_count} out of {len(selected_friends)} friends."
        return {'display': 'none'}, False, html.Div(message, style={'color': 'orange'}), "", False, "", ""
    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, "", html.Div("Failed to send recommendations. Please try again.", style={'color': 'red'})


# Callback to control error modal visibility
@callback(
    [Output({'type': 'error-modal', 'book_id': dash.dependencies.MATCH}, 'style'),
     Output({'type': 'error-modal-visible', 'book_id': dash.dependencies.MATCH}, 'data')],
    Input({'type': 'error-modal-visible',
          'book_id': dash.dependencies.MATCH}, 'data'),
    prevent_initial_call=False
)
def control_error_modal_visibility(is_visible):
    """Control the visibility of the error modal"""
    if is_visible:
        return {'display': 'block'}, is_visible
    else:
        return {'display': 'none'}, is_visible


# Callback to close error modal
@callback(
    [Output({'type': 'error-modal-visible', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'error-modal-content', 'book_id': dash.dependencies.MATCH}, 'children')],
    Input({'type': 'close-error-modal',
          'book_id': dash.dependencies.MATCH}, 'n_clicks'),
    prevent_initial_call=True
)
def close_error_modal(n_clicks):
    """Close the error modal when X button is clicked"""
    if n_clicks:
        return False, ""
    return dash.no_update, dash.no_update


# Callback to set initial rental status and Read/Rent button
@callback(
    [Output({'type': 'read-rent-button-container', 'book_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'rental-status-store', 'book_id': dash.dependencies.MATCH}, 'data')],
    [Input({'type': 'rental-status-store', 'book_id': dash.dependencies.MATCH}, 'id'),
     Input('user-session', 'data')],
    [State({'type': 'book-favorite-store', 'book_id': dash.dependencies.MATCH}, 'id')],
    prevent_initial_call=False
)
def set_initial_rental_status(store_id, session_data, book_store_id):
    """Set the initial rental status and show appropriate Read/Rent button"""
    book_id = store_id['book_id']

    # Check if book has available HTML
    book_data = get_book_details(book_id)
    if not book_data or not book_data.get('html_path'):
        return html.Div(), None

    if not session_data or not session_data.get('logged_in'):
        # Not logged in - show disabled rent button
        return html.Button(
            "Rent Book",
            className="rent-btn blue-btn",
            disabled=True,
            style={
                'background': '#ccc',
                'color': '#666',
                'fontSize': '1rem',
                'padding': '10px 24px',
                'borderRadius': '6px',
                'border': 'none',
                'fontWeight': 'bold',
                'marginRight': '0',
                'marginTop': '20px',
                'cursor': 'not-allowed'
            }
        ), None

    user_id = session_data.get('user_id')
    rental_status = check_book_rental_status(user_id, book_id)

    if rental_status:
        # User has active rental - show Read button
        return dcc.Link(
            "Read",
            href=f"/read/{book_id}",
            className="read-btn blue-btn",
            style={
                'background': 'var(--link-color)',
                'color': 'white',
                'fontSize': '1rem',
                'padding': '10px 24px',
                'borderRadius': '6px',
                'border': 'none',
                'fontWeight': 'bold',
                'marginRight': '0',
                'marginTop': '20px',
                'textDecoration': 'none',
                'cursor': 'pointer',
                'boxShadow': '0 2px 4px rgba(25, 118, 210, 0.08)'
            }
        ), rental_status
    else:
        # No active rental - show Rent button
        return html.Button(
            "Rent Book",
            id={'type': 'rent-book-btn', 'book_id': book_id},
            className="rent-btn blue-btn",
            style={
                'background': 'var(--link-color)',
                'color': 'white',
                'fontSize': '1rem',
                'padding': '10px 24px',
                'borderRadius': '6px',
                'border': 'none',
                'fontWeight': 'bold',
                'marginRight': '0',
                'marginTop': '20px',
                'cursor': 'pointer',
                'boxShadow': '0 2px 4px rgba(25, 118, 210, 0.08)'
            }
        ), None


# Callback to open rental modal
@callback(
    [Output({'type': 'rental-modal-visible', 'book_id': dash.dependencies.MATCH}, 'data'),
     Output({'type': 'rental-confirmation-content', 'book_id': dash.dependencies.MATCH}, 'children')],
    [Input({'type': 'rent-book-btn', 'book_id': dash.dependencies.MATCH}, 'n_clicks'),
     Input({'type': 'close-rental-modal',
           'book_id': dash.dependencies.MATCH}, 'n_clicks')],
    [State({'type': 'rental-modal-visible', 'book_id': dash.dependencies.MATCH}, 'data'),
     State('user-session', 'data'),
     State({'type': 'book-favorite-store', 'book_id': dash.dependencies.MATCH}, 'id')],
    prevent_initial_call=False
)
def toggle_rental_modal(open_clicks, close_clicks, is_visible, session_data, store_id):
    """Toggle rental modal visibility and populate confirmation content"""
    if open_clicks is None and close_clicks is None:
        return dash.no_update, dash.no_update

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered_prop = ctx.triggered[0]['prop_id']
    book_id = store_id['book_id']

    # Check if it's a close action
    if 'close-rental-modal' in triggered_prop:
        return False, dash.no_update
    elif 'rent-book-btn' in triggered_prop and session_data and session_data.get('logged_in'):
        # Opening modal - get rental info
        user_id = session_data['user_id']
        rental_info = get_rental_info_for_confirmation(user_id, book_id)

        if not rental_info['can_afford']:
            content = html.Div([
                html.P("You don't have enough points to rent this book.",
                       style={'color': 'red'}),
                html.P(f"Required: {rental_info['cost']} points"),
                html.P(f"Your balance: {rental_info['current_points']} points")
            ], style={'marginBottom': '20px'})
        else:
            content = html.Div([
                html.P(f"Cost: {rental_info['cost']} points"),
                html.P(
                    f"Rental duration: {rental_info['duration_days']} days"),
                html.P(
                    f"Your current balance: {rental_info['current_points']} points"),
                html.P(f"Balance after rental: {rental_info['points_after']} points",
                       style={'fontSize': 'smaller', 'fontWeight': 'normal'})
            ], style={'marginBottom': '20px'})

        return True, content

    return dash.no_update, dash.no_update


# Callback to control rental modal visibility
@callback(
    Output({'type': 'rental-modal', 'book_id': dash.dependencies.MATCH}, 'style'),
    Input({'type': 'rental-modal-visible',
          'book_id': dash.dependencies.MATCH}, 'data'),
    prevent_initial_call=False
)
def control_rental_modal_visibility(is_visible):
    """Control the visibility of the rental modal"""
    if is_visible:
        return {
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
    else:
        return {'display': 'none'}


# Callback to handle rental confirmation
@callback(
    [Output({'type': 'rental-modal-visible', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True),
     Output({'type': 'rental-modal-feedback',
            'book_id': dash.dependencies.MATCH}, 'children'),
     Output({'type': 'read-rent-button-container',
            'book_id': dash.dependencies.MATCH}, 'children', allow_duplicate=True),
     Output({'type': 'rental-status-store', 'book_id': dash.dependencies.MATCH}, 'data', allow_duplicate=True)],
    Input({'type': 'confirm-rental', 'book_id': dash.dependencies.MATCH}, 'n_clicks'),
    [State('user-session', 'data'),
     State({'type': 'book-favorite-store', 'book_id': dash.dependencies.MATCH}, 'id')],
    prevent_initial_call=True
)
def confirm_rental(n_clicks, session_data, store_id):
    """Handle rental confirmation and update UI"""
    if not n_clicks or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    book_id = store_id['book_id']
    user_id = session_data['user_id']

    success, message = rent_book(user_id, book_id)

    if success:
        # Update to show Read button
        read_button = dcc.Link(
            "Read",
            href=f"/read/{book_id}",
            className="read-btn blue-btn",
            style={
                'background': 'var(--link-color)',
                'color': 'white',
                'fontSize': '1rem',
                'padding': '10px 24px',
                'borderRadius': '6px',
                'border': 'none',
                'fontWeight': 'bold',
                'marginRight': '0',
                'textDecoration': 'none',
                'cursor': 'pointer',
                'boxShadow': '0 2px 4px rgba(25, 118, 210, 0.08)'
            }
        )
        return False, html.Div(message, style={'color': 'green'}), read_button, check_book_rental_status(user_id, book_id)
    else:
        return False, html.Div(message, style={'color': 'red'}), dash.no_update, dash.no_update

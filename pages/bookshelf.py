import dash
from dash import html, dcc, Input, Output, State, callback
import backend.bookshelf as bookshelf_backend
from backend.bookshelf import shelf_mapping, tab_info, empty_messages
import backend.reviews as reviews_backend
from backend.favorites import is_book_favorited
from datetime import datetime, date

dash.register_page(__name__, path='/profile/bookshelf')

layout = html.Div([
    html.H1("My Bookshelf", className="main-title bookshelf-main-title"),

    # Tab navigation
    html.Div([
        html.Button("Want to Read", id="bookshelf-want-to-read-tab",
                    className="card bookshelf-tab active-tab"),
        html.Button("Currently Reading",
                    id="bookshelf-reading-tab", className="card bookshelf-tab"),
        html.Button("Completed", id="bookshelf-completed-tab",
                    className="card bookshelf-tab"),
        html.Button("Rented", id="bookshelf-rented-tab",
                    className="card bookshelf-tab")
    ], className='bookshelf-tabs-container'),

    # Tab content
    html.Div(id='bookshelf-tab-content', children=[
        # This will be populated by callback based on active tab
    ]),

    # Store for active tab
    dcc.Store(id='bookshelf-active-tab', data='want-to-read'),

    # Store for refresh trigger
    dcc.Store(id='bookshelf-refresh-trigger', data=0),

    # Store for book to remove
    dcc.Store(id='book-to-remove', data=None),

    # Confirmation modal
    html.Div([
        html.Div([
            html.H3("Remove Book", className='confirm-modal-title'),
            html.P(id='remove-confirmation-text',
                   children="Are you sure you want to remove this book from your bookshelf?"),
            html.Div([
                html.Button("Cancel",
                            id='cancel-remove',
                            className='btn-cancel'),
                html.Button("Remove",
                            id='confirm-remove',
                            className='btn-remove')
            ], style={'text-align': 'right'})
        ], className='secondary-bg remove-modal-content')
    ], id='remove-confirmation-modal', style={'display': 'none'}, className='remove-confirmation-modal')
], className="app-container bookshelf-app-container")


def create_book_card(book, show_status_buttons=True, reading_status=None, user_id=None):
    """Create a book card component for bookshelf view (horizontal shelf layout)"""

    # Check if the book is favorited
    is_favorited = False
    if user_id and book.get('book_id'):
        try:
            is_favorited = is_book_favorited(user_id, book['book_id'])
        except:
            is_favorited = False

    # Determine card class based on favorite status
    card_class = 'bookshelf-book-card bookshelf-favorited' if is_favorited else 'bookshelf-book-card'

    # Get rating for completed books
    rating_display = None
    if reading_status == 'finished':
        rating = book.get('user_rating')
        if rating:
            rating_display = f"⭐ {rating}/5"

    return html.Div([
        # Remove button as subtle X in top-right corner
        html.Button("×",
                    id={'type': 'remove-book-btn', 'book_id': book['book_id']},
                    className='bookshelf-remove-btn-shelf',
                    title="Remove from bookshelf"
                    ) if show_status_buttons else html.Div(),

        # Wrap entire card content in a link
        dcc.Link([
            html.Div([
                html.Img(
                    src=book.get('cover_url') or '/assets/svg/default-book.svg',
                    className='bookshelf-book-cover',
                    title=f"{book.get('title', 'Unknown')} by {book.get('author_name', 'Unknown')}"
                )
            ], className='bookshelf-cover-wrapper'),
            html.Div([
                html.H4(book.get('title', 'Unknown'), className='bookshelf-book-title',
                       title=book.get('title', 'Unknown')),
                html.P(book.get('author_name', 'Unknown'), className='bookshelf-book-author',
                       title=book.get('author_name', 'Unknown')),
                html.P(rating_display, className='bookshelf-book-rating',
                       style={'fontWeight': 'bold', 'color': '#ffc107'}) if rating_display else None
            ], className='bookshelf-book-info')
        ], href=f"/book/{book.get('book_id')}", style={'textDecoration': 'none', 'color': 'inherit'})
    ], className=card_class)


# Callback to handle tab switching
@callback(
    [Output('bookshelf-want-to-read-tab', 'className'),
     Output('bookshelf-reading-tab', 'className'),
     Output('bookshelf-completed-tab', 'className'),
     Output('bookshelf-rented-tab', 'className'),
     Output('bookshelf-active-tab', 'data')],
    [Input('bookshelf-want-to-read-tab', 'n_clicks'),
     Input('bookshelf-reading-tab', 'n_clicks'),
     Input('bookshelf-completed-tab', 'n_clicks'),
     Input('bookshelf-rented-tab', 'n_clicks')],
    prevent_initial_call=True
)
def update_bookshelf_tabs(want_to_read_clicks, reading_clicks, completed_clicks, rented_clicks):
    """Handle tab switching for bookshelf"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return 'bookshelf-tab active-tab', 'bookshelf-tab', 'bookshelf-tab', 'bookshelf-tab', 'want-to-read'

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'bookshelf-want-to-read-tab':
        return 'bookshelf-tab active-tab', 'bookshelf-tab', 'bookshelf-tab', 'bookshelf-tab', 'want-to-read'
    elif button_id == 'bookshelf-reading-tab':
        return 'bookshelf-tab', 'bookshelf-tab active-tab', 'bookshelf-tab', 'bookshelf-tab', 'reading'
    elif button_id == 'bookshelf-completed-tab':
        return 'bookshelf-tab', 'bookshelf-tab', 'bookshelf-tab active-tab', 'bookshelf-tab', 'completed'
    elif button_id == 'bookshelf-rented-tab':
        return 'bookshelf-tab', 'bookshelf-tab', 'bookshelf-tab', 'bookshelf-tab active-tab', 'rented'

    return 'bookshelf-tab active-tab', 'bookshelf-tab', 'bookshelf-tab', 'bookshelf-tab', 'want-to-read'


# Callback to load bookshelf tab content
@callback(
    Output('bookshelf-tab-content', 'children'),
    [Input('user-session', 'data'),
     Input('bookshelf-refresh-trigger', 'data'),
     Input('bookshelf-active-tab', 'data')],
    prevent_initial_call=False
)
def load_bookshelf_tab_content(session_data, refresh_trigger, active_tab):
    """Load and display user's bookshelf based on active tab"""
    if not session_data or not session_data.get('logged_in'):
        return html.Div([
            html.P("Please log in to view your bookshelf.",
                   className='bookshelf-login-message')
        ])

    user_id = session_data.get('user_id')

    if active_tab == 'rented':
        success, message, books = bookshelf_backend.get_user_rented_books(
            user_id)
    else:
        success, message, bookshelf = bookshelf_backend.get_user_bookshelf(
            user_id)
        if success:
            # Use shared mappings from backend
            shelf_type = shelf_mapping.get(active_tab, 'to_read')
            books = bookshelf.get(shelf_type, [])

    if not success:
        return html.Div([
            html.P(
                f"Error loading bookshelf: {message}", className='bookshelf-error')
        ])

    current_tab_info = tab_info.get(active_tab, tab_info['want-to-read'])

    if not books:
        return html.Div([
            html.Div([
                html.Div("📚", className='bookshelf-empty-icon'),
                html.P(empty_messages.get(
                    active_tab, empty_messages['want-to-read']), className='bookshelf-empty-message')
            ], className='bookshelf-empty')
        ])

    # Create shelf layout with underline like profile page
    book_cards = [
        create_book_card(book, reading_status='rented' if active_tab == 'rented' else shelf_type, 
                        user_id=user_id, show_status_buttons=active_tab != 'rented') 
        for book in books
    ]

    return html.Div([
        html.Div([
            html.Div([
                html.H3(current_tab_info['title'], className="bookshelf-shelf-title"),
                html.Span(f"({len(books)} books)", className="bookshelf-book-count")
            ], className='bookshelf-shelf-header'),
            html.Div([
                html.Div(book_cards, className='bookshelf-books-row')
            ], className='bookshelf-shelf-container')
        ], className='bookshelf-shelf-section')
    ])


# Original callback modified to work with new layout
# (Keeping this for backwards compatibility if needed, but it's now replaced by load_bookshelf_tab_content)


# Callback to show confirmation modal
@callback(
    [Output('remove-confirmation-modal', 'style'),
     Output('book-to-remove', 'data'),
     Output('remove-confirmation-text', 'children')],
    Input({'type': 'remove-book-btn', 'book_id': dash.dependencies.ALL}, 'n_clicks'),
    [State('user-session', 'data'),
     State('bookshelf-tab-content', 'children')],
    prevent_initial_call=True
)
def show_remove_confirmation(remove_clicks, session_data, tab_content):
    """Show confirmation modal when remove button is clicked"""
    ctx = dash.callback_context
    if not ctx.triggered or not any(remove_clicks or []) or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    book_id = eval(trigger_id)['book_id']
    user_id = session_data.get('user_id')

    # Get book details to show in confirmation
    success, message, bookshelf = bookshelf_backend.get_user_bookshelf(user_id)
    if not success:
        return dash.no_update, dash.no_update, dash.no_update

    # Find the specific book and its shelf type
    book_title = "this book"
    book_shelf_type = None
    for shelf_type, books in bookshelf.items():
        for book in books:
            if book['book_id'] == book_id:
                book_title = f'"{book["title"]}"'
                book_shelf_type = shelf_type
                break

    modal_style = {'display': 'flex'}

    # Create confirmation message based on shelf type
    if book_shelf_type == 'finished':
        confirmation_text = f"Are you sure you want to remove {book_title} from your bookshelf? This will also delete your review for this book."
    else:
        confirmation_text = f"Are you sure you want to remove {book_title} from your bookshelf?"

    return modal_style, book_id, confirmation_text


# Callback to hide confirmation modal
@callback(
    Output('remove-confirmation-modal', 'style', allow_duplicate=True),
    Input('cancel-remove', 'n_clicks'),
    prevent_initial_call=True
)
def hide_remove_confirmation(cancel_clicks):
    """Hide confirmation modal when cancel is clicked"""
    if not cancel_clicks:
        return dash.no_update
    return {'display': 'none'}


# Callback to handle confirmed book removal
@callback(
    [Output('bookshelf-refresh-trigger', 'data', allow_duplicate=True),
     Output('remove-confirmation-modal', 'style', allow_duplicate=True)],
    Input('confirm-remove', 'n_clicks'),
    [State('user-session', 'data'),
     State('book-to-remove', 'data'),
     State('bookshelf-refresh-trigger', 'data')],
    prevent_initial_call=True
)
def handle_confirmed_removal(confirm_clicks, session_data, book_id, current_trigger):
    """Handle confirmed book removal"""
    if not confirm_clicks or not book_id or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update

    user_id = session_data.get('user_id')

    # First check what shelf type this book is on
    shelf_success, shelf_message, shelf_type = bookshelf_backend.get_book_shelf_status(
        user_id, book_id)

    # If the book is on the "completed" shelf (finished), also delete the review
    if shelf_success and shelf_type == 'completed':
        # Delete the review first (this will automatically update book ratings via triggers)
        review_success, review_message = reviews_backend.delete_review(
            user_id, book_id)
        # Note: We don't need to check review_success because the review might not exist
        # and that's okay - we still want to remove the book from bookshelf

    # Remove the book from bookshelf
    success, message = bookshelf_backend.remove_from_bookshelf(
        user_id, book_id)

    if success:
        return current_trigger + 1, {'display': 'none'}
    else:
        return dash.no_update, {'display': 'none'}

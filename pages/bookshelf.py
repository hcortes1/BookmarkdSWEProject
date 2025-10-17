import dash
from dash import html, dcc, Input, Output, State, callback
import backend.bookshelf as bookshelf_backend
import backend.reviews as reviews_backend

dash.register_page(__name__, path='/profile/bookshelf')

layout = html.Div([
    html.Div([
        html.H1("My Bookshelf", className="main-title", style={
            'text-align': 'center',
            'margin-bottom': '30px',
            'color': '#333'
        }),

        # Tab navigation
        html.Div([
            html.Button("Want to Read", id="bookshelf-want-to-read-tab", className="bookshelf-tab active-tab",
                        style={'margin-right': '5px'}),
            html.Button("Currently Reading", id="bookshelf-reading-tab", className="bookshelf-tab",
                        style={'margin-right': '5px'}),
            html.Button("Completed", id="bookshelf-completed-tab",
                        className="bookshelf-tab")
        ], style={
            'display': 'flex',
            'justify-content': 'center',
            'margin-bottom': '30px',
            'border-bottom': '1px solid #ddd',
            'padding-bottom': '10px'
        }),

        # Tab content
        html.Div(id='bookshelf-tab-content', children=[
            # This will be populated by callback based on active tab
        ]),

        # Store for active tab
        dcc.Store(id='bookshelf-active-tab', data='want-to-read'),

        # Store for refresh trigger
        dcc.Store(id='bookshelf-refresh-trigger', data=0),

        # Store for book to remove
        dcc.Store(id='book-to-remove', data=None)

    ], className="app-container", style={'max-width': '1200px', 'margin': '0 auto', 'padding': '20px'}),

    # Confirmation modal
    html.Div([
        html.Div([
            html.H3("Remove Book", style={
                    'margin': '0 0 15px 0', 'color': '#333'}),
            html.P(id='remove-confirmation-text',
                   children="Are you sure you want to remove this book from your bookshelf?"),
            html.Div([
                html.Button("Cancel",
                            id='cancel-remove',
                            style={
                               'padding': '10px 20px',
                               'margin-right': '10px',
                               'background': '#6c757d',
                               'color': 'white',
                               'border': 'none',
                               'border-radius': '4px',
                               'cursor': 'pointer'
                            }),
                html.Button("Remove",
                            id='confirm-remove',
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
            'background': 'white',
            'padding': '25px',
            'border-radius': '8px',
            'box-shadow': '0 4px 12px rgba(0,0,0,0.15)',
            'max-width': '400px',
            'width': '90%'
        })
    ], id='remove-confirmation-modal', style={'display': 'none'})
])


def create_book_card(book, show_status_buttons=True):
    """Create a book card component for grid bookshelf view"""
    return html.Div([
        # Remove button as subtle X in top-right corner
        html.Button("×",
                    id={'type': 'remove-book-btn', 'book_id': book['book_id']},
                    style={
                        'position': 'absolute',
                        'top': '5px',
                        'right': '5px',
                        'width': '20px',
                        'height': '20px',
                        'border': 'none',
                        'border-radius': '50%',
                        'background': 'rgba(220, 53, 69, 0.9)',
                        'color': 'white',
                        'font-size': '12px',
                        'font-weight': 'bold',
                        'cursor': 'pointer',
                        'display': 'flex',
                        'align-items': 'center',
                        'justify-content': 'center',
                        'z-index': '10',
                        'transition': 'all 0.2s ease',
                        'opacity': '0',
                        'box-shadow': '0 2px 4px rgba(0,0,0,0.2)'
                    },
                    className='bookshelf-remove-btn',
                    title="Remove from bookshelf"
                    ) if show_status_buttons else html.Div(),

        # Wrap entire card content in a link
        dcc.Link([
            # Book cover - prominent display
            html.Div([
                html.Img(
                    src=book.get('cover_url') or '/assets/svg/default-book.svg',
                    style={
                        'width': '100%',
                        'height': '180px',
                        'object-fit': 'contain',
                        'border-radius': '6px',
                        'box-shadow': '0 4px 8px rgba(0,0,0,0.15)',
                        'transition': 'transform 0.2s ease',
                        'background-color': '#f8f9fa'
                    }
                )
            ], style={'margin-bottom': '10px'}),
            
            # Book info - compact
            html.Div([
                html.H4(book['title'], style={
                    'margin': '0 0 5px 0',
                    'font-size': '14px',
                    'color': '#333',
                    'font-weight': '600',
                    'line-height': '1.2',
                    'height': '2.4em',
                    'overflow': 'hidden',
                    'display': '-webkit-box',
                    '-webkit-line-clamp': '2',
                    '-webkit-box-orient': 'vertical'
                }),
                html.P(book.get('author_name', 'Unknown Author'), style={
                    'margin': '0 0 8px 0',
                    'font-size': '12px',
                    'color': '#666',
                    'white-space': 'nowrap',
                    'overflow': 'hidden',
                    'text-overflow': 'ellipsis'
                }),
                # Show user rating if exists - X.X/5.0 format
                html.Div([
                    html.Span(f"{book.get('user_rating', 0):.1f}/5.0", 
                             style={'font-size': '12px', 'color': '#ffc107', 'font-weight': 'bold'}) if book.get('user_rating') else
                    html.Span("Not rated", style={'font-size': '11px', 'color': '#999'})
                ], style={'margin-bottom': '5px'}),
                # Show if has review
                html.Div([
                    html.Span("📝", style={'font-size': '12px', 'margin-right': '3px'}),
                    html.Span("Has review", style={'font-size': '10px', 'color': '#28a745'})
                ]) if book.get('review_text') and book.get('review_text').strip() else html.Div()
            ])
        ], href=f"/book/{book['book_id']}", style={
            'text-decoration': 'none',
            'color': 'inherit',
            'display': 'block'
        })

    ], style={
        'position': 'relative',
        'background': 'white',
        'padding': '15px',
        'border-radius': '8px',
        'box-shadow': '0 2px 6px rgba(0,0,0,0.1)',
        'transition': 'all 0.2s ease',
        'height': '300px',
        'overflow': 'hidden'
    }, className='bookshelf-book-card')


# Callback to handle tab switching
@callback(
    [Output('bookshelf-want-to-read-tab', 'className'),
     Output('bookshelf-reading-tab', 'className'),
     Output('bookshelf-completed-tab', 'className'),
     Output('bookshelf-active-tab', 'data')],
    [Input('bookshelf-want-to-read-tab', 'n_clicks'),
     Input('bookshelf-reading-tab', 'n_clicks'),
     Input('bookshelf-completed-tab', 'n_clicks')],
    prevent_initial_call=True
)
def update_bookshelf_tabs(want_to_read_clicks, reading_clicks, completed_clicks):
    """Handle tab switching for bookshelf"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return 'bookshelf-tab active-tab', 'bookshelf-tab', 'bookshelf-tab', 'want-to-read'

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'bookshelf-want-to-read-tab':
        return 'bookshelf-tab active-tab', 'bookshelf-tab', 'bookshelf-tab', 'want-to-read'
    elif button_id == 'bookshelf-reading-tab':
        return 'bookshelf-tab', 'bookshelf-tab active-tab', 'bookshelf-tab', 'reading'
    elif button_id == 'bookshelf-completed-tab':
        return 'bookshelf-tab', 'bookshelf-tab', 'bookshelf-tab active-tab', 'completed'

    return 'bookshelf-tab active-tab', 'bookshelf-tab', 'bookshelf-tab', 'want-to-read'


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
                   style={'text-align': 'center', 'color': '#666', 'margin-top': '50px'})
        ])

    user_id = session_data.get('user_id')
    success, message, bookshelf = bookshelf_backend.get_user_bookshelf(user_id)

    if not success:
        return html.Div([
            html.P(f"Error loading bookshelf: {message}",
                   style={'text-align': 'center', 'color': 'red', 'margin-top': '50px'})
        ])

    # Map active tab to shelf type
    shelf_mapping = {
        'want-to-read': 'to_read',
        'reading': 'reading',
        'completed': 'finished'
    }

    shelf_type = shelf_mapping.get(active_tab, 'to_read')
    books = bookshelf.get(shelf_type, [])

    # Define tab titles and colors
    tab_info = {
        'want-to-read': {'title': 'Want to Read', 'color': '#17a2b8'},
        'reading': {'title': 'Currently Reading', 'color': '#ffc107'},
        'completed': {'title': 'Completed', 'color': '#28a745'}
    }

    current_tab_info = tab_info.get(active_tab, tab_info['want-to-read'])

    if not books:
        empty_messages = {
            'want-to-read': "Your 'Want to Read' shelf is empty. Start building your reading list by adding books from the book detail pages!",
            'reading': "Your reading shelf is empty. Mark a book as 'Currently Reading' to see it here!",
            'completed': "Your completed shelf is empty. Finish reading books and mark them as 'Completed' to build your library!"
        }

        return html.Div([
            html.Div([
                html.Div("📚", style={
                    'font-size': '4rem',
                    'margin-bottom': '20px',
                    'opacity': '0.3'
                }),
                html.P(empty_messages.get(active_tab, empty_messages['want-to-read']),
                       style={
                           'text-align': 'center', 
                           'color': '#666', 
                           'font-size': '16px',
                           'line-height': '1.5',
                           'max-width': '400px'
                       })
            ], style={
                'display': 'flex',
                'flex-direction': 'column',
                'align-items': 'center',
                'justify-content': 'center',
                'margin-top': '80px'
            })
        ])

    return html.Div([
        html.H2(f"{current_tab_info['title']} ({len(books)})", style={
            'color': current_tab_info['color'],
            'margin-bottom': '20px',
            'border-bottom': f"2px solid {current_tab_info['color']}",
            'padding-bottom': '10px'
        }),
        html.Div([
            create_book_card(book) for book in books
        ], style={
            'display': 'grid',
            'grid-template-columns': 'repeat(auto-fill, minmax(150px, 1fr))',
            'gap': '20px',
            'padding': '10px 0'
        })
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

    modal_style = {
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

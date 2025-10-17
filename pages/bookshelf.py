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

        # Bookshelf sections
        html.Div(id='bookshelf-content', children=[
            # This will be populated by callback based on user session
        ]),

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
    """Create a book card component"""
    return html.Div([
        # Remove button as subtle X in top-right corner
        html.Button("×",
                    id={'type': 'remove-book-btn', 'book_id': book['book_id']},
                    style={
                        'position': 'absolute',
                        'top': '8px',
                        'right': '8px',
                        'width': '24px',
                        'height': '24px',
                        'border': 'none',
                        'border-radius': '50%',
                        'background': 'rgba(220, 53, 69, 0.1)',
                        'color': '#dc3545',
                        'font-size': '16px',
                        'font-weight': 'bold',
                        'cursor': 'pointer',
                        'display': 'flex',
                        'align-items': 'center',
                        'justify-content': 'center',
                        'z-index': '10',
                        'transition': 'all 0.2s ease',
                        'opacity': '0.7'
                    },
                    className='remove-btn-hover',
                    title="Remove from bookshelf"
                    ) if show_status_buttons else html.Div(),

        # Wrap entire card content in a link
        dcc.Link([
            # Book cover and info
            html.Div([
                html.Img(
                    src=book.get(
                        'cover_url') or '/assets/svg/default-book.svg',
                    style={
                        'width': '80px',
                        'height': '120px',
                        'object-fit': 'cover',
                        'border-radius': '6px',
                        'margin-right': '15px'
                    }
                ),
                html.Div([
                    html.H4(book['title'], style={
                        'margin': '0 0 8px 0',
                        'font-size': '16px',
                        'color': '#007bff'
                    }),
                    html.P(f"by {book.get('author_name', 'Unknown Author')}", style={
                        'margin': '0 0 8px 0',
                        'font-size': '14px',
                        'color': '#666'
                    }),
                    html.P(f"Genre: {book.get('genre', 'Unknown')}", style={
                        'margin': '0 0 8px 0',
                        'font-size': '12px',
                        'color': '#888'
                    }),
                    # Show user rating if exists
                    html.Div([
                        html.Span("Your rating: ", style={
                                  'font-size': '12px', 'color': '#666'}),
                        html.Span("⭐" * book['user_rating'] if book.get('user_rating') else "Not rated",
                                  style={'font-size': '12px', 'color': '#ffc107'})
                    ]) if book.get('user_rating') else html.Div(),
                    html.P(f"Added: {book['added_at'].strftime('%m/%d/%Y') if book.get('added_at') else 'Unknown'}",
                           style={
                        'margin': '8px 0 0 0',
                        'font-size': '11px',
                        'color': '#999'
                    })
                ], style={'flex': '1'})
            ], style={
                'display': 'flex',
                'align-items': 'flex-start'
            })
        ], href=f"/book/{book['book_id']}", style={
            'text-decoration': 'none',
            'color': 'inherit',
            'display': 'block'
        })

    ], style={
        'position': 'relative',
        'background': 'white',
        'padding': '20px',
        'border-radius': '8px',
        'box-shadow': '0 2px 8px rgba(0,0,0,0.1)',
        'margin-bottom': '15px',
        'transition': 'box-shadow 0.2s ease'
    })


# Callback to load bookshelf content
@callback(
    Output('bookshelf-content', 'children'),
    [Input('user-session', 'data'),
     Input('bookshelf-refresh-trigger', 'data')],
    prevent_initial_call=False
)
def load_bookshelf_content(session_data, refresh_trigger):
    """Load and display user's bookshelf"""
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

    if not any(bookshelf.values()):
        return html.Div([
            html.P("Your bookshelf is empty. Start adding books from the book detail pages!",
                   style={'text-align': 'center', 'color': '#666', 'margin-top': '50px'})
        ])

    sections = []

    # To Read section
    if bookshelf['to_read']:
        sections.append(
            html.Div([
                html.H2(f"Want to Read ({len(bookshelf['to_read'])})", style={
                    'color': '#17a2b8',
                    'margin-bottom': '20px',
                    'border-bottom': '2px solid #17a2b8',
                    'padding-bottom': '10px'
                }),
                html.Div([
                    create_book_card(book) for book in bookshelf['to_read']
                ])
            ], style={'margin-bottom': '40px'})
        )

    # Currently Reading section
    if bookshelf['reading']:
        sections.append(
            html.Div([
                html.H2(f"Currently Reading ({len(bookshelf['reading'])})", style={
                    'color': '#ffc107',
                    'margin-bottom': '20px',
                    'border-bottom': '2px solid #ffc107',
                    'padding-bottom': '10px'
                }),
                html.Div([
                    create_book_card(book) for book in bookshelf['reading']
                ])
            ], style={'margin-bottom': '40px'})
        )

    # Finished section
    if bookshelf['finished']:
        sections.append(
            html.Div([
                html.H2(f"Finished ({len(bookshelf['finished'])})", style={
                    'color': '#28a745',
                    'margin-bottom': '20px',
                    'border-bottom': '2px solid #28a745',
                    'padding-bottom': '10px'
                }),
                html.Div([
                    create_book_card(book) for book in bookshelf['finished']
                ])
            ], style={'margin-bottom': '40px'})
        )

    return sections


# Callback to show confirmation modal
@callback(
    [Output('remove-confirmation-modal', 'style'),
     Output('book-to-remove', 'data'),
     Output('remove-confirmation-text', 'children')],
    Input({'type': 'remove-book-btn', 'book_id': dash.dependencies.ALL}, 'n_clicks'),
    [State('user-session', 'data'),
     State('bookshelf-content', 'children')],
    prevent_initial_call=True
)
def show_remove_confirmation(remove_clicks, session_data, bookshelf_content):
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
    shelf_success, shelf_message, shelf_type = bookshelf_backend.get_book_shelf_status(user_id, book_id)
    
    # If the book is on the "completed" shelf (finished), also delete the review
    if shelf_success and shelf_type == 'completed':
        # Delete the review first (this will automatically update book ratings via triggers)
        review_success, review_message = reviews_backend.delete_review(user_id, book_id)
        # Note: We don't need to check review_success because the review might not exist
        # and that's okay - we still want to remove the book from bookshelf
    
    # Remove the book from bookshelf
    success, message = bookshelf_backend.remove_from_bookshelf(
        user_id, book_id)

    if success:
        return current_trigger + 1, {'display': 'none'}
    else:
        return dash.no_update, {'display': 'none'}

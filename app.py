import dash
from dash import Dash, html, dcc, Input, Output, State
from argparse import ArgumentParser
import time
import backend.settings as settings_backend
import backend.profile as profile_backend
import backend.friends as friends_backend


app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True
)

app.validation_layout = None


app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="user-session", storage_type="session",
              data={"logged_in": False}),
    dcc.Store(id="search-data-store", storage_type="memory", data={}),
    dcc.Interval(
        id='notifications-interval',
        interval=5*1000,  # Update every 5 seconds
        n_intervals=0
    ),
    # Store notification statuses
    dcc.Store(id='notification-status', data={}),

    html.Div(id='header', className="header", children=[
        html.Nav(className="nav", children=[
            html.Div(className="nav-left", children=[
                dcc.Link([
                    html.Span("Bookmarkd", className="brand-name", style={
                        'font-size': '24px',
                        'font-weight': 'bold',
                        'color': '#007bff',
                        'margin-right': '30px',
                        'text-decoration': 'none'
                    })
                ], href='/', className='brand-link', style={'text-decoration': 'none'}),
                dcc.Link(html.Img(src='/assets/svg/home.svg', className='home-icon',
                         alt='home'), href='/', className='nav-link'),
                dcc.Link('Trending', href='/trending', className='nav-link'),
                dcc.Link('Leaderboards', href='/leaderboards',
                         className='nav-link'),
                dcc.Link('Showcase', href='/showcase', className='nav-link'),
            ]),

            html.Div(className='nav-center', children=[
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='search-type-dropdown',
                            options=[
                                {'label': 'Users', 'value': 'users'},
                                {'label': 'Books', 'value': 'books'},
                                {'label': 'Authors', 'value': 'authors'}
                            ],
                            value='users',
                            clearable=False,
                            searchable=False,
                            className='search-type-dropdown',
                            style={
                                'width': '100px',
                                'margin-right': '8px'
                            }
                        ),
                        dcc.Input(id='header-search', placeholder='Search...',
                                  type='text', className='search-input',
                                  style={'flex': '1'})
                    ], style={'display': 'flex', 'align-items': 'center', 'width': '100%'}),
                    html.Div(id='search-results', className='search-results',
                             style={'display': 'none'})
                ], className='search-container')
            ]),

            html.Div(id='nav-right-container',
                     className='nav-right', children=[])
        ])
    ]),

    dcc.Loading(
        id="page-loading",
        children=[dash.page_container],
        type="default"
    )
])


@app.callback(
    Output('nav-right-container', 'children'),
    Input('user-session', 'data'),
    Input('url', 'pathname')
)
def update_nav_right(user_session, pathname):
    is_logged_in = user_session.get(
        'logged_in', False) if user_session else False

    if is_logged_in:
        # Get user's profile image from session data
        profile_image_url = user_session.get('profile_image_url')
        profile_image_src = '/assets/svg/default-profile.svg'  # Default fallback

        # Use profile image from session if available
        if profile_image_url and profile_image_url.strip():
            profile_image_src = profile_image_url

        # Show user navigation (bookshelf, profile, notifications, settings)
        return [
            dcc.Link(html.Img(src='/assets/svg/bookshelf.svg',
                     className='bookshelf-img', alt='bookshelf'), href='/profile/bookshelf'),
            dcc.Link(
                html.Div(className='profile-circle', children=[
                    html.Img(src=profile_image_src,
                             className='profile-img', alt='profile',
                             style={
                                 'width': '32px',
                                 'height': '32px',
                                 'border-radius': '50%',
                                 'object-fit': 'cover'
                             })
                ]),
                href=f"/profile/view/{user_session.get('username', '')}" if user_session.get(
                    'username') else '/login'
            ),
            html.Div([
                html.Img(src='/assets/svg/bell.svg',
                         className='notifications-img', alt='notifications',
                         style={'cursor': 'pointer'}),
                html.Div(id='notification-badge', className='notification-badge',
                         style={'display': 'none'}),
                html.Div([
                    html.Div(id='notifications-content', children=[])
                ], className='notifications-dropdown', style={
                    'position': 'absolute',
                    'top': '100%',
                    'right': '0',
                    'background': 'white',
                    'border': '1px solid #ddd',
                    'border-radius': '8px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.15)',
                    'z-index': '1000',
                    'min-width': '350px',
                    'max-width': '400px',
                    'margin-top': '2px',
                    'max-height': '400px',
                    'overflow-y': 'auto',
                    'display': 'none'
                })
            ], className='notifications-container',
                style={'position': 'relative', 'display': 'inline-block'}),
            html.Div([
                html.Img(src='/assets/svg/settings.svg',
                         className='settings-img', alt='settings',
                         style={'cursor': 'pointer'}),
                html.Div([
                    dcc.Link('Settings', href='/profile/settings',
                             className='dropdown-item'),
                    html.Hr(style={'margin': '5px 0', 'border-color': '#eee'}),
                    html.Button('Log Out', id='quick-logout-button',
                                className='dropdown-item logout-item',
                                style={
                                    'background': 'none',
                                    'border': 'none',
                                    'width': '100%',
                                    'text-align': 'left',
                                    'padding': '8px 16px',
                                    'cursor': 'pointer',
                                    'color': '#dc3545'
                                })
                ], className='settings-dropdown', style={
                    'position': 'absolute',
                    'top': '100%',
                    'right': '0',
                    'background': 'white',
                    'border': '1px solid #ddd',
                    'border-radius': '8px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.15)',
                    'z-index': '1000',
                    'min-width': '120px',
                    'display': 'none'
                })
            ], className='settings-menu-container',
                style={'position': 'relative', 'display': 'inline-block'})
        ]
    else:
        # Show login/signup button
        return [
            dcc.Link('Log In / Sign Up', href='/login',
                     className='nav-link login-signup-btn')
        ]


@app.callback(
    Output('header-search', 'placeholder'),
    Input('search-type-dropdown', 'value'),
    prevent_initial_call=True
)
def update_search_placeholder(search_type):
    placeholders = {
        'users': 'Search users by username...',
        'books': 'Search books by title...',
        'authors': 'Search authors by name...'
    }
    return placeholders.get(search_type, 'Search...')


@app.callback(
    [Output('search-results', 'children'),
     Output('search-results', 'style'),
     Output('search-data-store', 'data')],
    [Input('header-search', 'value'),
     Input('search-type-dropdown', 'value')],
    prevent_initial_call=True
)
def handle_search(search_value, search_type):
    if not search_value or len(search_value.strip()) < 2:
        return [], {'display': 'none'}, {}

    try:
        search_query = search_value.strip()
        search_data = {'books': [], 'authors': []}

        if search_type == 'users':
            # Search for users only
            users = profile_backend.search_users(search_query)

            if not users:
                return [html.Div("No users found", className='search-no-results')], {'display': 'block'}, {}

            results = []
            for user in users:
                # Ensure we always have a valid profile image URL
                profile_image_url = user.get('profile_image_url')
                if not profile_image_url or not profile_image_url.strip():
                    profile_image_url = '/assets/svg/default-profile.svg'

                user_item = html.Div([
                    html.Img(
                        src=profile_image_url,
                        className='search-user-avatar',
                        style={
                            'width': '30px',
                            'height': '30px',
                            'border-radius': '50%',
                            'object-fit': 'cover',
                            'margin-right': '10px'
                        }
                    ),
                    html.Span(user['username'], className='search-username')
                ], className='search-user-item')

                # Wrap in a link
                user_link = dcc.Link(
                    user_item,
                    href=f"/profile/view/{user['username']}",
                    className='search-user-link',
                    style={'text-decoration': 'none', 'color': 'inherit'}
                )
                results.append(user_link)

            return results, {'display': 'block'}, {}

        elif search_type == 'books':
            # Search for books only
            from backend.openlibrary import search_books_only

            books = search_books_only(search_query)
            search_data['books'] = books

            if not books:
                return [html.Div("No books found", className='search-no-results')], {'display': 'block'}, search_data

            results = []
            for i, book in enumerate(books[:8]):  # Limit to 8 books
                cover_url = book.get(
                    'cover_url') or '/assets/svg/default-book.svg'
                author_name = book.get('author_name') or (
                    book.get('author_names')[0] if book.get(
                        'author_names') else 'Unknown Author'
                )

                book_item = html.Div([
                    html.Img(
                        src=cover_url,
                        className='search-book-cover',
                        style={
                            'width': '30px',
                            'height': '40px',
                            'object-fit': 'contain',
                            'margin-right': '10px',
                            'border-radius': '2px'
                        }
                    ),
                    html.Div([
                        html.Div(book['title'], className='search-book-title'),
                        html.Div(f"by {author_name}", className='search-book-author',
                                 style={'font-size': '12px', 'color': '#666'})
                    ], style={'flex': '1'})
                ], className='search-book-item', style={
                    'display': 'flex',
                    'align-items': 'center',
                    'padding': '8px',
                    'cursor': 'pointer',
                    'border-radius': '4px'
                }, id={'type': 'search-book', 'index': i}, n_clicks=0)

                results.append(book_item)

            return results, {'display': 'block'}, search_data

        elif search_type == 'authors':
            # Search for authors only
            from backend.openlibrary import search_authors_only

            authors = search_authors_only(search_query)
            search_data['authors'] = authors

            if not authors:
                return [html.Div("No authors found", className='search-no-results')], {'display': 'block'}, search_data

            results = []
            for i, author in enumerate(authors[:8]):  # Limit to 8 authors
                image_url = author.get(
                    'image_url') or '/assets/svg/default-author.svg'

                author_item = html.Div([
                    html.Img(
                        src=image_url,
                        className='search-author-image',
                        style={
                            'width': '30px',
                            'height': '30px',
                            'border-radius': '50%',
                            'object-fit': 'cover',
                            'margin-right': '10px'
                        }
                    ),
                    html.Div([
                        html.Div(author['name'],
                                 className='search-author-name'),
                        html.Div(f"Works: {author.get('work_count', 'Unknown')}",
                                 className='search-author-works',
                                 style={'font-size': '12px', 'color': '#666'})
                    ], style={'flex': '1'})
                ], className='search-author-item', style={
                    'display': 'flex',
                    'align-items': 'center',
                    'padding': '8px',
                    'cursor': 'pointer',
                    'border-radius': '4px'
                }, id={'type': 'search-author', 'index': i}, n_clicks=0)

                results.append(author_item)

            return results, {'display': 'block'}, search_data

        return [], {'display': 'none'}, {}

    except Exception as e:
        print(f"Error in search: {e}")
        return [html.Div("Search error", className='search-error')], {'display': 'block'}, {}


@app.callback(
    [Output('notification-badge', 'children'),
     Output('notification-badge', 'style'),
     Output('notifications-content', 'children'),
     Output('notification-status', 'data', allow_duplicate=True)],
    [Input('user-session', 'data'),
     Input('notifications-interval', 'n_intervals')],
    [State('notification-status', 'data')],
    prevent_initial_call=True
)
def update_notifications(user_session, n_intervals, notification_status):
    # print(f"DEBUG: update_notifications called with user_session: {user_session}, n_intervals: {n_intervals}")

    # Check if user is logged in first to avoid component not found errors
    if not user_session or not user_session.get('logged_in', False):
        # print("DEBUG: User not logged in")
        # Return early to prevent component not found errors
        raise dash.exceptions.PreventUpdate

    user_id = user_session.get('user_id')
    # print(f"DEBUG: Extracted user_id: {user_id}")

    if not user_id:
        # print("DEBUG: No user_id found in session")
        raise dash.exceptions.PreventUpdate

    # Clean up old notification statuses (older than 5 seconds)
    import time
    if notification_status is None:
        notification_status = {}

    current_time = time.time()
    cleaned_status = {}
    for sender_id, status_data in notification_status.items():
        # Keep for 5 seconds
        if current_time - status_data.get('timestamp', 0) < 5:
            cleaned_status[sender_id] = status_data

    try:
        # Get pending friend requests - make sure we pass user_id as string
        pending_requests = friends_backend.get_pending_friend_requests(
            str(user_id))
        # print(f"DEBUG: Found {len(pending_requests)} pending requests for user {user_id}")
        # print(f"DEBUG: Pending requests data: {pending_requests}")
        # print(f"DEBUG: Current notification status: {cleaned_status}")

        # Filter out requests that have been responded to
        active_requests = []
        for request in pending_requests:
            sender_id = str(request['sender_id'])
            if sender_id not in cleaned_status:
                active_requests.append(request)

        # Add status messages for recently responded requests
        status_messages = []
        for sender_id, status_data in cleaned_status.items():
            # Get username for the status message
            username = None
            for request in pending_requests:
                if str(request['sender_id']) == sender_id:
                    username = request['username']
                    break

            if username:
                status_color = '#28a745' if status_data['status'] == 'accepted' else '#dc3545'
                status_message = html.Div([
                    html.Div([
                        html.Span("✓ " if status_data['status'] == 'accepted' else "✗ ",
                                  style={'font-weight': 'bold', 'color': status_color}),
                        html.Span(status_data['message'],
                                  style={'color': status_color, 'font-weight': '500'})
                    ], style={'padding': '12px 16px', 'text-align': 'center'})
                ], className='notification-item', style={
                    'background-color': '#f8f9fa',
                    'border-left': f'4px solid {status_color}'
                })
                status_messages.append(status_message)

        if not active_requests and not status_messages:
            # print("DEBUG: No pending requests or status messages found")
            return '', {'display': 'none'}, [html.Div("No notifications", className='no-notifications', style={'padding': '20px', 'text-align': 'center', 'color': '#666'})], cleaned_status

        # Show notification count badge
        total_notifications = len(active_requests) + len(status_messages)
        count = total_notifications
        badge_style = {
            'display': 'block',
            'position': 'absolute',
            'top': '-5px',
            'right': '-5px',
            'background': '#dc3545',
            'color': 'white',
            'border-radius': '50%',
            'width': '18px',
            'height': '18px',
            'font-size': '12px',
            'text-align': 'center',
            'line-height': '18px'
        } if count > 0 else {'display': 'none'}

        # Create notification items for active requests
        notification_items = []

        # Add status messages first
        notification_items.extend(status_messages)

        # Add active friend requests
        for request in active_requests:
            username = request['username']
            # Ensure we always have a valid profile image URL
            profile_image_url = request.get('profile_image_url')
            if not profile_image_url or not profile_image_url.strip():
                profile_image_url = '/assets/svg/default-profile.svg'
            sender_id = request['sender_id']

            notification_item = html.Div([
                # Profile image as clickable link
                dcc.Link([
                    html.Img(
                        src=profile_image_url,
                        style={
                            'width': '40px',
                            'height': '40px',
                            'border-radius': '50%',
                            'object-fit': 'cover',
                            'cursor': 'pointer'
                        }
                    )
                ], href=f'/profile/view/{username}', style={'margin-right': '12px'}),

                # Content area
                html.Div([
                    html.Div([
                        dcc.Link(
                            html.Strong(username, style={
                                        'color': '#1976d2', 'text-decoration': 'none'}),
                            href=f'/profile/view/{username}',
                            style={'text-decoration': 'none'}
                        ),
                        html.Span(" sent you a friend request",
                                  style={'font-size': '14px', 'color': '#666', 'margin-left': '4px'})
                    ], style={'margin-bottom': '8px'}),

                    # Action buttons
                    html.Div([
                        html.Button('Accept',
                                    id={'type': 'accept-friend',
                                        'sender_id': sender_id},
                                    className='btn-accept',
                                    style={
                                        'background': '#28a745',
                                        'color': 'white',
                                        'border': 'none',
                                        'padding': '6px 12px',
                                        'border-radius': '4px',
                                        'margin-right': '8px',
                                        'font-size': '12px',
                                        'cursor': 'pointer'
                                    }),
                        html.Button('Decline',
                                    id={'type': 'decline-friend',
                                        'sender_id': sender_id},
                                    className='btn-decline',
                                    style={
                                        'background': '#dc3545',
                                        'color': 'white',
                                        'border': 'none',
                                        'padding': '6px 12px',
                                        'border-radius': '4px',
                                        'font-size': '12px',
                                        'cursor': 'pointer'
                                    })
                    ], style={'display': 'flex', 'gap': '8px'})
                ], style={'flex': '1'})
            ], className='notification-item', style={
                'display': 'flex',
                'align-items': 'flex-start',
                'padding': '12px 16px',
                'border-bottom': '1px solid #f0f0f0'
            })
            notification_items.append(notification_item)

        return str(count) if count > 0 else '', badge_style, notification_items, cleaned_status

    except Exception as e:
        print(f"Error loading notifications: {e}")
        return '', {'display': 'none'}, [html.Div("Error loading notifications", className='notification-error')], {}


@app.callback(
    [Output('user-session', 'data', allow_duplicate=True),
     Output('notification-status', 'data', allow_duplicate=True)],
    [Input({'type': 'accept-friend', 'sender_id': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'decline-friend', 'sender_id': dash.dependencies.ALL}, 'n_clicks')],
    [State('user-session', 'data'),
     State('notification-status', 'data')],
    prevent_initial_call=True
)
def handle_friend_request_response(accept_clicks, decline_clicks, user_session, notification_status):
    # print(f"DEBUG: handle_friend_request_response called")
    # print(f"DEBUG: accept_clicks: {accept_clicks}")
    # print(f"DEBUG: decline_clicks: {decline_clicks}")

    if not user_session or not user_session.get('logged_in', False):
        # print("DEBUG: User not logged in")
        return dash.no_update, dash.no_update

    ctx = dash.callback_context
    # print(f"DEBUG: callback_context.triggered: {ctx.triggered}")

    if not ctx.triggered:
        print("DEBUG: No trigger detected")
        return dash.no_update, dash.no_update

    # Get the triggered component
    triggered_prop = ctx.triggered[0]['prop_id']
    clicked_value = ctx.triggered[0]['value']

    # print(f"DEBUG: triggered_prop: {triggered_prop}")
    # print(f"DEBUG: clicked_value: {clicked_value}")

    # Only proceed if a button was actually clicked (value is not None and > 0)
    if clicked_value is None or clicked_value == 0:
        # print("DEBUG: Button not actually clicked (value is None or 0)")
        return dash.no_update, dash.no_update

    try:
        # Parse the button ID more safely
        import json
        button_id_str = triggered_prop.split('.')[0]
        button_data = json.loads(button_id_str.replace("'", '"'))

        sender_id = button_data['sender_id']
        is_accept = button_data['type'] == 'accept-friend'

        # print(f"DEBUG: Processing friend request - sender_id: {sender_id}, accept: {is_accept}")

        result = friends_backend.respond_to_friend_request(
            receiver_id=str(user_session['user_id']),
            sender_id=str(sender_id),
            accept=is_accept
        )
        # print(f"DEBUG: Friend request response: {result['message']}")

        # Update notification status to show the message
        import time
        if notification_status is None:
            notification_status = {}

        notification_status[str(sender_id)] = {
            'status': 'accepted' if is_accept else 'declined',
            'message': 'Friend request accepted!' if is_accept else 'Friend request declined.',
            'timestamp': time.time()
        }

        # Return the same session data to trigger a refresh of notifications
        return user_session, notification_status

    except Exception as e:
        print(f"Error responding to friend request: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return dash.no_update, dash.no_update


@app.callback(
    Output('header-search', 'value', allow_duplicate=True),
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def clear_search_on_navigation(pathname):
    # Clear search when navigating to any profile page
    if pathname and ('/profile/' in pathname):
        return ''
    return dash.no_update


@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input({'type': 'search-book', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'search-author', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('search-data-store', 'data')],
    prevent_initial_call=True
)
def handle_search_item_clicks(book_clicks, author_clicks, search_data):
    print(f"DEBUG: Pattern-matching click handler called")
    print(f"DEBUG: Book clicks: {book_clicks}")
    print(f"DEBUG: Author clicks: {author_clicks}")
    print(f"DEBUG: Search data: {search_data}")

    ctx = dash.callback_context
    if not ctx.triggered:
        print("DEBUG: No trigger detected")
        return dash.no_update

    # Get the triggered component
    triggered_prop = ctx.triggered[0]['prop_id']
    clicked_value = ctx.triggered[0]['value']

    print(
        f"DEBUG: Triggered prop: {triggered_prop}, clicked_value: {clicked_value}")

    if clicked_value is None or clicked_value == 0:
        print("DEBUG: Click value is None or 0")
        return dash.no_update

    try:
        import json
        # Parse the component ID
        component_id_str = triggered_prop.split('.')[0]
        component_data = json.loads(component_id_str.replace("'", '"'))

        item_type = component_data['type']
        item_index = component_data['index']

        print(f"DEBUG: Item type: {item_type}, index: {item_index}")

        if item_type == 'search-book':
            books = search_data.get('books', [])
            print(
                f"DEBUG: Book click, index: {item_index}, books count: {len(books)}")

            if item_index < len(books):
                book_data = books[item_index]

                # Store the book in database if it's from API
                if book_data.get('source') == 'openlibrary':
                    from backend.openlibrary import get_or_create_book_with_author_books
                    book_id = get_or_create_book_with_author_books(book_data)
                    if book_id:
                        return f"/book/{book_id}"
                else:
                    # Local book
                    return f"/book/{book_data['book_id']}"

        elif item_type == 'search-author':
            authors = search_data.get('authors', [])
            print(
                f"DEBUG: Author click, index: {item_index}, authors count: {len(authors)}")

            if item_index < len(authors):
                author_data = authors[item_index]
                print(f"DEBUG: Author data: {author_data}")

                # Store the author and their books in database if it's from API
                if author_data.get('source') == 'openlibrary':
                    from backend.openlibrary import get_or_create_author_with_books
                    author_id = get_or_create_author_with_books(author_data)
                    print(f"DEBUG: Got author_id: {author_id}")
                    if author_id:
                        return f"/author/{author_id}"
                else:
                    # Local author
                    return f"/author/{author_data['author_id']}"

        return dash.no_update

    except Exception as e:
        print(f"Error handling search item click: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update


@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Output('user-session', 'data', allow_duplicate=True),
    Input('quick-logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_quick_logout(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update

    # Clear session and redirect to home page
    return '/', {
        "logged_in": False,
        "username": None,
        "user_id": None,
        "email": None,
        "profile_image_url": None,
        "created_at": None
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        prog='app.py',
        description='main application'
    )
    parser.add_argument('--hostname', default='localhost')
    parser.add_argument('--port', default='8050')
    args = parser.parse_args()

    app.run(debug=False, host=args.hostname, port=int(args.port))

import dash
from dash import Dash, html, dcc, Input, Output, State
from argparse import ArgumentParser
import time
import backend.settings as settings_backend
import backend.profile as profile_backend
import backend.friends as friends_backend
import backend.rewards as rewards_backend


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

    html.Div(id='header', className="header", children=[
        html.Nav(className="nav", children=[
            html.Div(id='nav-left-container', className="nav-left", children=[
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

    html.Div(
        id="page-container-wrapper",
        children=[dash.page_container]
    ),

    # Mobile overlay - only shown on mobile devices
    html.Div(
        id="mobile-overlay",
        className="mobile-overlay",
        children=[
            html.Div(
                "Bookmarkd",
                className="mobile-brand"
            ),
            html.Div(
                "is better experienced on a PC or tablet",
                className="mobile-subtext"
            )
        ]
    )
])


@app.callback(
    Output('page-container-wrapper', 'children'),
    Input('url', 'pathname')
)
def update_page_container(pathname):
    # Don't show loading for login page and notifications page
    if pathname in ['/login', '/notifications']:
        return dash.page_container
    else:
        return dcc.Loading(
            id="page-loading",
            children=[dash.page_container],
            type="default"
        )


@app.callback(
    [Output('nav-left-container', 'children'),
     Output('nav-right-container', 'children')],
    Input('user-session', 'data'),
    Input('url', 'pathname')
)
def update_navigation(user_session, pathname):
    is_logged_in = user_session.get(
        'logged_in', False) if user_session else False

    # Base left navigation (always visible)
    left_nav = [
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
    ]

    # Add trending, leaderboards, showcase only for logged-in users
    if is_logged_in:
        left_nav.extend([
            dcc.Link('Trending', href='/trending', className='nav-link'),
            dcc.Link('Leaderboards', href='/leaderboards',
                     className='nav-link'),
            dcc.Link('Showcase', href='/showcase', className='nav-link'),
        ])

    if is_logged_in:
        # Get user's profile image from session data
        profile_image_url = user_session.get('profile_image_url')
        profile_image_src = '/assets/svg/default-profile.svg'  # Default fallback

        # Use profile image from session if available
        if profile_image_url and profile_image_url.strip():
            profile_image_src = profile_image_url

        # Get user rewards for level display
        rewards = rewards_backend.get_user_rewards(user_session.get('user_id'))
        level = rewards.get('level', 1)
        xp = rewards.get('xp', 0)
        points = rewards.get('points', 0)
        _, current_level_xp, xp_to_next = rewards_backend.get_level_progress(
            xp)

        # Show user navigation (bookshelf, profile, notifications, settings)
        right_nav = [
            html.Div(
                html.Span(
                    f"Lvl {level}",
                    className='level-badge',
                    title=f"XP: {current_level_xp}/{xp_to_next} to Level {level + 1}\nPoints: {points}"
                ),
                className='user-level'
            ),
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
                dcc.Link(
                    html.Img(src='/assets/svg/bell.svg',
                             className='notifications-img', alt='notifications',
                             style={'cursor': 'pointer'}),
                    href='/notifications',
                    className='notifications-link'
                ),
                html.Div(id='notification-badge', className='notification-badge',
                         style={'display': 'none'}),
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
        right_nav = [
            dcc.Link('Log In / Sign Up', href='/login',
                     className='nav-link login-signup-btn')
        ]

    return left_nav, right_nav


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
     Output('notification-badge', 'style')],
    Input('user-session', 'data')
)
def update_notifications(user_session):
    # Check if user is logged in first
    if not user_session or not user_session.get('logged_in', False):
        return '', {'display': 'none'}

    user_id = user_session.get('user_id')
    if not user_id:
        return '', {'display': 'none'}

    # Use cached notifications from session immediately after login
    if 'notifications' in user_session:
        notifications_data = user_session['notifications']
    else:
        # Fallback: fetch fresh notifications
        import backend.notifications as notifications_backend
        notifications_data = notifications_backend.get_user_notifications(
            str(user_id))

    count = notifications_data.get('count', 0)
    new_badge_text = str(count) if count > 0 else ''

    if count > 0:
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
        }
        return new_badge_text, badge_style
    else:
        return '', {'display': 'none'}


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
    parser.add_argument('--hostname', default='0.0.0.0')
    parser.add_argument('--port', default='8080')
    args = parser.parse_args()

    app.run(debug=True, host=args.hostname, port=int(args.port))

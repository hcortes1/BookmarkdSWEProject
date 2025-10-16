import dash
from dash import Dash, html, dcc, Input, Output, State
from argparse import ArgumentParser
import backend.settings as settings_backend
import backend.profile as profile_backend


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

    html.Div(id='header', className="header", children=[
        html.Nav(className="nav", children=[
            html.Div(className="nav-left", children=[
                dcc.Link(html.Img(src='/assets/svg/home.svg', className='home-icon',
                         alt='home'), href='/', className='nav-link'),
                dcc.Link('Trending', href='/trending', className='nav-link'),
                dcc.Link('Leaderboards', href='/leaderboards',
                         className='nav-link'),
                dcc.Link('Showcase', href='/showcase', className='nav-link'),
            ]),

            html.Div(className='nav-center', children=[
                html.Div([
                    dcc.Input(id='header-search', placeholder='Search users...',
                              type='text', className='search-input'),
                    html.Div(id='search-results', className='search-results',
                             style={'display': 'none'})
                ], className='search-container')
            ]),

            html.Div(id='nav-right-container',
                     className='nav-right', children=[])
        ])
    ]),

    dash.page_container
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

        # Show user navigation (bookshelf, profile, settings)
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
    Output('search-results', 'children'),
    Output('search-results', 'style'),
    Input('header-search', 'value'),
    prevent_initial_call=True
)
def handle_search(search_value):
    if not search_value or len(search_value.strip()) < 2:
        return [], {'display': 'none'}

    try:
        # Search for users
        users = profile_backend.search_users(search_value.strip())

        if not users:
            return [html.Div("No users found", className='search-no-results')], {'display': 'block'}

        results = []
        for user in users:
            user_item = html.Div([
                html.Img(
                    src=user.get('profile_image_url',
                                 '/assets/svg/default-profile.svg'),
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

        return results, {'display': 'block'}

    except Exception as e:
        print(f"Error in search: {e}")
        return [html.Div("Search error", className='search-error')], {'display': 'block'}


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

    app.run(debug=True, host=args.hostname, port=int(args.port))

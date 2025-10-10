import dash
from dash import Dash, html, dcc, Input, Output
from argparse import ArgumentParser
import backend.settings as settings_backend


app = Dash(
    __name__,
    use_pages=True,
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
                dcc.Input(id='header-search', placeholder='Search...',
                          type='text', className='search-input')
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
        # Get user's profile image
        user_id = user_session.get('user_id')
        profile_image_src = '/assets/svg/profile.svg'  # Default fallback

        if user_id:
            try:
                success, message, image_url = settings_backend.get_user_profile_image_url(
                    user_id)
                if success and image_url and image_url.strip():
                    profile_image_src = image_url
            except Exception as e:
                print(f"Error loading profile image for navigation: {e}")

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
                href='/profile'
            ),
            dcc.Link(html.Img(src='/assets/svg/settings.svg',
                     className='settings-img', alt='settings'), href='/profile/settings')
        ]
    else:
        # Show login/signup button
        return [
            dcc.Link('Log In / Sign Up', href='/login',
                     className='nav-link login-signup-btn')
        ]


if __name__ == "__main__":
    parser = ArgumentParser(
        prog='app.py',
        description='main application'
    )
    parser.add_argument('--hostname', default='localhost')
    parser.add_argument('--port', default='8050')
    args = parser.parse_args()

    app.run(debug=True, host=args.hostname, port=int(args.port))

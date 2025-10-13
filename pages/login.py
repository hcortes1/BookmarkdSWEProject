import dash
from dash import dcc, html, Input, Output, State
import backend.login as login_backend

dash.register_page(__name__, path='/login')


def login_form():
    return html.Div([
        html.H1("Welcome back", className="login-title"),
        html.Label("Username", htmlFor="username", className="login-label"),
        dcc.Input(type="text", id="username", className="login-input",
                  placeholder="Enter your username"),
        html.Label("Password", htmlFor="password", className="login-label"),
        dcc.Input(type="password", id="password",
                  className="login-input", placeholder="Enter your password"),
        html.Button("Log in", id="login-button", className="login-button"),
        html.Div(dcc.Link("Sign up", href='/login?mode=signup',
                 className="signup-link"), style={"marginTop": "10px"})
    ], id='login-form')


def signup_form():
    return html.Div([
        html.H1("Create an account", className="login-title"),
        html.Label("Username", htmlFor="su-username", className="login-label"),
        dcc.Input(type="text", id="su-username",
                  className="login-input", placeholder="Choose a username"),
        html.Label("Email", htmlFor="su-email", className="login-label"),
        dcc.Input(type="email", id="su-email",
                  className="login-input", placeholder="name@example.com"),
        html.Label("Password", htmlFor="su-password", className="login-label"),
        dcc.Input(type="password", id="su-password",
                  className="login-input", placeholder="Create a password"),
        html.Label("Confirm password", htmlFor="su-password-confirm",
                   className="login-label"),
        dcc.Input(type="password", id="su-password-confirm",
                  className="login-input", placeholder="Confirm password"),
        html.Button("Sign up", id="signup-button", className="login-button"),
        html.Div(id='su-feedback', style={'marginTop': '8px'}),
        html.Div(dcc.Link("Log In", href='/login',
                 className="signup-link"), style={"marginTop": "10px"})
    ], id='signup-form')


layout = html.Div([
    dcc.Store(id='auth-mode', data={'mode': 'login'}),
    html.Div(id='auth-box', className='login-box', children=[
        login_form(),
        signup_form(),
    ]),
], className='login-page')


@dash.callback(
    Output('login-form', 'style'),
    Output('signup-form', 'style'),
    Input('url', 'search')
)
def toggle_auth(search):
    if search and 'mode=signup' in search:
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'block'}, {'display': 'none'}


@dash.callback(
    Output('login-button', 'disabled'),
    Input('username', 'value'),
    Input('password', 'value')
)
def set_login_disabled(username, password):
    return not (username and password)


@dash.callback(
    Output('signup-button', 'disabled'),
    Input('su-username', 'value'),
    Input('su-email', 'value'),
    Input('su-password', 'value'),
    Input('su-password-confirm', 'value')
)
def set_signup_disabled(username, email, password, password_confirm):
    return not (username and email and password and password_confirm)


@dash.callback(
    Output('su-feedback', 'children'),
    Output('url', 'pathname', allow_duplicate=True),
    Output('url', 'search', allow_duplicate=True),
    Input('signup-button', 'n_clicks'),
    State('su-username', 'value'),
    State('su-email', 'value'),
    State('su-password', 'value'),
    State('su-password-confirm', 'value'),
    prevent_initial_call=True
)
def handle_signup(n_clicks, username, email, password, password_confirm):
    if not n_clicks:
        return '', dash.no_update, dash.no_update

    # check if passwords match when signing up
    if (password or '') != (password_confirm or ''):
        return html.Span('Passwords do not match', style={'color': 'red', 'fontSize': '12px'}), dash.no_update, dash.no_update

    # call backend signup function
    success, message = login_backend.signup_user(
        username, email, password)

    if success:
        # redirect to login form on successful signup
        return '', '/login', ''
    else:
        # display error message
        return html.Span(message, style={'color': 'red', 'fontSize': '12px'}), dash.no_update, dash.no_update


@dash.callback(
    Output('url', 'pathname', allow_duplicate=True),
    Output('login-form', 'children'),
    Output('user-session', 'data', allow_duplicate=True),
    Input('login-button', 'n_clicks'),
    State('username', 'value'),
    State('password', 'value'),
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    # call backend login function
    success, message, user_data = login_backend.login_user(username, password)

    if success:
        # create comprehensive session data with all user information
        session_data = {
            "logged_in": True,
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "profile_image_url": user_data["profile_image_url"],
            "created_at": user_data["created_at"]
        }
        # update session and redirect to home page on successful login
        return '/', dash.no_update, session_data
    else:
        # display error message below the button
        error_message = html.Div(
            html.Span(message, style={'color': 'red', 'fontSize': '12px'}),
            style={'marginTop': '8px'}
        )

        # return updated form with error message
        updated_form = [
            html.H1("Welcome back", className="login-title"),
            html.Label("Username", htmlFor="username",
                       className="login-label"),
            dcc.Input(type="text", id="username", className="login-input",
                      placeholder="Enter your username", value=username),
            html.Label("Password", htmlFor="password",
                       className="login-label"),
            dcc.Input(type="password", id="password", className="login-input",
                      placeholder="Enter your password", value=password),
            html.Button("Log in", id="login-button", className="login-button"),
            error_message,
            html.Div(dcc.Link("Sign up", href='/login?mode=signup',
                     className="signup-link"), style={"marginTop": "10px"})
        ]

        return dash.no_update, updated_form, dash.no_update

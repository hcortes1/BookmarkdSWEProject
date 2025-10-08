import dash
from dash import dcc, html, Input, Output, State

dash.register_page(__name__, path='/login')


def login_form():
    return html.Div([
        html.H1("Welcome back", className="login-title"),
        html.Label("Username", htmlFor="username", className="login-label"),
        dcc.Input(type="text", id="username", className="login-input", placeholder="Enter your username"),
        html.Label("Password", htmlFor="password", className="login-label"),
        dcc.Input(type="password", id="password", className="login-input", placeholder="Enter your password"),
        html.Button("Log in", id="login-button", className="login-button"),
        html.Div(dcc.Link("Sign up", href='/login?mode=signup', className="signup-link"), style={"marginTop": "10px"})
    ], id='login-form')


def signup_form():
    return html.Div([
        html.H1("Create an account", className="login-title"),
        html.Label("Username", htmlFor="su-username", className="login-label"),
        dcc.Input(type="text", id="su-username", className="login-input", placeholder="Choose a username"),
        html.Label("Email", htmlFor="su-email", className="login-label"),
        dcc.Input(type="email", id="su-email", className="login-input", placeholder="name@example.com"),
        html.Label("Password", htmlFor="su-password", className="login-label"),
        dcc.Input(type="password", id="su-password", className="login-input", placeholder="Create a password"),
        html.Label("Confirm password", htmlFor="su-password-confirm", className="login-label"),
        dcc.Input(type="password", id="su-password-confirm", className="login-input", placeholder="Confirm password"),
        html.Button("Sign up", id="signup-button", className="login-button"),
        html.Div(id='su-feedback', style={'marginTop': '8px'}),
        html.Div(dcc.Link("Log In", href='/login', className="signup-link"), style={"marginTop": "10px"})
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
    Input('signup-button', 'n_clicks'),
    State('su-password', 'value'),
    State('su-password-confirm', 'value')
)
def show_signup_feedback(n_clicks, password, password_confirm):
    if not n_clicks:
        return ''
    if (password or '') != (password_confirm or ''):
        return html.Span('Passwords do not match', style={'color': 'red', 'fontSize': '12px'})
    return ''
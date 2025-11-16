import dash
from dash import dcc, html, Input, Output, State, callback
import backend.login as login_backend

# register page at /change-password to match email reset links
dash.register_page(__name__, path='/change-password')


def layout(token=None):
    """Password reset request and change password page"""
    # determine which form to show based on URL token parameter
    from dash import callback_context
    import flask

    # check if token is in URL query params
    try:
        request = flask.request
        token_from_url = request.args.get('token')
    except:
        token_from_url = None

    show_change_form = token_from_url is not None

    return html.Div([
        dcc.Location(id='reset-url', refresh=False),
        dcc.Store(id='reset-token-store', data=token_from_url),
        html.Div([
            # request reset form (shown first)
            html.Div([
                html.H1("Reset your password", className="login-title"),
                html.P("Enter your email address and we'll send you a link to reset your password.",
                       style={'marginBottom': '20px', 'color': '#666'}),
                html.Label("Email", htmlFor="reset-email",
                           className="login-label"),
                dcc.Input(type="email", id="reset-email",
                          className="login-input", placeholder="your@email.com",
                          debounce=True),
                html.Button("Send reset link", id="reset-request-button",
                            className="login-button"),
                html.Div(id='reset-request-feedback',
                         style={'marginTop': '10px'}),
                html.Div(
                    dcc.Link("Back to Login", href='/login',
                             className="signup-link"),
                    style={"marginTop": "15px"}
                )
            ], id='reset-request-form', style={'display': 'none' if show_change_form else 'block'}),

            # change password form (shown when token is present)
            html.Div([
                html.H1("Create new password", className="login-title"),
                html.Label("New Password", htmlFor="new-password",
                           className="login-label"),
                dcc.Input(type="password", id="new-password",
                          className="login-input", placeholder="Enter new password",
                          debounce=True),
                html.Label("Confirm Password", htmlFor="confirm-password",
                           className="login-label"),
                dcc.Input(type="password", id="confirm-password",
                          className="login-input", placeholder="Confirm new password",
                          debounce=True),
                html.Button("Reset password", id="reset-submit-button",
                            className="login-button"),
                html.Div(id='reset-submit-feedback',
                         style={'marginTop': '10px'}),
            ], id='change-password-form', style={'display': 'block' if show_change_form else 'none'})

        ], className='login-box')
    ], className='login-page')


@callback(
    Output('reset-request-button', 'disabled'),
    Input('reset-email', 'value')
)
def set_request_disabled(email):
    """Disable button if email is empty"""
    return not email


@callback(
    Output('reset-submit-button', 'disabled'),
    Input('new-password', 'value'),
    Input('confirm-password', 'value')
)
def set_submit_disabled(password, confirm):
    """Disable button if passwords are empty"""
    return not (password and confirm)


@callback(
    Output('reset-request-feedback', 'children'),
    Input('reset-request-button', 'n_clicks'),
    State('reset-email', 'value'),
    prevent_initial_call=True
)
def handle_reset_request(n_clicks, email):
    """Handle password reset request"""
    if not n_clicks:
        return ''

    if not email or not email.strip():
        return html.Span('Please enter your email address', style={'color': 'red', 'fontSize': '12px'})

    # request password reset
    success, message = login_backend.request_password_reset(email.strip())

    if success:
        return html.Div([
            html.Span(message, style={
                      'color': 'green', 'fontSize': '12px'}),
            html.Br(),
            html.Span('Check your email for the reset link.',
                      style={'color': '#666', 'fontSize': '12px'})
        ])
    else:
        return html.Span(message, style={'color': 'red', 'fontSize': '12px'})


@callback(
    Output('reset-submit-feedback', 'children'),
    Output('reset-url', 'pathname', allow_duplicate=True),
    Input('reset-submit-button', 'n_clicks'),
    State('new-password', 'value'),
    State('confirm-password', 'value'),
    State('reset-token-store', 'data'),
    prevent_initial_call=True
)
def handle_password_change(n_clicks, new_password, confirm_password, token):
    """Handle actual password reset with token"""
    if not n_clicks:
        return '', dash.no_update

    # validate passwords match
    if new_password != confirm_password:
        return html.Span('Passwords do not match', style={'color': 'red', 'fontSize': '12px'}), dash.no_update

    # validate password length
    if len(new_password) < 6:
        return html.Span('Password must be at least 6 characters', style={'color': 'red', 'fontSize': '12px'}), dash.no_update

    if not token:
        return html.Span('Invalid reset link', style={'color': 'red', 'fontSize': '12px'}), dash.no_update

    # reset password
    success, message = login_backend.reset_password(token, new_password)

    if success:
        return html.Div([
            html.Span(message, style={
                      'color': 'green', 'fontSize': '12px'}),
            html.Br(),
            html.Span('Redirecting to login...', style={
                      'color': '#666', 'fontSize': '12px'})
        ]), '/login'
    else:
        return html.Span(message, style={'color': 'red', 'fontSize': '12px'}), dash.no_update

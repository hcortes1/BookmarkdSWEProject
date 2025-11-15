import dash
from dash import dcc, html, Input, Output, State, callback
import backend.email_utils as email_utils

dash.register_page(__name__, path_template='/verify-email/<token>')


def layout(token=None):
    """Email verification page layout"""
    return html.Div([
        dcc.Store(id='verify-token', data=token),
        html.Div([
            html.Div([
                dcc.Loading(
                    id="verify-loading",
                    type="default",
                    children=[
                        html.Div(id='verify-result')
                    ]
                )
            ], className='login-box')
        ], className='login-page')
    ])


@callback(
    Output('verify-result', 'children'),
    Output('user-session', 'data', allow_duplicate=True),
    Input('verify-token', 'data'),
    State('user-session', 'data'),
    prevent_initial_call='initial_duplicate'
)
def verify_email(token, session_data):
    """Handle email verification"""
    if not token:
        return html.Div([
            html.H1("Invalid Verification Link", style={'color': 'red'}),
            html.P("No verification token provided."),
            html.Div(
                dcc.Link("Go to Login", href='/login',
                         className='login-button'),
                style={'marginTop': '20px'}
            )
        ]), dash.no_update

    # verify the token
    success, message = email_utils.verify_email_token(token)

    if success:
        # if user is logged in, update their session to reflect verified status
        updated_session = session_data
        if session_data and session_data.get('logged_in'):
            updated_session = session_data.copy()
            updated_session['email_verified'] = True

        return html.Div([
            html.H1("Email Verified!", style={'color': 'green'}),
            html.P(message),
            html.P("You can now log in to your account." if not session_data or not session_data.get(
                'logged_in') else "Your email has been verified!"),
            html.Div(
                dcc.Link("Go to Home" if session_data and session_data.get('logged_in') else "Go to Login",
                         href='/' if session_data and session_data.get(
                             'logged_in') else '/login',
                         className='login-button'),
                style={'marginTop': '20px'}
            )
        ]), updated_session
    else:
        return html.Div([
            html.H1("Verification Failed", style={'color': 'red'}),
            html.P(message),
            html.P(
                "Please try signing up again or contact support if the problem persists."),
            html.Div(
                dcc.Link("Go to Login", href='/login',
                         className='login-button'),
                style={'marginTop': '20px'}
            )
        ]), dash.no_update

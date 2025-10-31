import dash
from dash import html, dcc, Input, Output

dash.register_page(__name__, path='/leaderboards')


def welcome_layout():
    """Layout for non-logged-in users"""
    return html.Div([
        html.Div([
            html.H1("Welcome to Bookmarkd", className="welcome-title"),
            html.P("Discover, track, and share your favorite books with friends.", 
                   className="welcome-subtitle"),
            
            html.Div([
                dcc.Link(
                    html.Button("Log In", className="welcome-login-btn"),
                    href='/login'
                ),
                dcc.Link(
                    html.Button("Sign Up", className="welcome-signup-btn"),
                    href='/login?mode=signup'
                )
            ], className="welcome-buttons")
        ], className="welcome-container")
    ], className="welcome-page")


def leaderboards_layout():
    """Layout for logged-in users"""
    return html.Div([
        html.Div([
            html.H1("Leaderboards", className="main-title"),
            html.P("See who's reading the most and discover top reviewers.", 
                   className="page-subtitle")
        ], className="app-container")
    ])


def layout():
    return html.Div([
        # Store for checking login status
        dcc.Store(id='leaderboards-session-check', data={}),
        
        # Content will be dynamically loaded based on login status
        html.Div(id='leaderboards-content')
    ])


# Callback to check login status and show appropriate content
@dash.callback(
    Output('leaderboards-content', 'children'),
    Input('leaderboards-session-check', 'data'),
    Input('user-session', 'data')
)
def update_leaderboards_content(dummy, user_session):
    is_logged_in = user_session.get('logged_in', False) if user_session else False
    
    if is_logged_in:
        return leaderboards_layout()
    else:
        return welcome_layout()
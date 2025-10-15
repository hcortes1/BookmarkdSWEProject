import dash
from dash import html, dcc, Input, Output, State, callback

dash.register_page(__name__, path='/profile')

layout = html.Div([
    html.Div([
        html.H1("My Profile", className="main-title"),

        html.Div([
            # LEFT SIDE – Profile picture and username
            html.Div([
                html.Img(
                    id='profile-image',
                    src='',  # Will be dynamically loaded from session
                    className='profile-user-image'
                ),

                # Username will be dynamically loaded from session
                html.Span("Loading...", id="profile-username", className="profile-username"),
            ], className="profile-info"),

            # RIGHT SIDE – Scrollable friends list
            html.Div([
                html.H2("My Friends", className="friends-title"),
                html.Ul(id="friends-list", className="friends-list")
            ], className="profile-right")

        ], className="profile-header")

    ], className="app-container", id="profile-container")
])


# Callback to dynamically load username from session
@callback(
    Output("profile-username", "children"),
    Input("user-session", "data"),
    prevent_initial_call=False
)
def update_profile_username(session_data):
    """
    Update the profile username display based on session data
    """
    # Check if user is logged in and session data exists
    if not session_data:
        return "Guest"
    
    if not session_data.get('logged_in', False):
        return "Guest"
    
    # Get username directly from session data
    username = session_data.get('username', 'Unknown User')
    
    return username


# Callback to dynamically load profile image from session
@callback(
    Output("profile-image", "src"),
    Input("user-session", "data"),
    prevent_initial_call=False
)
def update_profile_image(session_data):
    """
    Update the profile image from session data
    """
    if not session_data or not session_data.get('logged_in', False):
        return ''  # Default/placeholder image
    
    # Get profile image URL from session
    profile_image_url = session_data.get('profile_image_url', '')
    
    return profile_image_url if profile_image_url else ''
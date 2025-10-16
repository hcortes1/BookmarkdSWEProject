import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import backend.profile as profile_backend

# Register the page with a path template that includes username
dash.register_page(__name__, path_template='/profile/view/<username>')


def layout(username=None):
    return html.Div([
        html.Div([
            html.H1("User Profile", className="main-title"),

            html.Div([
                # LEFT SIDE – Profile picture and username
                html.Div([
                    html.Img(
                        id='user-profile-image',
                        src='',  # Will be dynamically loaded from database
                        className='profile-user-image'
                    ),

                    # Username will be dynamically loaded from database
                    html.Span("Loading...", id="user-profile-username",
                              className="profile-username"),

                    # Display user info
                    html.Div(id="user-profile-info",
                             className="user-profile-info")
                ], className="profile-info"),

                # RIGHT SIDE – Scrollable friends list
                html.Div([
                    html.H2("Friends", className="friends-title"),
                    html.Ul(id="user-friends-list", className="friends-list")
                ], className="profile-right")

            ], className="profile-header"),

            # Hidden div to store the username parameter
            html.Div(id='username-store', children=username,
                     style={'display': 'none'})

        ], className="app-container", id="user-profile-container")
    ])


# Callback to load user profile data based on username parameter
@callback(
    [Output("user-profile-username", "children"),
     Output("user-profile-image", "src"),
     Output("user-profile-info", "children"),
     Output("user-friends-list", "children")],
    Input("username-store", "children"),
    prevent_initial_call=False
)
def load_user_profile(username):
    """
    Load user profile data from database based on username
    """
    if not username:
        return "User not found", "", "No user specified", []

    try:
        # Get user profile data from backend
        user_data = profile_backend.get_user_profile_by_username(username)

        if not user_data:
            return "User not found", "", f"User '{username}' not found", []

        # Format user info
        user_info = html.Div([
            html.P(
                f"Email: {user_data.get('email', 'Not provided')}", className="user-email"),
            html.P(
                f"Member since: {user_data.get('created_at', 'Unknown')[:10] if user_data.get('created_at') else 'Unknown'}", className="user-join-date")
        ])

        # Format friends list
        friends = user_data.get('friends', [])
        friends_list = []

        if friends:
            for friend in friends:
                friend_item = html.Li([
                    dcc.Link([
                        html.Img(
                            src=friend.get('profile_image_url',
                                           '/assets/svg/default-profile.svg'),
                            className='friend-avatar',
                            style={
                                'width': '30px',
                                'height': '30px',
                                'border-radius': '50%',
                                'object-fit': 'cover',
                                'margin-right': '10px'
                            }
                        ),
                        html.Span(friend['username'], className='friend-name')
                    ],
                        href=f"/profile/view/{friend['username']}",
                        className='friend-link',
                        style={'text-decoration': 'none', 'color': 'inherit'})
                ], className="friend-item")
                friends_list.append(friend_item)
        else:
            friends_list = [html.Li("No friends yet", className="no-friends")]

        profile_image_url = user_data.get(
            'profile_image_url', '/assets/svg/default-profile.svg')

        return user_data['username'], profile_image_url, user_info, friends_list

    except Exception as e:
        print(f"Error loading user profile: {e}")
        return "Error loading profile", "", "An error occurred while loading the profile", []

import dash
from dash import html, dcc, Input, Output, State, callback
import backend.profile as profile_backend

# Register only the view path - all profiles use the same structure
dash.register_page(__name__, path_template='/profile/view/<username>')


def layout(username=None, **kwargs):
    # All profiles use the same layout structure
    title = f"{username}'s Profile" if username else "Profile"
    friends_title = f"{username}'s Friends" if username else "Friends"

    return html.Div([
        html.Div([
            html.H1(title, className="main-title"),

            html.Div([
                # LEFT SIDE – Profile picture and username
                html.Div([
                    html.Img(
                        id='profile-image',
                        src='',  # Will be dynamically loaded
                        className='profile-user-image'
                    ),

                    # Username will be dynamically loaded
                    html.Span("Loading...", id="profile-username",
                              className="profile-username"),

                    # Additional user info
                    html.Div(id="profile-user-info",
                             className="user-profile-info"),
                ], className="profile-info"),

                # RIGHT SIDE – Scrollable friends list
                html.Div([
                    html.H2(friends_title, className="friends-title"),
                    html.Ul(id="friends-list", className="friends-list")
                ], className="profile-right")

            ], className="profile-header"),

            # Hidden div to store the username parameter
            html.Div(id='username-store', children=username,
                     style={'display': 'none'})

        ], className="app-container", id="profile-container")
    ])


# Combined callback to handle all profile views using the same path structure
@callback(
    [Output("profile-username", "children"),
     Output("profile-image", "src"),
     Output("profile-user-info", "children"),
     Output("friends-list", "children")],
    [Input("user-session", "data"),
     Input("username-store", "children")],
    prevent_initial_call=False
)
def update_profile_data(session_data, viewed_username):
    """
    Update profile data for any user profile view
    """

    if viewed_username:
        try:
            # Get user profile data from database
            user_data = profile_backend.get_user_profile_by_username(
                viewed_username)

            if not user_data:
                return "User not found", "", html.Div("User not found", style={'color': 'red'}), []

            # Check if this is the logged-in user viewing their own profile
            is_own_profile = (session_data and
                              session_data.get('logged_in', False) and
                              session_data.get('username', '').lower() == viewed_username.lower())

            # Format user info - show member date for all profiles
            created_at = user_data.get('created_at')
            member_since = 'Unknown'
            if created_at:
                if hasattr(created_at, 'strftime'):
                    member_since = created_at.strftime('%Y-%m-%d')
                elif isinstance(created_at, str):
                    member_since = created_at[:10]

            user_info = html.Div([
                html.P(f"Member since: {member_since}",
                       className="user-join-date")
            ])

            # Format friends list
            friends = user_data.get('friends', [])
            friends_list = []

            if friends:
                for friend in friends:
                    friend_item = html.Li([
                        dcc.Link([
                            html.Img(
                                src=friend.get(
                                    'profile_image_url', '/assets/svg/default-profile.svg'),
                                className='friend-avatar',
                                style={
                                    'width': '30px',
                                    'height': '30px',
                                    'border-radius': '50%',
                                    'object-fit': 'cover',
                                    'margin-right': '10px'
                                }
                            ),
                            html.Span(friend['username'],
                                      className='friend-name')
                        ],
                            href=f"/profile/view/{friend['username']}",
                            className='friend-link',
                            style={'text-decoration': 'none', 'color': 'inherit'})
                    ], className="friend-item")
                    friends_list.append(friend_item)
            else:
                friends_list = [
                    html.Li("No friends yet", className="no-friends")]

            profile_image_url = user_data.get(
                'profile_image_url', '/assets/svg/default-profile.svg')

            return user_data['username'], profile_image_url, user_info, friends_list

        except Exception as e:
            print(f"Error loading user profile: {e}")
            return "Error loading profile", "", html.Div("An error occurred", style={'color': 'red'}), []

    # No username provided - should not happen with the new structure
    else:
        return "No user specified", '', html.Div("No user specified"), []

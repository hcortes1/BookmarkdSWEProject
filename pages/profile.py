import dash
from dash import html, dcc, Input, Output, State, callback
import backend.profile as profile_backend
import backend.friends as friends_backend

# Register only the view path - all profiles use the same structure
dash.register_page(__name__, path_template='/profile/view/<username>')


def layout(username=None, **kwargs):
    # All profiles use the same layout structure
    # The title will be dynamically updated in the callback based on whether it's own profile
    title = f"{username}'s Profile" if username else "Profile"
    friends_title = f"{username}'s Friends" if username else "Friends"

    return html.Div([
        html.Div([
            html.Div([
                # LEFT SIDE – Profile picture, username, and friends
                html.Div([
                    html.Img(
                        id='profile-image',
                        src='',  # Will be dynamically loaded
                        className='profile-user-image'
                    ),

                    # Username will be dynamically loaded
                    html.Span("Loading...", id="profile-username",
                              className="profile-username"),

                    # Additional user info (Member since - below username)
                    html.Div(id="profile-user-info",
                             className="user-profile-info"),

                    # Friend request button (below member since)
                    html.Div(id="friend-request-section",
                             className="friend-request-section"),

                    # Friends list (below friend request button)
                    html.Div([
                        html.H3(id="friends-title", children=friends_title,
                                className="friends-title-left"),
                        html.Ul(id="friends-list",
                                className="friends-list-left")
                    ], className="friends-section-left")
                ], className="profile-info"),

                # RIGHT SIDE – Favorites only
                html.Div([
                    # Favorites section
                    html.Div(id="favorites-section",
                             className="favorites-section-container")
                ], className="profile-right")

            ], className="profile-header"),

            # Hidden div to store the username parameter
            html.Div(id='username-store', children=username,
                     style={'display': 'none'})

        ], className="app-container", id="profile-container")
    ])


# Combined callback to handle all profile views using the same path structure
@callback(
    [Output("friends-title", "children"),
     Output("profile-username", "children"),
     Output("profile-image", "src"),
     Output("profile-user-info", "children"),
     Output("friends-list", "children"),
     Output("friend-request-section", "children"),
     Output("favorites-section", "children")],
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
                return "Friends", "User not found", "", html.Div("User not found", style={'color': 'red'}), [], html.Div(), html.Div()

            # Check if this is the logged-in user viewing their own profile
            is_own_profile = (session_data and
                              session_data.get('logged_in', False) and
                              session_data.get('username', '').lower() == viewed_username.lower())

            # Set the friends title based on whether it's own profile or not
            if is_own_profile:
                friends_title = "Your Friends"
            else:
                friends_title = f"{user_data['username']}'s Friends"

            # Format user info - show display name, bio, and member date for all profiles
            created_at = user_data.get('created_at')
            member_since = 'Unknown'
            if created_at:
                if hasattr(created_at, 'strftime'):
                    member_since = created_at.strftime('%m/%d/%Y')
                elif isinstance(created_at, str):
                    # Try to parse the string and reformat
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(
                            created_at[:10], '%Y-%m-%d')
                        member_since = parsed_date.strftime('%m/%d/%Y')
                    except:
                        member_since = created_at[:10]

            # Use display name if available, otherwise use username with @
            display_name = user_data.get('display_name')
            has_display_name = display_name and display_name.strip()

            if has_display_name:
                # Show display name large, username small below it
                username_display = html.Div([
                    html.Div(display_name, className="profile-display-name",
                             style={'font-size': '1.8rem', 'font-weight': 'bold', 'margin-bottom': '5px', 'margin-top': '0px'}),
                    html.Div(f"@{user_data['username']}", className="profile-username-small",
                             style={'font-size': '1.2rem', 'color': '#666', 'font-weight': 'normal', 'margin-bottom': '0px', 'margin-top': '0px'})
                ], style={'margin-bottom': '0px'})
            else:
                # Show username with @ if no display name
                username_display = html.Div(f"@{user_data['username']}", className="profile-username",
                                            style={'font-size': '1.8rem', 'font-weight': 'bold', 'margin-bottom': '0px', 'margin-top': '0px'})

            user_info_elements = [
                html.P(f"Member since: {member_since}", className="user-join-date",
                       style={'margin-top': '0px', 'margin-bottom': '10px', 'padding-top': '0px'})
            ]

            # Add bio if it exists
            bio = user_data.get('bio')
            if bio and bio.strip():
                user_info_elements.append(
                    html.P(bio, className="user-bio",
                           style={'margin-top': '10px', 'font-style': 'italic'})
                )

            user_info = html.Div(user_info_elements)

            # Create favorite authors and books cards for the right side
            # Favorite Books Card (now first)
            favorite_books = user_data.get('favorite_books_details', [])
            if favorite_books:
                books_content = []
                for book in favorite_books:
                    # Use cover_url if available, otherwise use a default book image
                    book_image = book.get(
                        'cover_url', '/assets/svg/default-book.svg')
                    book_title = book['title']
                    author_name = book.get('author_name', 'Unknown Author')
                    book_id = book.get('book_id')

                    # Create clickable link to book page
                    books_content.append(
                        html.Li([
                            dcc.Link([
                                html.Img(
                                    src=book_image, className="favorite-item-image", alt=f"Cover of {book_title}"),
                                html.Div(
                                    book_title, className="favorite-item-title"),
                                html.Div(f"by {author_name}",
                                         className="favorite-item-author")
                            ], href=f"/book/{book_id}?from=profile&username={viewed_username}", className="favorite-item-link")
                        ], className="favorite-item")
                    )
                books_card_content = html.Ul(
                    books_content, className="favorites-list")
            else:
                # Show appropriate message when no favorite books
                if is_own_profile:
                    books_card_content = html.P("Search for a book and add it to your favorites!",
                                                className="favorites-empty-message")
                else:
                    books_card_content = html.P(f"{user_data['username']} doesn't have any favorite books yet",
                                                className="favorites-empty-message")

            # Favorite Authors Card (now second)
            favorite_authors = user_data.get('favorite_authors_details', [])
            if favorite_authors:
                authors_content = []
                for author in favorite_authors:
                    # Use author_image_url if available, otherwise use a default author image
                    author_image = author.get(
                        'author_image_url', '/assets/svg/default-author.svg')
                    author_name = author['name']
                    author_id = author.get('author_id')

                    # Create clickable link to author page
                    authors_content.append(
                        html.Li([
                            dcc.Link([
                                html.Img(
                                    src=author_image, className="favorite-author-image", alt=f"Photo of {author_name}"),
                                html.Div(
                                    author_name, className="favorite-item-title")
                            ], href=f"/author/{author_id}?from=profile&username={viewed_username}", className="favorite-item-link")
                        ], className="favorite-item")
                    )
                authors_card_content = html.Ul(
                    authors_content, className="favorites-list")
            else:
                # Show appropriate message when no favorite authors
                if is_own_profile:
                    authors_card_content = html.P("Search for an author and add them to your favorites!",
                                                  className="favorites-empty-message")
                else:
                    authors_card_content = html.P(f"{user_data['username']} doesn't have any favorite authors yet",
                                                  className="favorites-empty-message")

            # Create the favorites cards (books first, then authors)
            favorites_section = html.Div([
                html.Div([
                    html.H3("Favorite Books", className="favorites-card-title"),
                    books_card_content
                ], className="favorites-card"),
                html.Div([
                    html.H3("Favorite Authors",
                            className="favorites-card-title"),
                    authors_card_content
                ], className="favorites-card")
            ], className="favorites-container")

            # Friend request section
            friend_request_section = html.Div()
            if not is_own_profile and session_data and session_data.get('logged_in', False):
                # Check friendship status
                friendship_status = friends_backend.get_friendship_status(
                    str(session_data['user_id']), viewed_username)

                status = friendship_status.get('status', 'none')

                if status == 'friends':
                    # Show "Remove Friend" button
                    friend_request_section = html.Button(
                        "Remove Friend",
                        id={'type': 'remove-friend',
                            'username': viewed_username},
                        className='btn-remove-friend',
                        style={
                            'background': '#dc3545',
                            'color': 'white',
                            'border': 'none',
                            'padding': '8px 16px',
                            'border-radius': '6px',
                            'margin-top': '10px',
                            'cursor': 'pointer'
                        }
                    )
                elif status == 'pending_sent':
                    # Show "Friend Request Sent" (disabled)
                    friend_request_section = html.Div([
                        html.Span("Friend Request Sent",
                                  style={'color': '#6c757d', 'font-weight': 'bold', 'margin-top': '10px', 'display': 'block'})
                    ])
                elif status == 'pending_received':
                    # Show "Respond to Friend Request" message
                    friend_request_section = html.Div([
                        html.Span("This user sent you a friend request. Check your notifications!",
                                  style={'color': '#007bff', 'font-weight': 'bold', 'margin-top': '10px', 'display': 'block'})
                    ])
                else:  # status == 'none' or 'user_not_found'
                    # Show "Send Friend Request" button
                    friend_request_section = html.Button(
                        "Send Friend Request",
                        id={'type': 'send-friend-request',
                            'username': viewed_username},
                        className='btn-send-friend-request',
                        style={
                            'background': '#007bff',
                            'color': 'white',
                            'border': 'none',
                            'padding': '8px 16px',
                            'border-radius': '6px',
                            'margin-top': '10px',
                            'cursor': 'pointer'
                        }
                    )

            # Format friends list
            friends = user_data.get('friends', [])
            friends_list = []

            if friends:
                for friend in friends:
                    # Ensure we always have a valid profile image URL
                    friend_profile_image = friend.get('profile_image_url')
                    if not friend_profile_image or not friend_profile_image.strip():
                        friend_profile_image = '/assets/svg/default-profile.svg'

                    friend_item = html.Li([
                        dcc.Link([
                            html.Img(
                                src=friend_profile_image,
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

            # Ensure we always have a valid profile image URL for the main profile
            profile_image_url = user_data.get('profile_image_url')
            if not profile_image_url or not profile_image_url.strip():
                profile_image_url = '/assets/svg/default-profile.svg'

            return friends_title, username_display, profile_image_url, user_info, friends_list, friend_request_section, favorites_section

        except Exception as e:
            print(f"Error loading user profile: {e}")
            return "Friends", "Error loading profile", "", html.Div("An error occurred", style={'color': 'red'}), [], html.Div(), html.Div()

    # No username provided - should not happen with the new structure
    else:
        return "Friends", "No user specified", '', html.Div("No user specified"), [], html.Div(), html.Div()


# Handle send friend request button
@callback(
    Output("friend-request-section", "children", allow_duplicate=True),
    [Input({'type': 'send-friend-request', 'username': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'remove-friend', 'username': dash.dependencies.ALL}, 'n_clicks')],
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_friend_actions(send_clicks, remove_clicks, user_session):
    if not user_session or not user_session.get('logged_in', False):
        return dash.no_update

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    # Check if any button was actually clicked
    all_clicks = (send_clicks or []) + (remove_clicks or [])
    if not any(all_clicks):
        return dash.no_update

    # Get the button that was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_data = eval(button_id)  # Convert string back to dict
    target_username = button_data['username']
    action_type = button_data['type']

    try:
        if action_type == 'send-friend-request':
            result = friends_backend.send_friend_request(
                sender_id=user_session['user_id'],
                receiver_username=target_username
            )

            # Show success message
            return html.Div([
                html.Span("Friend request sent!", style={
                          'color': 'green', 'font-weight': 'bold'})
            ])

        elif action_type == 'remove-friend':
            # Get the target user's ID first
            target_user_data = profile_backend.get_user_profile_by_username(
                target_username)
            if not target_user_data:
                return html.Div([
                    html.Span("User not found", style={
                              'color': 'red', 'font-weight': 'bold'})
                ])

            result = friends_backend.remove_friend(
                user_id=str(user_session['user_id']),
                friend_id=str(target_user_data['user_id'])
            )

            # Show success message and replace with "Send Friend Request" button
            return html.Button(
                "Send Friend Request",
                id={'type': 'send-friend-request', 'username': target_username},
                className='btn-send-friend-request',
                style={
                    'background': '#007bff',
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 16px',
                    'border-radius': '6px',
                    'margin-top': '10px',
                    'cursor': 'pointer'
                }
            )

    except ValueError as e:
        # Show error message
        return html.Div([
            html.Span(str(e), style={'color': 'red', 'font-weight': 'bold'})
        ])
    except Exception as e:
        print(f"Error handling friend action: {e}")
        return html.Div([
            html.Span("Error processing request", style={
                      'color': 'red', 'font-weight': 'bold'})
        ])

    return dash.no_update

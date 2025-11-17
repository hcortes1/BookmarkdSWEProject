import dash
from dash import html, dcc, Input, Output, State, callback
import dash_cytoscape as cyto
import backend.profile as profile_backend
import backend.friends as friends_backend
import backend.rewards as rewards_backend
import backend.bookshelf as bookshelf_backend

# Register only the view path - all profiles use the same structure
dash.register_page(__name__, path_template='/profile/view/<username>')


def create_reviews_content(user_data, is_own_profile):
    """Create content for the reviews tab"""
    from backend.reviews import get_user_reviews

    user_id = user_data.get('user_id')
    if not user_id:
        return html.Div([
            html.H3("Reviews", className="tab-section-title"),
            html.P("Unable to load reviews.", className="tab-empty-message")
        ])

    # Get user's reviews and filter to only those with review text
    all_reviews = get_user_reviews(user_id)
    reviews = [review for review in all_reviews if review.get(
        'review_text') and review.get('review_text').strip()]

    if reviews:
        reviews_content = []
        for review in reviews:
            # Create consistent rating display (X.0/5.0 format)
            rating = review.get('rating', 0)
            rating_text = f"{rating}.0/5.0" if rating else "No rating"

            # Format the date
            created_at = review.get('created_at')
            date_str = 'Unknown date'
            if created_at:
                if hasattr(created_at, 'strftime'):
                    date_str = created_at.strftime('%m/%d/%Y')
                elif isinstance(created_at, str):
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(
                            created_at[:10], '%Y-%m-%d')
                        date_str = parsed_date.strftime('%m/%d/%Y')
                    except:
                        date_str = created_at[:10]

            # Create review card
            review_card = html.Div([
                html.Div([
                    # Book cover and title on the left
                    html.Div([
                        html.Img(
                            src=review.get(
                                'cover_url', '/assets/svg/default-book.svg'),
                            className="review-book-cover",
                            style={
                                'width': '60px',
                                'height': '90px',
                                'object-fit': 'contain',
                                'border-radius': '5px',
                                'background-color': '#f8f9fa'
                            }
                        )
                    ], style={'margin-right': '15px'}),

                    # Review content on the right
                    html.Div([
                        # Book title and author (clickable)
                        dcc.Link([
                            html.H4(review.get('title', 'Unknown Title'),
                                    className='text-link', style={'margin': '0 0 5px 0'}),
                            html.P(f"by {review.get('author_name', 'Unknown Author')}",
                                   className='text-secondary', style={'margin': '0 0 10px 0', 'font-size': '0.9rem'})
                        ], href=f"/book/{review.get('book_id')}", style={'text-decoration': 'none'}),

                        # Rating and date
                        html.Div([
                            html.Span(rating_text, style={
                                      'font-size': '1rem', 'font-weight': 'bold', 'margin-right': '10px'},
                                      className='rating-color'),
                            html.Span(date_str, className='text-secondary',
                                      style={'font-size': '0.9rem'})
                        ], style={'margin-bottom': '10px'}),

                        # Review text
                        html.P(review.get('review_text', ''),
                               style={'margin': '0', 'line-height': '1.5'}) if review.get('review_text') else None
                    ], style={'flex': '1'})
                ], style={
                    'display': 'flex',
                    'align-items': 'flex-start',
                    'padding': '15px',
                    'border': '1px solid var(--border-color)',
                    'border-radius': '8px',
                    'margin-bottom': '15px'
                }, className='card lighter-bg')
            ])

            reviews_content.append(review_card)

        title = "Your Reviews" if is_own_profile else f"{user_data['username']}'s Reviews"
        return html.Div([
            html.H3(title, className="tab-section-title"),
            html.Div(reviews_content)
        ])
    else:
        # No reviews found
        if is_own_profile:
            return html.Div([
                html.H3("Your Reviews", className="tab-section-title"),
                html.P("You haven't written any reviews yet. Mark a book as finished to leave a review!",
                       className="tab-empty-message")
            ])
        else:
            return html.Div([
                html.H3(f"{user_data['username']}'s Reviews",
                        className="tab-section-title"),
                html.P(f"{user_data['username']} hasn't written any reviews yet.",
                       className="tab-empty-message")
            ])


def create_completed_books_content(user_data, is_own_profile):
    """Create content for the completed books tab"""
    from backend.bookshelf import get_user_bookshelf

    user_id = user_data.get('user_id')
    if not user_id:
        return html.Div([
            html.H3("Completed Books", className="tab-section-title"),
            html.P("Unable to load completed books.",
                   className="tab-empty-message")
        ])

    # Get user's bookshelf and extract completed books
    success, message, bookshelf = get_user_bookshelf(user_id)

    if success and bookshelf and bookshelf.get('finished'):
        completed_books = bookshelf['finished']
        books_content = []

        for book in completed_books:
            # Format completion date
            added_at = book.get('added_at')
            date_str = 'Unknown date'
            if added_at:
                if hasattr(added_at, 'strftime'):
                    date_str = added_at.strftime('%m/%d/%Y')
                elif isinstance(added_at, str):
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(
                            added_at[:10], '%Y-%m-%d')
                        date_str = parsed_date.strftime('%m/%d/%Y')
                    except:
                        date_str = added_at[:10]

            # Create rating display consistent with rest of app (X.X/5.0 format)
            if book.get('user_rating'):
                rating = book['user_rating']
                rating_display = html.Div(f"{rating}.0/5.0", style={
                    'font-size': '0.9rem',
                    'font-weight': 'bold'
                }, className='rating-color')
            else:
                rating_display = html.Div("No rating", className='text-secondary',
                                          style={'font-size': '0.9rem'})

            # Create book card for grid layout
            book_card = html.Div([
                # Book cover (clickable)
                dcc.Link([
                    html.Img(
                        src=book.get(
                            'cover_url', '/assets/svg/default-book.svg'),
                        className="completed-book-cover",
                        style={
                            'width': '120px',
                            'height': '180px',
                            'object-fit': 'contain',
                            'border-radius': '8px',
                            'box-shadow': '0 2px 8px rgba(0,0,0,0.1)',
                            'transition': 'transform 0.2s',
                            'display': 'block',
                            'background-color': '#f8f9fa'
                        }
                    )
                ], href=f"/book/{book.get('book_id')}", style={'text-decoration': 'none'}),

                # Book title (clickable) - no gap below
                dcc.Link([
                    html.H4(book.get('title', 'Unknown Title'),
                            style={
                        'margin': '10px 0 0 0',  # Remove bottom margin to eliminate gap
                        'font-size': '0.95rem',
                        'line-height': '1.2',
                        'text-align': 'center',
                        'overflow': 'hidden',
                        'display': '-webkit-box',
                        '-webkit-line-clamp': '2',
                        '-webkit-box-orient': 'vertical',
                        'max-height': '2.4em'  # Limit height to 2 lines
                    }, className='text-primary')
                ], href=f"/book/{book.get('book_id')}", style={'text-decoration': 'none'}),

                # Completion date
                html.Div(f"Completed: {date_str}", className='text-secondary', style={
                    'text-align': 'center',
                    'margin-top': '5px',
                    'font-size': '0.8rem'
                }),

                # User's rating (centered)
                html.Div(rating_display, style={
                         'text-align': 'center', 'margin-top': '5px'})

            ], style={
                'display': 'flex',
                'flex-direction': 'column',
                'align-items': 'center',
                'padding': '15px',
                'border': '1px solid var(--border-color)',
                'border-radius': '10px',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.05)',
                'transition': 'box-shadow 0.2s, transform 0.2s',
                'width': '160px',
                'height': '300px',  # Increased height to accommodate completion date
                'cursor': 'pointer'
            }, className="card completed-book-card lighter-bg")

            books_content.append(book_card)

        title = "Your Completed Books" if is_own_profile else f"{user_data['username']}'s Completed Books"
        return html.Div([
            html.H3(title, className="tab-section-title"),
            html.Div(books_content, style={
                'display': 'grid',
                'grid-template-columns': 'repeat(auto-fill, minmax(160px, 1fr))',
                'gap': '20px',
                'padding': '10px 0'
            }, className="completed-books-grid")
        ])
    else:
        # No completed books found
        if is_own_profile:
            return html.Div([
                html.H3("Your Completed Books", className="tab-section-title"),
                html.P("You haven't completed any books yet. Start reading and mark books as finished!",
                       className="tab-empty-message")
            ])
        else:
            return html.Div([
                html.H3(
                    f"{user_data['username']}'s Completed Books", className="tab-section-title"),
                html.P(f"{user_data['username']} hasn't completed any books yet.",
                       className="tab-empty-message")
            ])


def layout(username=None, **kwargs):
    return html.Div([
        html.Div([
            # Tab Content - will show/hide different layouts
            html.Div(id='profile-tab-content', children=[]),

            # Store for active tab
            dcc.Store(id='profile-active-tab', data='profile'),

            # Hidden div to store the username parameter
            html.Div(id='username-store', children=username,
                     style={'display': 'none'})

        ], className="app-container", id="profile-container")
    ])


# Callback to load profile header (username, image, user info)
@callback(
    [Output("profile-username", "children"),
     Output("profile-image", "src"),
     Output("profile-user-info", "children"),
     Output("friend-request-section", "children")],
    [Input("user-session", "data"),
     Input("username-store", "children")],
    prevent_initial_call=False
)
def update_profile_header(session_data, viewed_username):
    """
    Update profile header with username, image, and basic info
    """

    if viewed_username:
        try:
            # Get user profile data from database
            user_data = profile_backend.get_user_profile_by_username(
                viewed_username)

            if not user_data:
                return "User not found", "", html.Div("User not found", style={'color': 'red'}), html.Div()

            # Check if this is the logged-in user viewing their own profile
            is_own_profile = (session_data and
                              session_data.get('logged_in', False) and
                              session_data.get('username', '').lower() == viewed_username.lower())

            # Check if this is own profile
            # (friends_title removed - now handled in tab content)

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
                    html.Div(f"@{user_data['username']}", className="profile-username-small text-secondary",
                             style={'font-size': '1.2rem', 'font-weight': 'normal', 'margin-bottom': '0px', 'margin-top': '0px'})
                ], style={'margin-bottom': '0px'})
            else:
                # Show username with @ if no display name
                username_display = html.Div(f"@{user_data['username']}", className="profile-username",
                                            style={'font-size': '1.8rem', 'font-weight': 'bold', 'margin-bottom': '0px', 'margin-top': '0px'})

            user_info_elements = [
                html.P(f"Member since: {member_since}", className="user-join-date",
                       style={'margin-top': '0px', 'margin-bottom': '10px', 'padding-top': '0px'})
            ]

            # Add level badge above bio
            profile_user_id = user_data.get('user_id')
            rewards = rewards_backend.get_user_rewards(profile_user_id)
            level = rewards.get('level', 1)

            # Only show XP and points tooltip for own profile
            level_title = ""
            level_style = {'cursor': 'default'}
            if is_own_profile:
                xp = rewards.get('xp', 0)
                points = rewards.get('points', 0)
                _, current_level_xp, xp_to_next = rewards_backend.get_level_progress(
                    xp)
                level_title = f"XP: {current_level_xp}/{xp_to_next} to Level {level + 1}\nPoints: {points}"
                level_style = {'cursor': 'help'}

            user_info_elements.append(
                html.Div(
                    html.Span(
                        f"Lvl {level}",
                        className=f'level-badge level-{level}',
                        title=level_title if level_title else None,
                        style=level_style
                    ),
                    className='profile-level-badge',
                    style={'margin-bottom': '10px'}
                )
            )

            # Add bio if it exists
            bio = user_data.get('bio')
            if bio and bio.strip():
                user_info_elements.append(
                    html.P(bio, className="user-bio",
                           style={'margin-top': '10px', 'font-style': 'italic'})
                )

            # Add yearly reading statistics
            from backend.bookshelf import get_yearly_reading_stats
            from datetime import datetime
            current_year = datetime.now().year

            stats_success, stats_message, yearly_stats = get_yearly_reading_stats(
                profile_user_id, current_year)
            if stats_success:
                books_count = yearly_stats.get('books_read', 0)
                pages_count = yearly_stats.get('pages_read', 0)

                user_info_elements.append(
                    html.Div([
                        html.P(f"Books read this year: {books_count}", className='text-primary',
                               style={'margin': '0px 0 3px 0'}),
                        html.P(f"Pages read this year: {pages_count:,}", className='text-primary',
                               style={'margin': '3px 0 0 0'})
                    ], className="yearly-stats")
                )

            user_info = html.Div(user_info_elements)

            # Friend request/Edit profile section
            friend_request_section = html.Div()
            if is_own_profile and session_data and session_data.get('logged_in', False):
                # Show "Edit Profile" button for own profile
                friend_request_section = html.Button(
                    "Edit Profile",
                    id='edit-profile-button',
                    className='btn-edit-profile',
                    style={
                        'background': '#007bff',
                        'color': 'white',
                        'border': 'none',
                        'padding': '8px 16px',
                        'border-radius': '6px',
                        'margin-top': '0px',
                        'cursor': 'pointer'
                    }
                )
            elif not is_own_profile and session_data and session_data.get('logged_in', False):
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
                            'margin-top': '0px',
                            'cursor': 'pointer'
                        }
                    )
                elif status == 'pending_sent':
                    # Show "Cancel Friend Request" button
                    friend_request_section = html.Button(
                        "Cancel Friend Request",
                        id={'type': 'cancel-friend-request',
                            'username': viewed_username},
                        className='btn-cancel-friend-request',
                        style={
                            'background': '#6c757d',
                            'color': 'white',
                            'border': 'none',
                            'padding': '8px 16px',
                            'border-radius': '6px',
                            'margin-top': '0px',
                            'cursor': 'pointer'
                        }
                    )
                elif status == 'pending_received':
                    # Show "Respond to Friend Request" message
                    friend_request_section = html.Div([
                        html.Span("This user sent you a friend request. Check your notifications!", className='text-link',
                                  style={'font-weight': 'bold', 'margin-top': '0px', 'display': 'block'})
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
                            'margin-top': '0px',
                            'cursor': 'pointer'
                        }
                    )

            # Ensure we always have a valid profile image URL for the main profile
            profile_image_url = user_data.get(
                'profile_image_url', '/assets/svg/default-profile.svg')

            return username_display, profile_image_url, user_info, friend_request_section

        except Exception as e:
            print(f"Error loading user profile: {e}")
            import traceback
            traceback.print_exc()
            return "Error loading profile", "", html.Div("An error occurred", style={'color': 'red'}), html.Div()

    # No username provided
    else:
        return "No user specified", '', html.Div("No user specified"), html.Div()


# Callback to handle tab switching
@callback(
    [Output('profile-active-tab', 'data'),
     Output('profile-profile-tab', 'className'),
     Output('profile-friends-tab', 'className'),
     Output('profile-bookshelf-tab', 'className')],
    [Input('profile-profile-tab', 'n_clicks'),
     Input('profile-friends-tab', 'n_clicks'),
     Input('profile-bookshelf-tab', 'n_clicks')],
    prevent_initial_call=True
)
def handle_tab_switch(profile_clicks, friends_clicks, bookshelf_clicks):
    """Handle tab switching and update tab classes"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Determine which tab was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'profile-profile-tab':
        return 'profile', 'profile-tab active-tab', 'profile-tab', 'profile-tab'
    elif button_id == 'profile-friends-tab':
        return 'friends', 'profile-tab', 'profile-tab active-tab', 'profile-tab'
    elif button_id == 'profile-bookshelf-tab':
        return 'bookshelf', 'profile-tab', 'profile-tab', 'profile-tab active-tab'

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update


# Callback to update tab content based on active tab
@callback(
    Output('profile-tab-content', 'children'),
    [Input('profile-active-tab', 'data'),
     Input('user-session', 'data'),
     Input('username-store', 'children')],
    prevent_initial_call=False
)
def update_tab_content(active_tab, session_data, viewed_username):
    """Update the displayed content based on which tab is active"""

    if not viewed_username:
        return html.Div("No user specified", className="text-secondary")

    # Get user data
    user_data = profile_backend.get_user_profile_by_username(viewed_username)
    if not user_data:
        return html.Div("User not found", className="text-secondary")

    is_own_profile = (session_data and
                      session_data.get('logged_in', False) and
                      session_data.get('username', '').lower() == viewed_username.lower())

    # Create profile info card (shown on all tabs)
    profile_card = create_profile_info_card(
        user_data, is_own_profile, session_data)

    # Create tab navigation
    tab_navigation = html.Div([
        html.Button("Profile", id="profile-profile-tab",
                    className="profile-tab active-tab" if active_tab == 'profile' else "profile-tab"),
        html.Button("Friends", id="profile-friends-tab",
                    className="profile-tab active-tab" if active_tab == 'friends' else "profile-tab"),
        html.Button("Bookshelf", id="profile-bookshelf-tab",
                    className="profile-tab active-tab" if active_tab == 'bookshelf' else "profile-tab")
    ], className='profile-tabs-container')

    # Get tab-specific content
    if active_tab == 'profile':
        tab_content = create_profile_tab_content(user_data, is_own_profile)
    elif active_tab == 'friends':
        tab_content = create_friends_tab_content(user_data, is_own_profile)
    elif active_tab == 'bookshelf':
        tab_content = create_bookshelf_tab_content(user_data, is_own_profile)
    else:
        tab_content = html.Div()

    # Return layout with profile card, tabs, then content
    return html.Div([
        html.Div([profile_card], className="profile-left-column"),
        html.Div([
            tab_navigation,
            tab_content
        ], className="profile-right-wrapper")
    ], className="profile-main-grid")


def create_profile_info_card(user_data, is_own_profile, session_data):
    """Create the profile info card shown on all tabs"""
    from datetime import datetime

    # Format user info
    created_at = user_data.get('created_at')
    member_since = 'Unknown'
    if created_at:
        if hasattr(created_at, 'strftime'):
            member_since = created_at.strftime('%m/%d/%Y')
        elif isinstance(created_at, str):
            try:
                parsed_date = datetime.strptime(created_at[:10], '%Y-%m-%d')
                member_since = parsed_date.strftime('%m/%d/%Y')
            except:
                member_since = created_at[:10]

    # Use display name if available
    display_name = user_data.get('display_name')
    has_display_name = display_name and display_name.strip()

    if has_display_name:
        username_display = html.Div([
            html.Div(display_name, className="profile-display-name",
                     style={'font-size': '1.8rem', 'font-weight': 'bold', 'margin-bottom': '5px', 'margin-top': '0px'}),
            html.Div(f"@{user_data['username']}", className="profile-username-small text-secondary",
                     style={'font-size': '1.2rem', 'font-weight': 'normal', 'margin-bottom': '0px', 'margin-top': '0px'})
        ], style={'margin-bottom': '0px'})
    else:
        username_display = html.Div(f"@{user_data['username']}", className="profile-username",
                                    style={'font-size': '1.8rem', 'font-weight': 'bold', 'margin-bottom': '0px', 'margin-top': '0px'})

    user_info_elements = [
        html.P(f"Member since: {member_since}", className="user-join-date",
               style={'margin-top': '0px', 'margin-bottom': '10px', 'padding-top': '0px'})
    ]

    # Get level badge (will be placed in left section)
    profile_user_id = user_data.get('user_id')
    rewards = rewards_backend.get_user_rewards(profile_user_id)
    level = rewards.get('level', 1)

    level_title = ""
    level_style = {'cursor': 'default'}
    if is_own_profile:
        xp = rewards.get('xp', 0)
        points = rewards.get('points', 0)
        _, current_level_xp, xp_to_next = rewards_backend.get_level_progress(
            xp)
        level_title = f"XP: {current_level_xp}/{xp_to_next} to Level {level + 1}\nPoints: {points}"
        level_style = {'cursor': 'help'}

    level_badge = html.Div(
        html.Span(
            f"Lvl {level}",
            className=f'level-badge level-{level}',
            title=level_title if level_title else None,
            style=level_style
        ),
        className='profile-level-badge',
        style={'margin-bottom': '10px'}
    )

    # Add bio
    bio = user_data.get('bio')
    if bio and bio.strip():
        user_info_elements.append(
            html.P(bio, className="user-bio",
                   style={'margin-top': '10px', 'font-style': 'italic'})
        )

    # Add yearly stats
    from backend.bookshelf import get_yearly_reading_stats
    current_year = datetime.now().year

    stats_success, stats_message, yearly_stats = get_yearly_reading_stats(
        profile_user_id, current_year)
    if stats_success:
        books_count = yearly_stats.get('books_read', 0)
        pages_count = yearly_stats.get('pages_read', 0)

        user_info_elements.append(
            html.Div([
                html.P(f"Books read this year: {books_count}", className='text-primary',
                       style={'margin': '0px 0 3px 0'}),
                html.P(f"Pages read this year: {pages_count:,}", className='text-primary',
                       style={'margin': '3px 0 0 0'})
            ], className="yearly-stats")
        )

    user_info = html.Div(user_info_elements)

    # Friend request section
    friend_request_section = html.Div()
    if is_own_profile and session_data and session_data.get('logged_in', False):
        friend_request_section = html.Button(
            "Edit Profile",
            id='edit-profile-button',
            className='btn-edit-profile',
            style={
                'background': '#007bff',
                'color': 'white',
                'border': 'none',
                'padding': '8px 16px',
                'border-radius': '6px',
                'margin-top': '0px',
                'cursor': 'pointer'
            }
        )
    elif not is_own_profile and session_data and session_data.get('logged_in', False):
        friendship_status = friends_backend.get_friendship_status(
            str(session_data['user_id']), user_data['username'])
        status = friendship_status.get('status', 'none')

        if status == 'friends':
            friend_request_section = html.Button(
                "Remove Friend",
                id={'type': 'remove-friend',
                    'username': user_data['username']},
                className='btn-remove-friend',
                style={'background': '#dc3545', 'color': 'white', 'border': 'none',
                       'padding': '8px 16px', 'border-radius': '6px', 'margin-top': '0px', 'cursor': 'pointer'}
            )
        elif status == 'pending_sent':
            friend_request_section = html.Button(
                "Cancel Friend Request",
                id={'type': 'cancel-friend-request',
                    'username': user_data['username']},
                className='btn-cancel-friend-request',
                style={'background': '#6c757d', 'color': 'white', 'border': 'none',
                       'padding': '8px 16px', 'border-radius': '6px', 'margin-top': '0px', 'cursor': 'pointer'}
            )
        elif status == 'pending_received':
            friend_request_section = html.Div([
                html.Span("This user sent you a friend request. Check your notifications!", className='text-link',
                          style={'font-weight': 'bold', 'margin-top': '0px', 'display': 'block'})
            ])
        else:
            friend_request_section = html.Button(
                "Send Friend Request",
                id={'type': 'send-friend-request',
                    'username': user_data['username']},
                className='btn-send-friend-request',
                style={'background': '#007bff', 'color': 'white', 'border': 'none',
                       'padding': '8px 16px', 'border-radius': '6px', 'margin-top': '0px', 'cursor': 'pointer'}
            )

    profile_image_url = user_data.get(
        'profile_image_url', '/assets/svg/default-profile.svg')

    return html.Div([
        # Left column: image, badge, and button stacked
        html.Div([
            html.Img(src=profile_image_url, className='profile-image-compact'),
            level_badge,
            friend_request_section
        ], className='profile-left-section'),
        # Right column: username and user info
        html.Div([
            username_display,
            user_info
        ], className='profile-right-section')
    ], className="profile-info-card card")


def create_profile_tab_content(user_data, is_own_profile):
    """Create the profile tab content - just the showcase sections without profile card"""

    # Create Favorite Books Section
    favorite_books = user_data.get('favorite_books_details', [])[:10]
    if favorite_books:
        books_showcase = []
        for book in favorite_books:
            books_showcase.append(
                html.Div([
                    dcc.Link([
                        html.Div([
                            html.Img(src=book.get('cover_url', '/assets/svg/default-book.svg'),
                                     className="showcase-cover")
                        ], className="showcase-cover-wrapper"),
                        html.H4(book['title'], className="showcase-title"),
                        html.P(f"by {book.get('author_name', 'Unknown Author')}",
                               className="showcase-author")
                    ], href=f"/book/{book.get('book_id')}", style={"textDecoration": "none", "color": "inherit"})
                ], className="showcase-card")
            )
        books_content = html.Div(books_showcase, className="showcase-scroll")
    else:
        msg = "Add books to your favorites!" if is_own_profile else f"{user_data['username']} has no favorite books"
        books_content = html.P(msg, className="showcase-empty")

    # Create Favorite Authors Section
    favorite_authors = user_data.get('favorite_authors_details', [])[:10]
    if favorite_authors:
        authors_showcase = []
        for author in favorite_authors:
            authors_showcase.append(
                html.Div([
                    dcc.Link([
                        html.Div([
                            html.Img(src=author.get('author_image_url', '/assets/svg/default-author.svg'),
                                     className="showcase-cover")
                        ], className="showcase-cover-wrapper"),
                        html.H4(author['name'], className="showcase-title")
                    ], href=f"/author/{author.get('author_id')}", style={"textDecoration": "none", "color": "inherit"})
                ], className="showcase-card author-card")
            )
        authors_content = html.Div(
            authors_showcase, className="showcase-scroll")
    else:
        msg = "Add authors to your favorites!" if is_own_profile else f"{user_data['username']} has no favorite authors"
        authors_content = html.P(msg, className="showcase-empty")

    # Create Recent Reviews Section
    from backend.reviews import get_user_reviews
    all_reviews = get_user_reviews(user_data['user_id'])
    reviews = [r for r in all_reviews if r.get(
        'review_text') and r.get('review_text').strip()][:5]

    if reviews:
        reviews_showcase = []
        for review in reviews:
            reviews_showcase.append(
                html.Div([
                    dcc.Link([
                        html.Div([
                            html.Img(src=review.get('cover_url', '/assets/svg/default-book.svg'),
                                     className="showcase-cover")
                        ], className="showcase-cover-wrapper"),
                        html.H4(review.get('title', 'Unknown'),
                                className="showcase-title"),
                        html.P(f"⭐ {review.get('rating', 0)}/5",
                               className="showcase-rating"),
                        html.P(review.get('review_text', ''),
                               className="showcase-description")
                    ], href=f"/book/{review.get('book_id')}", style={"textDecoration": "none", "color": "inherit"})
                ], className="showcase-card-wide")
            )
        reviews_content = html.Div(
            reviews_showcase, className="showcase-scroll")
    else:
        msg = "No reviews yet" if is_own_profile else f"{user_data['username']} hasn't written reviews"
        reviews_content = html.P(msg, className="showcase-empty")

    # Create Recently Completed Books Section - sorted by rating then recent
    success, _, bookshelf = bookshelf_backend.get_user_bookshelf(
        user_data['user_id'])
    completed_books = bookshelf.get(
        'finished', []) if success and bookshelf else []

    # Sort by rating (desc) then by added_at (desc)
    completed_books_sorted = sorted(
        completed_books,
        key=lambda x: (-(x.get('user_rating') or 0), -(x.get('added_at').timestamp()
                       if hasattr(x.get('added_at'), 'timestamp') else 0))
    )[:10]

    if completed_books_sorted:
        completed_showcase = []
        for book in completed_books_sorted:
            rating = book.get('user_rating')
            rating_display = f"⭐ {rating}/5" if rating else "No rating"

            completed_showcase.append(
                html.Div([
                    dcc.Link([
                        html.Div([
                            html.Img(src=book.get('cover_url', '/assets/svg/default-book.svg'),
                                     className="showcase-cover")
                        ], className="showcase-cover-wrapper"),
                        html.H4(book.get('title', 'Unknown'),
                                className="showcase-title"),
                        html.P(rating_display, className="showcase-rating",
                               style={'fontWeight': 'bold', 'color': '#ffc107' if rating else None})
                    ], href=f"/book/{book.get('book_id')}", style={"textDecoration": "none", "color": "inherit"})
                ], className="showcase-card")
            )
        completed_content = html.Div(
            completed_showcase, className="showcase-scroll")
    else:
        msg = "No completed books yet" if is_own_profile else f"{user_data['username']} hasn't completed books"
        completed_content = html.P(msg, className="showcase-empty")

    # Get user info for profile card
    created_at = user_data.get('created_at')
    member_since = 'Unknown'
    if created_at:
        if hasattr(created_at, 'strftime'):
            member_since = created_at.strftime('%m/%d/%Y')
        elif isinstance(created_at, str):
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(created_at[:10], '%Y-%m-%d')
                member_since = parsed_date.strftime('%m/%d/%Y')
            except:
                member_since = created_at[:10]

    # Use display name if available
    display_name = user_data.get('display_name')
    has_display_name = display_name and display_name.strip()

    if has_display_name:
        username_display = html.Div([
            html.Div(display_name, className="profile-display-name",
                     style={'font-size': '1.8rem', 'font-weight': 'bold', 'margin-bottom': '5px', 'margin-top': '0px'}),
            html.Div(f"@{user_data['username']}", className="profile-username-small text-secondary",
                     style={'font-size': '1.2rem', 'font-weight': 'normal', 'margin-bottom': '0px', 'margin-top': '0px'})
        ], style={'margin-bottom': '0px'})
    else:
        username_display = html.Div(f"@{user_data['username']}", className="profile-username",
                                    style={'font-size': '1.8rem', 'font-weight': 'bold', 'margin-bottom': '0px', 'margin-top': '0px'})

    user_info_elements = [
        html.P(f"Member since: {member_since}", className="user-join-date",
               style={'margin-top': '0px', 'margin-bottom': '10px', 'padding-top': '0px'})
    ]

    # Add level badge
    profile_user_id = user_data.get('user_id')
    rewards = rewards_backend.get_user_rewards(profile_user_id)
    level = rewards.get('level', 1)

    level_title = ""
    level_style = {'cursor': 'default'}
    if is_own_profile:
        xp = rewards.get('xp', 0)
        points = rewards.get('points', 0)
        _, current_level_xp, xp_to_next = rewards_backend.get_level_progress(
            xp)
        level_title = f"XP: {current_level_xp}/{xp_to_next} to Level {level + 1}\nPoints: {points}"
        level_style = {'cursor': 'help'}

    user_info_elements.append(
        html.Div(
            html.Span(
                f"Lvl {level}",
                className=f'level-badge level-{level}',
                title=level_title if level_title else None,
                style=level_style
            ),
            className='profile-level-badge',
            style={'margin-bottom': '10px'}
        )
    )

    # Add bio
    bio = user_data.get('bio')
    if bio and bio.strip():
        user_info_elements.append(
            html.P(bio, className="user-bio",
                   style={'margin-top': '10px', 'font-style': 'italic'})
        )

    # Add yearly stats
    from backend.bookshelf import get_yearly_reading_stats
    from datetime import datetime
    current_year = datetime.now().year

    stats_success, stats_message, yearly_stats = get_yearly_reading_stats(
        profile_user_id, current_year)
    if stats_success:
        books_count = yearly_stats.get('books_read', 0)
        pages_count = yearly_stats.get('pages_read', 0)

        user_info_elements.append(
            html.Div([
                html.P(f"Books read this year: {books_count}", className='text-primary',
                       style={'margin': '0px 0 3px 0'}),
                html.P(f"Pages read this year: {pages_count:,}", className='text-primary',
                       style={'margin': '3px 0 0 0'})
            ], className="yearly-stats")
        )

    user_info = html.Div(user_info_elements)

    # Friend request section - will be populated by the header callback
    # Return just the showcase sections - profile card will be shown separately
    return html.Div([
        html.Div([
            html.H3("Favorite Books", className="section-title-showcase"),
            html.Div(books_content, className="showcase-scroll-container")
        ], className="profile-section-card card"),

        html.Div([
            html.H3("Favorite Authors", className="section-title-showcase"),
            html.Div(authors_content, className="showcase-scroll-container")
        ], className="profile-section-card card"),

        html.Div([
            html.H3("Recent Reviews", className="section-title-showcase"),
            html.Div(reviews_content, className="showcase-scroll-container")
        ], className="profile-section-card card"),

        html.Div([
            html.H3("Recently Completed", className="section-title-showcase"),
            html.Div(completed_content, className="showcase-scroll-container")
        ], className="profile-section-card card")
    ], className="profile-right-column")


def create_friends_tab_content(user_data, is_own_profile):
    """Create the friends tab with a Cytoscape network graph (no labels)"""

    friends = user_data.get('friends', [])
    friends_count = len(friends)

    title = f"Your Friends ({friends_count})" if is_own_profile else f"{user_data['username']}'s Friends ({friends_count})"

    if not friends:
        msg = "No friends yet" if is_own_profile else f"{user_data['username']} has no friends"
        return html.Div([
            html.H3(title, className="section-title-showcase"),
            html.P(msg, className="showcase-empty",
                   style={'text-align': 'center', 'margin-top': '50px'})
        ])

    # Build Cytoscape elements
    elements = []

    # Calculate positions for circular layout
    import math
    center_x, center_y = 300, 300  # center of graph
    radius = 120  # radius of circle for friends

    # Central node (current user) - positioned at center
    profile_img = user_data.get(
        'profile_image_url') or '/assets/svg/default-profile.svg'
    elements.append({
        'data': {
            'id': user_data['username'],
            'label': user_data['username'],
            'image': profile_img,
            'type': 'center'
        },
        'position': {'x': center_x, 'y': center_y}
    })

    # Create a set of friend user IDs for quick lookup
    friend_user_ids = {friend['user_id'] for friend in friends}
    friend_usernames = {friend['username'] for friend in friends}

    # Friend nodes and edges from center to friends - arranged in circle
    for i, friend in enumerate(friends):
        # Calculate angle for this friend (evenly distributed around circle)
        angle = (2 * math.pi * i) / len(friends)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)

        friend_img = friend.get(
            'profile_image_url') or '/assets/svg/default-profile.svg'
        elements.append({
            'data': {
                'id': friend['username'],
                'label': friend['username'],
                'image': friend_img,
                'type': 'friend'
            },
            'position': {'x': x, 'y': y}
        })

        # Edge from center user to this friend
        elements.append({
            'data': {
                'source': user_data['username'],
                'target': friend['username']
            }
        })

    # Add edges between friends who are also friends with each other (mutual friends)
    for i, friend1 in enumerate(friends):
        # Get this friend's friends list from backend
        try:
            friend1_friends_data = friends_backend.get_friends_list(
                str(friend1['user_id']))
            # Extract friend IDs for comparison
            friend1_friend_ids = {f['friend_id'] for f in friend1_friends_data}
        except Exception as e:
            print(f"Error fetching friends for {friend1['username']}: {e}")
            friend1_friend_ids = set()

        # Check if any of the center user's friends are also friends with friend1
        # Only check friends after this one to avoid duplicates
        for friend2 in friends[i+1:]:
            # Check if friend2's user_id is in friend1's friend list
            if friend2['user_id'] in friend1_friend_ids:
                # Add edge between the two mutual friends
                elements.append({
                    'data': {
                        'source': friend1['username'],
                        'target': friend2['username'],
                        'type': 'mutual'
                    }
                })

    # Create Cytoscape graph without labels
    cytoscape_graph = cyto.Cytoscape(
        id='friends-network',
        elements=elements,
        style={'width': '100%', 'height': '600px'},
        layout={
            'name': 'preset',
            'animate': True,
            'animationDuration': 500,
            'fit': True,
            'padding': 50
        },
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'background-color': '#e0e0e0',
                    'background-image': 'data(image)',
                    'background-fit': 'cover',
                    'background-clip': 'node',
                    'width': '60px',
                    'height': '60px',
                    'cursor': 'pointer',
                    'transition-property': 'width, height',
                    'transition-duration': '0.2s',
                    'label': 'data(hoverLabel)',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'color': '#ffffff',
                    'font-size': '14px',
                    'font-weight': 'bold',
                    'text-background-color': 'rgba(0, 0, 0, 0.7)',
                    'text-background-opacity': 1,
                    'text-background-padding': '4px',
                    'text-background-shape': 'roundrectangle',
                    'shape': 'ellipse'
                }
            },
            {
                'selector': 'node:active',
                'style': {
                    'width': '75px',
                    'height': '75px'
                }
            },
            {
                'selector': 'node[type="center"]',
                'style': {
                    'background-color': '#d4edda',
                    'width': '80px',
                    'height': '80px'
                }
            },
            {
                'selector': 'node[type="center"]:active',
                'style': {
                    'width': '95px',
                    'height': '95px'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'width': 1.5,
                    'line-color': '#007bff',
                    'line-style': 'dashed',
                    'curve-style': 'bezier'
                }
            },
            {
                'selector': ':selected',
                'style': {
                    'overlay-opacity': 0
                }
            }
        ]
    )

    return html.Div([
        html.Div(cytoscape_graph, className="friends-network-container")
    ], className="tab-content-wrapper")


def create_bookshelf_tab_content(user_data, is_own_profile):
    """Create the bookshelf tab showing user's books organized by shelf in a visual bookshelf layout"""

    success, _, bookshelf = bookshelf_backend.get_user_bookshelf(
        user_data['user_id'])

    if not success or not bookshelf:
        msg = "No books on your bookshelf yet" if is_own_profile else f"{user_data['username']} has no books on their bookshelf"
        return html.Div([
            html.P(msg, className="showcase-empty",
                   style={'text-align': 'center', 'margin-top': '50px'})
        ])

    # Create sections for each shelf type - use correct keys from backend
    shelves = [
        ('reading', 'Currently Reading', bookshelf.get('reading', [])),
        ('to_read', 'Want to Read', bookshelf.get('to_read', [])),
        ('finished', 'Completed', bookshelf.get('finished', []))
    ]

    shelf_sections = []
    for shelf_key, shelf_name, books in shelves:
        # Create book cards for bookshelf visualization
        book_cards = []

        if books:
            # Sort books by rating (desc) then by added_at (desc) for completed shelf
            if shelf_key == 'finished':
                books = sorted(
                    books,
                    key=lambda x: (-(x.get('user_rating') or 0), -(
                        x.get('added_at').timestamp() if hasattr(x.get('added_at'), 'timestamp') else 0))
                )

            # Check which books are favorited
            from backend.favorites import get_favorite_books
            favorite_book_ids = set()
            try:
                favorites = get_favorite_books(user_data['user_id'])
                favorite_book_ids = {fav['book_id'] for fav in favorites}
            except:
                pass

            for book in books:
                # Get rating for completed books
                rating = book.get('user_rating')
                rating_display = None
                if shelf_key == 'finished' and rating:
                    rating_display = f"⭐ {rating}/5"

                # Check if book is favorited
                is_favorited = book.get('book_id') in favorite_book_ids
                card_class = 'bookshelf-book-card bookshelf-favorited' if is_favorited else 'bookshelf-book-card'

                # Create book card with vertical stacking
                book_cards.append(
                    html.Div([
                        dcc.Link([
                            html.Div([
                                html.Img(
                                    src=book.get(
                                        'cover_url', '/assets/svg/default-book.svg'),
                                    className='bookshelf-book-cover',
                                    title=f"{book.get('title', 'Unknown')} by {book.get('author_name', 'Unknown')}"
                                )
                            ], className='bookshelf-cover-wrapper'),
                            html.Div([
                                html.H4(book.get('title', 'Unknown'),
                                        className='bookshelf-book-title'),
                                html.P(book.get('author_name', 'Unknown'),
                                       className='bookshelf-book-author'),
                                html.P(rating_display, className='bookshelf-book-rating',
                                       style={'fontWeight': 'bold', 'color': '#ffc107'}) if rating_display else None
                            ], className='bookshelf-book-info')
                        ], href=f"/book/{book.get('book_id')}", style={'textDecoration': 'none', 'color': 'inherit'})
                    ], className=card_class)
                )
        else:
            # Show empty shelf message
            book_cards.append(
                html.Div(
                    "No books on this shelf yet",
                    className='bookshelf-empty-message'
                )
            )

        # Create individual shelf section
        # Add a border line below the completed books section
        section_children = [
            html.Div([
                html.H3(shelf_name, className="bookshelf-shelf-title"),
                html.Span(f"({len(books)} books)",
                          className="bookshelf-book-count")
            ], className='bookshelf-shelf-header'),
            html.Div([
                html.Div(book_cards, className='bookshelf-books-row')
            ], className='bookshelf-shelf-container')
        ]
        if shelf_key == 'finished':
            section_children.append(
                html.Div(style={
                    'borderBottom': '3px solid var(--border-color)',
                    'marginTop': '10px',
                    'marginBottom': '10px',
                    'width': '100%'
                })
            )
        shelf_sections.append(
            html.Div(section_children, className='bookshelf-shelf-section')
        )

    return html.Div(shelf_sections, className='bookshelf-layout tab-content-wrapper')


# Handle send friend request button
@callback(
    Output("friend-request-section", "children", allow_duplicate=True),
    [Input({'type': 'send-friend-request', 'username': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'remove-friend', 'username': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'cancel-friend-request', 'username': dash.dependencies.ALL}, 'n_clicks')],
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_friend_actions(send_clicks, remove_clicks, cancel_clicks, user_session):
    if not user_session or not user_session.get('logged_in', False):
        return dash.no_update

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    # Check if any button was actually clicked
    all_clicks = (send_clicks or []) + \
        (remove_clicks or []) + (cancel_clicks or [])
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

            # Show cancel button immediately after sending request
            return html.Button(
                "Cancel Friend Request",
                id={'type': 'cancel-friend-request',
                    'username': target_username},
                className='btn-cancel-friend-request',
                style={
                    'background': '#6c757d',
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 16px',
                    'border-radius': '6px',
                    'margin-top': '0px',
                    'cursor': 'pointer'
                }
            )

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
                    'margin-top': '0px',
                    'cursor': 'pointer'
                }
            )

        elif action_type == 'cancel-friend-request':
            # Get the target user's ID first
            target_user_data = profile_backend.get_user_profile_by_username(
                target_username)
            if not target_user_data:
                return html.Div([
                    html.Span("User not found", style={
                              'color': 'red', 'font-weight': 'bold'})
                ])

            result = friends_backend.cancel_friend_request(
                sender_id=str(user_session['user_id']),
                receiver_id=str(target_user_data['user_id'])
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
                    'margin-top': '0px',
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


# Removed old toggle_friends_list callback - no longer needed with showcase layout


# Handle edit profile button - navigate to settings page
@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('edit-profile-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_edit_profile(n_clicks):
    """Navigate to settings page when edit profile button is clicked"""
    if n_clicks and n_clicks > 0:
        return '/profile/settings'
    return dash.no_update


# Handle clicking on friend nodes in the graph - navigate to their profile
@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('friends-network', 'tapNodeData'),
    prevent_initial_call=True
)
def handle_friend_node_click(node_data):
    """Navigate to clicked user's profile when they click a node in the friends graph"""
    if node_data and node_data.get('id'):
        username = node_data['id']
        return f'/profile/view/{username}'
    return dash.no_update

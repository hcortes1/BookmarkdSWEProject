import dash
from dash import html, dcc, Input, Output, State, callback
import backend.profile as profile_backend
import backend.friends as friends_backend
import backend.rewards as rewards_backend

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
                                    style={'margin': '0 0 5px 0', 'color': '#007bff'}),
                            html.P(f"by {review.get('author_name', 'Unknown Author')}",
                                   style={'margin': '0 0 10px 0', 'color': '#666', 'font-size': '0.9rem'})
                        ], href=f"/book/{review.get('book_id')}", style={'text-decoration': 'none'}),

                        # Rating and date
                        html.Div([
                            html.Span(rating_text, style={
                                      'font-size': '1rem', 'font-weight': 'bold', 'margin-right': '10px'},
                                      className='rating-color'),
                            html.Span(date_str, style={
                                      'color': '#666', 'font-size': '0.9rem'})
                        ], style={'margin-bottom': '10px'}),

                        # Review text
                        html.P(review.get('review_text', ''),
                               style={'margin': '0', 'line-height': '1.5'}) if review.get('review_text') else None
                    ], style={'flex': '1'})
                ], style={
                    'display': 'flex',
                    'align-items': 'flex-start',
                    'padding': '15px',
                    'border': '1px solid #ddd',
                    'border-radius': '8px',
                    'margin-bottom': '15px'
                }, className='lighter-bg')
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
                rating_display = html.Div("No rating", style={
                    'color': '#999',
                    'font-size': '0.9rem'
                })

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
                        'color': '#333',
                        'font-size': '0.95rem',
                        'line-height': '1.2',
                        'text-align': 'center',
                        'overflow': 'hidden',
                        'display': '-webkit-box',
                        '-webkit-line-clamp': '2',
                        '-webkit-box-orient': 'vertical',
                        'max-height': '2.4em'  # Limit height to 2 lines
                    })
                ], href=f"/book/{book.get('book_id')}", style={'text-decoration': 'none'}),

                # Completion date
                html.Div(f"Completed: {date_str}", style={
                    'text-align': 'center',
                    'margin-top': '5px',
                    'color': '#666',
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
                'border': '1px solid #e0e0e0',
                'border-radius': '10px',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.05)',
                'transition': 'box-shadow 0.2s, transform 0.2s',
                'width': '160px',
                'height': '300px',  # Increased height to accommodate completion date
                'cursor': 'pointer'
            }, className="completed-book-card lighter-bg")

            books_content.append(book_card)

        title = "Your Completed Books" if is_own_profile else f"{user_data['username']}'s Completed Books"
        return html.Div([
            html.H3(title, className="tab-section-title"),
            html.Div(books_content, style={
                'display': 'grid',
                'grid-template-columns': 'repeat(auto-fill, minmax(160px, 1fr))',
                'gap': '20px',
                'padding': '10px 0'
            })
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

                    # Friends list (below friend request button) - collapsible
                    html.Div([
                        html.H3(id="friends-title", children=friends_title,
                                className="friends-title-left collapsible",
                                style={'cursor': 'pointer', 'user-select': 'none'}),
                        html.Ul(id="friends-list",
                                className="friends-list-left secondary-bg",
                                style={'display': 'none'})  # Hidden by default
                    ], className="friends-section-left")
                ], className="profile-info"),

                # RIGHT SIDE – Tabbed content (Favorites, Reviews, Completed)
                html.Div([
                    # Tab navigation
                    html.Div([
                        html.Button("Favorites", id="favorites-tab", className="profile-tab active-tab",
                                    style={'padding': '10px 20px', 'border': 'none', 'background': '#007bff',
                                           'color': 'white', 'cursor': 'pointer', 'margin-right': '5px',
                                           'border-radius': '5px 5px 0 0'}),
                        html.Button("Reviews", id="reviews-tab", className="profile-tab",
                                    style={'padding': '10px 20px', 'border': 'none', 'background': '#f8f9fa',
                                           'color': '#6c757d', 'cursor': 'pointer', 'margin-right': '5px',
                                           'border-radius': '5px 5px 0 0'}),
                        html.Button("Completed", id="completed-tab", className="profile-tab",
                                    style={'padding': '10px 20px', 'border': 'none', 'background': '#f8f9fa',
                                           'color': '#6c757d', 'cursor': 'pointer',
                                           'border-radius': '5px 5px 0 0'})
                    ], className="profile-tabs", style={'margin-bottom': '0', 'border-bottom': '2px solid #007bff'}),

                    # Tab content container
                    html.Div(id="tab-content",
                             className="tab-content-container secondary-bg",
                             style={'padding': '20px', 'border-radius': '0 0 10px 10px',
                                    'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'})
                ], className="profile-right")

            ], className="profile-header"),

            # Hidden div to store the username parameter
            html.Div(id='username-store', children=username,
                     style={'display': 'none'}),

            # Store for active tab
            dcc.Store(id='active-tab-store', data='favorites')

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
     Output("tab-content", "children")],
    [Input("user-session", "data"),
     Input("username-store", "children"),
     Input("active-tab-store", "data")],
    prevent_initial_call=False
)
def update_profile_data(session_data, viewed_username, active_tab):
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
                        className='level-badge',
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
                        html.P(f"Books read this year: {books_count}",
                               style={'margin': '0px 0 3px 0', 'color': '#333'}),
                        html.P(f"Pages read this year: {pages_count:,}",
                               style={'margin': '3px 0 0 0', 'color': '#333'})
                    ], className="yearly-stats")
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
                        ], className="favorite-item lighter-bg")
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
                        ], className="favorite-item lighter-bg")
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

            # Create tab content based on active tab
            if active_tab == 'favorites':
                # Create the favorites cards (books first, then authors)
                tab_content = html.Div([
                    html.Div([
                        html.H3("Favorite Books",
                                className="favorites-card-title"),
                        books_card_content
                    ], className="favorites-card lighter-bg"),
                    html.Div([
                        html.H3("Favorite Authors",
                                className="favorites-card-title"),
                        authors_card_content
                    ], className="favorites-card lighter-bg")
                ], className="favorites-container")
            elif active_tab == 'reviews':
                # Create reviews content
                tab_content = create_reviews_content(user_data, is_own_profile)
            elif active_tab == 'completed':
                # Create completed books content
                tab_content = create_completed_books_content(
                    user_data, is_own_profile)
            else:
                # Default to favorites
                tab_content = html.Div([
                    html.Div([
                        html.H3("Favorite Books",
                                className="favorites-card-title"),
                        books_card_content
                    ], className="favorites-card lighter-bg"),
                    html.Div([
                        html.H3("Favorite Authors",
                                className="favorites-card-title"),
                        authors_card_content
                    ], className="favorites-card lighter-bg")
                ], className="favorites-container")

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
                    # Show "Friend Request Sent" (disabled)
                    friend_request_section = html.Div([
                        html.Span("Friend Request Sent",
                                  style={'color': '#6c757d', 'font-weight': 'bold', 'margin-top': '0px', 'display': 'block'})
                    ])
                elif status == 'pending_received':
                    # Show "Respond to Friend Request" message
                    friend_request_section = html.Div([
                        html.Span("This user sent you a friend request. Check your notifications!",
                                  style={'color': '#007bff', 'font-weight': 'bold', 'margin-top': '0px', 'display': 'block'})
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

            # Format friends list
            friends = user_data.get('friends', [])
            friends_list = []

            if friends:
                for friend in friends:
                    # Ensure we always have a valid profile image URL
                    friend_profile_image = friend.get('profile_image_url')
                    if not friend_profile_image or not friend_profile_image.strip():
                        friend_profile_image = '/assets/svg/default-profile.svg'

                    # Format the friendship date
                    created_at = friend.get('created_at')
                    since_text = 'Unknown'
                    if created_at:
                        if hasattr(created_at, 'strftime'):
                            since_text = created_at.strftime('%m/%d/%Y')
                        elif isinstance(created_at, str):
                            # Try to parse the string and reformat
                            try:
                                from datetime import datetime
                                parsed_date = datetime.fromisoformat(
                                    created_at.replace('Z', '+00:00'))
                                since_text = parsed_date.strftime('%m/%d/%Y')
                            except:
                                since_text = created_at[:10] if len(
                                    created_at) >= 10 else created_at

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
                            html.Div([
                                html.Span(friend['username'],
                                          className='friend-name'),
                                html.Span(f"since: {since_text}",
                                          className='friend-since',
                                          style={
                                              'font-size': '0.8rem',
                                              'color': '#888',
                                              'display': 'block',
                                              'margin-top': '2px'
                                })
                            ], style={'flex': '1'})
                        ],
                            href=f"/profile/view/{friend['username']}",
                            className='friend-link',
                            style={'text-decoration': 'none', 'color': 'inherit'})
                    ], className="friend-item lighter-bg")
                    friends_list.append(friend_item)
            else:
                friends_list = [
                    html.Li("No friends yet", className="no-friends")]

            # Update friends title to include count
            friends_count = len(friends)
            if is_own_profile:
                friends_title = f"Your Friends ({friends_count})"
            else:
                friends_title = f"{user_data['username']}'s Friends ({friends_count})"

            # Ensure we always have a valid profile image URL for the main profile
            profile_image_url = user_data.get('profile_image_url')
            if not profile_image_url or not profile_image_url.strip():
                profile_image_url = '/assets/svg/default-profile.svg'

            return friends_title, username_display, profile_image_url, user_info, friends_list, friend_request_section, tab_content

        except Exception as e:
            print(f"Error loading user profile: {e}")
            return "Friends", "Error loading profile", "", html.Div("An error occurred", style={'color': 'red'}), [], html.Div(), html.Div()

    # No username provided - should not happen with the new structure
    else:
        return "Friends", "No user specified", '', html.Div("No user specified"), [], html.Div(), html.Div()


# Callback to handle tab switching
@callback(
    [Output('active-tab-store', 'data'),
     Output('favorites-tab', 'style'),
     Output('reviews-tab', 'style'),
     Output('completed-tab', 'style')],
    [Input('favorites-tab', 'n_clicks'),
     Input('reviews-tab', 'n_clicks'),
     Input('completed-tab', 'n_clicks')],
    prevent_initial_call=True
)
def handle_tab_switch(fav_clicks, reviews_clicks, completed_clicks):
    """Handle tab switching and update tab styles"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Determine which tab was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Base styles for tabs
    active_style = {
        'padding': '10px 20px', 'border': 'none', 'background': '#007bff',
        'color': 'white', 'cursor': 'pointer', 'margin-right': '5px',
        'border-radius': '5px 5px 0 0'
    }
    inactive_style = {
        'padding': '10px 20px', 'border': 'none', 'background': '#f8f9fa',
        'color': '#6c757d', 'cursor': 'pointer', 'margin-right': '5px',
        'border-radius': '5px 5px 0 0'
    }

    if button_id == 'favorites-tab':
        return 'favorites', active_style, inactive_style, inactive_style
    elif button_id == 'reviews-tab':
        return 'reviews', inactive_style, active_style, inactive_style
    elif button_id == 'completed-tab':
        return 'completed', inactive_style, inactive_style, active_style

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update


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


# Handle edit profile button
@callback(
    Output('friends-list', 'style'),
    Input('friends-title', 'n_clicks'),
    State('friends-list', 'style'),
    prevent_initial_call=True
)
def toggle_friends_list(n_clicks, current_style):
    if n_clicks and n_clicks > 0:
        # Toggle between hidden and visible
        if current_style and current_style.get('display') == 'none':
            return {'display': 'block'}
        else:
            return {'display': 'none'}
    return current_style or {'display': 'none'}

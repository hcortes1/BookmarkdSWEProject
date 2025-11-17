import dash
from dash import html, dcc, Input, Output, State, callback
import dash_cytoscape as cyto
import backend.profile as profile_backend
import backend.friends as friends_backend
import backend.rewards as rewards_backend
import backend.bookshelf as bookshelf_backend
import backend.reading_goals as reading_goals_backend

from datetime import datetime, date  

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
        

def create_reading_goals_tab_content(user_data, is_own_profile):
    """Create the reading goals tab - only visible to profile owner"""
    
    # Privacy check - should never happen if tab is hidden, but just in case
    if not is_own_profile:
        return html.Div([
            html.H3("Private", className="section-title-showcase"),
            html.P("Reading goals are private and only visible to the profile owner.",
                   className="showcase-empty", style={'text-align': 'center', 'margin-top': '50px'})
        ])
    
    user_id = user_data.get('user_id')
    
    success, message, goals = reading_goals_backend.get_user_goals(user_id)
    
    if not success:
        return html.Div([
            html.H3("Reading Goals", className="section-title-showcase"),
            html.P(f"Error loading goals: {message}", className="showcase-empty", 
                   style={'text-align': 'center', 'margin-top': '50px', 'color': 'red'})
        ])
    
    # Create goal cards in grid layout
    goal_cards = []
    if goals:
        for goal in goals:
            goal_cards.append(create_reading_goal_card(goal, user_id))
    else:
        # Empty state card
        goal_cards = [
            html.Div([
                html.Div(style={'fontSize': '4rem', 'margin-bottom': '20px'}),
                html.P("You haven't set any reading goals yet. Click the button above to create your first goal!",
                       style={'text-align': 'center', 'color': 'var(--text-secondary)', 'font-size': '1.1rem'})
            ], className='card secondary-bg', style={
                'text-align': 'center', 
                'padding': '60px 40px',
                'border-radius': '12px',
                'box-shadow': '0 2px 8px rgba(0,0,0,0.1)'
            })
        ]
    
    return html.Div([
        # Header with Create Goal button - spans full width at top
        html.Div([
            html.H3("Your Reading Goals", className="section-title-showcase", 
                   style={'margin': '0'}),
            html.Button("+ Create New Goal", id='open-create-goal-modal', 
                       className='btn-primary',
                       style={
                           'background': '#007bff',
                           'color': 'white',
                           'border': 'none',
                           'padding': '10px 20px',
                           'border-radius': '6px',
                           'cursor': 'pointer',
                           'font-weight': 'bold'
                       })
        ], style={
            'display': 'flex', 
            'justify-content': 'space-between', 
            'align-items': 'center', 
            'margin-bottom': '30px',
            'padding-bottom': '15px',
            'border-bottom': '2px solid var(--border-color)'
        }),
        
        # Goals grid (either with goal cards or empty state card)
        html.Div(goal_cards, className='reading-goals-grid', style={
            'display': 'grid',
            'grid-template-columns': 'repeat(auto-fill, minmax(300px, 1fr))' if goals else '1fr',
            'gap': '20px',
            'margin-top': '20px'
        }),
        
        # Create Goal Modal
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Create New Reading Goal", style={'margin': '0 0 20px 0'}),
                    html.Button("×", id='close-create-goal-modal',
                               style={
                                   'position': 'absolute',
                                   'top': '15px',
                                   'right': '15px',
                                   'background': 'none',
                                   'border': 'none',
                                   'font-size': '2rem',
                                   'cursor': 'pointer',
                                   'color': 'var(--text-color)'
                               })
                ], style={'position': 'relative', 'border-bottom': '1px solid var(--border-color)', 'padding-bottom': '15px', 'margin-bottom': '20px'}),
                
                # Form content - ONLY Pages per day for now
                html.Div([
                    html.Label("Goal Type:", style={'font-weight': '600', 'margin-bottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='profile-rg-goal-type',
                        options=[
                            {'label': 'Pages per day', 'value': 'pages_per_day'}
                        ],
                        value='pages_per_day',  # Default to pages per day
                        placeholder='Select goal type',
                        style={'margin-bottom': '15px'}
                    ),
                    
                    html.Label("Book (Optional):", style={'font-weight': '600', 'margin-bottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(id='profile-rg-book-search', options=[], placeholder='Search for a book (optional)',
                             style={'margin-bottom': '15px'}),
                    
                    html.Label("Pages per Day:", style={'font-weight': '600', 'margin-bottom': '8px', 'display': 'block'}),
                    dcc.Input(id='profile-rg-target', type='number', placeholder='e.g., 50', min=1,
                             style={'width': '100%', 'padding': '8px', 'margin-bottom': '15px', 'border': '1px solid var(--border-color)', 'border-radius': '4px'}),
                    
                    html.Label("Deadline:", style={'font-weight': '600', 'margin-bottom': '8px', 'display': 'block'}),
                    dcc.DatePickerSingle(id='profile-rg-end-date', placeholder='Select end date',
                                        disabled=False,
                                        style={'width': '100%', 'margin-bottom': '15px'}),
                    
                    dcc.Checklist(
                        id='profile-rg-reminder-enabled',
                        options=[{'label': ' Enable reminders for this goal', 'value': 'on'}],
                        value=[],
                        style={'margin-bottom': '20px'}
                    ),
                    
                    html.Div(id='profile-rg-create-status', style={'margin-bottom': '15px', 'text-align': 'center', 'font-weight': '600'}),
                    
                    html.Button("Create Goal", id='profile-rg-create-btn', className='btn-primary',
                               style={
                                   'width': '100%',
                                   'background': '#007bff',
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '12px',
                                   'border-radius': '6px',
                                   'cursor': 'pointer',
                                   'font-weight': 'bold',
                                   'font-size': '1rem'
                               })
                ])
            ], className='secondary-bg', style={
                'position': 'relative',
                'background': 'var(--card-bg)',
                'padding': '30px',
                'border-radius': '12px',
                'max-width': '500px',
                'width': '90%',
                'max-height': '90vh',
                'overflow-y': 'auto',
                'box-shadow': '0 10px 40px rgba(0,0,0,0.3)'
            })
        ], id='create-goal-modal', style={
            'display': 'none',
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'background': 'rgba(0,0,0,0.5)',
            'z-index': '1000',
            'justify-content': 'center',
            'align-items': 'center'
        }),
        
        # Stores for managing state
        dcc.Store(id='profile-rg-refresh-trigger', data=0),
        dcc.Store(id='profile-goal-to-delete', data=None),
        
        # Delete Confirmation Modal
        html.Div([
            html.Div([
                html.H3("Delete Goal", style={'margin': '0 0 15px 0'}),
                html.P("Are you sure you want to delete this reading goal? This action cannot be undone.",
                      style={'margin-bottom': '20px'}),
                html.Div([
                    html.Button("Cancel", id='cancel-delete-goal',
                               className='btn-cancel',
                               style={
                                   'background': '#6c757d',
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '10px 20px',
                                   'border-radius': '6px',
                                   'cursor': 'pointer',
                                   'margin-right': '10px'
                               }),
                    html.Button("Delete", id='confirm-delete-goal',
                               className='btn-danger',
                               style={
                                   'background': '#dc3545',
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '10px 20px',
                                   'border-radius': '6px',
                                   'cursor': 'pointer'
                               })
                ], style={'text-align': 'right'})
            ], className='secondary-bg', style={
                'background': 'var(--card-bg)',
                'padding': '25px',
                'border-radius': '12px',
                'max-width': '400px',
                'box-shadow': '0 10px 40px rgba(0,0,0,0.3)'
            })
        ], id='delete-goal-modal', style={
            'display': 'none',
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'background': 'rgba(0,0,0,0.5)',
            'z-index': '1001',
            'justify-content': 'center',
            'align-items': 'center'
        })
    ], className='profile-right-column')


def create_reading_goal_card(goal, user_id):
    """Create a reading goal card with progress bar"""
    goal_id = goal.get('goal_id')
    progress = goal.get('progress', 0) or 0
    target = goal.get('target_books', 1) or 1
    
    # Calculate percentage
    try:
        percentage = int((progress / target) * 100) if target else 0
    except:
        percentage = 0
    
    # Format dates
    start_date = goal.get('start_date')
    start_text = start_date.strftime('%m/%d/%Y') if hasattr(start_date, 'strftime') else (start_date or 'Unknown')
    
    end_date = goal.get('end_date')
    if hasattr(end_date, 'strftime'):
        end_text = end_date.strftime('%m/%d/%Y')
        days_left = (end_date - date.today()).days
        if days_left >= 0:
            days_text = f"{days_left} days left"
        else:
            days_text = "Overdue"
    else:
        end_text = "No deadline"
        days_text = ""
    
    reminder_text = "Enabled" if goal.get('reminder_enabled') else "Disabled"
    
    # Determine progress bar color
    if percentage >= 100:
        bar_color = '#28a745'  # Green
    elif percentage >= 50:
        bar_color = '#ffc107'  # Yellow
    else:
        bar_color = '#007bff'  # Blue
    
    # Show book name if goal is for a specific book
    book_name = goal.get('book_name')
    if book_name:
        # Fetch book details
        book_info_section = html.Div([
            html.Span("", style={'margin-right': '5px'}),
            html.Span(book_name, style={'font-style': 'italic', 'color': '#007bff'})
        ], style={'margin-bottom': '10px', 'padding': '8px', 'background': 'rgba(0, 123, 255, 0.1)', 'border-radius': '4px'})
    else:
        book_info_section = html.Div()
    
    return html.Div([
        # Goal header
        html.Div([
            html.H4("Reading Goal", style={'margin': '0', 'font-size': '1.1rem'}),
            html.Button("Delete", id={'type': 'delete-goal-btn', 'goal_id': goal_id},
                       style={
                           'background': '#dc3545',
                           'color': 'white',
                           'border': 'none',
                           'padding': '5px 12px',
                           'border-radius': '4px',
                           'cursor': 'pointer',
                           'font-size': '0.85rem'
                       })
        ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '15px'}),
        book_info_section,
        # Progress bar
        html.Div([
            html.Div([
                html.Div(style={
                    'width': f'{min(percentage, 100)}%',
                    'height': '100%',
                    'background': bar_color,
                    'border-radius': '10px',
                    'transition': 'width 0.3s ease'
                })
            ], style={
                'width': '100%',
                'height': '20px',
                'background': '#e0e0e0',
                'border-radius': '10px',
                'overflow': 'hidden',
                'margin-bottom': '8px'
            }),
            html.Div(f"{progress} / {target} ({percentage}%)", 
                    style={'text-align': 'center', 'font-weight': 'bold', 'font-size': '1.1rem', 'color': bar_color})
        ], style={'margin-bottom': '15px'}),
        
        # Goal details
        html.Div([
            html.Div([
                html.Span("Started: ", style={'font-weight': '600'}),
                html.Span(start_text)
            ], style={'margin-bottom': '8px'}),
            html.Div([
                html.Span("Deadline: ", style={'font-weight': '600'}),
                html.Span(end_text),
                html.Span(f" ({days_text})" if days_text else "", style={'color': '#dc3545' if 'Overdue' in days_text else '#28a745', 'font-weight': '600', 'margin-left': '5px'})
            ], style={'margin-bottom': '8px'}),
            html.Div([
                html.Span("Reminders: ", style={'font-weight': '600'}),
                html.Span(reminder_text)
            ], style={'margin-bottom': '15px'})
        ]),
        
        # Update progress section
        html.Div([
            html.Label("Update Progress:", style={'font-weight': '600', 'margin-bottom': '8px', 'display': 'block'}),
            html.Div([
                dcc.Input(
                    id={'type': 'set-progress-input', 'goal_id': goal_id},
                    type='number',
                    placeholder='New progress',
                    min=0,
                    style={
                        'flex': '1',
                        'padding': '8px',
                        'border': '1px solid var(--border-color)',
                        'border-radius': '4px',
                        'margin-right': '8px'
                    }
                ),
                html.Button("Update", id={'type': 'set-progress-btn', 'goal_id': goal_id},
                           style={
                               'background': '#007bff',
                               'color': 'white',
                               'border': 'none',
                               'padding': '8px 16px',
                               'border-radius': '4px',
                               'cursor': 'pointer',
                               'font-weight': '600'
                           })
            ], style={'display': 'flex'})
        ])
        
    ], className='card secondary-bg', style={
        'padding': '20px',
        'border-radius': '12px',
        'box-shadow': '0 2px 8px rgba(0,0,0,0.1)',
        'transition': 'transform 0.2s, box-shadow 0.2s',
        'height': '100%'
    })
def layout(username=None, **kwargs):
    return html.Div([
        html.Div([
            html.Div([
                html.Button("Profile", id="profile-profile-tab",
                            className="profile-tab active-tab"),
                html.Button("Friends", id="profile-friends-tab",
                            className="profile-tab"),
                html.Button("Bookshelf", id="profile-bookshelf-tab",
                            className="profile-tab"),
                
                html.Div(
                    id='reading-goals-tab-container',
                    children=[
                        html.Button("Reading Goals", id="profile-reading-goals-tab",
                                    className="profile-tab")
                    ]
                )
            ], className='profile-tabs-container'),

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
     Output('profile-bookshelf-tab', 'className'),
     Output('profile-reading-goals-tab', 'className')
    ],
    [Input('profile-profile-tab', 'n_clicks'),
     Input('profile-friends-tab', 'n_clicks'),
     Input('profile-bookshelf-tab', 'n_clicks'),
     Input('profile-reading-goals-tab', 'n_clicks')],
    prevent_initial_call=True
)
def handle_tab_switch(profile_clicks, friends_clicks, bookshelf_clicks, reading_goals_clicks):
    """Handle tab switching and update tab classes"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Determine which tab was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'profile-profile-tab':
        return 'profile', 'profile-tab active-tab', 'profile-tab', 'profile-tab', 'profile-tab'
    elif button_id == 'profile-friends-tab':
        return 'friends', 'profile-tab', 'profile-tab active-tab', 'profile-tab', 'profile-tab'
    elif button_id == 'profile-bookshelf-tab':
        return 'bookshelf', 'profile-tab', 'profile-tab', 'profile-tab active-tab', 'profile-tab'
    elif button_id == 'profile-reading-goals-tab':
        return 'reading-goals', 'profile-tab', 'profile-tab', 'profile-tab', 'profile-tab active-tab'

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


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
    profile_card = create_profile_info_card(user_data, is_own_profile, session_data)
    
    # Get tab-specific content
    if active_tab == 'profile':
        tab_content = create_profile_tab_content(user_data, is_own_profile)
    elif active_tab == 'friends':
        tab_content = create_friends_tab_content(user_data, is_own_profile)
    elif active_tab == 'bookshelf':
        tab_content = create_bookshelf_tab_content(user_data, is_own_profile)
    elif active_tab == 'reading-goals':
        tab_content = create_reading_goals_tab_content(user_data, is_own_profile)
    else:
        tab_content = html.Div()
    
    # Return layout with profile card on left and tab content on right
    return html.Div([
        html.Div([profile_card], className="profile-left-column"),
        tab_content
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

    # Add level badge
    profile_user_id = user_data.get('user_id')
    rewards = rewards_backend.get_user_rewards(profile_user_id)
    level = rewards.get('level', 1)

    level_title = ""
    level_style = {'cursor': 'default'}
    if is_own_profile:
        xp = rewards.get('xp', 0)
        points = rewards.get('points', 0)
        _, current_level_xp, xp_to_next = rewards_backend.get_level_progress(xp)
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
    current_year = datetime.now().year

    stats_success, stats_message, yearly_stats = get_yearly_reading_stats(profile_user_id, current_year)
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
                id={'type': 'remove-friend', 'username': user_data['username']},
                className='btn-remove-friend',
                style={'background': '#dc3545', 'color': 'white', 'border': 'none',
                       'padding': '8px 16px', 'border-radius': '6px', 'margin-top': '0px', 'cursor': 'pointer'}
            )
        elif status == 'pending_sent':
            friend_request_section = html.Button(
                "Cancel Friend Request",
                id={'type': 'cancel-friend-request', 'username': user_data['username']},
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
                id={'type': 'send-friend-request', 'username': user_data['username']},
                className='btn-send-friend-request',
                style={'background': '#007bff', 'color': 'white', 'border': 'none',
                       'padding': '8px 16px', 'border-radius': '6px', 'margin-top': '0px', 'cursor': 'pointer'}
            )
    
    profile_image_url = user_data.get('profile_image_url', '/assets/svg/default-profile.svg')
    
    return html.Div([
        html.Img(src=profile_image_url, className='profile-image-compact'),
        username_display,
        user_info,
        friend_request_section
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
        authors_content = html.Div(authors_showcase, className="showcase-scroll")
    else:
        msg = "Add authors to your favorites!" if is_own_profile else f"{user_data['username']} has no favorite authors"
        authors_content = html.P(msg, className="showcase-empty")
    
    # Create Recent Reviews Section
    from backend.reviews import get_user_reviews
    all_reviews = get_user_reviews(user_data['user_id'])
    reviews = [r for r in all_reviews if r.get('review_text') and r.get('review_text').strip()][:5]
    
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
                        html.H4(review.get('title', 'Unknown'), className="showcase-title"),
                        html.P(f"⭐ {review.get('rating', 0)}/5", className="showcase-rating"),
                        html.P(review.get('review_text', ''), className="showcase-description")
                    ], href=f"/book/{review.get('book_id')}", style={"textDecoration": "none", "color": "inherit"})
                ], className="showcase-card-wide")
            )
        reviews_content = html.Div(reviews_showcase, className="showcase-scroll")
    else:
        msg = "No reviews yet" if is_own_profile else f"{user_data['username']} hasn't written reviews"
        reviews_content = html.P(msg, className="showcase-empty")
    
    # Create Recently Completed Books Section - sorted by rating then recent
    success, _, bookshelf = bookshelf_backend.get_user_bookshelf(user_data['user_id'])
    completed_books = bookshelf.get('finished', []) if success and bookshelf else []
    
    # Sort by rating (desc) then by added_at (desc)
    completed_books_sorted = sorted(
        completed_books,
        key=lambda x: (-(x.get('user_rating') or 0), -(x.get('added_at').timestamp() if hasattr(x.get('added_at'), 'timestamp') else 0))
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
                        html.H4(book.get('title', 'Unknown'), className="showcase-title"),
                        html.P(rating_display, className="showcase-rating", 
                               style={'fontWeight': 'bold', 'color': '#ffc107' if rating else None})
                    ], href=f"/book/{book.get('book_id')}", style={"textDecoration": "none", "color": "inherit"})
                ], className="showcase-card")
            )
        completed_content = html.Div(completed_showcase, className="showcase-scroll")
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
        _, current_level_xp, xp_to_next = rewards_backend.get_level_progress(xp)
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

    stats_success, stats_message, yearly_stats = get_yearly_reading_stats(profile_user_id, current_year)
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
            html.P(msg, className="showcase-empty", style={'text-align': 'center', 'margin-top': '50px'})
        ])
    
    # Build Cytoscape elements
    elements = []
    
    # Calculate positions for circular layout
    import math
    center_x, center_y = 300, 300  # center of graph
    radius = 120  # radius of circle for friends
    
    # Central node (current user) - positioned at center
    profile_img = user_data.get('profile_image_url') or '/assets/svg/default-profile.svg'
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
        
        friend_img = friend.get('profile_image_url') or '/assets/svg/default-profile.svg'
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
            friend1_friends_data = friends_backend.get_friends_list(str(friend1['user_id']))
            # Extract friend IDs for comparison
            friend1_friend_ids = {f['friend_id'] for f in friend1_friends_data}
        except Exception as e:
            print(f"Error fetching friends for {friend1['username']}: {e}")
            friend1_friend_ids = set()
        
        # Check if any of the center user's friends are also friends with friend1
        for friend2 in friends[i+1:]:  # Only check friends after this one to avoid duplicates
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
    ])


def create_bookshelf_tab_content(user_data, is_own_profile):
    """Create the bookshelf tab showing user's books organized by shelf in a visual bookshelf layout"""
    
    success, _, bookshelf = bookshelf_backend.get_user_bookshelf(user_data['user_id'])
    
    if not success or not bookshelf:
        msg = "No books on your bookshelf yet" if is_own_profile else f"{user_data['username']} has no books on their bookshelf"
        return html.Div([
            html.P(msg, className="showcase-empty", style={'text-align': 'center', 'margin-top': '50px'})
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
                    key=lambda x: (-(x.get('user_rating') or 0), -(x.get('added_at').timestamp() if hasattr(x.get('added_at'), 'timestamp') else 0))
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
                                    src=book.get('cover_url', '/assets/svg/default-book.svg'),
                                    className='bookshelf-book-cover',
                                    title=f"{book.get('title', 'Unknown')} by {book.get('author_name', 'Unknown')}"
                                )
                            ], className='bookshelf-cover-wrapper'),
                            html.Div([
                                html.H4(book.get('title', 'Unknown'), className='bookshelf-book-title'),
                                html.P(book.get('author_name', 'Unknown'), className='bookshelf-book-author'),
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
        shelf_sections.append(
            html.Div([
                html.Div([
                    html.H3(shelf_name, className="bookshelf-shelf-title"),
                    html.Span(f"({len(books)} books)", className="bookshelf-book-count")
                ], className='bookshelf-shelf-header'),
                html.Div([
                    html.Div(book_cards, className='bookshelf-books-row')
                ], className='bookshelf-shelf-container')
            ], className='bookshelf-shelf-section')
        )
    
    return html.Div(shelf_sections, className='bookshelf-layout')


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

# Handle reading goals tab container - manage hiding reading goals tab if viewing someone elses profile

@callback(
    Output('reading-goals-tab-container', 'style'),
    [Input('user-session', 'data'),
     Input('username-store', 'children')],
    prevent_initial_call=False
)
def show_hide_reading_goals_tab(session_data, viewed_username):
    """Hide reading goals tab if viewing someone else's profile"""
    
    # Check if this is the logged-in user viewing their own profile
    is_own_profile = (session_data and
                      session_data.get('logged_in', False) and
                      session_data.get('username', '').lower() == (viewed_username or '').lower())
    
    if is_own_profile:
        # Show the tab
        return {'display': 'inline-block'}
    else:
        # Hide the tab
        return {'display': 'none'}
    
    # Open/Close Create Goal Modal
@callback(
    Output('create-goal-modal', 'style'),
    [Input('open-create-goal-modal', 'n_clicks'),
     Input('close-create-goal-modal', 'n_clicks'),
     Input('profile-rg-create-btn', 'n_clicks')],
    State('create-goal-modal', 'style'),
    prevent_initial_call=True
)
def toggle_create_goal_modal(open_clicks, close_clicks, create_clicks, current_style):
    """Toggle the create goal modal visibility"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'open-create-goal-modal':
        return {**current_style, 'display': 'flex'}
    else:
        return {**current_style, 'display': 'none'}


# Create Goal
@callback(
    [Output('profile-rg-create-status', 'children'),
     Output('profile-rg-refresh-trigger', 'data'),
     Output('profile-rg-target', 'value'),
     Output('profile-rg-book-search', 'value'),
     Output('profile-rg-end-date', 'date'),
     Output('profile-rg-goal-type', 'value'),
     Output('profile-rg-reminder-enabled', 'value')],
    Input('profile-rg-create-btn', 'n_clicks'),
    [State('user-session', 'data'),
     State('profile-rg-goal-type', 'value'),
     State('profile-rg-book-search', 'value'),
     State('profile-rg-book-search', 'options'),  
     State('profile-rg-target', 'value'),
     State('profile-rg-end-date', 'date'),
     State('profile-rg-reminder-enabled', 'value'),
     State('profile-rg-refresh-trigger', 'data')],
    prevent_initial_call=True
)
def create_reading_goal(n_clicks, session_data, goal_type, book_id, book_options, target, end_date, reminder_value, current_trigger):
    """Create a new reading goal"""
    if not n_clicks or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Validation
    if not target:
        return html.Span("Pages per day is required.", style={'color': '#dc3545'}), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if not end_date:
        return html.Span("Deadline is required.", style={'color': '#dc3545'}), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    user_id = int(session_data['user_id'])
    reminder_enabled = 'on' in (reminder_value or [])
    
    # Get book name from options if book_id is selected
    book_name = None
    if book_id and book_options:
        for option in book_options:
            if option.get('value') == book_id:
                book_name = option.get('label', '')
                break
    
    import backend.reading_goals as reading_goals_backend
    success, message = reading_goals_backend.create_goal(
    user_id=user_id,
    goal_type=goal_type,
    book_name=book_name,
    target=target,
    start_date=None,
    end_date=end_date,
    reminder_enabled=reminder_enabled
)
    
    if success:
        # Clear form and refresh goals
        return (
            html.Span("Goal created successfully!", style={'color': '#28a745'}),
            current_trigger + 1,
            None,  # Clear target
            None,  # Clear book_id
            None,  # Clear end_date
            'pages_per_day',  # Reset to pages_per_day
            []     # Clear reminder checkbox
        )
    else:
        return html.Span(f"Error: {message}", style={'color': '#dc3545'}), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# Update Progress
@callback(
    [Output('profile-rg-refresh-trigger', 'data', allow_duplicate=True),
     Output({'type': 'set-progress-input', 'goal_id': dash.ALL}, 'value')],
    Input({'type': 'set-progress-btn', 'goal_id': dash.ALL}, 'n_clicks'),
    [State({'type': 'set-progress-input', 'goal_id': dash.ALL}, 'value'),
     State({'type': 'set-progress-input', 'goal_id': dash.ALL}, 'id'),
     State('profile-rg-refresh-trigger', 'data')],
    prevent_initial_call=True
)
def update_goal_progress(set_clicks, progress_values, progress_ids, current_trigger):
    """Update progress for a reading goal"""
    ctx = dash.callback_context
    if not ctx.triggered or not any(set_clicks or []):
        return dash.no_update, dash.no_update
    
    # Find which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    goal_id = eval(button_id)['goal_id']
    
    # Find the corresponding input value
    val_index = next((i for i, pid in enumerate(progress_ids) if pid['goal_id'] == goal_id), None)
    if val_index is None or progress_values[val_index] is None:
        return dash.no_update, dash.no_update
    
    new_progress = progress_values[val_index]
    
    import backend.reading_goals as reading_goals_backend
    result = reading_goals_backend.update_progress_manual(int(goal_id), int(new_progress))
    
    if result.get('success'):
        # Clear all inputs and refresh
        return current_trigger + 1, [None for _ in progress_values]
    
    return dash.no_update, dash.no_update


# Show Delete Confirmation
@callback(
    [Output('delete-goal-modal', 'style'),
     Output('profile-goal-to-delete', 'data')],
    Input({'type': 'delete-goal-btn', 'goal_id': dash.ALL}, 'n_clicks'),
    State('delete-goal-modal', 'style'),
    prevent_initial_call=True
)
def show_delete_goal_confirmation(delete_clicks, current_style):
    """Show delete confirmation modal"""
    ctx = dash.callback_context
    if not ctx.triggered or not any(delete_clicks or []):
        return dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    goal_id = eval(button_id)['goal_id']
    
    return {**current_style, 'display': 'flex'}, goal_id


# Cancel Delete
@callback(
    Output('delete-goal-modal', 'style', allow_duplicate=True),
    Input('cancel-delete-goal', 'n_clicks'),
    State('delete-goal-modal', 'style'),
    prevent_initial_call=True
)
def cancel_delete_goal(n_clicks, current_style):
    """Cancel goal deletion"""
    if not n_clicks:
        return dash.no_update
    return {**current_style, 'display': 'none'}


# Confirm Delete
@callback(
    [Output('profile-rg-refresh-trigger', 'data', allow_duplicate=True),
     Output('delete-goal-modal', 'style', allow_duplicate=True)],
    Input('confirm-delete-goal', 'n_clicks'),
    [State('profile-goal-to-delete', 'data'),
     State('profile-rg-refresh-trigger', 'data'),
     State('delete-goal-modal', 'style')],
    prevent_initial_call=True
)
def confirm_delete_goal(n_clicks, goal_id, current_trigger, modal_style):
    """Delete the goal"""
    if not n_clicks or not goal_id:
        return dash.no_update, dash.no_update
    
    import backend.reading_goals as reading_goals_backend
    result = reading_goals_backend.delete_goal(int(goal_id))
    
    if result.get('success'):
        return current_trigger + 1, {**modal_style, 'display': 'none'}
    
    return dash.no_update, {**modal_style, 'display': 'none'}


# Refresh Goals when trigger changes
@callback(
    Output('profile-tab-content', 'children', allow_duplicate=True),
    Input('profile-rg-refresh-trigger', 'data'),
    [State('user-session', 'data'),
     State('username-store', 'children'),
     State('profile-active-tab', 'data')],
    prevent_initial_call=True
)
def refresh_reading_goals(trigger, session_data, viewed_username, active_tab):
    """Refresh the reading goals content when goals are modified"""
    
    if active_tab != 'reading-goals':
        return dash.no_update
    
    if not viewed_username or not session_data or not session_data.get('logged_in'):
        return dash.no_update
    
    user_data = profile_backend.get_user_profile_by_username(viewed_username)
    if not user_data:
        return dash.no_update
    
    is_own_profile = (session_data.get('username', '').lower() == viewed_username.lower())
    
    # Create profile card and tab content
    profile_card = create_profile_info_card(user_data, is_own_profile, session_data)
    tab_content = create_reading_goals_tab_content(user_data, is_own_profile)
    
    return html.Div([
        html.Div([profile_card], className="profile-left-column"),
        tab_content
    ], className="profile-main-grid")


# Enable/disable date picker based on goal type
@callback(
    Output('profile-rg-end-date', 'disabled'),
    Input('profile-rg-goal-type', 'value'),
    prevent_initial_call=True
)
def toggle_profile_end_date(goal_type):
    """Enable date picker only for deadline goals"""
    return goal_type != 'deadline'

# Populate book dropdown with user's Currently Reading bookshelf books
@callback(
    Output('profile-rg-book-search', 'options'),
    Input('open-create-goal-modal', 'n_clicks'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def populate_book_dropdown(n_clicks, session_data):
    """Populate the book dropdown with books from user's Currently Reading shelf"""
    if not n_clicks or not session_data or not session_data.get('logged_in'):
        return []
    
    user_id = session_data.get('user_id')
    
    # Get user's bookshelf
    success, message, bookshelf = bookshelf_backend.get_user_bookshelf(user_id)
    
    if not success or not bookshelf:
        return []
    
    # Only get books from "Currently Reading" shelf (key is 'reading')
    currently_reading_books = bookshelf.get('reading', [])
    
    if not currently_reading_books:
        return [{'label': 'No books currently reading', 'value': None, 'disabled': True}]
    
    # Create dropdown options with book title and author
    options = []
    
    for book in currently_reading_books:
        book_id = book.get('book_id')
        title = book.get('title', 'Unknown')
        author = book.get('author_name', 'Unknown Author')
        options.append({
            'label': f"{title} by {author}",
            'value': book_id
        })
    
    # Sort alphabetically by title
    options.sort(key=lambda x: x['label'])
    
    return options
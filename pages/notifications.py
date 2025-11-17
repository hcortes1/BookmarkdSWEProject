import dash
from dash import html, dcc, Input, Output, State, no_update, callback
import backend.notifications as notifications_backend
import backend.bookshelf as bookshelf_backend
import backend.reviews as reviews_backend
from datetime import datetime, timezone

dash.register_page(__name__, path='/notifications')


def get_relative_time(created_at):
    """
    Convert a datetime object to a relative time string like '2 minutes ago', '3 hours ago', etc.
    """
    if not created_at:
        return 'recently'

    # Ensure created_at is a datetime object
    if isinstance(created_at, str):
        try:
            # Try to parse the string as datetime
            created_at = datetime.fromisoformat(
                created_at.replace('Z', '+00:00'))
        except:
            return 'recently'

    # If created_at is naive, assume it's UTC
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - created_at

    # Calculate time differences
    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24

    if seconds < 60:
        return 'just now'
    elif minutes < 60:
        return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
    elif hours < 24:
        return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
    elif days < 7:
        return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"
    else:
        # For older notifications, show the date
        return created_at.strftime('%b %d, %Y')


def layout():
    return html.Div([
        # Store for notification data
        dcc.Store(id='notifications-data',
                  data={'count': 0, 'notifications': []}),

        # Store for resend email feedback
        dcc.Store(id='resend-feedback-store', data=None),
        # Store for last resend time (for rate limiting)
        dcc.Store(id='last-resend-time', data=0),

        # Stores for bookshelf modal
        dcc.Store(id='bookshelf-modal-visible', data=False),
        dcc.Store(id='bookshelf-book-data', data={}),
        dcc.Store(id='bookshelf-modal-mode', data='add'),  # 'add' or 'edit'
        dcc.Store(id='bookshelf-selected-status',
                  data='want-to-read'),  # selected status

        # Auto-refresh interval (4 seconds)
        dcc.Interval(
            id='notifications-refresh-interval',
            interval=4*1000,
            n_intervals=0
        ),

        # Page header
        html.Div([
            html.H1("Notifications", className="page-title"),
            html.Div(id='notification-count-display',
                     className='notification-count-header')
        ], className='card notifications-header'),

        # Notifications list
        html.Div(id='notifications-list', className='card notifications-list'),

        # Bookshelf modal
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Add to Bookshelf", className="modal-header"),
                    html.Button("×", id='close-bookshelf-modal',
                                className="close-modal-btn"),

                    # Status selection
                    html.Div([
                        html.H4("Choose status:", className="modal-subheader"),
                        html.Div([
                            html.Button("Want to Read", id='select-status-want-to-read',
                                        className="status-btn"),
                            html.Button("Currently Reading", id='select-status-reading',
                                        className="status-btn reading"),
                            html.Button("Mark as Finished", id='select-status-finished',
                                        className="status-btn finished"),
                        ])
                    ], id='status-selection'),

                    # Review form (shown when marking as finished)
                    html.Div([
                        html.H4("Write a Review", className="modal-subheader"),
                        html.Div([
                            html.Label("Rating (required):", style={
                                       'display': 'block', 'margin-bottom': '5px'}),
                            dcc.Dropdown(
                                id='rating-dropdown',
                                options=[
                                    {'label': '⭐ 1 - Poor', 'value': 1},
                                    {'label': '⭐⭐ 2 - Fair', 'value': 2},
                                    {'label': '⭐⭐⭐ 3 - Good', 'value': 3},
                                    {'label': '⭐⭐⭐⭐ 4 - Very Good', 'value': 4},
                                    {'label': '⭐⭐⭐⭐⭐ 5 - Excellent', 'value': 5},
                                ],
                                placeholder="Select a rating...",
                                className="rating-dropdown"
                            ),
                            html.Label("Review (optional):", style={
                                       'display': 'block', 'margin-top': '15px', 'margin-bottom': '5px'}),
                            dcc.Textarea(
                                id='review-text',
                                placeholder="Share your thoughts about this book...",
                                className="review-textarea",
                                style={'width': '100%',
                                       'height': '100px', 'resize': 'vertical'}
                            )
                        ])
                    ], id='review-form', style={'display': 'none'}),

                    # Action buttons
                    html.Div([
                        html.Button("Save", id='save-bookshelf',
                                    className="save-bookshelf-btn")
                    ], className="modal-buttons-right"),

                    html.Div(id='bookshelf-feedback',
                             className="modal-feedback")
                ], className='secondary-bg modal-content')
            ], id='bookshelf-modal-overlay', className="modal-overlay")
        ], id='bookshelf-modal', style={'display': 'none'})
    ], className='notifications-page')


# Callback to refresh notifications data
@callback(
    Output('notifications-data', 'data'),
    [Input('notifications-refresh-interval', 'n_intervals'),
     Input('user-session', 'data')]
)
def refresh_notifications(n_intervals, user_session):
    if not user_session or not user_session.get('logged_in', False):
        return {'count': 0, 'notifications': []}

    user_id = user_session.get('user_id')
    if not user_id:
        return {'count': 0, 'notifications': []}

    # Use session cache only for initial load (n_intervals == 0)
    # For interval-triggered refreshes, always fetch fresh data
    if n_intervals == 0 and 'notifications' in user_session and user_session['notifications']:
        return user_session['notifications']

    # check email_verified status from database (in case it was just verified)
    email_verified = user_session.get('email_verified', False)

    # if showing unverified notification, check database for updates
    if not email_verified:
        try:
            from backend.db import get_conn
            import psycopg2.extras
            with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT email_verified FROM users WHERE user_id = %s", (int(user_id),))
                result = cur.fetchone()
                if result and result['email_verified']:
                    email_verified = True
        except Exception as e:
            pass

    # Fetch fresh notifications (pass email_verified status)
    new_data = notifications_backend.get_user_notifications(
        str(user_id), email_verified=email_verified)
    return new_data


# Callback to update session with fresh notifications and email_verified status
@callback(
    Output('user-session', 'data', allow_duplicate=True),
    [Input('notifications-data', 'data')],
    [State('user-session', 'data')],
    prevent_initial_call=True
)
def update_session_notifications(notifications_data, user_session):
    if not user_session:
        return dash.no_update

    # Update session with latest notifications
    user_session['notifications'] = notifications_data

    # check if email verification notification is gone (meaning email was verified)
    if notifications_data and 'notifications' in notifications_data:
        has_email_notif = any(n.get(
            'type') == 'email_verification' for n in notifications_data['notifications'])
        # if notification is gone but session still shows unverified, update session
        if not has_email_notif and not user_session.get('email_verified', False):
            try:
                from backend.db import get_conn
                import psycopg2.extras
                user_id = user_session.get('user_id')
                with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT email_verified FROM users WHERE user_id = %s", (int(user_id),))
                    result = cur.fetchone()
                    if result and result['email_verified']:
                        user_session['email_verified'] = True
            except Exception as e:
                pass

    return user_session


# Callback to update the notifications display
@callback(
    [Output('notifications-list', 'children'),
     Output('notification-count-display', 'children')],
    [Input('notifications-data', 'data'),
     Input('user-session', 'data')]
)
def update_notifications_display(notifications_data, user_session):
    if not user_session or not user_session.get('logged_in', False):
        return [], ""

    # Use cached notifications in session if store is empty
    if not notifications_data.get('notifications') and 'notifications' in user_session:
        notifications_data = user_session['notifications']

    count = notifications_data.get('count', 0)
    notifications = notifications_data.get('notifications', [])

    # Sort notifications by created_at in descending order (newest first)
    # Put email verification notification first (it has None created_at), then sort others
    def sort_key(x):
        created_at = x.get('created_at')
        if created_at is None:
            return 'zzzzzzzzz'  # put at top (reverse=True makes this first)
        return created_at if created_at else ''

    notifications = sorted(notifications, key=sort_key, reverse=True)

    # Update header count
    count_display = f"{count} notification{'s' if count != 1 else ''}"

    if not notifications:
        return [], count_display

    # Create notification items
    notification_items = []
    for notification in notifications:
        if notification['type'] == 'email_verification':
            # email verification notification (cannot be dismissed)
            item = html.Div([
                html.Div([
                    html.Img(
                        src='/assets/svg/email-icon.svg',
                        style={
                            'width': '50px',
                            'height': '50px',
                            'border-radius': '50%',
                            'object-fit': 'cover',
                            'padding': '10px',
                            'background-color': 'var(--secondary-bg)'
                        }
                    )
                ], className='notification-avatar'),

                html.Div([
                    # Row 1: Title
                    html.Strong(
                        'Verify Your Email',
                        className='notification-title text-link',
                        style={'display': 'block', 'margin-bottom': '6px'}
                    ),
                    # Row 2: Body text and button
                    html.Div([
                        html.Div(
                            'Please verify your email address to secure your account',
                            className='notification-message text-primary',
                            style={'flex': '1', 'display': 'flex',
                                   'align-items': 'center'}
                        ),
                        html.Div([
                            html.Button(
                                'Resend Email',
                                id='resend-verification-btn',
                                n_clicks=0,
                                className='btn-accept-notification btn-email-verify'
                            ),
                            html.Div(
                                id='resend-email-feedback', className='resend-feedback', style={'marginTop': '5px'})
                        ], className='notification-actions', style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start', 'gap': '5px'})
                    ], className='notification-row', style={'display': 'flex', 'align-items': 'center', 'gap': '12px'})
                ], className='notification-main-content', style={'flex': '1'})
            ], className='card notification-item notification-no-hover', style={
                'display': 'flex',
                'align-items': 'flex-start',
                'padding': '16px',
                'border-left': '4px solid var(--link-color)'
            })

            notification_items.append(item)

        elif notification['type'] == 'friend_request':
            sender_username = notification.get('sender_username') or ''
            profile_href = f"/profile/view/{sender_username}"

            item = html.Div([
                dcc.Link(
                    html.Div([
                        html.Img(
                            src=notification.get(
                                'sender_profile_image_url') or '/assets/svg/default-profile.svg',
                            style={
                                'width': '50px',
                                'height': '50px',
                                'border-radius': '50%',
                                'object-fit': 'cover'
                            }
                        )
                    ], className='notification-avatar'),
                    href=profile_href,
                    style={'text-decoration': 'none', 'color': 'inherit'}
                ),

                html.Div([
                    # Row 1: Title
                    dcc.Link(
                        html.Strong(f"{sender_username} sent you a friend request",
                                    className='notification-title text-link'),
                        href=profile_href,
                        style={'text-decoration': 'none',
                               'display': 'block', 'margin-bottom': '6px'}
                    ),
                    # Row 2: Timestamp and buttons
                    html.Div([
                        html.Div(
                            get_relative_time(notification.get('created_at')),
                            className='notification-time text-secondary',
                            style={'flex': '1', 'display': 'flex',
                                   'align-items': 'center'}
                        ),
                        html.Div([
                            html.Button(
                                'Accept',
                                id={'type': 'accept-notification',
                                    'notification_id': notification['id']},
                                className='btn-accept-notification'
                            ),
                            html.Button(
                                'Decline',
                                id={'type': 'decline-notification',
                                    'notification_id': notification['id']},
                                className='btn-decline-notification'
                            ),
                        ], className='notification-actions')
                    ], style={'display': 'flex', 'align-items': 'center', 'gap': '12px'})
                ], className='notification-main-content', style={'flex': '1'})
            ], className='card notification-item', style={
                'display': 'flex',
                'align-items': 'flex-start',
                'padding': '16px'
            })

            notification_items.append(item)

        elif notification['type'] == 'book_recommendation':
            sender_username = notification.get('sender_username') or ''
            profile_href = f"/profile/view/{sender_username}"
            book_href = f"/book/{notification.get('book_id')}"

            item = html.Div([
                # Dismiss button in top-right corner
                html.Button(
                    '✕',
                    id={'type': 'dismiss-notification',
                        'notification_id': notification['id']},
                    className='btn-dismiss-small text-muted',
                    title='Dismiss notification'
                ),

                dcc.Link(
                    html.Div([
                        html.Img(
                            src=notification.get(
                                'book_cover_url') or '/assets/svg/default-book.svg',
                            style={
                                'width': '50px',
                                'height': '50px',
                                'border-radius': '8px',
                                'object-fit': 'contain'
                            },
                            className='bg-light'
                        )
                    ], className='notification-avatar'),
                    href=book_href,
                    style={'text-decoration': 'none', 'color': 'inherit'}
                ),

                html.Div([
                    # Row 1: Title
                    dcc.Link(
                        html.Strong(notification.get('book_title', 'a book'),
                                    className='notification-title text-link'),
                        href=book_href,
                        style={'text-decoration': 'none',
                               'display': 'block', 'margin-bottom': '6px'}
                    ),
                    # Row 2: Details (sender and reason)
                    html.Div([
                        html.Div([
                            html.Span('Recommended by ',
                                      className='text-primary'),
                            dcc.Link(html.Strong(sender_username, className='text-link'),
                                     href=profile_href, style={'text-decoration': 'none'})
                        ], style={'margin-bottom': '4px'}),
                        # Show reason if provided
                        html.Div(
                            f"\"{notification.get('reason', 'You might like this book!')}\"",
                            className='notification-reason text-secondary',
                            style={'font-style': 'italic',
                                   'margin-bottom': '8px'}
                        ) if notification.get('reason') else html.Div(),
                    ]),
                    # Row 3: Timestamp and button
                    html.Div([
                        html.Div(
                            get_relative_time(notification.get('created_at')),
                            className='notification-time text-secondary',
                            style={'flex': '1', 'display': 'flex',
                                   'align-items': 'center'}
                        ),
                        html.Div([
                            html.Button(
                                'Add to Bookshelf',
                                id={'type': 'add-to-bookshelf-notification',
                                    'notification_id': notification['id']},
                                className='btn-add-to-bookshelf'
                            )
                        ], className='notification-actions')
                    ], style={'display': 'flex', 'align-items': 'center', 'gap': '12px'})
                ], className='notification-main-content', style={'flex': '1'})
            ], className='card notification-item', style={
                'display': 'flex',
                'align-items': 'flex-start',
                'padding': '16px'
            })

            notification_items.append(item)

        elif notification['type'] == 'reading_goal_reminder':
            goal_href = f"/profile/view/{user_session.get('username')}"
            book_id = notification.get('book_id')
            
            # Use book cover if available, otherwise use goal icon
            if book_id and notification.get('book_cover_url'):
                avatar = dcc.Link(
                    html.Div([
                        html.Img(
                            src=notification.get('book_cover_url') or '/assets/svg/default-book.svg',
                            style={
                                'width': '50px',
                                'height': '50px',
                                'border-radius': '8px',
                                'object-fit': 'contain'
                            },
                            className='bg-light'
                        )
                    ], className='notification-avatar'),
                    href=f"/book/{book_id}",
                    style={'text-decoration': 'none', 'color': 'inherit'}
                )
            else:
                avatar = html.Div([
                    html.Div(
                        style={
                            'width': '50px',
                            'height': '50px',
                            'display': 'flex',
                            'align-items': 'center',
                            'justify-content': 'center',
                            'font-size': '2rem',
                            'border-radius': '50%',
                            'background-color': 'var(--secondary-bg)'
                        }
                    )
                ], className='notification-avatar')
            
            # Build progress text
            percentage = notification.get('percentage', 0)
            progress = notification.get('progress', 0)
            target = notification.get('target', 1)
            days_left_text = notification.get('days_left_text', '')
            
            # Determine border color based on status
            if 'Overdue' in days_left_text:
                border_color = '#dc3545'  # Red
            elif percentage < 50:
                border_color = '#ffc107'  # Yellow
            else:
                border_color = '#28a745'  # Green
            
            item = html.Div([
                # Dismiss button
                html.Button(
                    '✕',
                    id={'type': 'dismiss-goal-reminder', 'goal_id': notification['goal_id']},
                    className='btn-dismiss-small text-muted',
                    title='Dismiss reminder'
                ),
                
                avatar,
                
                html.Div([
                    # Row 1: Title
                    dcc.Link(
                        html.Strong(
                            notification.get('book_title', 'Reading Goal'),
                            className='notification-title text-link'
                        ),
                        href=goal_href,
                        style={'text-decoration': 'none', 'display': 'block', 'margin-bottom': '6px'}
                    ),
                    # Row 2: Progress details
                    html.Div([
                        html.Div(
                            f"{percentage}% complete ({progress}/{target})",
                            className='text-primary',
                            style={'margin-bottom': '4px', 'font-weight': '600'}
                        ),
                        html.Div(
                            days_left_text,
                            className='text-secondary' if 'Overdue' not in days_left_text else 'text-danger',
                            style={'font-weight': 'bold' if 'Overdue' in days_left_text or 'today' in days_left_text.lower() else 'normal'}
                        ) if days_left_text else html.Div()
                    ]),
                    # Row 3: Timestamp
                    html.Div([
                        html.Div(
                            get_relative_time(notification.get('created_at')),
                            className='notification-time text-secondary',
                            style={'flex': '1', 'display': 'flex', 'align-items': 'center', 'margin-top': '8px'}
                        )
                    ])
                ], className='notification-main-content', style={'flex': '1'})
            ], className='card notification-item', style={
                'display': 'flex',
                'align-items': 'flex-start',
                'padding': '16px',
                'border-left': f'4px solid {border_color}'
            })
            
            notification_items.append(item)

    return notification_items, count_display


# Callback to handle notification responses (non-resend actions)
@callback(
    [Output('notifications-refresh-interval', 'n_intervals'),
     Output('bookshelf-modal-visible', 'data'),
     Output('bookshelf-book-data', 'data')],
    [Input({'type': 'accept-notification', 'notification_id': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'decline-notification',
           'notification_id': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'dismiss-notification',
           'notification_id': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'add-to-bookshelf-notification',
           'notification_id': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'dismiss-goal-reminder', 'goal_id': dash.dependencies.ALL}, 'n_clicks')],  
    [State('user-session', 'data'),
     State('notifications-refresh-interval', 'n_intervals'),
     State('notifications-data', 'data')],
    prevent_initial_call=True
)
def handle_notification_response(accept_clicks, decline_clicks, dismiss_clicks, add_bookshelf_clicks, dismiss_goal_clicks, user_session, current_interval, notifications_data):
    if not user_session or not user_session.get('logged_in', False):
        return dash.no_update, dash.no_update, dash.no_update

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update

    # Get the triggered component
    triggered_prop = ctx.triggered[0]['prop_id']
    clicked_value = ctx.triggered[0]['value']

    if clicked_value is None or clicked_value == 0:
        return dash.no_update, dash.no_update, dash.no_update

    try:
        import json
        # Parse the button ID
        button_id_str = triggered_prop.split('.')[0]
        button_data = json.loads(button_id_str.replace("'", '"'))

        button_type = button_data['type']

        # Handle different notification types
        if button_type in ['accept-notification', 'decline-notification']:
            # Friend request response
            notification_id = button_data['notification_id']
            is_accept = button_type == 'accept-notification'
            result = notifications_backend.respond_to_friend_request_notification(
                user_id=str(user_session['user_id']),
                notification_id=notification_id,
                accept=is_accept
            )
            
        elif button_type == 'dismiss-notification':
            # Book recommendation dismissal
            notification_id = button_data['notification_id']
            result = notifications_backend.respond_to_book_recommendation_notification(
                user_id=str(user_session['user_id']),
                notification_id=notification_id,
                dismiss=True
            )
            
        elif button_type == 'dismiss-goal-reminder':
            # Reading goal reminder dismissal
            goal_id = button_data['goal_id']
            result = notifications_backend.dismiss_reading_goal_reminder(
                user_id=str(user_session['user_id']),
                goal_id=goal_id
            )
            
        elif button_type == 'add-to-bookshelf-notification':
            # Open bookshelf modal with book data
            notification_id = button_data['notification_id']
            if notifications_data and 'notifications' in notifications_data:
                for notification in notifications_data['notifications']:
                    if notification['id'] == notification_id:
                        book_data = {
                            'notification_id': notification['id'],
                            'book_id': notification.get('book_id'),
                            'title': notification.get('book_title', ''),
                            'author': notification.get('book_author', ''),
                            'isbn': notification.get('book_isbn', ''),
                            'cover_url': notification.get('book_cover_url', ''),
                            'description': notification.get('book_description', ''),
                            'pages': notification.get('book_pages', 0),
                            'published_date': notification.get('book_published_date', ''),
                            'genres': notification.get('book_genres', [])
                        }
                        return current_interval, True, book_data
            return dash.no_update, dash.no_update, dash.no_update
            
        else:
            return dash.no_update, dash.no_update, dash.no_update

        # For all notification responses except add-to-bookshelf (which returns above)
        if result.get('success'):
            # Trigger a refresh by incrementing the interval counter
            return current_interval + 1, dash.no_update, dash.no_update
        else:
            return dash.no_update, dash.no_update, dash.no_update

    except Exception as e:
        print(f"Error handling notification response: {e}")
        return dash.no_update, dash.no_update, dash.no_update


# Callback to handle bookshelf modal actions
@callback(
    [Output('bookshelf-modal-visible', 'data', allow_duplicate=True),
     Output('bookshelf-book-data', 'data', allow_duplicate=True),
     Output('bookshelf-feedback', 'children'),
     Output('bookshelf-selected-status', 'data', allow_duplicate=True),
     Output('notifications-refresh-interval', 'n_intervals', allow_duplicate=True)],
    [Input('save-bookshelf', 'n_clicks'),
     Input('close-bookshelf-modal', 'n_clicks'),
     Input('select-status-want-to-read', 'n_clicks'),
     Input('select-status-reading', 'n_clicks'),
     Input('select-status-finished', 'n_clicks')],
    [State('user-session', 'data'),
     State('bookshelf-book-data', 'data'),
     State('bookshelf-selected-status', 'data'),
     State('rating-dropdown', 'value'),
     State('review-text', 'value'),
     State('notifications-refresh-interval', 'n_intervals')],
    prevent_initial_call=True
)
def handle_bookshelf_modal(save_clicks, close_clicks, want_read_clicks, reading_clicks, finished_clicks, user_session, book_data, selected_status, rating, review, current_interval):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, "", dash.no_update

    if not user_session or not user_session.get('logged_in', False):
        return False, None, "Please log in to add books to your bookshelf.", dash.no_update

    user_id = user_session['user_id']
    triggered_prop = ctx.triggered[0]['prop_id']

    # Handle status selection - immediate save for want-to-read and reading
    if 'select-status-want-to-read' in triggered_prop:
        if not book_data:
            return no_update, no_update, "No book data available.", no_update, no_update

        try:
            # Immediately add to bookshelf as plan-to-read
            success, message = bookshelf_backend.add_to_bookshelf(
                user_id=int(user_id),
                book_id=int(book_data['book_id']),
                shelf_type='plan-to-read'
            )

            if success:
                # Mark notification as responded to
                notification_result = notifications_backend.respond_to_book_recommendation_notification(
                    user_id=str(user_id),
                    notification_id=book_data['notification_id'],
                    dismiss=True
                )
                # Close modal and refresh notifications
                return False, None, "Book added to Want to Read!", no_update, current_interval + 1
            else:
                return no_update, no_update, f"Error: {message}", no_update, no_update
        except Exception as e:
            print(f"Error adding book to bookshelf: {e}")
            return no_update, no_update, "An error occurred while adding the book.", no_update, no_update

    elif 'select-status-reading' in triggered_prop:
        if not book_data:
            return no_update, no_update, "No book data available.", no_update, no_update

        try:
            # Immediately add to bookshelf as reading
            success, message = bookshelf_backend.add_to_bookshelf(
                user_id=int(user_id),
                book_id=int(book_data['book_id']),
                shelf_type='reading'
            )

            if success:
                # Mark notification as responded to
                notification_result = notifications_backend.respond_to_book_recommendation_notification(
                    user_id=str(user_id),
                    notification_id=book_data['notification_id'],
                    dismiss=True
                )
                # Close modal and refresh notifications
                return False, None, "Book added to Currently Reading!", no_update, current_interval + 1
            else:
                return no_update, no_update, f"Error: {message}", no_update, no_update
        except Exception as e:
            print(f"Error adding book to bookshelf: {e}")
            return no_update, no_update, "An error occurred while adding the book.", no_update, no_update

    elif 'select-status-finished' in triggered_prop:
        # Just update selected status for finished (requires review form)
        return no_update, no_update, "", 'finished', no_update

    # Handle close
    if 'close-bookshelf-modal' in triggered_prop:
        return False, None, "", dash.no_update, dash.no_update

    # Handle save
    if 'save-bookshelf' in triggered_prop:
        if not book_data:
            return dash.no_update, dash.no_update, "No book data available.", dash.no_update

        # Use selected status or default
        status = selected_status or 'want-to-read'

        try:
            # Map status to shelf type (database values)
            shelf_mapping = {
                'want-to-read': 'plan-to-read',
                'currently-reading': 'reading',
                'finished': 'completed'
            }
            shelf_type = shelf_mapping.get(status, 'plan-to-read')

            # Handle review submission for finished books
            if status == 'finished':
                if not rating:
                    return no_update, no_update, "Please select a rating to mark the book as finished.", no_update, no_update

                # Add to bookshelf first
                success, message = bookshelf_backend.add_to_bookshelf(
                    user_id=int(user_id),
                    book_id=int(book_data['book_id']),
                    shelf_type=shelf_type
                )

                if not success:
                    return no_update, no_update, f"Error adding to bookshelf: {message}", no_update, no_update

                # Then save review
                review_success, review_message = reviews_backend.create_or_update_review(
                    user_id=int(user_id),
                    book_id=int(book_data['book_id']),
                    rating=int(rating),
                    review_text=review or ""
                )

                if review_success:
                    # Mark notification as responded to (dismiss the recommendation)
                    notification_result = notifications_backend.respond_to_book_recommendation_notification(
                        user_id=str(user_id),
                        notification_id=book_data['notification_id'],
                        dismiss=True
                    )
                    return False, None, "Book marked as finished with review!", no_update, current_interval + 1
                else:
                    return no_update, no_update, f"Bookshelf updated but error saving review: {review_message}", no_update, no_update
            else:
                # Add book to bookshelf for other statuses
                success, message = bookshelf_backend.add_to_bookshelf(
                    user_id=int(user_id),
                    book_id=int(book_data['book_id']),
                    shelf_type=shelf_type
                )

                if success:
                    # Mark notification as responded to (dismiss the recommendation)
                    notification_result = notifications_backend.respond_to_book_recommendation_notification(
                        user_id=str(user_id),
                        notification_id=book_data['notification_id'],
                        dismiss=True
                    )
                    # Close modal and refresh notifications
                    return False, None, f"Book added to your bookshelf!", no_update, current_interval + 1
                else:
                    return no_update, no_update, f"Error: {message}", no_update, no_update

        except Exception as e:
            print(f"Error adding book to bookshelf: {e}")
            return no_update, no_update, "An error occurred while adding the book.", no_update, no_update

    return dash.no_update, dash.no_update, "", dash.no_update, dash.no_update


# Callback to update status button styles based on selected status
@callback(
    [Output('select-status-want-to-read', 'className'),
     Output('select-status-reading', 'className'),
     Output('select-status-finished', 'className')],
    Input('bookshelf-selected-status', 'data'),
    prevent_initial_call=False
)
def update_status_button_styles(selected_status):
    base_class = 'status-btn'
    want_class = base_class
    reading_class = base_class
    finished_class = base_class

    if selected_status == 'want-to-read':
        want_class += ' selected'
    elif selected_status == 'currently-reading':
        reading_class += ' reading selected'
    elif selected_status == 'finished':
        finished_class += ' finished selected'

    return want_class, reading_class, finished_class


# Callback to update modal visibility based on store
@callback(
    Output('bookshelf-modal', 'style'),
    Input('bookshelf-modal-visible', 'data'),
    prevent_initial_call=False
)
def update_bookshelf_modal_visibility(is_visible):
    """Update modal style based on visibility state"""
    if is_visible:
        return {'display': 'block'}
    else:
        return {'display': 'none'}


# Callback to show/hide review form based on status selection
@callback(
    [Output('review-form', 'style', allow_duplicate=True),
     Output('status-selection', 'style', allow_duplicate=True)],
    [Input('select-status-want-to-read', 'n_clicks'),
     Input('select-status-reading', 'n_clicks'),
     Input('select-status-finished', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_review_form(want_clicks, reading_clicks, finished_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered_prop = ctx.triggered[0]['prop_id']

    if 'select-status-finished' in triggered_prop:
        # Show review form for finished books
        return {'display': 'block'}, {'display': 'none'}
    else:
        # Hide review form for other statuses
        return {'display': 'none'}, {'display': 'block'}


def toggle_review_form(status):
    if status == 'finished':
        return {'display': 'block'}
    return {'display': 'none'}


# Separate callback to handle resend verification with rate limiting
@callback(
    [Output('resend-feedback-store', 'data'),
     Output('last-resend-time', 'data'),
     Output('notifications-refresh-interval', 'n_intervals', allow_duplicate=True)],
    Input('resend-verification-btn', 'n_clicks'),
    [State('user-session', 'data'),
     State('last-resend-time', 'data'),
     State('notifications-refresh-interval', 'n_intervals')],
    prevent_initial_call=True
)
def handle_resend_verification(n_clicks, user_session, last_resend_time, current_interval):
    """Handle resend verification email with rate limiting (60 seconds)"""
    if not n_clicks or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update

    if not user_session or not user_session.get('logged_in', False):
        return {'success': False, 'message': 'Please log in'}, dash.no_update, dash.no_update

    import time
    current_time = time.time()

    # Check if 90 seconds have passed since last resend
    if last_resend_time and (current_time - last_resend_time) < 90:
        remaining = int(90 - (current_time - last_resend_time))
        return {'success': False, 'message': f'retry in {remaining}s'}, dash.no_update, dash.no_update

    # Send the email
    result = notifications_backend.resend_verification_email(
        user_id=int(user_session['user_id'])
    )

    if result.get('success'):
        return {'success': True, 'message': 'Verification email sent!'}, current_time, current_interval + 1
    else:
        return {'success': False, 'message': result.get('message', 'Failed to send email')}, dash.no_update, dash.no_update


# Callback to update button state based on rate limiting
@callback(
    [Output('resend-verification-btn', 'disabled'),
     Output('resend-verification-btn', 'children')],
    [Input('last-resend-time', 'data'),
     Input('notifications-refresh-interval', 'n_intervals')],
    prevent_initial_call=False
)
def update_resend_button_state(last_resend_time, n_intervals):
    """Update button disabled state and text based on rate limiting"""
    if not last_resend_time or last_resend_time == 0:
        return False, 'Resend Email'

    import time
    current_time = time.time()
    time_since_last = current_time - last_resend_time

    if time_since_last < 90:
        remaining = int(90 - time_since_last)
        return True, f'Resend Email'
    else:
        return False, 'Resend Email'


# Callback to display resend email feedback with live countdown
@callback(
    Output('resend-email-feedback', 'children'),
    [Input('resend-feedback-store', 'data'),
     Input('last-resend-time', 'data'),
     Input('notifications-refresh-interval', 'n_intervals')],
    prevent_initial_call=False
)
def display_resend_feedback(feedback_data, last_resend_time, n_intervals):
    """Display success or error message after resending verification email with live countdown"""
    # If there's a last resend time, show countdown
    if last_resend_time and last_resend_time != 0:
        import time
        current_time = time.time()
        time_since_last = current_time - last_resend_time

        if time_since_last < 90:
            remaining = int(90 - time_since_last)
            return html.Span(
                f'Message sent: retry in {remaining}s',
                style={
                    'color': '#28a745',
                    'font-size': '0.9rem',
                    'font-weight': '500'
                }
            )

    # Show feedback from store if no active countdown
    if not feedback_data:
        return ""

    if feedback_data.get('success'):
        return html.Span(
            'Message sent: retry in 90s',
            style={
                'color': '#28a745',
                'font-size': '0.9rem',
                'font-weight': '500'
            }
        )
    else:
        message = feedback_data.get('message', 'Failed to send')
        # If message contains 'retry in', treat as success (rate limit)
        if 'retry in' in message:
            return html.Span(
                f"Message sent: {message}",
                style={
                    'color': '#28a745',
                    'font-size': '0.9rem',
                    'font-weight': '500'
                }
            )
        else:
            return html.Span(
                message,
                style={
                    'color': '#dc3545',
                    'font-size': '0.9rem',
                    'font-weight': '500'
                }
            )

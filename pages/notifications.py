import dash
from dash import html, dcc, Input, Output, State
import backend.notifications as notifications_backend
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
        ], className='notifications-header'),

        # Notifications list
        html.Div(id='notifications-list', className='notifications-list')
    ], className='notifications-page')


# Callback to refresh notifications data
@dash.callback(
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

    # Fetch fresh notifications
    new_data = notifications_backend.get_user_notifications(str(user_id))
    return new_data


# Callback to update session with fresh notifications
@dash.callback(
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
    return user_session


# Callback to update the notifications display
@dash.callback(
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

    # Update header count
    count_display = f"{count} notification{'s' if count != 1 else ''}"

    if not notifications:
        return [], count_display

    # Create notification items
    notification_items = []
    for notification in notifications:
        if notification['type'] == 'friend_request':
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
                    html.Div([
                        html.Div([
                            dcc.Link(html.Strong(sender_username, className='notification-username'),
                                     href=profile_href, style={'text-decoration': 'none', 'color': '#1976d2'}),
                            html.Span(' sent you a friend request', className='notification-message', style={
                                      'margin-left': '6px', 'color': '#333'})
                        ], style={'display': 'flex', 'align-items': 'center'}),

                        html.Div(
                            get_relative_time(notification.get('created_at')),
                            className='notification-time',
                            style={'font-size': '12px',
                                   'color': '#666', 'margin-top': '4px'}
                        )
                    ], className='notification-content'),

                    html.Div([
                        html.Button(
                            'Accept',
                            id={'type': 'accept-notification',
                                'notification_id': notification['id']},
                            className='btn-accept-notification',
                            style={
                                'background': '#28a745',
                                'color': 'white',
                                'border': 'none',
                                'padding': '8px 16px',
                                'border-radius': '4px',
                                'margin-right': '8px',
                                'cursor': 'pointer',
                                'font-size': '14px'
                            }
                        ),
                        html.Button(
                            'Decline',
                            id={'type': 'decline-notification',
                                'notification_id': notification['id']},
                            className='btn-decline-notification',
                            style={
                                'background': '#dc3545',
                                'color': 'white',
                                'border': 'none',
                                'padding': '8px 16px',
                                'border-radius': '4px',
                                'cursor': 'pointer',
                                'font-size': '14px'
                            }
                        )
                    ], className='notification-actions')
                ], className='notification-main-content')
            ], className='notification-item', style={
                'display': 'flex',
                'align-items': 'flex-start',
                'padding': '16px',
                'border-bottom': '1px solid #f0f0f0',
                'background': 'white'
            })

            notification_items.append(item)

    return notification_items, count_display


# Callback to handle notification responses
@dash.callback(
    Output('notifications-refresh-interval', 'n_intervals'),
    [Input({'type': 'accept-notification', 'notification_id': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'decline-notification', 'notification_id': dash.dependencies.ALL}, 'n_clicks')],
    [State('user-session', 'data'),
     State('notifications-refresh-interval', 'n_intervals')],
    prevent_initial_call=True
)
def handle_notification_response(accept_clicks, decline_clicks, user_session, current_interval):
    if not user_session or not user_session.get('logged_in', False):
        return dash.no_update

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    # Get the triggered component
    triggered_prop = ctx.triggered[0]['prop_id']
    clicked_value = ctx.triggered[0]['value']

    if clicked_value is None or clicked_value == 0:
        return dash.no_update

    try:
        import json
        # Parse the button ID
        button_id_str = triggered_prop.split('.')[0]
        button_data = json.loads(button_id_str.replace("'", '"'))

        notification_id = button_data['notification_id']
        is_accept = button_data['type'] == 'accept-notification'

        # Respond to the notification
        result = notifications_backend.respond_to_friend_request_notification(
            user_id=str(user_session['user_id']),
            notification_id=notification_id,
            accept=is_accept
        )

        if result['success']:
            # Trigger a refresh by incrementing the interval counter
            return current_interval + 1
        else:
            return dash.no_update

    except Exception as e:
        print(f"Error handling notification response: {e}")
        return dash.no_update

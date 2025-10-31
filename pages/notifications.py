import dash
from dash import html, dcc, Input, Output, State
import backend.notifications as notifications_backend

dash.register_page(__name__, path='/notifications')


def layout():
    return html.Div([
        # Store for notification data
        dcc.Store(id='notifications-data',
                  data={'count': 0, 'notifications': []}),

        # Auto-refresh interval (3-5 seconds)
        dcc.Interval(
            id='notifications-refresh-interval',
            interval=4*1000,  # 4 seconds
            n_intervals=0
        ),

        # Page header
        html.Div([
            html.H1("Notifications", className="page-title"),
            html.Div(id='notification-count-display',
                     className='notification-count-header')
        ], className='notifications-header'),

        # Notifications list
        html.Div(id='notifications-list',
                 className='notifications-list', children=[])
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

    # If we have cached notifications in session, use them immediately
    if 'notifications' in user_session and user_session['notifications']:
        return user_session['notifications']

    # Otherwise, fetch fresh notifications
    new_data = notifications_backend.get_user_notifications(str(user_id))
    return new_data


# Callback to update the notifications display
@dash.callback(
    [Output('notifications-list', 'children'),
     Output('notification-count-display', 'children')],
    [Input('notifications-data', 'data'),
     Input('user-session', 'data')],
    prevent_initial_call=True
)
def update_notifications_display(notifications_data, user_session):
    if not user_session or not user_session.get('logged_in', False):
        return [], ""

    # Use cached notifications from session if store is empty
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
            item = html.Div([
                # Profile image
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

                # Content
                html.Div([
                    html.Div([
                        html.Span(notification['message'],
                                  className='notification-message'),
                        html.Div(
                            f"Sent {notification.get('created_at', 'recently')}",
                            className='notification-time',
                            style={'font-size': '12px',
                                   'color': '#666', 'margin-top': '4px'}
                        )
                    ], className='notification-content'),

                    # Action buttons
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
    Output('notifications-data', 'data', allow_duplicate=True),
    [Input({'type': 'accept-notification', 'notification_id': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'decline-notification', 'notification_id': dash.dependencies.ALL}, 'n_clicks')],
    [State('user-session', 'data'),
     State('notifications-data', 'data')],
    prevent_initial_call=True
)
def handle_notification_response(accept_clicks, decline_clicks, user_session, notifications_data):
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
            # Refresh notifications after response
            return notifications_backend.get_user_notifications(str(user_session['user_id']))
        else:
            return dash.no_update

    except Exception as e:
        return dash.no_update

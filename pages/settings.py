import dash
from dash import html, dcc, Input, Output, State, callback
import backend.settings as settings_backend
import base64

dash.register_page(__name__, path='/profile/settings')

layout = html.Div([
    html.H1("Settings", style={
            'margin': '32px 0 8px 0', 'font-size': '28px', 'font-weight': '600', 'text-align': 'center'}),
    # Navigation sidebar and content container
    html.Div([
        # Navigation sidebar
        html.Div([
            html.Div("Navigation", style={
                'font-weight': 'bold', 'margin-bottom': '12px', 'font-size': '13px', 'color': 'var(--text-color-secondary)'
            }),
            html.Div([
                html.A("Profile Settings", href="#profile-settings", style={
                    'display': 'block', 'padding': '6px 10px', 'margin-bottom': '3px',
                    'text-decoration': 'none', 'color': 'var(--link-color)', 'border-radius': '4px',
                    'transition': 'background-color 0.2s', 'font-size': '13px'
                }),
                html.A("Account Settings", href="#account-settings", style={
                    'display': 'block', 'padding': '6px 10px', 'margin-bottom': '3px',
                    'text-decoration': 'none', 'color': 'var(--link-color)', 'border-radius': '4px',
                    'transition': 'background-color 0.2s', 'font-size': '13px'
                }),
                html.A("Account Actions", href="#account-actions", style={
                    'display': 'block', 'padding': '6px 10px', 'margin-bottom': '3px',
                    'text-decoration': 'none', 'color': 'var(--link-color)', 'border-radius': '4px',
                    'transition': 'background-color 0.2s', 'font-size': '13px'
                }),
            ], style={'list-style': 'none', 'padding': '0', 'margin': '0'})
        ], className="card settings-sidebar", style={
            'width': '140px', 'padding': '15px',
            'border-radius': '8px',
            'margin-right': '20px', 'height': 'fit-content', 'position': 'sticky', 'top': '20px'
        }),

        # Main content area
        html.Div([
            # Profile Settings section
            html.Div([
                html.H2("Profile Settings", id="profile-settings", style={
                        'margin-bottom': '20px', 'font-size': '24px', 'font-weight': '500'}),
                # Profile Picture section
                html.Img(
                    id="current-profile-image",
                    src="/assets/svg/default-profile.svg",
                    className="profile-image-preview"
                ),
                dcc.Upload(
                    id='profile-image-upload',
                    children=html.Div([
                        html.I(className="fas fa-cloud-upload-alt",
                               style={'margin-right': '8px'}),
                        'Click or drag to upload new profile picture'
                    ]),
                    className='upload-area',
                    multiple=False,
                    accept='image/*'
                ),
                html.Div([
                    html.Button(
                        "Remove Profile Picture",
                        id="delete-profile-image-button",
                        className='btn-danger'
                    )
                ], style={'text-align': 'center', 'margin-bottom': '15px'}),
                html.Div(id='profile-image-feedback'),

                # Display Name Section
                html.H3("Display Name", style={'margin-top': '20px'}),
                dcc.Input(
                    id='edit-display-name-input',
                    type='text',
                    placeholder='Enter display name',
                    className='form-input',
                    style={'width': '100%', 'margin-bottom': '10px'}
                ),
                html.Div([
                    html.Button(
                        "Update",
                        id="update-display-name-button",
                        className='btn-primary',
                        style={'width': '48%', 'margin-right': '4%'}
                    ),
                    html.Button(
                        "Remove",
                        id="remove-display-name-button",
                        className='btn-danger',
                        style={'width': '48%'}
                    )
                ]),
                html.Div(id='display-name-feedback',
                         style={'margin-top': '10px'}),

                # Bio section
                html.H3("Bio", style={'margin-top': '30px'}),
                dcc.Textarea(
                    id='edit-bio-input',
                    placeholder='Tell others about yourself...',
                    className='form-input',
                    style={'width': '100%', 'height': '100px',
                           'margin-bottom': '10px', 'resize': 'vertical'}
                ),
                html.Button(
                    "Update",
                    id="update-bio-button",
                    className='btn-primary',
                    style={'width': '200px'}
                ),
                html.Div(id='bio-feedback', style={'margin-top': '10px'})
            ], className='card settings-card'),

            # Account Settings Card
            html.Div([
                html.H2("Account Settings", id="account-settings", style={
                        'margin-bottom': '20px', 'font-size': '24px', 'font-weight': '500'}),
                html.Div([
                    # Username editing (left column)
                    html.Div([
                        html.H3("Username"),
                        html.Div([
                            dcc.Input(
                                id='edit-username-input',
                                type='text',
                                placeholder='Enter new username',
                                className='form-input',
                                style={'width': '100%',
                                       'margin-bottom': '10px'}
                            ),
                            html.Button(
                                "Update Username",
                                id="update-username-button",
                                className='btn-primary',
                                style={'width': '100%', 'margin-bottom': '5px'}
                            )
                        ]),
                        html.Div(id='username-feedback',
                                 style={'margin-bottom': '0px'}),

                        # Email editing (same column, below username)
                        html.H3("Email"),
                        html.Div([
                            dcc.Input(
                                id='edit-email-input',
                                type='email',
                                placeholder='Enter new email',
                                className='form-input',
                                style={'width': '100%',
                                       'margin-bottom': '10px'}
                            ),
                            html.Button(
                                "Update Email",
                                id="update-email-button",
                                className='btn-primary',
                                style={'width': '100%'}
                            )
                        ]),
                        html.Div(id='email-feedback')
                    ], className='column'),

                    # Password editing (right column)
                    html.Div([
                        html.H3("Password"),
                        html.Div([
                            dcc.Input(
                                id='current-password-input',
                                type='password',
                                placeholder='Current password',
                                className='form-input',
                                style={'width': '100%',
                                       'margin-bottom': '25px'}
                            ),
                            dcc.Input(
                                id='new-password-input',
                                type='password',
                                placeholder='New password',
                                className='form-input',
                                style={'width': '100%', 'margin-bottom': '8px'}
                            ),
                            dcc.Input(
                                id='confirm-password-input',
                                type='password',
                                placeholder='Confirm new password',
                                className='form-input',
                                style={'width': '100%',
                                       'margin-bottom': '10px'}
                            ),
                            html.Button(
                                "Update Password",
                                id="update-password-button",
                                className='btn-primary',
                                style={'width': '100%'}
                            )
                        ]),
                        html.Div(id='password-feedback')
                    ], className='column'),
                ], className='two-column-container')
            ], className='card settings-card'),

            # Account Actions section
            html.Div([
                html.H2("Account Actions", id="account-actions", style={
                        'margin-bottom': '20px', 'font-size': '24px', 'font-weight': '500'}),
                html.Div([
                    html.Button(
                        "Log Out",
                        id="logout-button",
                        className="btn-primary",
                        style={'margin-right': '15px'}
                    ),
                    html.Button(
                        "Delete My Account",
                        id="delete-account-button",
                        className="btn-danger",
                        disabled=True
                    )
                ], style={'text-align': 'center', 'margin-bottom': '20px'}),

                # Delete confirmation checkbox
                html.Div([
                    dcc.Checklist(
                        id="delete-confirmation",
                        options=[
                            {'label': ' I understand that deleting my account cannot be undone',
                                'value': 'confirmed'}
                        ],
                        value=[],
                        style={'margin-bottom': '15px'}
                    ),
                    html.Div(id='settings-feedback')
                ], style={'text-align': 'center'})
            ], className='card settings-card')
        ], className="settings-content", style={'flex': '1', 'max-width': '800px'})
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'flex-start', 'max-width': '1200px', 'margin': '0 auto', 'padding': '20px'})
], className="settings-page")


# Callback to enable/disable delete account button based on confirmation checkbox
@callback(
    Output('delete-account-button', 'disabled'),
    Input('delete-confirmation', 'value'),
    prevent_initial_call=False
)
def toggle_delete_button(confirmation_value):
    # Enable button only if checkbox is checked
    return 'confirmed' not in (confirmation_value or [])


@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Output('user-session', 'data', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update

    # Clear session and redirect to home page
    return '/', {
        "logged_in": False,
        "username": None,
        "user_id": None,
        "email": None,
        "profile_image_url": None,
        "created_at": None
    }


# Callback to handle account deletion
@callback(
    Output('settings-feedback', 'children'),
    Output('url', 'pathname', allow_duplicate=True),
    Output('user-session', 'data', allow_duplicate=True),
    Input('delete-account-button', 'n_clicks'),
    State('user-session', 'data'),
    State('delete-confirmation', 'value'),
    prevent_initial_call=True
)
def handle_delete_account(n_clicks, session_data, confirmation):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    # Check if user is logged in
    if not session_data or not session_data.get('logged_in') or not session_data.get('user_id'):
        return html.Div("Error: You must be logged in to delete your account.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    # Check confirmation
    if 'confirmed' not in (confirmation or []):
        return html.Div("Please confirm that you understand this action cannot be undone.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    # Delete the user account
    user_id = session_data['user_id']
    success, message = settings_backend.delete_user_account(user_id)

    if success:
        # Account deleted successfully - clear session and redirect to home
        return dash.no_update, '/', {
            "logged_in": False,
            "username": None,
            "user_id": None,
            "email": None,
            "profile_image_url": None,
            "created_at": None
        }
    else:
        # Show error message
        return html.Div(f"Error deleting account: {message}",
                        style={'color': 'red'}), dash.no_update, dash.no_update


# Callback to load current profile picture
@callback(
    Output('current-profile-image', 'src'),
    [Input('user-session', 'data'), Input('url', 'pathname')],
    prevent_initial_call=False
)
def load_current_profile_image(session_data, pathname):
    # Only load if we're on the settings page
    if pathname != '/profile/settings':
        return dash.no_update

    if not session_data or not session_data.get('logged_in') or not session_data.get('user_id'):
        # Default profile image if not logged in
        return '/assets/svg/default-profile.svg'

    # Use profile image from session data first
    profile_image_url = session_data.get('profile_image_url')
    if profile_image_url and profile_image_url.strip():
        return profile_image_url
    else:
        # Return default profile image if no custom image in session
        return '/assets/svg/default-profile.svg'


# Callback to handle profile image upload
@callback(
    Output('profile-image-feedback', 'children'),
    Output('current-profile-image', 'src', allow_duplicate=True),
    Output('user-session', 'data', allow_duplicate=True),
    Input('profile-image-upload', 'contents'),
    State('profile-image-upload', 'filename'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_profile_image_upload(contents, filename, session_data):
    if not contents:
        return dash.no_update, dash.no_update, dash.no_update

    # Check if user is logged in
    if not session_data or not session_data.get('logged_in') or not session_data.get('user_id'):
        return html.Div("Error: You must be logged in to upload a profile picture.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    try:
        # Decode the uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Check file size (limit to 5MB)
        if len(decoded) > 5 * 1024 * 1024:
            return html.Div("Error: File size must be less than 5MB.",
                            style={'color': 'red'}), dash.no_update, dash.no_update

        # Check file type
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            return html.Div("Error: Please upload a valid image file (PNG, JPG, JPEG, GIF, WebP).",
                            style={'color': 'red'}), dash.no_update, dash.no_update

        user_id = session_data['user_id']
        success, message, image_url = settings_backend.upload_profile_image(
            user_id, decoded, filename)

        if success:
            # Update session data with new profile image URL
            updated_session = session_data.copy()
            updated_session['profile_image_url'] = image_url

            return html.Div("Profile picture updated successfully!",
                            style={'color': 'green'}), image_url, updated_session
        else:
            return html.Div(f"Error uploading image: {message}",
                            style={'color': 'red'}), dash.no_update, dash.no_update

    except Exception as e:
        return html.Div(f"Error processing image: {str(e)}",
                        style={'color': 'red'}), dash.no_update, dash.no_update


# Callback to handle profile image deletion
@callback(
    Output('profile-image-feedback', 'children', allow_duplicate=True),
    Output('current-profile-image', 'src', allow_duplicate=True),
    Output('user-session', 'data', allow_duplicate=True),
    Input('delete-profile-image-button', 'n_clicks'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_profile_image_deletion(n_clicks, session_data):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    # Check if user is logged in
    if not session_data or not session_data.get('logged_in') or not session_data.get('user_id'):
        return html.Div("Error: You must be logged in to delete your profile picture.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    user_id = session_data['user_id']
    success, message = settings_backend.delete_profile_image(user_id)

    if success:
        # Update session data to remove profile image URL
        updated_session = session_data.copy()
        updated_session['profile_image_url'] = None

        return html.Div("Profile picture removed successfully!",
                        style={'color': 'green'}), '/assets/svg/default-profile.svg', updated_session
    else:
        return html.Div(f"Error removing profile picture: {message}",
                        style={'color': 'red'}), dash.no_update, dash.no_update


# Callback to handle username updates
@callback(
    Output('username-feedback', 'children'),
    Output('user-session', 'data', allow_duplicate=True),
    Output('edit-username-input', 'value'),
    Input('update-username-button', 'n_clicks'),
    State('edit-username-input', 'value'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_username_update(n_clicks, new_username, session_data):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    # Check if user is logged in
    if not session_data or not session_data.get('logged_in') or not session_data.get('user_id'):
        return html.Div("Error: You must be logged in to update your username.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    if not new_username or not new_username.strip():
        return html.Div("Error: Username cannot be empty.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    new_username = new_username.strip()
    user_id = session_data['user_id']

    # Check if username is the same as current
    if new_username == session_data.get('username'):
        return html.Div("Username is already set to this value.",
                        style={'color': 'orange'}), dash.no_update, ""

    success, message = settings_backend.update_username(user_id, new_username)

    if success:
        # Update session data with new username
        updated_session = session_data.copy()
        updated_session['username'] = new_username

        return html.Div("Username updated successfully!",
                        style={'color': 'green'}), updated_session, ""
    else:
        return html.Div(f"Error: {message}",
                        style={'color': 'red'}), dash.no_update, dash.no_update


# Callback to handle password updates
@callback(
    Output('password-feedback', 'children'),
    Output('current-password-input', 'value'),
    Output('new-password-input', 'value'),
    Output('confirm-password-input', 'value'),
    Input('update-password-button', 'n_clicks'),
    State('current-password-input', 'value'),
    State('new-password-input', 'value'),
    State('confirm-password-input', 'value'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_password_update(n_clicks, current_password, new_password, confirm_password, session_data):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Check if user is logged in
    if not session_data or not session_data.get('logged_in') or not session_data.get('user_id'):
        return html.Div("Error: You must be logged in to update your password.",
                        style={'color': 'red'}), dash.no_update, dash.no_update, dash.no_update

    # Validate inputs
    if not current_password or not new_password or not confirm_password:
        return html.Div("Error: All password fields are required.",
                        style={'color': 'red'}), dash.no_update, dash.no_update, dash.no_update

    if new_password != confirm_password:
        return html.Div("Error: New passwords do not match.",
                        style={'color': 'red'}), dash.no_update, dash.no_update, dash.no_update

    if len(new_password) < 4:
        return html.Div("Error: Password must be at least 4 characters long.",
                        style={'color': 'red'}), dash.no_update, dash.no_update, dash.no_update

    # Check if new password is the same as current password
    if new_password == current_password:
        return html.Div("Error: New password must be different from current password.",
                        style={'color': 'red'}), dash.no_update, dash.no_update, dash.no_update

    user_id = session_data['user_id']
    success, message = settings_backend.update_password(
        user_id, current_password, new_password)

    if success:
        return html.Div("Password updated successfully!",
                        style={'color': 'green'}), "", "", ""
    else:
        return html.Div(f"Error: {message}",
                        style={'color': 'red'}), dash.no_update, dash.no_update, dash.no_update


# Callback to load current username in input placeholder
@callback(
    Output('edit-username-input', 'placeholder'),
    Input('user-session', 'data'),
    prevent_initial_call=False
)
def update_username_placeholder(session_data):
    if session_data and session_data.get('logged_in') and session_data.get('username'):
        return f"Current: {session_data['username']}"
    return "Enter new username"


# Callback to handle email updates
@callback(
    Output('email-feedback', 'children'),
    Output('user-session', 'data', allow_duplicate=True),
    Output('edit-email-input', 'value'),
    Input('update-email-button', 'n_clicks'),
    State('edit-email-input', 'value'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_email_update(n_clicks, new_email, session_data):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    # Check if user is logged in
    if not session_data or not session_data.get('logged_in') or not session_data.get('user_id'):
        return html.Div("Error: You must be logged in to update your email.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    if not new_email or not new_email.strip():
        return html.Div("Error: Email cannot be empty.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    new_email = new_email.strip().lower()
    user_id = session_data['user_id']

    # Check if email is the same as current
    if new_email == session_data.get('email'):
        return html.Div("Email is already set to this value.",
                        style={'color': 'orange'}), dash.no_update, ""

    # Basic email validation
    if '@' not in new_email or '.' not in new_email.split('@')[1]:
        return html.Div("Error: Please enter a valid email address.",
                        style={'color': 'red'}), dash.no_update, dash.no_update

    success, message = settings_backend.update_email(user_id, new_email)

    if success:
        # Update session data with new email
        updated_session = session_data.copy()
        updated_session['email'] = new_email

        return html.Div("Email updated successfully!",
                        style={'color': 'green'}), updated_session, ""
    else:
        return html.Div(f"Error: {message}",
                        style={'color': 'red'}), dash.no_update, dash.no_update


# Callback to load current email in input placeholder
@callback(
    Output('edit-email-input', 'placeholder'),
    Input('user-session', 'data'),
    prevent_initial_call=False
)
def update_email_placeholder(session_data):
    if session_data and session_data.get('logged_in') and session_data.get('email'):
        return f"Current: {session_data['email']}"
    return "Enter new email"


# Callback to update display name
@callback(
    [Output('display-name-feedback', 'children'),
     Output('edit-display-name-input', 'value')],
    [Input('update-display-name-button', 'n_clicks'),
     Input('remove-display-name-button', 'n_clicks')],
    [State('edit-display-name-input', 'value'),
     State('user-session', 'data')],
    prevent_initial_call=True
)
def handle_display_name_actions(update_clicks, remove_clicks, new_display_name, session_data):
    if not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        import backend.profile as profile_backend

        if button_id == 'update-display-name-button':
            if not update_clicks:
                return dash.no_update, dash.no_update

            if not new_display_name or not new_display_name.strip():
                return html.Div("Display name cannot be empty", style={'color': 'red'}), dash.no_update

            result = profile_backend.update_user_profile(
                user_id=str(session_data['user_id']),
                display_name=new_display_name.strip()
            )

            if result.get('success'):
                return html.Div("Display name updated successfully!", style={'color': 'green'}), ""
            else:
                error_msg = result.get(
                    'error', result.get('message', 'Unknown error'))
                return html.Div(f"Error updating display name: {error_msg}", style={'color': 'red'}), dash.no_update

        elif button_id == 'remove-display-name-button':
            if not remove_clicks:
                return dash.no_update, dash.no_update

            # Set display name to empty string to remove it
            result = profile_backend.update_user_profile(
                user_id=str(session_data['user_id']),
                display_name=""
            )

            if result.get('success'):
                return html.Div("Display name removed successfully!", style={'color': 'green'}), ""
            else:
                error_msg = result.get(
                    'error', result.get('message', 'Unknown error'))
                return html.Div(f"Error removing display name: {error_msg}", style={'color': 'red'}), dash.no_update

    except Exception as e:
        return html.Div(f"Error updating display name: {str(e)}", style={'color': 'red'}), dash.no_update

    return dash.no_update, dash.no_update


# Callback to update bio
@callback(
    [Output('bio-feedback', 'children'),
     Output('edit-bio-input', 'value')],
    Input('update-bio-button', 'n_clicks'),
    [State('edit-bio-input', 'value'),
     State('user-session', 'data')],
    prevent_initial_call=True
)
def update_bio(n_clicks, new_bio, session_data):
    if not n_clicks or not session_data or not session_data.get('logged_in'):
        return dash.no_update, dash.no_update

    try:
        import backend.profile as profile_backend
        result = profile_backend.update_user_profile(
            user_id=str(session_data['user_id']),
            bio=new_bio.strip() if new_bio else ""
        )

        if result.get('success'):
            return html.Div("Bio updated successfully!", style={'color': 'green'}), ""
        else:
            return html.Div(f"Error: {result.get('message', 'Unknown error')}", style={'color': 'red'}), dash.no_update

    except Exception as e:
        return html.Div(f"Error updating bio: {str(e)}", style={'color': 'red'}), dash.no_update


# Callback to load current display name and bio
@callback(
    [Output('edit-display-name-input', 'placeholder'),
     Output('edit-bio-input', 'placeholder')],
    Input('user-session', 'data'),
    prevent_initial_call=False
)
def update_profile_placeholders(session_data):
    if not session_data or not session_data.get('logged_in'):
        return "Enter display name", "Tell others about yourself..."

    try:
        import backend.profile as profile_backend
        user_data = profile_backend.get_user_profile_by_username(
            session_data.get('username'))

        if user_data:
            display_name_placeholder = f"Current: {user_data.get('display_name', 'Not set')}"
            bio_placeholder = f"Current: {user_data.get('bio', 'No bio set')}" if user_data.get(
                'bio') else "Tell others about yourself..."
            return display_name_placeholder, bio_placeholder
        else:
            return "Enter display name", "Tell others about yourself..."

    except Exception as e:
        return "Enter display name", "Tell others about yourself..."

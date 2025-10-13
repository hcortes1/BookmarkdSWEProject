import dash
from dash import html, dcc, Input, Output, State, callback
import backend.settings as settings_backend
import base64

dash.register_page(__name__, path='/profile/settings')

layout = html.Div([
    html.Div([
        html.H1("Settings", className="main-title"),

        # Account section
        html.Div([
            html.H2("Account Management", style={'margin-bottom': '20px'}),

            # Profile Picture section
            html.Div([
                html.H3("Profile Picture", style={'margin-bottom': '15px'}),

                # Current profile picture display
                html.Div([
                    html.Img(
                        id="current-profile-image",
                        src="/assets/default-profile.svg",  # Set default source
                        style={
                            'width': '120px',
                            'height': '120px',
                            'border-radius': '50%',
                            'object-fit': 'cover',
                            'border': '3px solid #ddd',
                            'margin': '0 auto 15px auto',
                            'display': 'block',
                            'background-color': '#f8f9fa',
                            'box-shadow': '0 2px 8px rgba(0,0,0,0.1)',
                            'max-width': '120px',
                            'max-height': '120px'
                        }
                    )
                ], style={'text-align': 'center', 'margin-bottom': '20px'}),

                # Upload new profile picture
                html.Div([
                    dcc.Upload(
                        id='profile-image-upload',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt",
                                   style={'margin-right': '8px'}),
                            'Upload New Profile Picture'
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '8px',
                            'textAlign': 'center',
                            'margin': '10px 0',
                            'cursor': 'pointer',
                            'background-color': '#fafafa'
                        },
                        multiple=False,
                        accept='image/*'
                    ),

                    # Delete profile picture button
                    html.Button(
                        "Remove Profile Picture",
                        id="delete-profile-image-button",
                        style={
                            'background-color': '#6c757d',
                            'color': 'white',
                            'border': 'none',
                            'padding': '8px 16px',
                            'margin': '10px 0',
                            'border-radius': '5px',
                            'cursor': 'pointer'
                        }
                    ),

                    # Profile picture feedback
                    html.Div(id='profile-image-feedback',
                             style={'margin-top': '10px'})
                ])
            ], style={
                'border': '1px solid #ddd',
                'border-radius': '8px',
                'padding': '20px',
                'margin-bottom': '30px',
                'background-color': '#f9f9f9'
            }),

            # Logout button
            html.Div([
                html.Button(
                    "Log Out",
                    id="logout-button",
                    className="settings-button logout-button",
                    style={
                        'background-color': '#007bff',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'margin': '10px 10px 10px 0',
                        'border-radius': '5px',
                        'cursor': 'pointer'
                    }
                ),
            ], style={'margin-bottom': '30px'}),

            # Delete account section
            html.Div([
                html.H3("Danger Zone", style={
                        'color': '#dc3545', 'margin-bottom': '15px'}),
                html.P("Once you delete your account, there is no going back. Please be certain.",
                       style={'margin-bottom': '15px', 'color': '#666'}),

                # Delete confirmation checkbox
                dcc.Checklist(
                    id="delete-confirmation",
                    options=[
                        {'label': ' I understand that this action cannot be undone',
                            'value': 'confirmed'}
                    ],
                    value=[],
                    style={'margin-bottom': '15px'}
                ),

                # Delete account button
                html.Button(
                    "Delete My Account",
                    id="delete-account-button",
                    className="settings-button delete-button",
                    disabled=True,
                    style={
                        'background-color': '#dc3545',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'margin': '10px 0',
                        'border-radius': '5px',
                        'cursor': 'pointer'
                    }
                ),

                # Feedback messages
                html.Div(id='settings-feedback', style={'margin-top': '15px'})
            ], style={
                'border': '1px solid #dc3545',
                'border-radius': '5px',
                'padding': '20px',
                'background-color': '#fff5f5'
            })

        ], style={'max-width': '600px'})

    ], className="app-container")
])


# Callback to enable/disable delete button based on confirmation
@callback(
    Output('delete-account-button', 'disabled'),
    Input('delete-confirmation', 'value')
)
def toggle_delete_button(confirmation):
    return 'confirmed' not in (confirmation or [])


# Callback to handle logout
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
        return '/assets/default-profile.svg'

    # Use profile image from session data first
    profile_image_url = session_data.get('profile_image_url')
    if profile_image_url and profile_image_url.strip():
        return profile_image_url
    else:
        # Return default profile image if no custom image in session
        return '/assets/default-profile.svg'


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
                        style={'color': 'green'}), '/assets/default-profile.svg', updated_session
    else:
        return html.Div(f"Error removing profile picture: {message}",
                        style={'color': 'red'}), dash.no_update, dash.no_update

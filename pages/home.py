import dash
from dash import html, dcc, Input, Output, State
from backend.gemini_helper import get_book_recommendation_chat

dash.register_page(__name__, path='/')


def welcome_layout():
    """Layout for non-logged-in users"""
    return html.Div([
        html.Div([
            html.H1("Welcome to Bookmarkd", className="welcome-title"),
            html.P("Discover, track, and share your favorite books with friends.",
                   className="welcome-subtitle"),

            html.Div([
                dcc.Link(
                    html.Button("Log In", className="welcome-login-btn"),
                    href='/login'
                ),
                dcc.Link(
                    html.Button("Sign Up", className="welcome-signup-btn"),
                    href='/login?mode=signup'
                )
            ], className="welcome-buttons")
        ], className="welcome-container")
    ], className="welcome-page")


def homefeed_layout():
    """Layout for logged-in users"""
    return html.Div([
        # EXISTING CONTENT - DON'T TOUCH
        html.Div([
            html.H1("Home Feed", className="main-title"),
            html.P("Your personalized book recommendations and activity feed will appear here.",
                   className="homefeed-subtitle")
        ], className="app-container"),
        
        # NEW: Floating Chat Widget (ADD THIS SECTION)
        html.Div([
            # Chat toggle button (bottom right corner)
            html.Button(
                "💬",
                id='chat-toggle-btn',
                style={
                    'position': 'fixed',
                    'bottom': '20px',
                    'right': '20px',
                    'width': '60px',
                    'height': '60px',
                    'borderRadius': '50%',
                    'backgroundColor': '#007bff',
                    'color': 'white',
                    'border': 'none',
                    'fontSize': '24px',
                    'cursor': 'pointer',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.3)',
                    'zIndex': '1000'
                }
            ),
            
            # Chat window (hidden by default)
            html.Div([
                # Chat header
                html.Div([
                    html.Span("📚 Book Assistant", style={'fontWeight': 'bold', 'fontSize': '16px'}),
                    html.Button('×', id='chat-close-btn', style={
                        'background': 'none',
                        'border': 'none',
                        'fontSize': '24px',
                        'cursor': 'pointer',
                        'color': 'white'
                    })
                ], style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center',
                    'padding': '15px',
                    'borderBottom': '1px solid #ddd',
                    'backgroundColor': '#007bff',
                    'color': 'white',
                    'borderRadius': '12px 12px 0 0'
                }),
                
                # Chat messages display
                html.Div(
                    id='home-chat-display',
                    children=[
                        html.P("Hi! I'm your book assistant. Ask me for recommendations or questions about books!", 
                               style={'color': '#666', 'fontStyle': 'italic', 'fontSize': '14px'})
                    ],
                    style={
                        'height': '350px',
                        'overflowY': 'auto',
                        'padding': '15px',
                        'backgroundColor': '#f9f9f9'
                    }
                ),
                
                # Chat input area
                html.Div([
                    dcc.Input(
                        id='home-chat-input',
                        type='text',
                        placeholder='Ask me anything about books...',
                        style={
                            'flex': '1',
                            'padding': '10px',
                            'border': '1px solid #ddd',
                            'borderRadius': '20px',
                            'marginRight': '10px',
                            'outline': 'none'
                        }
                    ),
                    html.Button('Send', id='home-chat-send-btn', style={
                        'padding': '10px 20px',
                        'backgroundColor': '#007bff',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '20px',
                        'cursor': 'pointer'
                    })
                ], style={
                    'display': 'flex',
                    'padding': '15px',
                    'borderTop': '1px solid #ddd',
                    'backgroundColor': 'white'
                })
            ], id='home-chat-window', style={
                'display': 'none',
                'position': 'fixed',
                'bottom': '90px',
                'right': '20px',
                'width': '350px',
                'backgroundColor': 'white',
                'borderRadius': '12px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                'zIndex': '999'
            }),
            
            # Store for chat history
            dcc.Store(id='home-chat-history', data=[])
        ])
    ])


def layout():
    return html.Div([
        # Store for checking login status
        dcc.Store(id='home-session-check', data={}),

        # Content will be dynamically loaded based on login status
        html.Div(id='home-content')
    ])


# Callback to check login status and show appropriate content
@dash.callback(
    Output('home-content', 'children'),
    Input('home-session-check', 'data'),
    Input('user-session', 'data')
)
def update_home_content(dummy, user_session):
    is_logged_in = user_session.get(
        'logged_in', False) if user_session else False

    if is_logged_in:
        return homefeed_layout()
    else:
        return welcome_layout()
# Callback 1: Toggle chat window open/close
@dash.callback(
    Output('home-chat-window', 'style'),
    Input('chat-toggle-btn', 'n_clicks'),
    Input('chat-close-btn', 'n_clicks'),
    State('home-chat-window', 'style'),
    prevent_initial_call=True
)
def toggle_chat_window(toggle_clicks, close_clicks, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Copy current style
    new_style = current_style.copy()
    
    if button_id == 'chat-toggle-btn':
        # Toggle visibility
        new_style['display'] = 'none' if current_style.get('display') == 'block' else 'block'
    elif button_id == 'chat-close-btn':
        # Close chat
        new_style['display'] = 'none'
    
    return new_style


# Callback 2: Handle chat messages
@dash.callback(
    Output('home-chat-display', 'children'),
    Output('home-chat-input', 'value'),
    Output('home-chat-history', 'data'),
    Input('home-chat-send-btn', 'n_clicks'),
    State('home-chat-input', 'value'),
    State('home-chat-display', 'children'),
    State('home-chat-history', 'data'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_home_chat(n_clicks, user_input, current_display, chat_history, user_session):
    if not n_clicks or not user_input or not user_input.strip():
        return dash.no_update, dash.no_update, dash.no_update
    
    # Get user's favorite genres from session
    user_genres = user_session.get('favorite_genres', []) if user_session else []
    
    # Call Gemini API
    success, response_text = get_book_recommendation_chat(user_input, user_genres, chat_history)
    
    # Handle error
    if not success:
        error_msg = html.Div(
            f"Error: {response_text}",
            style={'color': 'red', 'padding': '10px', 'fontSize': '14px'}
        )
        updated_display = current_display + [error_msg]
        return updated_display, '', dash.no_update
    
    # Create user message
    user_message_div = html.Div(
        user_input,
        style={
            'backgroundColor': '#007bff',
            'color': 'white',
            'padding': '10px 15px',
            'borderRadius': '15px',
            'margin': '10px 0',
            'maxWidth': '70%',
            'marginLeft': 'auto',
            'fontSize': '14px',
            'wordWrap': 'break-word'
        }
    )
    
    # Create AI response
    ai_message_div = html.Div(
        response_text,
        style={
            'backgroundColor': '#f0f0f0',
            'padding': '10px 15px',
            'borderRadius': '15px',
            'margin': '10px 0',
            'maxWidth': '70%',
            'fontSize': '14px',
            'wordWrap': 'break-word'
        }
    )
    
    # Update display
    updated_display = current_display + [user_message_div, ai_message_div]
    
    # Update chat history
    if chat_history is None:
        chat_history = []
    updated_history = chat_history + [
        {"role": "user", "message": user_input},
        {"role": "ai", "message": response_text}
    ]
    
    return updated_display, '', updated_history
import dash
from dash import dcc, html, Input, Output, State, callback
import backend.login as login_backend
from backend.gemini_helper import get_genre_recommendation

dash.register_page(__name__, path='/genre-selection')

# The 10 popular genres
GENRES = [
    "Mystery",
    "Thriller/Suspense", 
    "Romance",
    "Science Fiction",
    "Fantasy",
    "Horror",
    "Historical Fiction",
    "Biography/Memoir",
    "Self-Help",
    "History"
]

layout = html.Div([
    # Store for chat history
    dcc.Store(id='genre-chat-history', data=[]),
    
    html.Div([
        # Header Section
        html.H1("What do you like to read?", className="login-title"),
        html.P("Select your favorite genres or chat with our AI for personalized recommendations!", 
               style={'textAlign': 'center', 'marginBottom': '30px', 'color': '#666'}),
        
        # Checkbox Section
html.Div([
    html.H3("Popular Genres", style={'marginBottom': '15px'}),
    html.Div([
        dcc.Checklist(
            id='genre-checklist',
            options=[{'label': genre, 'value': genre} for genre in GENRES],
            value=[],  # Nothing selected by default
            inline=False,
            labelStyle={
                'display': 'block',
                'marginBottom': '10px',
                'cursor': 'pointer'
            },
            style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(2, 1fr)',
                'gap': '15px',
                'padding': '20px'
            }
        )
    ]),
], style={'marginBottom': '30px'}),
        
       # Gemini Chat Section
html.Div([
    html.H3("Not sure? Ask our AI!", style={'marginBottom': '15px'}),
    
    # Chat display area (scrollable)
    html.Div(
        id='genre-chat-display',
        children=[
            html.P("Hi! I'm here to help you discover books you'll love. Tell me about books you've enjoyed, or ask me for recommendations!", 
                   style={'color': '#666', 'fontStyle': 'italic'})
        ],
        style={
            'border': '1px solid #ddd',
            'borderRadius': '8px',
            'padding': '15px',
            'height': '300px',
            'overflowY': 'scroll',
            'backgroundColor': '#f9f9f9',
            'marginBottom': '15px'
        }
    ),
    
    # Input area
    html.Div([
        dcc.Input(
            id='genre-chat-input',
            type='text',
            placeholder='Ask me anything about books or genres...',
            className='login-input',
            style={'flex': '1', 'marginRight': '10px'}
        ),
        html.Button('Send', id='genre-chat-send-btn', className='login-button',
                   style={'width': 'auto', 'padding': '0 20px'})
    ], style={'display': 'flex', 'alignItems': 'center'}),
    
], style={'marginBottom': '30px'}),
        # Action Buttons
        html.Div([
            html.Button("Skip for now", id="genre-skip-btn", className="login-button", 
                       style={'backgroundColor': '#gray', 'marginRight': '10px'}),
            html.Button("Save preferences", id="genre-save-btn", className="login-button"),
        ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '10px'}),
        
    ], className='login-box')
], className='login-page')

# Callback 1: Handle chat send button
@callback(
    Output('genre-chat-display', 'children'),
    Output('genre-chat-input', 'value'),
    Output('genre-checklist', 'value'),
    Output('genre-chat-history', 'data'),
    Input('genre-chat-send-btn', 'n_clicks'),
    State('genre-chat-input', 'value'),
    State('genre-chat-display', 'children'),
    State('genre-checklist', 'value'),
    State('genre-chat-history', 'data'),
    prevent_initial_call=True
)
def handle_chat_send(n_clicks, user_input, current_display, current_selections, chat_history):
    """
    When user sends a message:
    1. Call Gemini API with the message
    2. Add user message and AI response to chat display
    3. Auto-check any genres Gemini suggests
    4. Clear the input box
    """
    
    # Check if button was clicked and input has text
    if not n_clicks or not user_input or not user_input.strip():
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Call Gemini API
    success, response_text, suggested_genres = get_genre_recommendation(user_input, chat_history)
    
    # If error, show error message
    if not success:
        error_msg = html.Div(
            f"Error: {response_text}",
            style={'color': 'red', 'padding': '10px', 'marginTop': '10px'}
        )
        updated_display = current_display + [error_msg]
        return updated_display, '', dash.no_update, dash.no_update
    
   
    
    user_message_div = html.Div(
        user_input,
        style={
        'backgroundColor': '#ADD8E6',  
        'padding': '10px 15px', 
        'borderRadius': '15px', 
        'margin': '10px 0', 
        'maxWidth': '70%',  
        'marginLeft': 'auto', 
        'textAlign': 'right'  
        }
    )

    ai_message_div = html.Div(
        response_text,
        style={
        'backgroundColor': '#f0f0f0', 
        'padding': '10px 15px',
        'borderRadius': '15px',
        'margin': '10px 0',
        'maxWidth': '70%',
        'textAlign': 'left'  
        }  
    )
    updated_display = current_display + [user_message_div, ai_message_div]

    if current_selections is None:
        current_selections = []
    updated_selections = list(set(current_selections + suggested_genres))

    if chat_history is None:
        chat_history = []
    updated_history = chat_history + [
    {"role": "user", "message": user_input},
    {"role": "ai", "message": response_text}
]
    return updated_display, '', updated_selections, updated_history
    

# Callback 2: Handle skip button
@callback(
    Output('url', 'pathname'),
    Input('genre-skip-btn', 'n_clicks'),
    prevent_initial_call=True
)
def handle_skip(n_clicks):
    """
    When user clicks skip:
    1. Redirect to home page without saving anything
    """
    
    if not n_clicks:
        return dash.no_update
    return '/'

# Callback 3: Handle save button
@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Output('user-session', 'data'),
    Input('genre-save-btn', 'n_clicks'),
    State('genre-checklist', 'value'),
    State('user-session', 'data'),
    prevent_initial_call=True
)
def handle_save(n_clicks, selected_genres, user_session):
    """
    When user clicks save:
    1. Get selected genres from checklist
    2. Call backend to save to database
    3. Update user session to mark first_login as false
    4. Redirect to home page
    """
    
    if not n_clicks:
        return dash.no_update, dash.no_update
    
    # Check if user is logged in
    if not user_session or not user_session.get('logged_in'):
        return '/login', dash.no_update
    
    # import backend.login as login_backend
    success, message = login_backend.update_user_genres(user_session['user_id'], selected_genres or [])
    
    if success: 
        # update session data to set first login to False
        updated_session = user_session.copy()
        updated_session['first_login'] = False
        # redirect to home with updated session
        return '/', updated_session
    
    else:
    # If save failed, stay on page
        return dash.no_update, dash.no_update

    
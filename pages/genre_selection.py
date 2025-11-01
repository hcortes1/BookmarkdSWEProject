import dash
from dash import dcc, html, Input, Output, State, callback

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
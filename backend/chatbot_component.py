from dash import html, dcc

"""
Reusable chatbot component for book recommendations and assistance.
Can be imported into any page to add the floating chat interface.
"""

def create_chatbot_component(page_id):
    """
    Create a chatbot component with unique IDs for a specific page.
    
    Args:
        page_id: Unique identifier for the page (e.g., 'home', 'trending', 'bookshelf')
    
    Returns:
        html.Div containing the complete chatbot UI
    """
    return html.Div([
        # Floating chat button
        html.Button(
            "💬",
            id=f'{page_id}-chat-toggle-btn',
            className='chat-toggle-btn',
            style={
                'position': 'fixed',
                'bottom': '20px',
                'right': '20px',
                'width': '60px',
                'height': '60px',
                'borderRadius': '50%',
                'backgroundColor': 'var(--link-color)',
                'color': 'var(--button-text-color)',
                'border': 'none',
                'fontSize': '24px',
                'cursor': 'pointer',
                'boxShadow': '0 4px 12px rgba(0,0,0,0.3)',
                'zIndex': '3000'
            }
        ),

        # Chat window
        html.Div([
            # Chat header
            html.Div([
                html.Span("Bookmarkd Librarian", style={
                    'fontWeight': 'bold',
                    'fontSize': '16px'
                }),
                html.Button('×', id=f'{page_id}-chat-close-btn', style={
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
                'backgroundColor': 'var(--link-color)',
                'color': 'white',
                'borderRadius': '12px 12px 0 0'
            }),

            # Chat display area
            html.Div(
                id=f'{page_id}-chat-display',
                children=[
                    html.P(
                        "Hi! I'm your book assistant. Ask me for recommendations or questions about books.",
                        style={
                            'color': 'var(--text-color-secondary)',
                            'fontStyle': 'italic',
                            'fontSize': '14px'
                        }
                    )
                ],
                style={
                    'height': '350px',
                    'overflowY': 'auto',
                    'padding': '15px',
                    'backgroundColor': 'var(--secondary-bg)'
                }
            ),

            # Chat input area
            html.Div([
                dcc.Input(
                    id=f'{page_id}-chat-input',
                    type='text',
                    placeholder='Ask me anything about books...',
                    style={
                        'flex': '1',
                        'padding': '10px',
                        'border': '1px solid #ddd',
                        'borderRadius': '20px',
                        'marginRight': '10px',
                        'backgroundColor': 'var(--input-field-bg)',
                        'color': 'var(--text-color)'
                    }
                ),
                html.Button('Send', id=f'{page_id}-chat-send-btn', style={
                    'padding': '10px 20px',
                    'backgroundColor': 'var(--link-color)',
                    'color': 'var(--button-text-color)',
                    'border': 'none',
                    'borderRadius': '20px',
                    'cursor': 'pointer'
                })
            ], style={
                'display': 'flex',
                'padding': '15px',
                'borderTop': '1px solid #ddd',
                'backgroundColor': 'var(--secondary-bg)'
            })
        ], id=f'{page_id}-chat-window', style={
            'display': 'none',
            'position': 'fixed',
            'bottom': '90px',
            'right': '20px',
            'width': '350px',
            'backgroundColor': 'var(--secondary-bg)',
            'borderRadius': '12px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
            'zIndex': '2999'
        })
    ], className='chatbot-container')
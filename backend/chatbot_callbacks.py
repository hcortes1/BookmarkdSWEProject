"""
Shared callback logic for the chatbot component.
Registers callbacks for chat interactions and window toggling.
"""

import dash
from dash import Input, Output, State, html, dcc, callback
from backend.gemini_helper import get_book_recommendation_chat


def register_chatbot_callbacks(page_id):
    """
    Register callbacks for the chatbot component on a specific page.
    
    Args:
        page_id: Unique identifier for the page (e.g., 'home', 'trending', 'bookshelf')
    """
    
    # Callback to toggle chat window open
    @callback(
        Output(f"{page_id}-chat-window", "style"),
        Input(f"{page_id}-chat-toggle-btn", "n_clicks"),
        Input(f"{page_id}-chat-close-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_chat(open_click, close_click):
        """Toggle chat window visibility"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id == f"{page_id}-chat-toggle-btn":
            return {
                'display': 'block',
                'position': 'fixed',
                'bottom': '90px',
                'right': '20px',
                'width': '350px',
                'backgroundColor': 'var(--secondary-bg)',
                'borderRadius': '12px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                'zIndex': '2999'
            }
        elif button_id == f"{page_id}-chat-close-btn":
            return {'display': 'none'}
        else:
            raise dash.exceptions.PreventUpdate
    
    # Callback to handle chat messages
    @callback(
        Output(f"{page_id}-chat-display", "children"),
        Output("global-chat-history", "data", allow_duplicate=True),  # Added allow_duplicate=True
        Output(f"{page_id}-chat-input", "value"),
        Input(f"{page_id}-chat-send-btn", "n_clicks"),
        State(f"{page_id}-chat-input", "value"),
        State("global-chat-history", "data"),
        State("user-session", "data"),
        prevent_initial_call=True
    )
    def update_chat(n_clicks, user_input, history, user_session):
        """Handle chat message sending and AI response"""
        if not user_input:
            raise dash.exceptions.PreventUpdate
        
        # Get user's favorite genres from session if available
        user_genres = None
        if user_session and user_session.get('logged_in'):
            user_genres = user_session.get('favorite_genres', [])
        
        # Add user message to history
        history.append({'role': 'user', 'content': user_input})
        
        # Get AI response with user preferences
        success, ai_response = get_book_recommendation_chat(
            user_input,
            user_genres=user_genres
        )
        
        if not success:
            ai_response = "Sorry, I'm having trouble connecting right now. Please try again later."
        
        # Split AI response by newlines to create multiple message bubbles
        response_parts = [part.strip() for part in ai_response.split('\n\n') if part.strip()]
        
        # Add each part as a separate message
        for part in response_parts:
            history.append({'role': 'ai', 'content': part})
        
        # Build chat display from history
        chat_display = []
        for msg in history:
            if msg['role'] == 'user':
                chat_display.append(
                    html.Div(
                        [html.Div(msg['content'], className="chat-bubble user-bubble")]
                    )
                )
            else:
                chat_display.append(
                    html.Div(
                        [dcc.Markdown(msg['content'], className="chat-bubble ai-bubble")]
                    )
                )
        
        return chat_display, history, ""
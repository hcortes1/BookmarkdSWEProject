import dash
from dash import html, dcc, Input, Output, State
from backend.gemini_helper import get_book_recommendation_chat
import backend.home as home_backend

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
        html.Div([
            html.H1("Home Feed", className="main-title"),
            html.P("See recent reviews, your friends’ activity, and book recommendations.",
                   className="homefeed-subtitle"),
            html.Hr(className="home-divider"),

            # Recommended Books (top)
            html.Div([
                html.H2("Recommended Books", className="section-title"),
                html.Div(id="ai-recommendations-container", className="home-section-container")
            ], className="home-section"),

            # Two-column layout for Recent Reviews + Friend Activity
            html.Div([
                html.Div([
                    html.H2("Recent Reviews", className="section-title"),
                    html.Div(id="recent-reviews-container", className="home-section-container")
                ], className="home-section"),

                html.Div([
                    html.H2("Friend Activity", className="section-title"),
                    html.Div(id="friend-activity-container", className="home-section-container")
                ], className="home-section")
            ], className="home-sections-grid"),
        ], className="app-container"),

        # Floating Chat Assistant
        html.Div([
            # Chat toggle button
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
                    'backgroundColor': 'var(--link-color)',
                    'color': 'var(--button-text-color)',
                    'border': 'none',
                    'fontSize': '24px',
                    'cursor': 'pointer',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.3)',
                    'zIndex': '3000'
                }
            ),

            # Chat window (hidden by default)
            html.Div([
                html.Div([
                    html.Span("Book Assistant", style={'fontWeight': 'bold', 'fontSize': '16px'}),
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
                    'backgroundColor': 'var(--link-color)',
                    'color': 'white',
                    'borderRadius': '12px 12px 0 0'
                }),

                html.Div(
                    id='home-chat-display',
                    children=[
                        html.P("Hi! I'm your book assistant. Ask me for recommendations or questions about books.",
                               style={'color': 'var(--text-color-secondary)', 'fontStyle': 'italic', 'fontSize': '14px'})
                    ],
                    style={
                        'height': '350px',
                        'overflowY': 'auto',
                        'padding': '15px',
                        'backgroundColor': 'var(--secondary-bg)'
                    }
                ),

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
                            'backgroundColor': 'var(--input-field-bg)',
                            'color': 'var(--text-color)'
                        }
                    ),
                    html.Button('Send', id='home-chat-send-btn', style={
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
            ], id='home-chat-window', style={
                'display': 'none',
                'position': 'fixed',
                'bottom': '90px',
                'right': '20px',
                'width': '350px',
                'backgroundColor': 'var(--secondary-bg)',
                'borderRadius': '12px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                'zIndex': '2999'
            }),

            # Chat message store
            dcc.Store(id='home-chat-history', data=[])
        ])
    ])


def layout():
    return html.Div([
        dcc.Store(id='home-session-check', data={}),
        html.Div(id='home-content')
    ])


# Check login
@dash.callback(
    Output('home-content', 'children'),
    Input('home-session-check', 'data'),
    Input('user-session', 'data')
)
def update_home_content(dummy, user_session):
    is_logged_in = user_session.get('logged_in', False) if user_session else False
    return homefeed_layout() if is_logged_in else welcome_layout()


# Populate reviews and friend activity
@dash.callback(
    Output("recent-reviews-container", "children"),
    Output("friend-activity-container", "children"),
    Input("user-session", "data")
)
def load_home_data(user_session):
    if not user_session or not user_session.get("logged_in"):
        return dash.no_update, dash.no_update

    user_id = user_session.get("user_id")

    # Recent Reviews
    reviews = home_backend.get_recent_reviews(limit=10)
    if not reviews:
        recent_reviews = html.P("No recent reviews found.", className="home-empty-message")
    else:
        recent_reviews = [
            html.Div([
                html.Div([
                    dcc.Link([
                        html.Img(
                            src=r.get('profile_image_url', '/assets/svg/default-profile.svg'),
                            className="activity-avatar-small"
                        ),
                        html.Strong(r['username'], className="activity-username")
                    ], href=f"/profile/view/{r['username']}",
                        style={'textDecoration': 'none', 'color': 'inherit'}),

                    html.Span(" reviewed " if r["is_review"] else " rated ",
                              className="activity-action"),

                    dcc.Link(
                        html.Em(r["book_title"]),
                        href=f"/book/{r['book_id']}",
                        style={'textDecoration': 'none', 'color': 'var(--link-color)', 'fontWeight': '600'}
                    ),
                ], className="activity-header"),

                html.Div([
                    dcc.Link([
                        html.Img(
                            src=r.get('cover_url', '/assets/svg/default-book.svg'),
                            className="activity-book-cover"
                        )
                    ], href=f"/book/{r['book_id']}", style={'textDecoration': 'none'}),

                    html.Div([
                        html.Span(f"⭐ {r['rating']}/5", className="activity-rating"),

                        html.P(r["snippet"],
                               className="activity-snippet") if r["is_review"] else None,

                        html.Span(r["display_time"], className="activity-timestamp")
                    ], className="activity-book-info")
                ], className="activity-card-content")
            ], className="activity-card")
            for r in reviews
        ]

    # Friend Activity
    friends = home_backend.get_friend_activity(user_id)
    if not friends:
        friend_activity = html.P("No recent activity from your friends.", className="home-empty-message")
    else:
        friend_activity = [
            html.Div([
                html.Div([
                    html.Img(
                        src=f.get('cover_url', '/assets/svg/default-book.svg'),
                        className="activity-book-cover"
                    ),
                    html.Div([
                        html.Div([
                            dcc.Link(
                                html.Img(
                                    src=f.get('profile_image_url', '/assets/svg/default-profile.svg'),
                                    className="activity-avatar-small"
                                ),
                                href=f"/profile/view/{f['username']}",
                                style={'textDecoration': 'none'}
                            ),
                            dcc.Link(
                                html.Strong(f['username'], className="activity-username"),
                                href=f"/profile/view/{f['username']}",
                                style={'textDecoration': 'none', 'color': 'inherit', 'marginLeft': '8px'}
                            ),
                        ], className="activity-user-info"),
                        html.Span(f" {f['action']} ", className="activity-action"),
                        html.H4(f["book_title"], className="activity-book-title"),
                        html.Span(f["display_time"], className="activity-timestamp"),
                    ], className="activity-book-info")
                ], className="activity-card-content")
            ], className="activity-card") for f in friends
        ]

    return recent_reviews, friend_activity
# Chat Window Toggle
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
    new_style = current_style.copy()

    if button_id == 'chat-close-btn':
        new_style['display'] = 'none'
    elif button_id == 'chat-toggle-btn':
        new_style['display'] = (
            'none' if current_style.get('display') == 'block' else 'block'
        )

    return new_style


# Chat Message Handling
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

    # Get user's favorite genres for context
    user_genres = user_session.get('favorite_genres', []) if user_session else []

    # Send message to Gemini backend
    success, response_text = get_book_recommendation_chat(user_input, user_genres, chat_history)

    # Error handling
    if not success:
        error_msg = html.Div(
            f"Error: {response_text}",
            style={'color': 'var(--danger-color)', 'padding': '10px', 'fontSize': '14px'}
        )
        return current_display + [error_msg], '', chat_history

    # User message bubble
    user_message_div = html.Div(
        user_input,
        className="chat-bubble user-bubble"
    )

    # AI response bubble
    ai_message_div = html.Div(
        response_text,
        className="chat-bubble ai-bubble"
    )

    # Append both to chat
    updated_display = current_display + [user_message_div, ai_message_div]

    # Update chat history for context continuity
    updated_history = (chat_history or []) + [
        {"role": "user", "message": user_input},
        {"role": "ai", "message": response_text}
    ]

    return updated_display, '', updated_history

@dash.callback(
    Output("ai-recommendations-container", "children"),
    Input("user-session", "data")
)
def load_ai_recommendations(user_session):
    if not user_session or not user_session.get("logged_in"):
        return html.P("Log in to see AI-powered book recommendations.",
                      className="home-empty-message")

    user_genres = user_session.get("favorite_genres", [])
    if not user_genres:
        return html.P("Add some favorite genres in your profile to receive recommendations.",
                      className="home-empty-message")

    recs = home_backend.get_ai_recommendations(user_genres, limit=12)
    if not recs:
        return html.P("No recommendations available right now.",
                      className="home-empty-message")

    # --- Render recommendation cards with cover images ---
    return html.Div([
        html.Div([
            html.Div([
                dcc.Link([
                    html.Img(
                        src=r.get("cover_url", "/assets/svg/default-book.svg"),
                        className="rec-cover"
                    ),
                    html.H4(r["title"], className="rec-title"),
                    html.P(f"by {r['author']}", className="rec-author")
                ],
                    href=f"/book/{r['book_id']}" if r["book_id"] else f"/search?query={r['title']}+{r['author']}",
                    style={"textDecoration": "none", "color": "inherit"})
            ], className="rec-card")
            for r in recs
        ], className="rec-grid")
    ])
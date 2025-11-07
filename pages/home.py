import dash
from dash import html, dcc, Input, Output, State
from backend.gemini_helper import get_book_recommendation_chat
import backend.home as home_backend

dash.register_page(__name__, path='/')


def welcome_layout():
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
    return html.Div([
        html.Div([
            html.H1("Home Feed", className="main-title"),
            html.P("See recent reviews, your friends’ activity, and book recommendations.",
                   className="homefeed-subtitle"),
            html.Hr(className="home-divider"),

            html.Div([
                html.H2("Recommended Books", className="section-title"),
                html.Div(id="ai-recommendations-container", className="home-section-container")
            ], className="home-section"),

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

            dcc.Store(id='home-chat-history', data=[])
        ])
    ])


def layout():
    return html.Div([
        dcc.Store(id='home-session-check', data={}),
        html.Div(id='home-content')
    ])


@dash.callback(
    Output('home-content', 'children'),
    Input('home-session-check', 'data'),
    Input('user-session', 'data')
)
def update_home_content(dummy, user_session):
    is_logged_in = user_session.get('logged_in', False) if user_session else False
    return homefeed_layout() if is_logged_in else welcome_layout()


@dash.callback(
    Output("recent-reviews-container", "children"),
    Output("friend-activity-container", "children"),
    Input("user-session", "data")
)
def load_home_data(user_session):
    if not user_session or not user_session.get("logged_in"):
        return dash.no_update, dash.no_update

    user_id = user_session.get("user_id")

    reviews = home_backend.get_recent_reviews(limit=10)
    if not reviews:
        recent_reviews = html.P("No recent reviews found.", className="home-empty-message")
    else:
        recent_reviews = [
            html.Div([
                html.Div([
                    html.Img(
                        src=r.get('profile_image_url', '/assets/svg/default-profile.svg'),
                        className="activity-avatar-small"
                    ),
                    html.Strong(r['username'], className="activity-username"),
                    html.Span(" reviewed " if r["is_review"] else " rated ",
                              className="activity-action"),
                    html.Em(r["book_title"]),
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

    friends = home_backend.get_friend_activity(user_id)
    if not friends:
        friend_activity = html.P("No recent activity from your friends.", className="home-empty-message")
    else:
        friend_activity = [
            html.Div([
                html.Div([
                    dcc.Link([
                        html.Img(
                            src=f.get('cover_url', '/assets/svg/default-book.svg'),
                            className="activity-book-cover"
                        )
                    ], href=f"/book/{f['book_id']}", style={'textDecoration': 'none'}),
                    html.Div([
                        html.Div([
                            html.Img(
                                src=f.get('profile_image_url', '/assets/svg/default-profile.svg'),
                                className="activity-avatar-small"
                            ),
                            html.Strong(f['username'], className="activity-username"),
                        ], className="activity-user-info"),
                        html.Span(f" {f['action']} ", className="activity-action"),
                        html.H4(f["book_title"], className="activity-book-title"),
                        html.Span(f["display_time"], className="activity-timestamp"),
                    ], className="activity-book-info")
                ], className="activity-card-content")
            ], className="activity-card") for f in friends
        ]

    return recent_reviews, friend_activity


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

    recs = home_backend.get_ai_recommendations(user_genres, limit=10)
    if not recs:
        return html.P("No recommendations available right now.",
                      className="home-empty-message")

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

@dash.callback(
    Output("home-chat-window", "style"),
    Input("chat-toggle-btn", "n_clicks"),
    Input("chat-close-btn", "n_clicks"),
    prevent_initial_call=True
)
def toggle_chat(open_click, close_click):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "chat-toggle-btn":
        return {'display': 'block',
                'position': 'fixed',
                'bottom': '90px',
                'right': '20px',
                'width': '350px',
                'backgroundColor': 'var(--secondary-bg)',
                'borderRadius': '12px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                'zIndex': '2999'}
    elif button_id == "chat-close-btn":
        return {'display': 'none'}
    else:
        raise dash.exceptions.PreventUpdate


@dash.callback(
    Output("home-chat-display", "children"),
    Output("home-chat-history", "data"),
    Input("home-chat-send-btn", "n_clicks"),
    State("home-chat-input", "value"),
    State("home-chat-history", "data"),
    prevent_initial_call=True
)
def update_chat(n_clicks, user_input, history):
    if not user_input:
        raise dash.exceptions.PreventUpdate

    user_bubble = html.Div(user_input, className="chat-bubble user-bubble")
    history.append({'role': 'user', 'content': user_input})

    ai_response = get_book_recommendation_chat(user_input)
    ai_bubble = html.Div(ai_response, className="chat-bubble ai-bubble")
    history.append({'role': 'ai', 'content': ai_response})

    chat_display = [
        html.Div(
            [html.Div(msg['content'], className=f"chat-bubble {'user-bubble' if msg['role']=='user' else 'ai-bubble'}")]
        ) for msg in history
    ]

    return chat_display, history

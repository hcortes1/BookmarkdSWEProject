import dash
from dash import html, dcc, Input, Output, State
import backend.leaderboards as leaderboard_backend
from backend.chatbot_component import create_chatbot_component
from backend.chatbot_callbacks import register_chatbot_callbacks

dash.register_page(__name__, path='/leaderboards')


def welcome_layout():
    """Layout for non-logged-in users"""
    return html.Div([
        html.Div([
            html.H1("Welcome to Bookmarkd", className="welcome-title"),
            html.P("Discover, track, and share your favorite books with friends.",
                   className="welcome-subtitle"),
            html.Div([
                dcc.Link(html.Button(
                    "Log In", className="welcome-login-btn"), href='/login'),
                dcc.Link(html.Button(
                    "Sign Up", className="welcome-signup-btn"), href='/login?mode=signup')
            ], className="welcome-buttons")
        ], className="welcome-container")
    ], className="welcome-page")


def leaderboards_layout():
    """Layout for logged-in users"""
    return html.Div([
        html.Div([
            html.H1("Leaderboards", className="main-title"),
            html.P("Bookmarkd's Top Bookworms!", className="lb-main-subtitle"),

            # Tabs (Friends / Global)
            html.Div([
                html.Button("Friends", id="friends-tab",
                            n_clicks=0, className="tab active-tab"),
                html.Button("Global", id="global-tab",
                            n_clicks=0, className="tab"),
            ], className="leaderboard-tabs"),

            # Section title + time dropdown ("This: Month/Week/Year")
            html.Div([
                html.H2([
                    "This: ",
                    dcc.Dropdown(
                        id='time-range-dropdown',
                        options=[
                            {'label': 'Week', 'value': 'week'},
                            {'label': 'Month', 'value': 'month'},
                            {'label': 'Year', 'value': 'year'}
                        ],
                        value='month',
                        clearable=False,
                        className="time-dropdown"
                    )
                ], className="leaderboard-section-title")
            ], className="leaderboard-section"),

            # Leaderboard display
            html.Div(id='leaderboard-table',
                     className='card leaderboard-card'),

            # Hidden store for selected tab
            dcc.Store(id='leaderboard-scope', data='friends'),

        ], className="leader-app-container"),
        create_chatbot_component('leaderboards')
    ])


def layout():
    return html.Div([
        dcc.Store(id='leaderboards-session-check', data={}),
        html.Div(id='leaderboards-content')
    ])


# Logged-in check
@dash.callback(
    Output('leaderboards-content', 'children'),
    Input('leaderboards-session-check', 'data'),
    Input('user-session', 'data')
)
def update_leaderboards_content(_, user_session):
    is_logged_in = user_session.get(
        'logged_in', False) if user_session else False
    return leaderboards_layout() if is_logged_in else welcome_layout()


# Tab switching
@dash.callback(
    Output('leaderboard-scope', 'data'),
    Output('friends-tab', 'className'),
    Output('global-tab', 'className'),
    Input('friends-tab', 'n_clicks'),
    Input('global-tab', 'n_clicks'),
    prevent_initial_call=True
)
def switch_tabs(friends_clicks, global_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    clicked = ctx.triggered_id
    if clicked == "global-tab":
        return "global", "tab", "tab active-tab"
    else:
        return "friends", "tab active-tab", "tab"


# update leaderboard display
@dash.callback(
    Output('leaderboard-table', 'children'),
    Input('time-range-dropdown', 'value'),
    Input('leaderboard-scope', 'data'),
    Input('user-session', 'data')
)
def update_leaderboard(time_window, scope, user_session):
    if not user_session or not user_session.get('logged_in'):
        return html.P("Please log in to view leaderboards.", className="error-message")

    user_id = user_session.get('user_id')

    # Load leaderboard data
    data = (leaderboard_backend.get_friend_leaderboard(user_id, time_window)
            if scope == 'friends'
            else leaderboard_backend.get_global_leaderboard(time_window))

    if not data:
        return html.P("No reading data found for this period.", className="empty-message")

    # Build leaderboard list
    rows = []
    for rank, entry in enumerate(data, start=1):
        is_current_user = entry.get("user_id") == user_id
        row_class = "leaderboard-row current-user-row" if is_current_user else "leaderboard-row"
        username = entry.get('username', 'Unknown')
        profile_link = f"/profile/view/{username}"

        # Clickable avatar + username
        user_link = dcc.Link([
            html.Img(
                src=entry.get('profile_image_url',
                              '/assets/svg/default-profile.svg'),
                className="leaderboard-avatar"
            ),
            html.Span(username, className="leaderboard-username-link")
        ],
            href=profile_link,
            refresh=False,
            className="leaderboard-user-link"
        )

        rows.append(
            html.Div([
                html.Span(f"#{rank}", className="leaderboard-rank"),
                user_link,
                html.Span(str(entry.get('books_completed', 0)),
                          className="leaderboard-count")
            ], className=row_class)
        )

    return html.Div(rows, className="leaderboard-list")
register_chatbot_callbacks('leaderboards')
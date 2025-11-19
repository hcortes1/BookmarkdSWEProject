import dash
from dash import html, dcc, Input, Output, State
from backend.gemini_helper import get_book_recommendation_chat
import backend.home as home_backend
from backend.chatbot_component import create_chatbot_component
from backend.chatbot_callbacks import register_chatbot_callbacks

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
                html.Div([
                    html.H2("Recommended Books", className="section-title", style={'display': 'inline-block', 'marginRight': '15px'}),
                    html.Span(id="refresh-countdown", style={
                        'fontSize': '14px',
                        'color': 'var(--secondary-text-color)',
                        'fontWeight': 'normal'
                    })
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
                html.Div(id="ai-recommendations-container",
                         className="home-section-container")
            ], className="home-section"),

            html.Div([
                html.Div([
                    html.H2("Recent Reviews", className="section-title"),
                    html.Div(id="recent-reviews-container",
                             className="home-section-container")
                ], className="home-section"),

                html.Div([
                    html.H2("Friend Activity", className="section-title"),
                    html.Div(id="friend-activity-container",
                             className="home-section-container")
                ], className="home-section")
            ], className="home-sections-grid"),
        ], className="app-container"),
        #chatbot component
        create_chatbot_component('home')
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
    is_logged_in = user_session.get(
        'logged_in', False) if user_session else False
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
        recent_reviews = html.P(
            "No recent reviews found.", className="home-empty-message")
    else:
        recent_reviews = []
        for r in reviews:

            user_profile_link = f"/profile/view/{r['username']}"
            user_link = dcc.Link(
                [
                    html.Img(
                        src=r.get('profile_image_url',
                                  '/assets/svg/default-profile.svg'),
                        className="activity-avatar-small"
                    ),
                    html.Strong(r["username"], className="activity-username"),
                ],
                href=user_profile_link,
                style={'textDecoration': 'none',
                       'display': 'flex', 'alignItems': 'center'}
            )

            book_title_link = dcc.Link(
                html.H4(r["book_title"], className="activity-book-title"),
                href=f"/book/{r['book_id']}",
                style={'textDecoration': 'none', 'color': 'var(--text-color)'}
            )

            recent_reviews.append(
                html.Div([
                    html.Div([
                        dcc.Link([
                            html.Img(
                                src=r.get(
                                    'cover_url', '/assets/svg/default-book.svg'),
                                className="activity-book-cover"
                            )
                        ], href=f"/book/{r['book_id']}", style={'textDecoration': 'none'}),

                        html.Div([
                            html.Div([
                                user_link,
                                html.Span(" reviewed " if r["is_review"] else " rated ",
                                          className="activity-action"),
                                book_title_link,
                            ], className="activity-header"),
                            html.P(
                                r["snippet"], className="activity-snippet") if r["is_review"] else None,
                            html.Span(
                                f"{r.get('avg_rating', r['rating'])}/5 ({r.get('total_ratings', 1)})", className="activity-rating"),
                            html.Span(r["display_time"],
                                      className="activity-timestamp")
                        ], className="activity-book-info")
                    ], className="activity-card-content")
                ], className="activity-card")
            )

    friends = home_backend.get_friend_activity(user_id)
    if not friends:
        friend_activity = html.P(
            "No recent activity from your friends.", className="home-empty-message")
    else:
        friend_activity = []
        for f in friends:

            friend_profile_link = f"/profile/view/{f['username']}"

            friend_link = dcc.Link(
                [
                    html.Img(
                        src=f.get('profile_image_url',
                                  '/assets/svg/default-profile.svg'),
                        className="activity-avatar-small"
                    ),
                    html.Strong(f["username"], className="activity-username"),
                ],
                href=friend_profile_link,
                style={'textDecoration': 'none',
                       'display': 'flex', 'alignItems': 'center'}
            )

            book_title_link = dcc.Link(
                html.H4(f["book_title"], className="activity-book-title"),
                href=f"/book/{f['book_id']}",
                style={'textDecoration': 'none', 'color': 'var(--text-color)'}
            )

            # build rating display for friend activity
            total_ratings = f.get("total_ratings", 0)
            avg_rating = f.get("avg_rating")
            rating_element = None
            if total_ratings and total_ratings > 0 and avg_rating:
                rating_element = html.Span(
                    f"{avg_rating}/5 ({total_ratings})",
                    className="activity-rating"
                )

            friend_activity.append(
                html.Div([
                    html.Div([
                        dcc.Link([
                            html.Img(
                                src=f.get(
                                    'cover_url', '/assets/svg/default-book.svg'),
                                className="activity-book-cover"
                            )
                        ], href=f"/book/{f['book_id']}", style={'textDecoration': 'none'}),

                        html.Div([
                            html.Div([friend_link],
                                     className="activity-user-info"),
                            html.Span(f" {f['action']} ",
                                      className="activity-action"),
                            book_title_link,
                            rating_element if rating_element else None,
                            html.Span(f["display_time"],
                                      className="activity-timestamp")
                        ], className="activity-book-info")
                    ], className="activity-card-content")
                ], className="activity-card")
            )

    return recent_reviews, friend_activity


@dash.callback(
    Output("ai-recommendations-container", "children"),
    Input("user-session", "data")
)
def load_ai_recommendations(user_session):
    if not user_session or not user_session.get("logged_in"):
        return html.P(
            "Log in to see AI-powered book recommendations.",
            className="home-empty-message"
        )

    user_id = user_session.get("user_id")
    user_genres = user_session.get("favorite_genres", [])

    if not user_genres:
        return html.P(
            "Add some favorite genres in your profile to receive recommendations.",
            className="home-empty-message"
        )

    recs = home_backend.get_ai_recommendations_with_cache(
        user_id=user_id,
        user_genres=user_genres,
        limit=10
    )

    if not recs:
        return html.P(
            "No recommendations available right now.",
            className="home-empty-message"
        )

    # build recommendation cards
    rec_cards = []
    for r in recs:
        cover_url = r.get("cover_url", "")
        has_cover = cover_url and cover_url not in ("", " ", "/assets/svg/default-book.svg")
        
        if has_cover:
            cover_element = html.Img(src=cover_url, className="rec-cover-large")
        else:
            # create placeholder with book title
            cover_element = html.Div([
                html.Div(r["title"], className="rec-placeholder-title")
            ], className="rec-cover-placeholder-large")
        
        # build rating display
        total_ratings = r.get("total_ratings", 0)
        avg_rating = r.get("avg_rating")
        
        rating_element = None
        if total_ratings and total_ratings > 0 and avg_rating:
            rating_element = html.Span(
                f"⭐ {avg_rating}/5 ({total_ratings})",
                className="rec-rating"
            )
        
        # get description, truncate if too long
        description = r.get("description", "")
        print(f"Frontend: Book '{r['title']}' has description: '{description[:100] if description else 'EMPTY'}...'")
        if description and len(description) > 120:
            description = description[:120] + "... Read more"
        
        rec_cards.append(
            html.Div([
                dcc.Link([
                    html.Div([
                        cover_element,
                        html.Div([
                            html.H4(r["title"], className="rec-title-large"),
                            html.P(f"by {r['author']}", className="rec-author-large"),
                            rating_element if rating_element else html.Span("No ratings yet", className="rec-no-rating"),
                            html.P(description if description else "No description available.", className="rec-description")
                        ], className="rec-info")
                    ], className="rec-card-content")
                ],
                    href=f"/book/{r['book_id']}" if r["book_id"] else f"/search?query={r['title']}+{r['author']}",
                    style={"textDecoration": "none", "color": "inherit"}
                )
            ], className="rec-card-large")
        )
    
    return html.Div([
        html.Div(rec_cards, className="rec-scroll-container")
    ])

# Register chatbot callbacks
register_chatbot_callbacks('home')
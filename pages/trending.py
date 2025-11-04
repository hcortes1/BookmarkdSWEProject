import dash
from dash import html, dcc, Input, Output
import backend.trending as trending_backend

dash.register_page(__name__, path='/trending')


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


def trending_layout():
    """Layout for logged-in users"""
    return html.Div([
        html.Div([
            html.H1("Trending Books", className="main-title"),
            html.P("See what Bookmarkd users have been reading lately!",
                   className="trending-page-subtitle"),

            # Container for trending book cards
            html.Div(id='trending-books-container', className='trending-books-container')
        ], className="trending-app-container")
    ])


def layout():
    return html.Div([
        # Store for checking login status
        dcc.Store(id='trending-session-check', data={}),

        html.Div(id='trending-content')
    ])


# Check login state and render layout
@dash.callback(
    Output('trending-content', 'children'),
    Input('trending-session-check', 'data'),
    Input('user-session', 'data')
)
def update_trending_content(dummy, user_session):
    is_logged_in = user_session.get('logged_in', False) if user_session else False
    if is_logged_in:
        return trending_layout()
    else:
        return welcome_layout()


# Load trending books within the last 30 days
@dash.callback(
    Output('trending-books-container', 'children'),
    Input('user-session', 'data')
)
def update_trending_books(user_session):
    if not user_session or not user_session.get('logged_in'):
        return html.P("Please log in to view trending books.", className="error-message")

    books = trending_backend.get_trending_books(limit=30)  # Top 30 trending books
    if not books:
        return html.P("No trending books found for the last 30 days.",
                      className="empty-message")

    # Render trending books grid
    return html.Div([
        html.Div([
            html.Div([
                dcc.Link([
                    html.Img(
                        src=book.get('cover_url', '/assets/svg/default-book.svg'),
                        className='trending-book-cover'
                    ),
                    html.H4(book.get('title', 'Unknown Title'),
                            className='trending-book-title'),
                    html.P(f"by {book.get('author_name', 'Unknown Author')}",
                           className='trending-book-author'),
                    html.Span(f"{book.get('activity_count', 0)} readers",
                              className='trending-book-stats')
                ], href=f"/book/{book.get('book_id')}",
                    style={'textDecoration': 'none', 'color': 'inherit'})
            ], className='trending-book-card')
            for book in books
        ], className='trending-books-grid')
    ])

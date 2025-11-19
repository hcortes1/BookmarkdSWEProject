import dash
from dash import html, dcc, Input, Output
import backend.showcase as showcase_backend
from backend.chatbot_component import create_chatbot_component
from backend.chatbot_callbacks import register_chatbot_callbacks

dash.register_page(__name__, path='/showcase')


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


def showcase_layout():
    """Layout for logged-in users"""
    return html.Div([
        html.Div([
            html.H1("Book Showcase", className="main-title"),
            html.P("Explore featured and sponsored books.",
                   className="showcase-page-subtitle"),
            html.Hr(className="showcase-divider"),

            # Scrollable book section
            html.Div(id='showcase-books-container', className='showcase-books-container')
        ], className="app-container"),
        create_chatbot_component('showcase')

    ])


def layout():
    return html.Div([
        dcc.Store(id='showcase-session-check', data={}),
        html.Div(id='showcase-content')
    ])


@dash.callback(
    Output('showcase-content', 'children'),
    Input('showcase-session-check', 'data'),
    Input('user-session', 'data')
)
def update_showcase_content(dummy, user_session):
    is_logged_in = user_session.get('logged_in', False) if user_session else False
    return showcase_layout() if is_logged_in else welcome_layout()


@dash.callback(
    Output('showcase-books-container', 'children'),
    Input('user-session', 'data')
)
def update_showcase_books(user_session):
    if not user_session or not user_session.get('logged_in'):
        return html.Div(
            html.P("Please log in to view showcase books.", className="error-message"),
            className="showcase-books-grid"
        )

    books = showcase_backend.get_showcase_books(limit=30)

    # Empty state
    if not books:
        return html.Div([
            html.Div([
                html.P("No sponsored books available right now.",
                       className="empty-message-main"),
                html.P("Check back soon for new featured titles!",
                       className="empty-message-sub")
            ], className="showcase-empty-state")
        ], className="showcase-books-container")

    # Display books
    return html.Div([
        html.Div([
            dcc.Link([
                html.Div("Sponsored", className="showcase-badge"),
                html.Img(
                    src=book.get('cover_url', '/assets/svg/default-book.svg'),
                    className='showcase-book-cover'
                ),
                html.H4(book.get('title', 'Unknown Title'),
                        className='showcase-book-title'),
                html.P(f"by {book.get('author_name', 'Unknown Author')}",
                       className='showcase-book-author'),
                html.Span(f"Sponsored by {book.get('sponsor_name', 'Unknown')}",
                          className='showcase-book-sponsor'),
                html.Span(f"{book.get('start_date', '')} → {book.get('end_date', 'Ongoing')}",
                          className='showcase-book-dates')
            ],
                href=f"/book/{book.get('book_id')}",
                style={'textDecoration': 'none', 'color': 'inherit'})
        ], className='showcase-book-card')
        for book in books
    ], className='showcase-books-grid')
register_chatbot_callbacks('showcase')
# pages/reviews.py
import dash
from dash import html, dcc, Input, Output, State, callback
import psycopg2.extras
from backend.db import get_conn
from backend.reviews import get_book_reviews
from urllib.parse import unquote, parse_qs
from typing import Dict, Any
from datetime import datetime

dash.register_page(__name__, path_template="/reviews/<book_id>")


def layout(book_id=None, **kwargs):
    if not book_id:
        return html.Div("Book not found", className="error-message")

    try:
        book_id = int(book_id)
        book_data = get_book_details(book_id)

        if not book_data:
            return html.Div("Book not found", className="error-message")

        return html.Div([
            # Store for book data
            dcc.Store(id='reviews-book-store', data={'book_id': book_id}),

            html.Div([
                # Header section with book info
                html.Div([
                    html.Div([
                        # Book cover (smaller)
                        html.Img(
                            src=book_data.get(
                                'cover_url') or '/assets/svg/default-book.svg',
                            style={
                                'width': '100px',
                                'height': '150px',
                                'object-fit': 'cover',
                                'border-radius': '8px',
                                'margin-right': '20px'
                            }
                        ),
                        # Book info
                        html.Div([
                            html.H1([
                                "Reviews for ",
                                dcc.Link(
                                    book_data['title'],
                                    href=f"/book/{book_id}",
                                    style={
                                        'color': '#007bff',
                                        'text-decoration': 'none'
                                    }
                                )
                            ], style={
                                'margin': '0 0 10px 0',
                                'font-size': '24px'
                            }),
                            html.H2([
                                "by ",
                                dcc.Link(
                                    book_data.get(
                                        'author_name', 'Unknown Author'),
                                    href=f"/author/{book_data.get('author_id')}" if book_data.get(
                                        'author_id') else "#",
                                    style={
                                        'color': '#007bff',
                                        'text-decoration': 'none'
                                    }
                                ) if book_data.get('author_id') else book_data.get('author_name', 'Unknown Author')
                            ], style={
                                'margin': '0 0 15px 0',
                                'font-size': '18px',
                                'color': '#666'
                            }),
                            # Rating summary
                            html.Div([
                                html.Strong("Overall Rating: "),
                                html.Span(
                                    f"{book_data.get('average_rating', 0):.1f}/5.0 ({book_data.get('rating_count', 0)} reviews)",
                                    style={
                                        'font-weight': 'bold',
                                        'color': '#007bff'
                                    }
                                ) if book_data.get('average_rating') and book_data.get('average_rating') > 0 else html.Span(
                                    "No ratings yet",
                                    style={'color': '#666'}
                                )
                            ], style={
                                'margin-bottom': '15px',
                                'font-size': '16px'
                            })
                        ], style={'flex': '1'})
                    ], style={
                        'display': 'flex',
                        'align-items': 'flex-start',
                        'background': 'white',
                        'padding': '20px',
                        'border-radius': '12px',
                        'box-shadow': '0 4px 12px rgba(0,0,0,0.1)',
                        'margin-bottom': '30px'
                    })
                ]),

                # Reviews section
                html.Div([
                    html.H3("All Reviews", style={
                        'color': '#333',
                        'margin-bottom': '20px',
                        'font-size': '20px'
                    }),

                    # Reviews container - will be populated by callback
                    html.Div(id='reviews-container', children=[
                        html.Div("Loading reviews...", style={
                                 'text-align': 'center', 'color': '#666'})
                    ]),

                    # Pagination controls
                    html.Div(id='reviews-pagination', style={
                        'margin-top': '30px',
                        'text-align': 'center'
                    }),

                    # Store for pagination
                    dcc.Store(id='reviews-page-store',
                              data={'current_page': 1, 'per_page': 10})

                ], style={
                    'background': 'white',
                    'padding': '20px',
                    'border-radius': '12px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.1)'
                })

            ], style={
                'max-width': '800px',
                'margin': '0 auto',
                'padding': '30px'
            })
        ], style={
            'background': '#f5f5f5',
            'min-height': '100vh'
        })

    except Exception as e:
        print(f"Error loading reviews page: {e}")
        return html.Div("Error loading reviews", className="error-message")


def get_book_details(book_id: int):
    """Get book details for the reviews page header"""
    try:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            sql = """
                SELECT b.book_id, b.title, b.cover_url, b.author_id,
                       b.average_rating, b.rating_count,
                       a.name as author_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                WHERE b.book_id = %s
            """
            cur.execute(sql, (book_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    except Exception as e:
        print(f"Error getting book details: {e}")
        return None


def create_review_card(review: Dict[str, Any]):
    """Create a review card component"""
    # Format the date
    created_at = review.get('created_at')
    if created_at:
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(
                created_at.replace('Z', '+00:00'))
        formatted_date = created_at.strftime("%B %d, %Y")
    else:
        formatted_date = "Unknown date"

    # Create rating display
    rating = review.get('rating', 0)

    return html.Div([
        # User info section
        html.Div([
            # Profile image
            dcc.Link([
                html.Img(
                    src=review.get(
                        'profile_image_url') or '/assets/svg/default-profile.svg',
                    style={
                        'width': '50px',
                        'height': '50px',
                        'border-radius': '50%',
                        'object-fit': 'cover',
                        'margin-right': '15px'
                    }
                )
            ], href=f"/profile/view/{review.get('username')}" if review.get('username') else "#"),

            # User details
            html.Div([
                dcc.Link(
                    review.get('display_name') or review.get(
                        'username', 'Anonymous'),
                    href=f"/profile/view/{review.get('username')}" if review.get(
                        'username') else "#",
                    style={
                        'font-weight': 'bold',
                        'color': '#007bff',
                        'text-decoration': 'none',
                        'font-size': '16px'
                    }
                ),
                html.Div([
                    html.Span(f"{rating}/5.0", style={
                        'color': '#007bff',
                        'font-weight': 'bold',
                        'margin-right': '10px'
                    }),
                    html.Span(formatted_date, style={
                        'color': '#888',
                        'font-size': '14px'
                    })
                ], style={'margin-top': '5px'})
            ], style={'flex': '1'})
        ], style={
            'display': 'flex',
            'align-items': 'center',
            'margin-bottom': '15px'
        }),

        # Review text
        html.Div(
            review.get('review_text', ''),
            style={
                'color': '#333',
                'line-height': '1.6',
                'white-space': 'pre-wrap'
            }
        ) if review.get('review_text') else html.Div(
            "No written review",
            style={
                'color': '#999',
                'font-style': 'italic'
            }
        )

    ], style={
        'background': '#f8f9fa',
        'border-radius': '8px',
        'padding': '20px',
        'margin-bottom': '20px',
        'border-left': '4px solid #007bff'
    })


def create_pagination_controls(current_page, total_pages, book_id):
    """Create pagination controls for reviews"""
    if total_pages <= 1:
        return []

    controls = []

    # Previous button
    if current_page > 1:
        controls.append(
            html.Button(
                "← Previous",
                id={'type': 'reviews-pagination-btn', 'page': current_page - 1},
                style={
                    'margin': '0 5px',
                    'padding': '8px 16px',
                    'background': '#007bff',
                    'color': 'white',
                    'border': 'none',
                    'border-radius': '4px',
                    'cursor': 'pointer'
                }
            )
        )

    # Page numbers (show current and adjacent pages)
    start_page = max(1, current_page - 2)
    end_page = min(total_pages, current_page + 2)

    for page_num in range(start_page, end_page + 1):
        is_current = page_num == current_page
        controls.append(
            html.Button(
                str(page_num),
                id={'type': 'reviews-pagination-btn', 'page': page_num},
                style={
                    'margin': '0 2px',
                    'padding': '8px 12px',
                    'background': '#007bff' if is_current else '#f8f9fa',
                    'color': 'white' if is_current else '#333',
                    'border': '1px solid #dee2e6' if not is_current else 'none',
                    'border-radius': '4px',
                    'cursor': 'pointer',
                    'font-weight': 'bold' if is_current else 'normal'
                }
            )
        )

    # Next button
    if current_page < total_pages:
        controls.append(
            html.Button(
                "Next →",
                id={'type': 'reviews-pagination-btn', 'page': current_page + 1},
                style={
                    'margin': '0 5px',
                    'padding': '8px 16px',
                    'background': '#007bff',
                    'color': 'white',
                    'border': 'none',
                    'border-radius': '4px',
                    'cursor': 'pointer'
                }
            )
        )

    return controls


# Callback to load reviews
@callback(
    [Output('reviews-container', 'children'),
     Output('reviews-pagination', 'children')],
    [Input('reviews-book-store', 'data'),
     Input('reviews-page-store', 'data')],
    prevent_initial_call=False
)
def load_reviews(book_data, page_data):
    """Load and display reviews for the book"""
    if not book_data or not book_data.get('book_id'):
        return [html.Div("No book selected")], []

    book_id = book_data['book_id']
    current_page = page_data.get('current_page', 1)
    per_page = page_data.get('per_page', 10)

    # Calculate offset for pagination
    offset = (current_page - 1) * per_page

    # Get reviews from backend
    success, message, data = get_book_reviews(
        book_id, limit=per_page, offset=offset)

    if not success or not data:
        return [html.Div("No reviews found for this book.", style={
            'text-align': 'center',
            'color': '#666',
            'padding': '40px'
        })], []

    reviews = data.get('reviews', [])
    total_count = data.get('total_count', 0)

    if not reviews:
        return [html.Div("No reviews found for this book.", style={
            'text-align': 'center',
            'color': '#666',
            'padding': '40px'
        })], []

    # Create review cards
    review_cards = [create_review_card(review) for review in reviews]

    # Create pagination
    total_pages = (total_count + per_page - 1) // per_page
    pagination_controls = create_pagination_controls(
        current_page, total_pages, book_id)

    return review_cards, pagination_controls


# Callback to handle pagination clicks
@callback(
    Output('reviews-page-store', 'data'),
    Input({'type': 'reviews-pagination-btn',
          'page': dash.dependencies.ALL}, 'n_clicks'),
    State('reviews-page-store', 'data'),
    prevent_initial_call=True
)
def handle_pagination_click(clicks_list, page_data):
    """Handle pagination button clicks"""
    if not dash.callback_context.triggered or not any(clicks_list or []):
        return dash.no_update

    # Find which button was clicked
    triggered = dash.callback_context.triggered[0]
    button_id = triggered['prop_id'].split('.')[0]
    button_info = eval(button_id)  # Convert string back to dict

    new_page = max(1, int(button_info.get('page', 1)))

    return {**page_data, 'current_page': new_page}

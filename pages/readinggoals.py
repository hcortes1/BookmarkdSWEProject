import dash
from dash import html, dcc, Input, Output, State
from flask import session
from backend import readinggoals

dash.register_page(__name__, path="/readinggoals", title="Reading Goals")

layout = html.Div(
    className="reading-goals-container",
    children=[
        html.H1("📚 Your Reading Goals", className="page-title"),
        html.Div(
            className="goal-form",
            children=[
                html.H3("Set a New Goal"),
                dcc.Input(id="goal-book-id", type="number", placeholder="Book ID", className="goal-input"),
                dcc.Dropdown(
                    id="goal-type",
                    options=[
                        {"label": "Pages per day", "value": "pages_per_day"},
                        {"label": "Books per month", "value": "books_per_month"},
                        {"label": "Deadline (finish by date)", "value": "deadline"}
                    ],
                    placeholder="Select goal type",
                    className="goal-dropdown"
                ),
                dcc.Input(id="goal-target", type="number", placeholder="Target (e.g., 50 pages)", className="goal-input"),
                dcc.DatePickerSingle(id="goal-deadline", placeholder="Deadline (optional)"),
                html.Button("Create Goal", id="create-goal-btn", className="btn btn-primary"),
                html.Div(id="goal-create-status", className="status-message")
            ]
        ),
        html.Hr(),
        html.Div(id="user-goals-display", className="goal-list")
    ]
)


# --- Callbacks --- #

@dash.callback(
    Output("goal-create-status", "children"),
    Output("user-goals-display", "children"),
    Input("create-goal-btn", "n_clicks"),
    State("goal-book-id", "value"),
    State("goal-type", "value"),
    State("goal-target", "value"),
    State("goal-deadline", "date"),
    prevent_initial_call=True
)
def create_goal(n_clicks, book_id, goal_type, target, deadline):
    """Handles goal creation and updates the displayed list."""
    user_id = session.get("user_id")
    if not user_id:
        return "Please log in to set a reading goal.", []

    if not all([book_id, goal_type, target]):
        return "All fields except deadline are required.", []

    success, message = readinggoals.create_reading_goal(user_id, book_id, goal_type, target, deadline)
    goals = readinggoals.get_user_goals(user_id)[2] if success else []
    return message, _generate_goal_cards(goals)


@dash.callback(
    Output("user-goals-display", "children"),
    Input("goal-create-status", "children")
)
def refresh_goals(_):
    """Refresh goals whenever status changes."""
    user_id = session.get("user_id")
    if not user_id:
        return html.Div("Please log in to view your goals.")

    success, _, goals = readinggoals.get_user_goals(user_id)
    if not success or not goals:
        return html.Div("You don’t have any goals yet.")
    return _generate_goal_cards(goals)


def _generate_goal_cards(goals):
    """Helper to generate goal cards."""
    cards = []
    for goal in goals:
        cards.append(html.Div(
            className="goal-card",
            children=[
                html.H4(goal.get("book_title", "Unknown Book")),
                html.P(f"Goal Type: {goal.get('goal_type')}"),
                html.P(f"Progress: {goal.get('progress', 0)}/{goal.get('target')}"),
                html.P(f"Deadline: {goal.get('deadline', '—')}"),
                html.Progress(value=goal.get('progress', 0), max=goal.get('target', 1))
            ]
        ))
    return cards

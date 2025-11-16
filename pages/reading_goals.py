# pages/reading_goals.py
import dash
from dash import html, dcc, Input, Output, State, callback, ctx
import backend.reading_goals as reading_goals_backend
from datetime import datetime

dash.register_page(__name__, path="/readinggoals", title="Reading Goals")


# Goal Card Renderer
def goal_card(goal: dict):
    goal_id = goal.get('goal_id')
    progress = goal.get('progress', 0) or 0
    target = goal.get('target_books', 1) or 1
    try:
        pct = int((progress / target) * 100) if target else 0
    except Exception:
        pct = 0

    start_date = goal.get('start_date')
    start_text = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else (start_date or '')

    end_date = goal.get('end_date')
    end_text = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else 'n/a'

    reminder_flag = "Yes" if goal.get('reminder_enabled') else "No"

    return html.Div([
        html.Div([
            html.Div("Goal", className='goal-title'),
            html.Div(f"Start: {start_text}", className='goal-field'),
            html.Div(f"Target: {target}", className='goal-field'),
            html.Div(f"Progress: {progress} ({pct}%)", className='goal-field'),
            html.Div(f"End: {end_text}", className='goal-field'),
            html.Div(f"Reminders: {reminder_flag}", className='goal-field'),
        ], style={'flex': '1 1 60%'}),

        html.Div([
            dcc.Input(id={'type': 'set-input', 'i': goal_id}, type='number', placeholder='New progress',
                      persistence=True, persistence_type='session', style={'width': '100%', 'marginBottom': '4px'}),
            html.Button("Set", id={'type': 'set-btn', 'i': goal_id}, n_clicks=0,
                        className='btn btn-primary', style={'width': '100%', 'marginBottom': '6px'}),
            html.Button("Delete", id={'type': 'delete-btn', 'i': goal_id}, n_clicks=0,
                        className='btn btn-danger', style={'width': '100%'})
        ], style={'flex': '0 0 140px', 'marginLeft': '12px'})
    ], className='goal-card')


# Page Layout
layout = html.Div([
    dcc.Markdown("""
    <style>
    .goal-card {
        padding: 18px; margin-bottom: 16px; display: flex; align-items: flex-start; gap: 12px;
        border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        background-color: #f0f0f0; color: #111;
    }
    @media (prefers-color-scheme: dark) {
        .goal-card {background-color: #1e1e1e; color: #eee; box-shadow: 0 2px 6px rgba(0,0,0,0.3);}
    }
    .goal-title {font-weight: 700; font-size: 18px; margin-bottom: 4px;}
    .goal-field {font-size: 14px; margin-top: 4px;}
    .create-goal-form {padding: 16px; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.2); background-color: #eaeaea; color: #111;}
    @media (prefers-color-scheme: dark) {
        .create-goal-form {background-color: #2c2c2c; color: #eee; box-shadow: 0 1px 6px rgba(0,0,0,0.5);}
    }
    </style>
    """, dangerously_allow_html=True),

    html.Div([
        html.H1("Reading Goals", style={'textAlign': 'center', 'fontSize': '32px', 'fontWeight': 700}),
        html.Div("Set, track and remind yourself about reading targets.",
                 style={'textAlign': 'center', 'fontSize': '16px', 'marginBottom': '24px'}),

        # Create Goal Form
        html.Div([
            html.Div([
                html.Label("Goal type:", style={'fontWeight': 600, 'marginBottom': '4px'}),
                dcc.Dropdown(
                    id='rg-goal-type',
                    options=[
                        {'label': 'Pages per day', 'value': 'pages_per_day'},
                        {'label': 'Books per month', 'value': 'books_per_month'},
                        {'label': 'Deadline (finish by date)', 'value': 'deadline'}
                    ],
                    placeholder='Select goal type',
                    style={'color': '#000'}
                ),
                html.Label("Book ID (Optional):", style={'fontWeight': 600, 'marginTop': '12px'}),
                dcc.Input(id='rg-book-id', type='number', placeholder='Book ID', style={'width': '100%', 'color': '#000'}),
                html.Label("Target (pages/books/days):", style={'fontWeight': 600, 'marginTop': '12px'}),
                dcc.Input(id='rg-target', type='number', placeholder='pages/books/days', min=1,
                          style={'width': '100%', 'color': '#000'}),
                html.Label("Deadline:", style={'fontWeight': 600, 'marginTop': '12px'}),
                dcc.DatePickerSingle(id='rg-end-date', placeholder='Select Date', style={'width': '100%'}),
                dcc.Checklist(id='rg-reminder-enabled',
                              options=[{'label': 'Enable reminders', 'value': 'on'}],
                              value=[], style={'marginTop': '12px'}),
                html.Button("Create Goal", id='rg-create-btn', className='btn btn-primary',
                            n_clicks=0, style={'marginTop': '16px', 'width': '100%'})
            ], className='create-goal-form')
        ], style={'marginBottom': '24px'}),

        html.Div(id='rg-create-status', style={'marginBottom': '16px', 'textAlign': 'center', 'fontWeight': 600}),
        html.H3("Your Goals", style={'textAlign': 'center', 'marginBottom': '12px'}),
        html.Div(id='rg-goals-list', style={'maxWidth': '980px', 'margin': '0 auto'}),

        dcc.Store(id='rg-action-store', data={}),
        dcc.Store(id='rg-last-create-status', data='')
    ], style={'maxWidth': '980px', 'margin': '24px auto'})
])

# Callbacks
@callback(
    Output('rg-last-create-status', 'data'),
    Output('rg-action-store', 'data'),
    Input('rg-create-btn', 'n_clicks'),
    Input({'type': 'set-btn', 'i': dash.ALL}, 'n_clicks'),
    Input({'type': 'delete-btn', 'i': dash.ALL}, 'n_clicks'),
    State({'type': 'set-input', 'i': dash.ALL}, 'value'),
    State({'type': 'set-input', 'i': dash.ALL}, 'id'),
    State('user-session', 'data'),
    State('rg-goal-type', 'value'),
    State('rg-book-id', 'value'),
    State('rg-target', 'value'),
    State('rg-end-date', 'date'),
    State('rg-reminder-enabled', 'value'),
    prevent_initial_call=True
)
def handle_create_or_actions(create_clicks, set_clicks, delete_clicks,
                             set_values, set_ids, session_data, goal_type, book_id, target, end_date, reminder_value):
    if not session_data or not session_data.get('logged_in'):
        return "Please log in.", dash.no_update
    user_id = int(session_data['user_id'])
    triggered = ctx.triggered_id
    if not triggered:
        return dash.no_update, dash.no_update

    # CREATE
    if triggered == 'rg-create-btn':
        if not goal_type or not target:
            return "Goal type and target are required.", dash.no_update
        if goal_type == 'deadline' and not end_date:
            return "Deadline goals require an end date.", dash.no_update
        reminder_enabled = 'on' in (reminder_value or [])
        res = reading_goals_backend.create_goal(
            user_id=user_id, book_id=book_id, goal_type=goal_type,
            target=target, start_date=None, end_date=end_date,
            reminder_enabled=reminder_enabled
        )
        if res[0]:
            return "Goal created.", {"last_action": "create", "time": datetime.now().isoformat()}
        else:
            return f"Error: {res[1]}", dash.no_update

    # ACTIONS
    if isinstance(triggered, dict):
        typ = triggered.get('type')
        goal_id = triggered.get('i')

        if typ == 'set-btn':
            # find corresponding value for this button
            val_index = next((i for i, sid in enumerate(set_ids) if sid['i'] == goal_id), None)
            if val_index is None:
                return "No input found for this goal.", dash.no_update
            new_val = set_values[val_index]
            if new_val is None:
                return "Please enter a numeric value.", dash.no_update
            res = reading_goals_backend.update_progress_manual(int(goal_id), int(new_val))
            return res.get('message') if res.get('success') else f"Error: {res.get('message')}", \
                   {"last_action": "set", "goal_id": goal_id, "time": datetime.now().isoformat()}

        if typ == 'delete-btn':
            res = reading_goals_backend.delete_goal(int(goal_id))
            return res.get('message') if res.get('success') else f"Error: {res.get('message')}", \
                   {"last_action": "delete", "goal_id": goal_id, "time": datetime.now().isoformat()}

    return dash.no_update, dash.no_update


@callback(
    Output('rg-goals-list', 'children'),
    Input('rg-action-store', 'data'),
    State('user-session', 'data')
)
def refresh_goals(action_store, session_data):
    if not session_data or not session_data.get('logged_in'):
        return html.Div("Please log in to view your goals.", style={'color': '#ccc'})
    user_id = int(session_data['user_id'])
    ok, msg, goals = reading_goals_backend.get_user_goals(user_id)
    if not ok:
        return html.Div(f"Error loading goals: {msg}", style={'color': '#c0392b'})
    if not goals:
        return html.Div("No goals yet. Create one above!", style={'color': '#ccc'})
    return html.Div([goal_card(g) for g in goals],
                    style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(320px, 1fr))', 'gap': '12px'})


@callback(
    Output('rg-create-status', 'children'),
    Input('rg-last-create-status', 'data')
)
def show_status(status_text):
    if not status_text:
        return ''
    color = '#198754' if 'created' in status_text.lower() or 'set' in status_text.lower() else '#c0392b'
    return html.Div(status_text, style={'color': color, 'fontWeight': 600})

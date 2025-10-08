import dash
from dash import html

dash.register_page(__name__, path='/leaderboards')

layout = html.Div([
    html.Div([
        html.H1("This is the leaderboards view", className="main-title"),

    ], className="app-container")
])
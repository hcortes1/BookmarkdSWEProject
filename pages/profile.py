import dash
from dash import html

dash.register_page(__name__, path='/profile')

layout = html.Div([
    html.Div([
        html.H1("This is the profile view", className="main-title"),

    ], className="app-container")
])
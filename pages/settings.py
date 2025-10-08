import dash
from dash import html

dash.register_page(__name__, path='/profile/settings')

layout = html.Div([
    html.Div([
        html.H1("This is the settings view", className="main-title"),

    ], className="app-container")
])
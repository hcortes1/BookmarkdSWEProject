import dash
from dash import html

dash.register_page(__name__, path='/')

layout = html.Div([
    html.Div([
        html.H1("This will be the main homefeed", className="main-title"),

    ], className="app-container")
])
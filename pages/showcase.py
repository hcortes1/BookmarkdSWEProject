import dash
from dash import html

dash.register_page(__name__, path='/showcase')

layout = html.Div([
    html.Div([
        html.H1("This is the sponsored books view", className="main-title"),

    ], className="app-container")
])
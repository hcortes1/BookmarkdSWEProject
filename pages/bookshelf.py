import dash
from dash import html

dash.register_page(__name__, path='/profile/bookshelf')

layout = html.Div([
    html.Div([
        html.H1("This will be the bookshelf view", className="main-title"),

    ], className="app-container")
])
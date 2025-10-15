import dash
from dash import html, dcc, Input, Output, State

dash.register_page(__name__, path='/profile')

layout = html.Div([
    html.Div([
        html.H1("My Profile", className="main-title"),

        html.Div([
            # LEFT SIDE – Profile picture and username
            html.Div([
                html.Img(
                    id='profile-image',
                    # TODO: dynamically load profile image
                    src='',
                    className='profile-user-image'
                ),

                # TODO: dynamically load username
                html.Span("<>", id="profile-username", className="profile-username"),
            ], className="profile-info"),

            # RIGHT SIDE – Scrollable friends list
            html.Div([
                html.H2("My Friends", className="friends-title"),
                html.Ul(id="friends-list", className="friends-list")
            ], className="profile-right")

        ], className="profile-header")

    ], className="app-container", id="profile-container")
])

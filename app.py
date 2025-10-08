import dash
from dash import Dash, html, dcc, Input, Output
from argparse import ArgumentParser


app = Dash(
    __name__,
    use_pages=True
)

app.layout = html.Div([
    dcc.Location(id="url"),

    html.Div(className="header", children=[
        html.Nav(className="nav", children=[
            html.Div(className="nav-left", children=[
                dcc.Link(html.Img(src='/assets/svg/home.svg', className='home-icon', alt='home'), href='/', className='nav-link'),
                dcc.Link('Trending', href='/trending', className='nav-link'),
                dcc.Link('Leaderboards', href='/leaderboards', className='nav-link'),
                dcc.Link('Showcase', href='/showcase', className='nav-link'),
            ]),

            html.Div(className='nav-center', children=[
                dcc.Input(id='header-search', placeholder='Search...', type='text', className='search-input')
            ]),

            html.Div(className='nav-right', children=[
                dcc.Link(html.Img(src='/assets/svg/bookshelf.svg', className='bookshelf-img', alt='bookshelf'), href='/profile/bookshelf'),
                dcc.Link(
                    html.Div(className='profile-circle', children=[
                        html.Img(src='/assets/svg/profile.svg', className='profile-img', alt='profile')
                    ]),
                    href='/profile'
                ),
                dcc.Link(html.Img(src='/assets/svg/settings.svg', className='settings-img', alt='settings'), href='/profile/settings')
            ])
        ])
    ]),

    dash.page_container
])


@app.callback(
    Output("url", "pathname"),
    Input("url", "pathname"),
)
def sync_dropdown(pathname):
    ctx = dash.callback_context

    if ctx.triggered_id == "url":
        return pathname

    return pathname


if __name__ == "__main__":
    parser = ArgumentParser(
        prog='app.py',
        description='main application'
    )
    parser.add_argument('--hostname', default='localhost')
    parser.add_argument('--port', default='8050')
    args = parser.parse_args()

    app.run(debug=True, host=args.hostname, port=int(args.port))
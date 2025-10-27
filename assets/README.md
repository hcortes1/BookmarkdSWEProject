# Bookmarkd

Software Engineering Fall 2025 Project

## How to run the app locally

```bash
# install the requirements
pip3 install -r requirements.txt
```

```bash
# run the app (hostname and port are optional)
python3 app.py --hostname --port
```

```bash
# by default the app runs at
http://127.0.0.1:8080/
# unless hostname and port were specified
```


Note: you need an `.env` file in `backend/` to be able to connect to the database with the database credentials.

## About Dash Framework

This project uses **Dash** by Plotly, a Python web framework for building interactive web applications. Here's what you need to know:

### Key Concepts:
- **Pages**: Each page is a separate Python file in the `pages/` directory
- **Components**: Dash uses HTML-like components (`html.Div`, `html.H1`, etc.) and interactive components (`dcc.Input`, `dcc.Link`, etc.)
- **Callbacks**: Interactive functionality using `@app.callback` decorators to handle user inputs
- **Layouts**: Each page defines a `layout` variable that contains the page structure
- **Registration**: Pages are registered using `dash.register_page(__name__, path='/your-path')`

### Useful Dash Documentation:
- [Dash Tutorial](https://dash.plotly.com/tutorial)
- [Dash Components](https://dash.plotly.com/dash-html-components)
- [Callbacks](https://dash.plotly.com/basic-callbacks)

## Project Structure & Development Guidelines

### Frontend Files:
**Location**: `pages/` directory and `assets/` for styling

- **Pages** (`pages/`): 
  - Each `.py` file represents a different page
  - Must include `dash.register_page(__name__, path='/route-name')`
  - Must define a `layout` variable with the page content
  - Example: `login.py`

- **Styling** (`assets/`):
  - `.css` files for styling (automatically loaded by Dash)
  - `svg/` for icons and graphics
  - Global styles go in `global.css`
  - Page-specific styles: `page-name.css`

#### Adding a New Page:

1. Create `pages/new_page.py`
2. Add the basic structure:
```python
import dash
from dash import html

dash.register_page(__name__, path='/new-page')

layout = html.Div([
    html.H1("Your Page Content"),
    # Add more components here
])
```
3. Create corresponding CSS file: `assets/new-page.css`
4. Add navigation link in `app.py` if needed


### Backend Files:
**Location**: `backend/` directory

- Create a new file for the functionality you are implementing
- Each backend module should handle a specific domain (e.g., `login.py` for authentication)

#### Using Backend Modules in Frontend:

To use backend functionality in your Dash pages:

```python
# Import the backend module at the top of your page file
import backend.login as login_backend

# Use the functions in callbacks or layout functions
@app.callback(...)
def handle_login(username, password):
    success, message = login_backend.login_user(username, password)
    if success:
        # Handle successful login
        return "Login successful!"
    else:
        # Handle login failure
        return f"Error: {message}"
```


#### Creating New Backend Modules:

When creating new backend files, follow this structure:

```python
import os
import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error

# Load environment variables
load_dotenv()

# Database configuration
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

def get_db_connection():
    """Get database connection - reuse this function across modules"""
    try:
        connection = psycopg2.connect(
            user=USER, password=PASSWORD, host=HOST, port=PORT, dbname=DBNAME
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def your_function(param1, param2):
    connection = get_db_connection()
    if not connection:
        return False, "Database connection failed"
    
    cursor = connection.cursor()
    
    try:
        # Your SQL operations here
        cursor.execute("SELECT * FROM table WHERE condition = %s", (param1,))
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return True, results
        
    except Error as e:
        cursor.close()
        connection.close()
        return False, f"Database error: {e}"
```

## User Session Management

The application implements a comprehensive user session system that stores all user data upon login for efficient access throughout the app.

### Session Data Structure

When a user logs in, the following data is stored in the browser session:

```python
session_data = {
    "logged_in": True,           # Boolean - user authentication status
    "user_id": 123,             # Integer - unique user identifier
    "username": "john_doe",     # String - user's username
    "email": "john@example.com", # String - user's email address
    "profile_image_url": "https://...", # String - URL to profile image (or None)
    "created_at": "2025-01-01T12:00:00" # String - ISO format timestamp
}
```

### Benefits

- **Reduced Database Calls**: User information is cached in session, eliminating repeated queries
- **Improved Performance**: Faster page loads with readily available user data
- **Real-time Updates**: Profile changes immediately reflect across the application
- **Consistent Access**: Standardized way to access user data throughout the app

### Usage in Pages

Access session data in any page callback:

```python
from dash import callback, Input, Output, State

@callback(
    Output('some-output', 'children'),
    Input('some-input', 'n_clicks'),
    State('user-session', 'data')
)
def handle_user_action(n_clicks, session_data):
    if not session_data or not session_data.get('logged_in'):
        return "Please log in"
    
    # Access user data
    user_id = session_data['user_id']
    username = session_data['username']
    email = session_data['email']
    profile_image = session_data['profile_image_url']
    
    return f"Welcome, {username}!"
```

### Session Updates

The session is automatically updated when:

- User logs in (all data populated)
- Profile image is uploaded/deleted (profile_image_url updated)
- User logs out (all data cleared)
- Account is deleted (session cleared)

### Backend Functions

**Login**: `backend/login.py`

- `login_user(username, password)` - Returns complete user data
- `refresh_user_session_data(user_id)` - Refreshes session from database

**Settings**: `backend/settings.py`

- `get_updated_user_data(user_id)` - Gets fresh user data for updates
- Profile image functions automatically update session data

### Git Workflow

#### DO NOT COMMIT DIRECTLY TO MAIN

1. Create feature branches from `main`
2. Make changes in appropriate directories (`pages/` for frontend, `backend/` for logic)
3. Test locally before pushing
4. Create pull requests
5. Merge the PR if no conflict
6. If merge was successful you can delete the branch


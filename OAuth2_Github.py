import os
import secrets
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import Flask, make_response, redirect, render_template_string, request, session, url_for
from itsdangerous import URLSafeTimedSerializer, BadSignature

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Serializer for signed cookies
cookie_serializer = URLSafeTimedSerializer(app.secret_key)

# GitHub OAuth Configuration (changed from Google)
CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:5000/callback")

# GitHub OAuth endpoints (changed from Google)
AUTH_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_API_URL = "https://api.github.com/user"  # GitHub uses API, not userinfo endpoint

# Validate configuration
if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "Missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET. "
        "Please set them in your .env file or environment variables."
    )


# --- HTML Templates ---

def make_page(content):
    # Use double braces {{ and }} for CSS to escape Python format
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub OAuth App</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #24292e 0%, #586069 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 400px;
            width: 100%;
            text-align: center;
        }}
        h1 {{ color: #333; margin-bottom: 10px; font-size: 28px; }}
        h2 {{ color: #555; margin-bottom: 20px; font-size: 22px; }}
        p {{ color: #666; margin-bottom: 30px; line-height: 1.6; }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #24292e;
            color: white;
            padding: 14px 28px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(36, 41, 46, 0.4);
        }}
        .btn-secondary {{
            background: #6c757d;
            margin-top: 10px;
        }}
        .btn-secondary:hover {{
            box-shadow: 0 8px 20px rgba(108, 117, 125, 0.4);
        }}
        .profile-img {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            margin-bottom: 20px;
            border: 4px solid #24292e;
        }}
        .success-icon {{
            font-size: 60px;
            color: #28a745;
            margin-bottom: 20px;
        }}
        .info {{
            background: #f6f8fa;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: left;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e1e4e8;
        }}
        .info-row:last-child {{ border-bottom: none; }}
        .label {{ color: #586069; font-size: 14px; }}
        .value {{ color: #24292e; font-weight: 600; }}
        .logout {{
            color: #dc3545;
            text-decoration: none;
            font-size: 14px;
            margin-top: 20px;
            display: inline-block;
        }}
        .logout:hover {{ text-decoration: underline; }}
        .error {{
            background: #ffeef0;
            color: #86181d;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #fdaeb7;
        }}
        .debug {{
            background: #fff3cd;
            color: #856404;
            padding: 12px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 11px;
            text-align: left;
            font-family: monospace;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""
HOME_PAGE = make_page("""
    <h1>🐙 Welcome</h1>
    <p>Sign in with your GitHub account to access your personalized dashboard.</p>
    <a href="{{ url_for('login') }}" class="btn">
        <svg width="18" height="18" viewBox="0 0 16 16" fill="white" style="vertical-align: middle;">
            <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
        </svg>
        Sign in with GitHub
    </a>
""")

WELCOME_PAGE = """
    <div class="success-icon">✅</div>
    <h1>Welcome!</h1>
    <h2>You have successfully signed in with GitHub</h2>
    <p>Your OAuth 2.0 authentication is working correctly.</p>
    <a href="{{ dashboard_url }}" class="btn">View Dashboard</a>
    <br>
    <a href="{{ logout_url }}" class="btn btn-secondary">Sign Out</a>
"""


def dashboard_page(name, username, email, avatar_url, bio, public_repos):
    # Handle None values
    bio_text = bio or "No bio available"
    email_text = email or "No public email"
    
    return make_page(f"""
    <img src="{avatar_url}" alt="Profile" class="profile-img">
    <h1>Hello, {name or username}!</h1>
    <div class="info">
        <div class="info-row">
            <span class="label">Username</span>
            <span class="value">@{username}</span>
        </div>
        <div class="info-row">
            <span class="label">Email</span>
            <span class="value">{email_text}</span>
        </div>
        <div class="info-row">
            <span class="label">Public Repos</span>
            <span class="value">{public_repos}</span>
        </div>
        <div class="info-row">
            <span class="label">Bio</span>
            <span class="value" style="text-align: right; max-width: 200px;">{bio_text}</span>
        </div>
    </div>
    <a href="{url_for('logout')}" class="logout">← Sign out</a>
""")


def error_page(error_msg, debug_info=""):
    debug_html = f'<div class="debug">{debug_info}</div>' if debug_info else ""
    return make_page(f"""
    <div class="error">⚠️ {error_msg}</div>
    <a href="{url_for('home')}" class="btn">Back to Home</a>
    {debug_html}
""")


# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


# --- Routes ---

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("welcome"))
    return render_template_string(HOME_PAGE)


@app.route("/login")
def login():
    # Generate state parameter
    state = secrets.token_urlsafe(32)
    
    # Build GitHub authorization URL (simpler than Google - no scope needed for basic profile)
    auth_url = (
        f"{AUTH_URL}"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
        # Optional: add scope for more permissions
        # f"&scope=user:email"  # Uncomment to request email access
    )
    
    # Store state in a signed cookie
    response = make_response(redirect(auth_url))
    cookie_value = cookie_serializer.dumps(state)
    
    response.set_cookie(
        'oauth_state',
        cookie_value,
        max_age=600,
        httponly=False,
        secure=False,
        samesite='Lax',
        path='/',
    )
    
    response.set_cookie(
        'test_cookie',
        'works',
        max_age=600,
        httponly=False,
        secure=False,
        samesite='Lax',
        path='/',
    )
    
    return response


@app.route("/callback")
def callback():
    # Get state from signed cookie
    state_cookie = request.cookies.get('oauth_state')
    received_state = request.args.get('state')
    
    # Emergency fallback for cookie issues
    if not state_cookie:
        if received_state and len(received_state) > 20:
            return _handle_oauth_callback(received_state, received_state, emergency=True)
        
        return render_template_string(error_page(
            "State cookie not found. Try using http://127.0.0.1:5000 instead of localhost"
        )), 400
    
    try:
        expected_state = cookie_serializer.loads(state_cookie, max_age=600)
    except BadSignature:
        return render_template_string(error_page("Invalid state signature")), 400
    
    if not received_state or received_state != expected_state:
        return render_template_string(error_page("State mismatch")), 400
    
    return _handle_oauth_callback(expected_state, received_state)


def _handle_oauth_callback(expected_state, received_state, emergency=False):
    """Handle the actual OAuth token exchange"""
    
    # Clear cookies
    response = make_response()
    response.set_cookie('oauth_state', '', expires=0)
    response.set_cookie('test_cookie', '', expires=0)
    
    # Check for OAuth errors
    if "error" in request.args:
        return render_template_string(error_page(f"OAuth error: {request.args['error']}")), 400
    
    code = request.args.get("code")
    if not code:
        return render_template_string(error_page("Authorization code missing")), 400
    
    # Exchange code for token - GitHub requires JSON Accept header
    token_response = requests.post(
        TOKEN_URL,
        headers={"Accept": "application/json"},  # GitHub specific: need this to get JSON instead of form data
        data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    
    if token_response.status_code != 200:
        return render_template_string(error_page(f"Token error: {token_response.text}")), 400
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        error_description = token_data.get("error_description", "Unknown error")
        return render_template_string(error_page(f"OAuth error: {error_description}")), 400
    
    # Fetch user info from GitHub API
    user_response = requests.get(
        USER_API_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",  # GitHub API version
        },
        timeout=30,
    )
    
    if user_response.status_code != 200:
        return render_template_string(error_page(f"User info error: {user_response.text}")), 400
    
    user_data = user_response.json()
    
    # Store user data in session (GitHub has different fields than Google)
    session["user"] = {
        "id": user_data.get("id"),
        "login": user_data.get("login"),  # GitHub username
        "name": user_data.get("name"),    # Display name (can be null)
        "email": user_data.get("email"),  # Public email (can be null)
        "avatar_url": user_data.get("avatar_url"),
        "bio": user_data.get("bio"),
        "public_repos": user_data.get("public_repos", 0),
        "html_url": user_data.get("html_url"),
    }
    
    # Redirect to welcome page
    return redirect(url_for("welcome"))


@app.route("/welcome")
@login_required
def welcome():
    """Simple welcome page after successful login"""
    return render_template_string(
        make_page(WELCOME_PAGE),
        dashboard_url=url_for('dashboard'),
        logout_url=url_for('logout')
    )


@app.route("/dashboard")
@login_required
def dashboard():
    """Detailed dashboard with user info"""
    user = session["user"]
    return render_template_string(
        dashboard_page(
            name=user["name"],
            username=user["login"],
            email=user["email"],
            avatar_url=user["avatar_url"],
            bio=user["bio"],
            public_repos=user["public_repos"],
        )
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.errorhandler(404)
def not_found(error):
    return render_template_string(error_page("Page not found")), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template_string(error_page("Server error")), 500


if __name__ == "__main__":
    print("=" * 50)
    print("🐙 GitHub OAuth 2.0 App Starting")
    print("=" * 50)
    print(f"📍 Open: http://127.0.0.1:5000")
    print(f"🔧 Redirect URI: {REDIRECT_URI}")
    print(f"🔑 Client ID: {CLIENT_ID[:20]}..." if CLIENT_ID else "❌ MISSING!")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
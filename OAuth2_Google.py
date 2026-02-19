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

# OAuth Configuration from environment
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:5000/callback")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Validate configuration
if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET. "
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
    <title>OAuth App</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            background: #4285f4;
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
            box-shadow: 0 8px 20px rgba(66, 133, 244, 0.4);
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
            border: 4px solid #4285f4;
        }}
        .success-icon {{
            font-size: 60px;
            color: #28a745;
            margin-bottom: 20px;
        }}
        .info {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: left;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .info-row:last-child {{ border-bottom: none; }}
        .label {{ color: #666; font-size: 14px; }}
        .value {{ color: #333; font-weight: 600; }}
        .logout {{
            color: #dc3545;
            text-decoration: none;
            font-size: 14px;
            margin-top: 20px;
            display: inline-block;
        }}
        .logout:hover {{ text-decoration: underline; }}
        .error {{
            background: #f8d7da;
            color: #721c24;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
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
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 14px;
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
    <h1>🔐 Welcome</h1>
    <p>Sign in with your Google account to access your personalized dashboard.</p>
    <a href="{{ url_for('login') }}" class="btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="white" style="vertical-align: middle;">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Sign in with Google
    </a>
""")


# Use render_template_string with explicit variables instead of .format()
WELCOME_PAGE = """
    <div class="success-icon">✅</div>
    <h1>Welcome!</h1>
    <h2>You have successfully signed in</h2>
    <p>Your OAuth 2.0 authentication is working correctly.</p>
    <a href="{{ dashboard_url }}" class="btn">View Dashboard</a>
    <br>
    <a href="{{ logout_url }}" class="btn btn-secondary">Sign Out</a>
"""


def dashboard_page(name, email, picture, google_id, verified):
    return make_page(f"""
    <img src="{picture}" alt="Profile" class="profile-img">
    <h1>Hello, {name}!</h1>
    <div class="info">
        <div class="info-row">
            <span class="label">Email</span>
            <span class="value">{email}</span>
        </div>
        <div class="info-row">
            <span class="label">Google ID</span>
            <span class="value">{google_id[:12]}...</span>
        </div>
        <div class="info-row">
            <span class="label">Verified</span>
            <span class="value">{'Yes' if verified else 'No'}</span>
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
    
    # Build authorization URL
    auth_url = (
        f"{GOOGLE_AUTH_URL}"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
        f"&response_type=code"
        f"&state={state}"
        f"&access_type=offline"
        f"&prompt=consent"
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
    
    # Exchange code for tokens
    token_response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    
    if token_response.status_code != 200:
        return render_template_string(error_page(f"Token error: {token_response.text}")), 400
    
    tokens = token_response.json()
    access_token = tokens.get("access_token")
    
    if not access_token:
        return render_template_string(error_page("No access token")), 400
    
    # Get user info
    user_response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    
    if user_response.status_code != 200:
        return render_template_string(error_page(f"User info error: {user_response.text}")), 400
    
    user_data = user_response.json()
    
    # Store in session
    session["user"] = {
        "id": user_data.get("id"),
        "email": user_data.get("email"),
        "name": user_data.get("name", user_data.get("email", "User")),
        "picture": user_data.get("picture", "https://via.placeholder.com/100"),
        "verified_email": user_data.get("verified_email", False),
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
            email=user["email"],
            picture=user["picture"],
            google_id=user["id"],
            verified=user["verified_email"],
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
    print("🚀 OAuth 2.0 App Starting")
    print("=" * 50)
    print(f"📍 Open: http://127.0.0.1:5000")
    print(f"🔧 Redirect URI: {REDIRECT_URI}")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
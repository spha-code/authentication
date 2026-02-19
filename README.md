# Authentication Methods

### The Authorization Code Flow - OAuth 2.0 Authorization Code Grant

1. Authorize → GET /authorize?client_id=...&response_type=code&...
2. Exchange code → POST /token with grant_type=authorization_code
3. Use token → Authorization: Bearer {token}

In detail:
1. **Initiation:** The user clicks login, triggering a redirect to the authorization server (e.g., accounts.google.com) with a specified callback URL.
2. **Consent:** After authenticating and granting permission, the user is redirected back to the callback URL with a temporary authorization code.
3. **Token Exchange:** The application exchanges this code for an access token by sending it directly to the authorization server.
4. **Resource Access:** With the verified access token, the application can now request protected resources from the resource server (e.g., contacts.google.com).

*** The **secret key**, and also the **client id**, are created upon setting up a client in Google, that is the initial setup at our end as the app owners and both are used to identify the user against the authorization server. 

### OAuth 2.0 with Google Authentication

#### OAuth2_Google.py

## Setup

### 1. Install dependencies
```bash

pip install -r requirements.txt

OR

INSTALL MANUALLY:

pip install flask requests python-dotenv itsdangerous

### 2. Get credentials from Google Cloud Console:
#    - Create project → APIs & Services → Credentials → OAuth 2.0 Client ID
#    - Authorized redirect URIs: http://localhost:5000/callback

Main console: https://console.cloud.google.com/

Direct to Credentials page: https://console.cloud.google.com/apis/credentials

Go to https://console.cloud.google.com/
Select/create a project (dropdown at top)
Click "APIs & Services" in the left menu
Click "Credentials"
Click "+ CREATE CREDENTIALS" → "OAuth Client ID"
Configure consent screen --> Get started 
fill app name + email
Application type: "Web application"
Name: webApp
Authorized redirect URIs: Add http://localhost:5000/callback
Click CREATE
Copy the Client ID and Client Secret into your code

### 3. Create environment file
Create a .env file in the project root:

GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
FLASK_SECRET_KEY=your-random-secret-key-here
REDIRECT_URI=http://localhost:5000/callback

Test that everything works with the values in .env
python test_env.py

### 4. .gitignore

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# 4. Run
python OAuth2_Google.py


```

```
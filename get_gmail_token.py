"""
One-time Gmail OAuth2 token generator.

Steps:
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Edit your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs" add:  http://localhost:8080/
4. Save, then run:  python get_gmail_token.py
5. A browser window will open — sign in and approve Gmail access
6. Token saved to credentials/gmail_token.json
"""

import os
import sys
import json
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # allow HTTP for local dev
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
]

CLIENT_SECRET_FILE = "client_secret_677937694195-ka1jn3971g0ps4oc7ohjmtda1uh89io7.apps.googleusercontent.com.json"
TOKEN_PATH = "credentials/gmail_token.json"
REDIRECT_URI = "http://localhost:8080/"


def main():
    os.makedirs("credentials", exist_ok=True)

    # Load client config
    with open(CLIENT_SECRET_FILE) as f:
        client_config = json.load(f)

    # Build flow
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    # Generate authorization URL
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )

    print("\n" + "="*60)
    print("STEP 1: Open this URL in your browser:")
    print("="*60)
    print(f"\n{auth_url}\n")
    print("="*60)
    print("STEP 2: After approving, you will be redirected to")
    print("        http://localhost:8080/?code=...&state=...")
    print("        Copy the FULL redirect URL from your browser address bar.")
    print("="*60)

    redirect_response = input("\nPaste the full redirect URL here: ").strip()

    # Exchange code for token
    flow.fetch_token(authorization_response=redirect_response)
    creds = flow.credentials

    # Save token
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }

    with open(TOKEN_PATH, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"\n✅ Token saved to {TOKEN_PATH}")
    print("   Gmail integration is now active.")
    print("   Restart the backend server to pick it up.")


if __name__ == "__main__":
    main()

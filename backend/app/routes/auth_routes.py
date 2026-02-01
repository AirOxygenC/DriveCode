from flask import Blueprint, jsonify, redirect, request, current_app
import requests
import os

auth_bp = Blueprint('auth', __name__)

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

@auth_bp.route('/github/login', methods=['GET'])
def github_login():
    client_id = os.getenv('GITHUB_CLIENT_ID')
    if not client_id:
        return jsonify({"error": "Missing GITHUB_CLIENT_ID"}), 500
        
    scope = "repo read:user"
    return redirect(f"{GITHUB_AUTH_URL}?client_id={client_id}&scope={scope}")

@auth_bp.route('/github/callback', methods=['GET'])
def github_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Missing code parameter"}), 400
        
    client_id = os.getenv('GITHUB_CLIENT_ID')
    client_secret = os.getenv('GITHUB_CLIENT_SECRET') or os.getenv('GITHUB_SECRET_ID')
    
    if not client_id or not client_secret:
        return jsonify({"error": "Missing GitHub credentials"}), 500

    # Exchange code for access token
    response = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code
        }
    )
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to exchange code for token"}), 500
        
    data = response.json()
    access_token = data.get("access_token")
    
    if not access_token:
        # Handle case where GitHub returns an error in the JSON
        return jsonify(data), 400
        
    # In a real app, we would store this in a secure HTTP-only cookie or server-side session.
    # For this MVP, we'll redirect back to the frontend with the token in the URL fragment.
    # Since we are "Ship-from-Car", simplicity is key.
    
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    return redirect(f"{frontend_url}?token={access_token}")

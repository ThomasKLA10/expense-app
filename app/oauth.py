from flask import current_app, url_for, flash
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import os
from .extensions import db
from .models import User
from flask_login import login_user

# Allow OAuth over HTTP for development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class GoogleOAuth:
    def __init__(self, app):
        self.client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])
        
    def get_google_provider_cfg(self):
        try:
            response = requests.get(
                'https://accounts.google.com/.well-known/openid-configuration'
            )
            return response.json()
        except Exception as e:
            print(f"Error fetching Google configuration: {e}")
            return None

    def get_login_url(self):
        google_provider_cfg = self.get_google_provider_cfg()
        if not google_provider_cfg:
            flash('Error connecting to Google', 'error')
            return None
            
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        request_uri = self.client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=url_for('auth.callback', _external=True),
            scope=['openid', 'email', 'profile'],
        )
        return request_uri

    def handle_callback(self, request_url):
        try:
            google_provider_cfg = self.get_google_provider_cfg()
            if not google_provider_cfg:
                flash('Error connecting to Google', 'error')
                return None

            # Print request URL for debugging
            print(f"Request URL: {request_url}")

            code = request_url.split('?')[1].split('code=')[1].split('&')[0]
            print(f"Extracted code: {code}")
            
            # Get tokens
            token_endpoint = google_provider_cfg["token_endpoint"]
            token_url, headers, body = self.client.prepare_token_request(
                token_endpoint,
                authorization_response=request_url,
                redirect_url=url_for('auth.callback', _external=True),
                code=code
            )
            
            # Print token request details for debugging
            print(f"Token URL: {token_url}")
            print(f"Token Headers: {headers}")
            print(f"Token Body: {body}")
            
            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(current_app.config['GOOGLE_CLIENT_ID'], 
                      current_app.config['GOOGLE_CLIENT_SECRET']),
            )

            # Print token response for debugging
            print(f"Token Response Status: {token_response.status_code}")
            print(f"Token Response: {token_response.text}")

            if token_response.status_code != 200:
                flash('Failed to get token from Google', 'error')
                return None

            self.client.parse_request_body_response(token_response.text)
            
            # Get user info
            userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
            uri, headers, body = self.client.add_token(userinfo_endpoint)
            userinfo_response = requests.get(uri, headers=headers, data=body)
            
            # Print user info response for debugging
            print(f"User Info Response Status: {userinfo_response.status_code}")
            print(f"User Info Response: {userinfo_response.text}")

            if userinfo_response.status_code != 200:
                flash('Failed to get user info from Google', 'error')
                return None

            if userinfo_response.json().get("email_verified"):
                users_email = userinfo_response.json()["email"]
                users_name = userinfo_response.json()["name"]
                
                # Check if email is from bakkenbaeck.com domain
                if not users_email.endswith('@bakkenbaeck.no'):
                    flash('Only @bakkenbaeck.no email addresses are allowed.', 'error')
                    return None
                
                # Create or update user
                user = User.query.filter_by(email=users_email).first()
                if not user:
                    user = User(
                        email=users_email,
                        name=users_name
                    )
                    db.session.add(user)
                    db.session.commit()
                
                login_user(user)
                return user
            else:
                return None
            
        except Exception as e:
            print(f"Error in handle_callback: {str(e)}")
            import traceback
            traceback.print_exc()
            current_app.logger.error(f"OAuth error: {str(e)}\n{traceback.format_exc()}")
            return None

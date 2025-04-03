from flask import Blueprint, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .oauth import GoogleOAuth

auth = Blueprint('auth', __name__)
oauth = None

@auth.record
def record_oauth(state):
    global oauth
    oauth = GoogleOAuth(state.app)

@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if oauth is None:
        flash('Authentication service not available.', 'error')
        return redirect(url_for('main.index'))
    
    return redirect(oauth.get_login_url())

@auth.route('/login/callback')
def callback():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
            
        user = oauth.handle_callback(request.url)
        if user:
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        
        return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Error during authentication: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from . import main
from ..models import Receipt
from datetime import datetime, timezone

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    page_active = request.args.get('page_active', 1, type=int)
    page_archived = request.args.get('page_archived', 1, type=int)
    per_page = 6
    
    # Check for status updates since last visit
    status_updates = []
    if current_user.last_checked:
        status_updates = Receipt.query.filter(
            Receipt.user_id == current_user.id,
            Receipt.updated_at > current_user.last_checked,
            Receipt.status.in_(['approved', 'rejected'])
        ).all()
    
    # Update last_checked timestamp
    current_user.last_checked = datetime.now(timezone.utc)
    from .. import db
    db.session.commit()
    
    # Get paginated receipts
    active_receipts = Receipt.query.filter_by(
        user_id=current_user.id,
        archived=False
    ).order_by(Receipt.date_submitted.desc()).paginate(
        page=page_active,
        per_page=per_page,
        error_out=False
    )
    
    archived_receipts = Receipt.query.filter_by(
        user_id=current_user.id,
        archived=True
    ).order_by(Receipt.date_submitted.desc()).paginate(
        page=page_archived,
        per_page=per_page,
        error_out=False
    )
    
    return render_template('dashboard.html',
                         active_receipts=active_receipts,
                         archived_receipts=archived_receipts,
                         status_updates=status_updates)

@main.route('/office/<location>')
@login_required
def office(location):
    receipts = Receipt.query.filter_by(office=location).order_by(Receipt.date_submitted.desc()).all()
    return render_template('office.html', receipts=receipts, location=location) 
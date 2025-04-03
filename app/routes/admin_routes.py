from flask import render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from functools import wraps
from . import admin
from .. import db
from ..models import Receipt, User
from datetime import datetime, timezone

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin')
@admin_required
def admin_dashboard():
    page_pending = request.args.get('page_pending', 1, type=int)
    page_processed = request.args.get('page_processed', 1, type=int)
    search = request.args.get('search', '')
    per_page = 6

    # Get pending receipts
    pending_receipts = Receipt.query.filter_by(
        status='pending'
    ).order_by(Receipt.date_submitted.desc()).paginate(
        page=page_pending,
        per_page=per_page,
        error_out=False
    )

    # Get processed receipts with search
    processed_query = Receipt.query.join(User).filter(
        Receipt.status.in_(['approved', 'rejected'])
    )
    
    if search:
        processed_query = processed_query.filter(
            User.name.ilike(f'%{search}%')
        )
    
    processed_receipts = processed_query.order_by(
        Receipt.date_submitted.desc()
    ).paginate(
        page=page_processed,
        per_page=per_page,
        error_out=False
    )

    return render_template('admin/admin_dashboard.html',
                         pending_receipts=pending_receipts,
                         processed_receipts=processed_receipts)

@admin.route('/admin/receipt/<int:id>/review', methods=['GET', 'POST'])
@login_required
def admin_receipt_review(id):
    if not current_user.is_admin:
        abort(403)
    
    receipt = Receipt.query.get_or_404(id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action in ['approve', 'reject']:
            receipt.status = action + 'd'  # 'approved' or 'rejected'
            receipt.archived = True
            receipt.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for('admin.admin_dashboard'))
    
    return render_template('admin/receipt_review.html', receipt=receipt)

@admin.route('/admin/receipt/<int:id>/<action>', methods=['POST'])
@login_required
@admin_required
def admin_receipt_action(id, action):
    receipt = Receipt.query.get_or_404(id)
    
    if action in ['approve', 'reject']:
        # Get reviewer notes from form
        reviewer_notes = request.form.get('reviewer_notes', '')
        receipt.reviewer_notes = reviewer_notes
        
        receipt.status = 'approved' if action == 'approve' else 'rejected'
        receipt.archived = True
        receipt.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Send notification to user - using the correct function name
        from ..utils.email import send_receipt_status_notification
        send_receipt_status_notification(receipt)
        
        return redirect(url_for('admin.admin_dashboard'))

@admin.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.name).all()
    return render_template('admin/users.html', users=users, current_user=current_user)

@admin.route('/admin/users/toggle_reviewer/<int:user_id>', methods=['POST'])
@admin_required
def toggle_reviewer(user_id):
    user = User.query.get_or_404(user_id)
    user.is_reviewer = not user.is_reviewer
    db.session.commit()
    return redirect(url_for('admin.admin_users'))

@admin.route('/admin/users/toggle_admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        return redirect(url_for('admin.admin_users'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    return redirect(url_for('admin.admin_users'))

@admin.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        return redirect(url_for('admin.admin_users'))
    
    user = User.query.get_or_404(user_id)
    # Delete all associated receipts first
    Receipt.query.filter_by(user_id=user_id).delete()
    # Then delete the user
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin.admin_users'))

@admin.route('/create-test-user')
@admin_required
def create_test_user():
    test_user = User(
        email='test@bakkenbaeck.no',
        name='Test User',
        is_admin=False,
        is_reviewer=False
    )
    db.session.add(test_user)
    db.session.commit()
    return redirect(url_for('admin.admin_users')) 
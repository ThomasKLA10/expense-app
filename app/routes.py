from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from . import db
from .models import Receipt
from flask_login import login_required, current_user
import importlib

main = Blueprint('main', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    receipts = Receipt.query.filter_by(user_id=current_user.id)\
                          .order_by(Receipt.date_submitted.desc())\
                          .all()
    return render_template('dashboard.html', receipts=receipts)

@main.route('/office/<location>')
@login_required
def office(location):
    receipts = Receipt.query.filter_by(
        office=location,
        user_id=current_user.id
    ).order_by(Receipt.date_submitted.desc()).all()
    return render_template('office.html', receipts=receipts, location=location)

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            file = request.files['receipt']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file
                file.save(filepath)
                
                # Create receipt record
                receipt = Receipt(
                    file_path=filepath,
                    user_id=current_user.id,
                    amount=float(request.form.get('amount', 0)),
                    currency=request.form.get('currency', 'EUR'),
                    category=request.form.get('category', 'other'),
                    date_submitted=datetime.utcnow(),
                    status='pending',
                    purpose=request.form.get('purpose', '')
                )
                
                db.session.add(receipt)
                db.session.commit()
                
                flash('Receipt uploaded successfully!', 'success')
                return redirect(url_for('main.dashboard'))
                
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
            return redirect(request.url)
            
    return render_template('upload.html')

@main.route('/receipt/<int:receipt_id>')
@login_required
def view_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    if receipt.user_id != current_user.id:
        abort(403)
    return render_template('view_receipt.html', receipt=receipt)

@main.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    try:
        return send_from_directory(
            os.path.join(current_app.root_path, 'uploads'),
            filename
        )
    except Exception:
        abort(404)
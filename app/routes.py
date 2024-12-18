from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from . import db
from .models import Receipt
from flask_login import login_required, current_user
import importlib
from .ocr import ReceiptScanner
import logging

logger = logging.getLogger(__name__)

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
            logger.info(f"Received file: {file.filename}")
            
            if file and allowed_file(file.filename):
                # Try OCR first
                scanner = ReceiptScanner()
                logger.info("Starting OCR scan...")
                ocr_result = scanner.scan_receipt(file)
                logger.info(f"OCR Result: {ocr_result}")
                
                # Reset file pointer for saving
                file.seek(0)
                
                # Save the file
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                logger.info(f"File saved to: {filepath}")
                
                # Get amount from OCR or form
                amount = float(request.form.get('amount', 0))
                logger.info(f"Form amount: {amount}")
                
                if ocr_result and ocr_result.get('amount') and amount == 0:
                    amount = ocr_result['amount']
                    logger.info(f"Using OCR amount: {amount}")
                
                # Create receipt record
                receipt = Receipt(
                    file_path=filepath,
                    user_id=current_user.id,
                    amount=amount,
                    currency=request.form.get('currency', 'EUR'),
                    category=request.form.get('category', 'other'),
                    date_submitted=datetime.utcnow(),
                    status='pending',
                    office='oslo',
                    purpose=request.form.get('purpose', '')
                )
                
                db.session.add(receipt)
                db.session.commit()
                logger.info("Receipt saved to database")
                
                if ocr_result:
                    flash('Receipt uploaded successfully with OCR!', 'success')
                else:
                    flash('Receipt uploaded successfully!', 'success')
                return redirect(url_for('main.dashboard'))
                
        except Exception as e:
            logger.error(f"Upload Error: {str(e)}", exc_info=True)
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

@main.route('/ocr', methods=['POST'])
@login_required
def process_ocr():
    try:
        file = request.files['receipt']
        if file and allowed_file(file.filename):
            scanner = ReceiptScanner()
            result = scanner.scan_receipt(file)
            if result:
                return jsonify({
                    'amount': result.get('amount'),
                    'subtotal': result.get('subtotal'),
                    'tax': result.get('tax'),
                    'date': result.get('date'),
                    'merchant': result.get('merchant'),
                    'currency': result.get('currency'),
                    'success': True
                })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False})
    
    return jsonify({'success': False})
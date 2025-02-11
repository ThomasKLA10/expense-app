from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from . import db
from .models import Receipt, User
from flask_login import login_required, current_user
import importlib
from .ocr import ReceiptScanner
import logging
from .pdf_generator import ExpenseReportGenerator
from functools import wraps

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

@main.route('/submit_expense', methods=['POST'])
@login_required
def submit_expense():
    try:
        # Get form data
        dates = request.form.getlist('date[]')
        amounts = request.form.getlist('amount[]')
        descriptions = request.form.getlist('description[]')
        expense_type = request.form.get('expense-type', 'other')
        receipt_files = request.files.getlist('receipt[]')
        
        # Prepare expenses data for PDF
        expenses = []
        for i in range(len(dates)):
            expenses.append({
                'date': dates[i],
                'description': descriptions[i],
                'amount': float(amounts[i]),  # This is already in EUR
                'currency': 'EUR'  # Since we're storing the EUR value
            })
        
        # Get travel details if applicable
        travel_details = None
        if expense_type == 'travel':
            travel_details = {
                'purpose': request.form.get('purpose'),
                'from': request.form.get('from'),
                'to': request.form.get('to'),
                'departure': request.form.get('departure'),
                'return': request.form.get('return')
            }
        
        # Get comment for other expenses
        comment = request.form.get('comment') if expense_type == 'other' else None
        
        # Generate PDF
        generator = ExpenseReportGenerator(current_user.name, expense_type)
        summary_pdf_path, report_id = generator.generate_report(
            expenses=expenses,
            travel_details=travel_details,
            comment=comment
        )
        
        # Save receipt files and merge with summary
        receipt_paths = []
        for file in receipt_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                receipt_paths.append(filepath)
        
        # Merge summary with receipts
        final_pdf_path = ExpenseReportGenerator.merge_with_receipts(summary_pdf_path, receipt_paths)
        
        # Calculate total in EUR (already converted in frontend)
        total_eur = sum(float(amount) for amount in amounts)
        
        # Create receipt record
        receipt = Receipt(
            user_id=current_user.id,
            amount=total_eur,
            currency='EUR',
            category=expense_type,
            purpose=descriptions[0] if descriptions else 'Multiple expenses',
            status='pending',
            file_path_db=final_pdf_path,
            comment=comment
        )
        
        # Add travel details if applicable
        if expense_type == 'travel':
            receipt.travel_from = request.form.get('from')
            receipt.travel_to = request.form.get('to')
            receipt.departure_date = datetime.strptime(request.form.get('departure'), '%Y-%m-%d').date() if request.form.get('departure') else None
            receipt.return_date = datetime.strptime(request.form.get('return'), '%Y-%m-%d').date() if request.form.get('return') else None
        
        db.session.add(receipt)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'redirect': url_for('dashboard')
        })
        
    except Exception as e:
        print(f"Error in submit_expense: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@main.route('/admin/users/toggle_reviewer/<int:user_id>', methods=['POST'])
@admin_required
def toggle_reviewer(user_id):
    user = User.query.get_or_404(user_id)
    user.is_reviewer = not user.is_reviewer
    db.session.commit()
    flash(f'{"Added" if user.is_reviewer else "Removed"} reviewer role for {user.name}', 'success')
    return redirect(url_for('main.admin_users'))

@main.route('/admin/users/toggle_admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        flash('You cannot modify your own admin status', 'error')
        return redirect(url_for('main.admin_users'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'{"Added" if user.is_admin else "Removed"} admin role for {user.name}', 'success')
    return redirect(url_for('main.admin_users'))
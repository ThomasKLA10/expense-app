from flask import render_template, request, flash, redirect, url_for, current_app, abort, send_from_directory, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timezone, timedelta
from . import receipt
from .. import db
from ..models import Receipt
from ..pdf_generator import ExpenseReportGenerator
from pathlib import Path
from ..utils.email import notify_reviewers_of_new_receipt
from functools import wraps

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@receipt.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            expense_type = request.form.get('type')
            
            # Get all expense data
            expenses = []
            index = 0
            while f'description{index}' in request.form:
                receipt_file = request.files.get(f'receipt{index}')
                if not receipt_file:
                    return jsonify({'success': False, 'error': 'Missing receipt file'})
                
                # Save receipt file
                filename = secure_filename(receipt_file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                receipt_file.save(file_path)
                
                expenses.append({
                    'description': request.form.get(f'description{index}'),
                    'amount': float(request.form.get(f'amount{index}', 0)),
                    'amount_foreign': float(request.form.get(f'amount_foreign{index}', 0) or 0),
                    'currency': request.form.get(f'currency{index}'),
                    'type': request.form.get(f'type{index}'),
                    'file_path': file_path
                })
                index += 1
            
            # Create receipt records
            for expense in expenses:
                receipt = Receipt(
                    user_id=current_user.id,
                    description=expense['description'],
                    amount=expense['amount'],
                    amount_foreign=expense['amount_foreign'],
                    currency=expense['currency'],
                    category=expense['type'],
                    expense_type=expense['type'],
                    file_path=expense['file_path'],
                    status='pending'
                )
                
                if expense['type'] == 'travel':
                    receipt.travel_purpose = request.form.get('purpose')
                    receipt.travel_from = request.form.get('from')
                    receipt.travel_to = request.form.get('to')
                    receipt.travel_departure = request.form.get('departure')
                    receipt.travel_return = request.form.get('return')
                
                db.session.add(receipt)
            
            db.session.commit()

            # After saving the receipt to the database:
            from app.utils.email import notify_reviewers_of_new_receipt
            notify_reviewers_of_new_receipt(receipt)

            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    return render_template('upload.html')

@receipt.route('/receipt/<int:receipt_id>')
@login_required
def view_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    if receipt.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    return render_template('view_receipt.html', receipt=receipt)

@receipt.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    print(f"Accessing file: {filename}")
    print(f"Upload folder: {current_app.config['UPLOAD_FOLDER']}")
    print(f"Full path: {os.path.join(current_app.config['UPLOAD_FOLDER'], filename)}")
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return f"Error: {str(e)}", 500

@receipt.route('/receipt/<int:receipt_id>/archive', methods=['POST'])
@login_required
def archive_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    if receipt.user_id != current_user.id:
        abort(403)
    
    receipt.archived = True
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@receipt.route('/receipt/<int:id>/edit', methods=['POST'])
@login_required
def edit_receipt(id):
    receipt = Receipt.query.get_or_404(id)
    if receipt.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Update receipt fields
    receipt.amount = request.form.get('amount')
    receipt.category = request.form.get('category')
    receipt.purpose = request.form.get('purpose')
    receipt.currency = request.form.get('currency')
    receipt.office = request.form.get('office')
    # ... other fields ...
    
    # Update the updated_at timestamp
    receipt.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@receipt.route('/receipt/new', methods=['POST'])
@login_required
def new_receipt():
    # Create new receipt
    receipt = Receipt(
        user_id=current_user.id,
        amount=request.form.get('amount'),
        category=request.form.get('category'),
        purpose=request.form.get('purpose'),
        currency=request.form.get('currency'),
        office=request.form.get('office'),
        date_submitted=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)  # Set initial updated_at
    )
    
    db.session.add(receipt)
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@receipt.route('/receipt/<int:receipt_id>/file')
@login_required
def view_receipt_file(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    
    # Check if user has permission to view this receipt
    if not current_user.is_admin and receipt.user_id != current_user.id:
        abort(403)
    
    # Use pathlib for safer file path handling
    if not receipt.file_path_db:
        abort(404)
    
    # Convert string path to Path object
    file_path = Path(receipt.file_path_db)
    
    # Check if file exists
    if not file_path.exists():
        flash('Receipt file not found', 'error')
        return redirect(url_for('receipt.view_receipt', receipt_id=receipt_id))
    
    # Send the file - pathlib objects work directly with send_file
    return send_file(
        file_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'receipt_{receipt_id}.pdf'
    )

@receipt.route('/submit_expense', methods=['POST'])
@login_required
def submit_expense():
    try:
        # Get German time by adding 1 hour to UTC
        current_time = datetime.utcnow() + timedelta(hours=1)
        
        # Get form data
        dates = request.form.getlist('date[]')
        amounts = request.form.getlist('amount[]')
        descriptions = request.form.getlist('description[]')
        expense_type = request.form.get('expense-type', 'other')
        receipt_files = request.files.getlist('receipt[]')
        
        # Prepare expense data for PDF
        expenses = []
        for i in range(len(dates)):
            expense = {
                'date': dates[i],
                'description': descriptions[i],
                'amount': float(amounts[i]),  # EUR amount
                'original_currency': request.form.getlist('currency[]')[i],  # Original currency
                'original_amount': float(request.form.getlist('original_amount[]')[i])  # Original amount
            }
            expenses.append(expense)
        
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
        
        # Get travel details if it's a travel expense
        travel_purpose = request.form.get('purpose') if expense_type == 'travel' else None
        
        receipt = Receipt(
            user_id=current_user.id,
            amount=total_eur,
            currency='EUR',
            category=expense_type,
            status='pending',
            file_path_db=final_pdf_path,
            comment=travel_purpose if expense_type == 'travel' else request.form.get('comment'),  # Use purpose as comment for travel
            date_submitted=current_time,
            updated_at=current_time
        )
        
        if expense_type == 'travel':
            receipt.travel_purpose = travel_purpose
            receipt.travel_from = request.form.get('from')
            receipt.travel_to = request.form.get('to')
            receipt.departure_date = datetime.strptime(request.form.get('departure'), '%Y-%m-%d').date() if request.form.get('departure') else None
            receipt.return_date = datetime.strptime(request.form.get('return'), '%Y-%m-%d').date() if request.form.get('return') else None
        
        db.session.add(receipt)
        db.session.commit()
        
        # Add this block to notify reviewers
        from app.utils.email import notify_reviewers_of_new_receipt
        current_app.logger.info("Attempting to notify reviewers about new receipt")
        # Get the last receipt created for this user
        latest_receipt = Receipt.query.filter_by(user_id=current_user.id).order_by(Receipt.id.desc()).first()
        if latest_receipt:
            notify_reviewers_of_new_receipt(latest_receipt)
            current_app.logger.info(f"Notification sent for receipt {latest_receipt.id}")
        
        return jsonify({
            'success': True,
            'redirect': url_for('main.dashboard')
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in submit_expense: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}) 
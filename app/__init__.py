import os
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, jsonify, send_file
from flask_login import login_required, current_user
from .extensions import db, migrate, login_manager
from .config import Config
from .models import Receipt, User
from .ocr import ReceiptScanner
from werkzeug.utils import secure_filename
from functools import wraps
from flask import abort
from datetime import datetime, timezone, timedelta
import logging
from .pdf_generator import ExpenseReportGenerator
from PIL import Image
import io

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Create uploads directory with absolute path
    uploads_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = uploads_dir
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')

    @app.route('/dashboard')
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

    @app.route('/upload', methods=['GET', 'POST'])
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
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
                return jsonify({'success': True})
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)})
        
        return render_template('upload.html')

    @app.route('/receipt/<int:receipt_id>')
    @login_required
    def view_receipt(receipt_id):
        receipt = Receipt.query.get_or_404(receipt_id)
        if receipt.user_id != current_user.id:
            return redirect(url_for('dashboard'))
        return render_template('receipt.html', receipt=receipt)

    @app.route('/uploads/<filename>')
    @login_required
    def uploaded_file(filename):
        print(f"Accessing file: {filename}")
        print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
        print(f"Full path: {os.path.join(app.config['UPLOAD_FOLDER'], filename)}")
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        except Exception as e:
            print(f"Error serving file: {str(e)}")
            return f"Error: {str(e)}", 500

    @app.route('/office/<location>')
    @login_required
    def office(location):
        receipts = Receipt.query.filter_by(office=location).order_by(Receipt.date_submitted.desc()).all()
        return render_template('office.html', receipts=receipts, location=location)

    @app.route('/ocr', methods=['POST'])
    @login_required
    def ocr():
        if 'receipt' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['receipt']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        try:
            scanner = ReceiptScanner()
            result = scanner.scan_receipt(file)
            print("OCR Result:", result)
            return jsonify({
                'success': True,
                'amount': result.get('amount'),
                'date': result.get('date'),
                'merchant': result.get('merchant'),
                'currency': result.get('currency'),
                'subtotal': result.get('subtotal'),
                'tax': result.get('tax')
            })
        except Exception as e:
            print("OCR Error:", str(e))
            return jsonify({'error': str(e)}), 500

    @app.route('/admin')
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

    @app.route('/receipt/<int:receipt_id>/archive', methods=['POST'])
    @login_required
    def archive_receipt(receipt_id):
        receipt = Receipt.query.get_or_404(receipt_id)
        if receipt.user_id != current_user.id:
            abort(403)
        
        receipt.archived = True
        db.session.commit()
        return redirect(url_for('dashboard'))

    @app.route('/admin/receipt/<int:id>/review', methods=['GET', 'POST'])
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
                return redirect(url_for('admin_dashboard'))
        
        return render_template('admin/receipt_review.html', receipt=receipt)

    @app.route('/admin/receipt/<int:id>/<action>')
    @login_required
    def admin_receipt_action(id, action):
        if not current_user.is_admin:
            abort(403)
        
        receipt = Receipt.query.get_or_404(id)
        
        if action in ['approve', 'reject']:
            receipt.status = 'approved' if action == 'approve' else 'rejected'
            receipt.archived = True
            receipt.updated_at = datetime.now(timezone.utc)
            db.session.commit()
        
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/users')
    @admin_required
    def admin_users():
        users = User.query.order_by(User.name).all()
        return render_template('admin/users.html', users=users, current_user=current_user)

    @app.route('/admin/users/toggle_reviewer/<int:user_id>', methods=['POST'])
    @admin_required
    def toggle_reviewer(user_id):
        user = User.query.get_or_404(user_id)
        user.is_reviewer = not user.is_reviewer
        db.session.commit()
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/toggle_admin/<int:user_id>', methods=['POST'])
    @admin_required
    def toggle_admin(user_id):
        if user_id == current_user.id:
            return redirect(url_for('admin_users'))
        
        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
    @admin_required
    def delete_user(user_id):
        if user_id == current_user.id:
            return redirect(url_for('admin_users'))
        
        user = User.query.get_or_404(user_id)
        # Delete all associated receipts first
        Receipt.query.filter_by(user_id=user_id).delete()
        # Then delete the user
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('admin_users'))

    @app.route('/receipt/<int:id>/edit', methods=['POST'])
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
        return redirect(url_for('dashboard'))

    @app.route('/receipt/new', methods=['POST'])
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
        return redirect(url_for('dashboard'))

    @app.route('/process_receipt', methods=['POST'])
    def process_receipt():
        print("Receipt processing endpoint hit")  # Debug print
        try:
            if 'file' not in request.files:
                print("No file in request")  # Debug print
                return jsonify({'error': 'No file provided'})
            
            file = request.files['file']
            if file.filename == '':
                print("No filename")  # Debug print
                return jsonify({'error': 'No file selected'})
            
            if file and allowed_file(file.filename):
                print(f"Processing file: {file.filename}")  # Debug print
                
                # Save file temporarily
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + secure_filename(file.filename))
                file.save(temp_path)
                
                try:
                    # Process the receipt
                    scanner = ReceiptScanner()
                    results = scanner.process_receipt(temp_path)
                    print(f"OCR Results: {results}")  # Debug print
                    
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    return jsonify(results)
                    
                except Exception as e:
                    print(f"Error processing receipt: {str(e)}")  # Debug print
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return jsonify({'error': str(e)})
                
            return jsonify({'error': 'Invalid file type'})
            
        except Exception as e:
            print(f"Server error: {str(e)}")  # Debug print
            return jsonify({'error': 'Server error occurred'})

    @app.route('/submit_expense', methods=['POST'])
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
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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

    @app.route('/receipt/<int:receipt_id>/file')
    @login_required
    def view_receipt_file(receipt_id):
        receipt = Receipt.query.get_or_404(receipt_id)
        
        # Check if user has permission to view this receipt
        if receipt.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        
        # Convert relative path to absolute path
        base_dir = os.path.abspath(os.path.dirname(__file__))
        absolute_path = os.path.join(base_dir, receipt.file_path_db)
        
        # Check if file exists
        if not receipt.file_path_db or not os.path.exists(absolute_path):
            abort(404)
        
        # Send the file
        return send_file(
            absolute_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f'receipt_{receipt_id}.pdf'
        )

    @app.route('/create-test-user')
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
        return redirect(url_for('admin_users'))

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
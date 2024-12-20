import os
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_login import login_required, current_user
from .extensions import db, migrate, login_manager
from .config import Config
from .models import Receipt, User
from .ocr import ReceiptScanner
from werkzeug.utils import secure_filename
from functools import wraps
from flask import abort

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
        receipts = Receipt.query.filter_by(user_id=current_user.id).order_by(Receipt.date_submitted.desc()).all()
        return render_template('dashboard.html', receipts=receipts)

    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        if request.method == 'POST':
            if 'receipt' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['receipt']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)

            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                receipt = Receipt(
                    amount=float(request.form['amount']),
                    currency=request.form['currency'],
                    category=request.form['category'],
                    file_path_db=filename,
                    user_id=current_user.id,
                    office=request.form['office']
                )
                
                if request.form['category'] == 'travel':
                    receipt.purpose = request.form.get('purpose')
                    receipt.travel_from = request.form.get('travel_from')
                    receipt.travel_to = request.form.get('travel_to')
                    receipt.departure_date = request.form.get('departure_date')
                    receipt.return_date = request.form.get('return_date')
                
                db.session.add(receipt)
                db.session.commit()
                
                flash('Receipt uploaded successfully!', 'success')
                return redirect(url_for('dashboard'))
        
        return render_template('upload.html')

    @app.route('/receipt/<int:receipt_id>')
    @login_required
    def view_receipt(receipt_id):
        receipt = Receipt.query.get_or_404(receipt_id)
        if receipt.user_id != current_user.id:
            flash('Unauthorized access', 'error')
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
        receipts = Receipt.query.order_by(Receipt.date_submitted.desc()).all()
        return render_template('admin/admin_dashboard.html', receipts=receipts)

    @app.route('/admin/receipt/<int:receipt_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_receipt(receipt_id):
        receipt = Receipt.query.get_or_404(receipt_id)
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'approve':
                receipt.status = 'approved'
                flash('Receipt approved', 'success')
            elif action == 'reject':
                receipt.status = 'rejected'
                flash('Receipt rejected', 'success')
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        return render_template('admin/receipt_review.html', receipt=receipt)

    @app.route('/admin/users')
    @admin_required
    def admin_users():
        users = User.query.order_by(User.name).all()
        return render_template('admin/users.html', users=users, current_user=current_user)

    @app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
    @admin_required
    def toggle_admin(user_id):
        if current_user.id == user_id:
            flash('You cannot modify your own admin status.', 'error')
            return redirect(url_for('admin_users'))
        
        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()
        
        flash(f'{"Removed admin privileges from" if not user.is_admin else "Granted admin privileges to"} {user.name}.', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/receipt/<int:receipt_id>/archive', methods=['POST'])
    @login_required
    def archive_receipt(receipt_id):
        receipt = Receipt.query.get_or_404(receipt_id)
        if receipt.user_id != current_user.id:
            abort(403)
        
        receipt.archived = True
        db.session.commit()
        
        flash('Receipt archived successfully.', 'success')
        return redirect(url_for('dashboard'))

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
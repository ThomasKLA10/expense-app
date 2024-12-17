from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from . import db
from .models import Receipt

main = Blueprint('main', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/office/<location>')
def office(location):
    receipts = Receipt.query.filter_by(office=location).order_by(Receipt.date_submitted.desc()).all()
    return render_template('office.html', location=location, receipts=receipts)

@main.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        try:
            # Get form data
            amount = float(request.form['amount'].replace(',', ''))
            currency = request.form['currency']
            category = request.form['category']
            
            # Get travel-specific data only if category is travel
            travel_data = {}
            if category == 'travel':
                travel_data = {
                    'purpose': request.form.get('purpose'),
                    'travel_from': request.form.get('travel_from'),
                    'travel_to': request.form.get('travel_to'),
                    'departure_date': datetime.strptime(request.form.get('departure_date'), '%Y-%m-%d').date() if request.form.get('departure_date') else None,
                    'return_date': datetime.strptime(request.form.get('return_date'), '%Y-%m-%d').date() if request.form.get('return_date') else None
                }
            
            # Handle file upload
            if 'receipt' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(request.url)
            
            file = request.files['receipt']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + secure_filename(file.filename)
                
                # Save file
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                
                # Create receipt record
                receipt = Receipt(
                    amount=amount,
                    currency=currency,
                    category=category,
                    file_path=filename,
                    office=request.args.get('office', 'bonn'),
                    **travel_data  # Add travel data if present
                )
                
                db.session.add(receipt)
                db.session.commit()
                
                flash('Receipt uploaded successfully!', 'success')
                return redirect(url_for('main.office', location=receipt.office))
            
            flash('Invalid file type', 'error')
            return redirect(request.url)
            
        except Exception as e:
            flash(f'Error uploading receipt: {str(e)}', 'error')
            return redirect(request.url)
            
    return render_template('upload.html')

@main.route('/receipt/<int:receipt_id>')
def view_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    return render_template('receipt.html', receipt=receipt)
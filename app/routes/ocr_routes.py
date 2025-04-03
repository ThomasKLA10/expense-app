from flask import request, jsonify, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
import time
from functools import wraps
from . import main
from ..ocr import ReceiptScanner

# Simple in-memory rate limiting
request_history = {}

def rate_limit(limit=10, per=60):
    """Basic rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get client IP
            ip = request.remote_addr
            now = time.time()
            
            # Initialize or clean history
            if ip not in request_history:
                request_history[ip] = []
            request_history[ip] = [t for t in request_history[ip] if now - t < per]
            
            # Check limit
            if len(request_history[ip]) >= limit:
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            # Add request
            request_history[ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/ocr', methods=['POST'])
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

@main.route('/process_receipt', methods=['POST'])
@rate_limit(10, 60)  # 10 requests per minute
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
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_' + secure_filename(file.filename))
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
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import time
from functools import wraps
from . import main
from ..ocr import ReceiptScanner
from datetime import datetime, timedelta
import threading

# Better rate limiting with automatic cleanup
class RateLimiter:
    def __init__(self, limit=10, period=60, cleanup_interval=300):
        self.limit = limit  # Number of requests allowed
        self.period = period  # Time period in seconds
        self.request_logs = {}  # identifier -> list of timestamps
        self.lock = threading.RLock()  # Thread-safe operations
        self.last_cleanup = datetime.now()
        self.cleanup_interval = cleanup_interval  # Cleanup every 5 minutes by default
    
    def is_rate_limited(self, identifier):
        with self.lock:
            # Perform cleanup if needed
            self._cleanup_if_needed()
            
            # Get current time
            now = datetime.now()
            
            # Initialize or get existing log for this identifier
            if identifier not in self.request_logs:
                self.request_logs[identifier] = []
            
            # Remove timestamps older than the period
            cutoff = now - timedelta(seconds=self.period)
            self.request_logs[identifier] = [t for t in self.request_logs[identifier] if t > cutoff]
            
            # Check if limit is exceeded
            if len(self.request_logs[identifier]) >= self.limit:
                return True
            
            # Add current timestamp and allow request
            self.request_logs[identifier].append(now)
            return False
    
    def _cleanup_if_needed(self):
        """Periodically clean up old entries to prevent memory leaks"""
        now = datetime.now()
        if (now - self.last_cleanup).total_seconds() > self.cleanup_interval:
            cutoff = now - timedelta(seconds=self.period)
            # Clean up all identifiers with timestamps
            for identifier in list(self.request_logs.keys()):
                self.request_logs[identifier] = [t for t in self.request_logs[identifier] if t > cutoff]
                # Remove empty lists to save memory
                if not self.request_logs[identifier]:
                    del self.request_logs[identifier]
            self.last_cleanup = now

# Create a global rate limiter instance
rate_limiter = RateLimiter(limit=15, period=60)  # Increased limit for company usage

def rate_limit(f):
    """Rate limiting decorator using user ID for authenticated users and IP for others"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Use user ID for authenticated users, IP for others
        if current_user.is_authenticated:
            identifier = f"user:{current_user.id}"
        else:
            identifier = f"ip:{request.remote_addr}"
        
        if rate_limiter.is_rate_limited(identifier):
            return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
        
        return f(*args, **kwargs)
    return decorated_function

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
@rate_limit  # Using the improved rate limiting decorator
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

@main.route('/test_rate_limit', methods=['GET'])
@rate_limit  # Apply the rate limiter
def test_rate_limit():
    """Simple endpoint to test rate limiting"""
    # Print the current state of the rate limiter for this user/IP
    if current_user.is_authenticated:
        identifier = f"user:{current_user.id}"
        user_info = f"User: {current_user.name} (ID: {current_user.id})"
    else:
        identifier = f"ip:{request.remote_addr}"
        user_info = f"IP: {request.remote_addr}"
    
    count = len(rate_limiter.request_logs.get(identifier, []))
    print(f"{user_info}, Request count: {count}")
    
    return jsonify({
        "success": True, 
        "message": "Request successful", 
        "count": count,
        "identifier": identifier,
        "limit": rate_limiter.limit
    }) 
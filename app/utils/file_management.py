import os
import time
import shutil
from datetime import datetime
from flask import current_app
from .. import db
from ..models import Receipt

def setup_directories():
    """Create necessary directories if they don't exist"""
    app_root = current_app.root_path
    
    # Create temp directory at root level (matches current implementation)
    temp_dir = os.path.join(os.path.dirname(app_root), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create archive directory
    archive_dir = os.path.join(app_root, 'archive')
    os.makedirs(archive_dir, exist_ok=True)
    
    return temp_dir, archive_dir

def archive_processed_receipts():
    """Move processed receipts to long-term storage"""
    temp_dir, archive_dir = setup_directories()
    
    processed_receipts = Receipt.query.filter(
        (Receipt.status == 'approved') | 
        (Receipt.status == 'rejected')
    ).all()
    
    count = 0
    for receipt in processed_receipts:
        if receipt.file_path_db and os.path.exists(receipt.file_path_db):
            # Skip if already in archive
            if '/archive/' in receipt.file_path_db:
                continue
                
            # Create user archive directory
            user_archive_dir = os.path.join(archive_dir, str(receipt.user_id))
            os.makedirs(user_archive_dir, exist_ok=True)
            
            # Move file to archive
            filename = os.path.basename(receipt.file_path_db)
            archive_path = os.path.join(user_archive_dir, filename)
            
            if not os.path.exists(archive_path):
                try:
                    shutil.copy2(receipt.file_path_db, archive_path)
                    receipt.file_path_db = archive_path
                    count += 1
                except Exception as e:
                    current_app.logger.error(f"Error archiving receipt {receipt.id}: {e}")
    
    if count > 0:
        db.session.commit()
        current_app.logger.info(f"Archived {count} receipts")
    
    return count

def cleanup_temp_reports():
    """Clean up temporary PDF reports"""
    temp_dir, _ = setup_directories()
    now = time.time()
    max_age = 7 * 86400  # 7 days in seconds
    
    count = 0
    for filename in os.listdir(temp_dir):
        if filename.endswith('_complete.pdf') or filename.endswith('_summary.pdf'):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path) and (now - os.path.getmtime(file_path)) > max_age:
                try:
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    current_app.logger.error(f"Error removing temp file {file_path}: {e}")
    
    current_app.logger.info(f"Removed {count} temporary files")
    return count
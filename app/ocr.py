import logging
import os
from .utils.ocr_processor import process_image, process_pdf

class ReceiptScanner:
    """
    A class to scan and extract information from receipt images and PDFs.
    Supports multiple languages and currencies.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Set logging level to DEBUG
        self.logger.setLevel(logging.DEBUG)
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def scan_receipt(self, file):
        """
        Scan a receipt file to extract information.
        Args:
            file: File object from request or file path string
        Returns:
            dict: Extracted receipt information
        """
        try:
            # Check if file is a string (path) or a file object
            if isinstance(file, str):
                # It's already a file path
                temp_path = file
                filename = os.path.basename(file)
                self.logger.info(f"Scanning receipt from path: {filename}")
            else:
                # It's a file object from request
                filename = file.filename
                temp_path = f"/tmp/{filename}"
                self.logger.info(f"Scanning receipt: {filename}")
                file.save(temp_path)
            
            # Process based on file type
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                result = process_image(temp_path)
            elif filename.lower().endswith('.pdf'):
                result = process_pdf(temp_path)
            else:
                result = {"error": "Unsupported file type", "total": None, "date": None, "currency": None}
            
            # Clean up only if we created the temp file
            if not isinstance(file, str):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file: {str(e)}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error in scan_receipt: {str(e)}", exc_info=True)
            return {"error": f"Receipt scanning failed: {str(e)}", "total": None, "date": None, "currency": None}
    
    # Add this method to maintain backward compatibility
    def process_receipt(self, file):
        """
        Alias for scan_receipt to maintain backward compatibility.
        """
        return self.scan_receipt(file)
import logging
import re
from datetime import datetime
from PIL import Image, ExifTags
import pytesseract

logger = logging.getLogger(__name__)

class ReceiptScanner:
    def scan_receipt(self, image_file):
        try:
            logger.info("Starting OCR scan...")
            image = Image.open(image_file)
            
            # Auto-rotate based on EXIF
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = dict(image._getexif().items())
                if exif[orientation] == 3:
                    image = image.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    image = image.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    image = image.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                pass
            
            logger.info(f"Image opened successfully: {image.size}")
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text
            text = pytesseract.image_to_string(image)
            logger.info(f"Full extracted text:\n{text}")
            
            # Extract information
            amount = self._extract_amount(text)
            subtotal = self._extract_subtotal(text)
            tax = self._extract_tax(text)
            date = self._extract_date(text)
            merchant = self._extract_merchant(text)
            
            result = {
                'amount': amount,
                'subtotal': subtotal,
                'tax': tax,
                'date': date,
                'merchant': merchant,
                'currency': 'EUR',
                'text': text
            }
            return result
            
        except Exception as e:
            logger.error(f"OCR Error: {str(e)}")
            raise

    def _extract_amount(self, text):
        """Extract amount from text."""
        # First look for Summe patterns
        summe_patterns = [
            r'Summe\s*(\d+[,.]\d{2})',
            r'Su\s*mm\s*e\s*(\d+[,.]\d{2})',
            r'SUMME\s*(\d+[,.]\d{2})',
            r'Summe\s*EUR\s*(\d+[,.]\d{2})',
            r'Su\s*mm\s*e\s*EUR\s*(\d+[,.]\d{2})'
        ]
        
        # Then look for payment patterns
        payment_patterns = [
            r'Kartenzahlung\s*EUR\s*(\d+[,.]\d{2})',
            r'(\d+[,.]\d{2})\s*€',
            r'€\s*(\d+[,.]\d{2})'
        ]
        
        # Try Summe patterns first
        for pattern in summe_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.info(f"Found amount using Summe pattern: {match.group(1)}")
                return float(match.group(1).replace(',', '.'))
        
        # If no Summe found, try payment patterns
        for pattern in payment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.info(f"Found amount using payment pattern: {match.group(1)}")
                return float(match.group(1).replace(',', '.'))
        
        return None

    def _extract_subtotal(self, text):
        """Extract subtotal amount."""
        patterns = [
            r'Netto\s*(\d+[,.]\d{2})',
            r'Subtotal\s*(\d+[,.]\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', '.'))
        return None

    def _extract_tax(self, text):
        """Extract tax amount."""
        patterns = [
            r'Mwst\s*(\d+[,.]\d{2})',
            r'MwSt\.\s*(\d+[,.]\d{2})',
            r'USt\.\s*(\d+[,.]\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', '.'))
        return None

    def _extract_date(self, text):
        """Extract date from text."""
        patterns = [
            r'(\d{2}\.\d{2}\.\d{2})',  # DD.MM.YY
            r'(\d{2}/\d{2}/\d{2})',    # DD/MM/YY
            r'(\d{2}\.\d{2}\.\d{2})\s*\d{2}:\d{2}'  # DD.MM.YY HH:MM
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    date_obj = datetime.strptime(date_str, '%d.%m.%y')
                    return date_obj.strftime('%d.%m.%Y')
                except ValueError:
                    continue
        return None

    def _extract_merchant(self, text):
        """Extract merchant name from the first meaningful line."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            return lines[0]
        return None 
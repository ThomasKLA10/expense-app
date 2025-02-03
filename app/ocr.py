import logging
import re
from datetime import datetime
from PIL import Image, ExifTags
import pytesseract
from decimal import Decimal
import os

# Configure Tesseract path if needed
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
            
            # Convert text to lowercase for easier matching
            text_lower = text.lower()
            
            # Initialize results
            result = {
                'total': None,
                'currency': None,
                'date': None,
                'amount': None,
                'subtotal': None,
                'tax': None,
                'merchant': None,
                'text': text
            }
            
            # Currency detection patterns
            currency_patterns = {
                'USD': [r'\$', 'usd', 'dollar'],
                'EUR': [r'€', 'eur', 'euro'],
                'GBP': [r'£', 'gbp', 'pound'],
                'NOK': ['nok', 'kr', 'krone']
            }
            
            # Detect currency
            for curr, patterns in currency_patterns.items():
                if any(re.search(pattern, text_lower) for pattern in patterns):
                    result['currency'] = curr
                    logging.info(f"Currency detected: {curr}")
                    break
            
            # Find total amount
            total_patterns = [
                r'total[\s:]*[\$€£]?\s*(\d+[.,]\d{2})',
                r'sum[\s:]*[\$€£]?\s*(\d+[.,]\d{2})',
                r'amount[\s:]*[\$€£]?\s*(\d+[.,]\d{2})',
                r'[\$€£]\s*(\d+[.,]\d{2})',  # Just currency symbol followed by amount
                r'(\d+[.,]\d{2})\s*[\$€£]'   # Amount followed by currency symbol
            ]
            
            for pattern in total_patterns:
                logging.info(f"Trying pattern: {pattern}")
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    try:
                        # Replace comma with dot for decimal parsing
                        amount_str = match.group(1).replace(',', '.')
                        amount = float(amount_str)
                        result['total'] = amount
                        result['amount'] = amount
                        logging.info(f"Total amount found: {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
                if result['total'] is not None:
                    break
            
            # Enhanced date detection patterns
            date_patterns = [
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',    # YYYY/MM/DD
                r'(\d{1,2})[-.](\d{1,2})[-.](\d{2,4})',  # European format
                r'(\d{2,4})[-.](\d{1,2})[-.](\d{1,2})'   # ISO format
            ]
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    try:
                        # Extract the components
                        d1, d2, d3 = match.groups()
                        
                        # If year is 2 digits, assume 20XX
                        if len(d3) == 2:
                            d3 = '20' + d3
                        
                        # Try to parse as MM/DD/YYYY (common US format)
                        try:
                            date_obj = datetime.strptime(f"{d1}/{d2}/{d3}", "%m/%d/%Y")
                            result['date'] = date_obj.strftime("%Y-%m-%d")
                            logging.info(f"Date found: {result['date']}")
                            break
                        except ValueError:
                            # If that fails, try DD/MM/YYYY
                            try:
                                date_obj = datetime.strptime(f"{d2}/{d1}/{d3}", "%m/%d/%Y")
                                result['date'] = date_obj.strftime("%Y-%m-%d")
                                logging.info(f"Date found: {result['date']}")
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logging.error(f"Error parsing date: {str(e)}")
                        continue
                if result['date'] is not None:
                    break
            
            # Extract information
            subtotal = self._extract_subtotal(text)
            tax = self._extract_tax(text)
            merchant = self._extract_merchant(text)
            
            result['subtotal'] = subtotal
            result['tax'] = tax
            result['merchant'] = merchant
            
            logging.info(f"OCR Results: {result}")
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
                    # Parse and format in European style
                    date_obj = datetime.strptime(date_str, '%d.%m.%y')
                    return date_obj.strftime('%d.%m.%Y')  # European format
                except ValueError:
                    continue
        return None

    def _extract_merchant(self, text):
        """Extract merchant name from the first meaningful line."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            return lines[0]
        return None

def process_receipt(image_path):
    try:
        logging.info(f"Processing receipt at path: {image_path}")
        
        # Perform OCR
        image = Image.open(image_path)
        logging.info("Image opened successfully")
        
        text = pytesseract.image_to_string(image)
        logging.info(f"OCR Text extracted: {text[:200]}...")
        
        # Convert text to lowercase for easier matching
        text_lower = text.lower()
        
        # Initialize results
        result = {
            'total': None,
            'currency': None,
            'date': None
        }
        
        # Currency detection patterns
        currency_patterns = {
            'USD': [r'\$', 'usd', 'dollar'],
            'EUR': [r'€', 'eur', 'euro'],
            'GBP': [r'£', 'gbp', 'pound'],
            'NOK': ['nok', 'kr', 'krone']
        }
        
        # Detect currency
        for curr, patterns in currency_patterns.items():
            if any(re.search(pattern, text_lower) for pattern in patterns):
                result['currency'] = curr
                logging.info(f"Currency detected: {curr}")
                break
        
        # Find total amount
        total_patterns = [
            r'total[\s:]*[\$€£]?\s*(\d+[.,]\d{2})',
            r'[\$€£]\s*(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*[\$€£]',
            r'total:?\s*(\d+[.,]\d{2})',
            r'total\s*\$?\s*(\d+[.,]\d{2})'
        ]
        
        for pattern in total_patterns:
            logging.info(f"Trying pattern: {pattern}")
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '.')
                    amount = float(amount_str)
                    result['total'] = amount
                    logging.info(f"Total amount found: {amount}")
                    break
                except (ValueError, IndexError):
                    continue
            if result['total'] is not None:
                break
        
        # Enhanced date detection patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',    # YYYY/MM/DD
            r'(\d{1,2})[-.](\d{1,2})[-.](\d{2,4})',  # European format
            r'(\d{2,4})[-.](\d{1,2})[-.](\d{1,2})'   # ISO format
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    # Extract the components
                    d1, d2, d3 = match.groups()
                    
                    # If year is 2 digits, assume 20XX
                    if len(d3) == 2:
                        d3 = '20' + d3
                    
                    # Try to parse as MM/DD/YYYY (common US format)
                    try:
                        date_obj = datetime.strptime(f"{d1}/{d2}/{d3}", "%m/%d/%Y")
                        result['date'] = date_obj.strftime("%Y-%m-%d")
                        logging.info(f"Date found: {result['date']}")
                        break
                    except ValueError:
                        # If that fails, try DD/MM/YYYY
                        try:
                            date_obj = datetime.strptime(f"{d2}/{d1}/{d3}", "%m/%d/%Y")
                            result['date'] = date_obj.strftime("%Y-%m-%d")
                            logging.info(f"Date found: {result['date']}")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logging.error(f"Error parsing date: {str(e)}")
                    continue
            if result['date'] is not None:
                break
        
        logging.info(f"Final OCR Results: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error in process_receipt: {str(e)}")
        raise 
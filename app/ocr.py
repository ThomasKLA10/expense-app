import logging
import re
from PIL import Image
import pytesseract
from datetime import datetime
from pdf2image import convert_from_path
import os

class ReceiptScanner:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_receipt(self, image_path):
        try:
            # Handle PDF files
            if image_path.lower().endswith('.pdf'):
                # Convert PDF to image
                pages = convert_from_path(image_path)
                if pages:
                    # Save first page as temporary image
                    temp_image_path = image_path.replace('.pdf', '_temp.jpg')
                    pages[0].save(temp_image_path, 'JPEG')
                    # Process the image
                    result = self._process_image(temp_image_path)
                    # Clean up
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
                    return result
            else:
                return self._process_image(image_path)
                
        except Exception as e:
            self.logger.error(f"Error in process_receipt: {str(e)}")
            raise

    def _process_image(self, image_path):
        try:
            self.logger.info(f"Processing receipt at path: {image_path}")
            
            text = pytesseract.image_to_string(
                Image.open(image_path), 
                lang='eng+deu+nor+spa+nld'
            )
            self.logger.info(f"OCR Text extracted: {text}")
            
            text_lower = text.lower()
            
            result = {
                'total': None,
                'date': None,
                'currency': None
            }
            
            # Currency detection patterns
            currency_patterns = {
                'USD': [r'us[\$]', r'usd', r'dollar', r'US\$'],
                'EUR': [r'€', r'eur', r'euro'],
                'GBP': [r'£', r'gbp', 'pound'],
                'NOK': ['nok', 'kr', 'krone']
            }
            
            # Detect currency
            for curr, patterns in currency_patterns.items():
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    result['currency'] = curr
                    break
            
            # Total amount patterns
            total_patterns = [
                r'total:?\s*[\$€£]?\s*(\d+[.,]\d{2})',
                r'amount:?\s*[\$€£]?\s*(\d+[.,]\d{2})',
                r'sum:?\s*[\$€£]?\s*(\d+[.,]\d{2})',
                r'[\$€£]\s*(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*[\$€£]',
                r'(?:^|\s)(\d+[.,]\d{2})(?:\s|$)'  # Any number with 2 decimals
            ]
            
            # Process total amount
            for pattern in total_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    try:
                        amount_str = match.group(1).replace(',', '.')
                        amount = float(amount_str)
                        result['total'] = amount
                        self.logger.info(f"Total amount found: {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
                if result['total'] is not None:
                    break
            
            # Date patterns for all formats
            date_patterns = [
                # US format (MM/DD/YYYY)
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                # European format (DD.MM.YYYY)
                r'(\d{1,2})[.-](\d{1,2})[.-](\d{4})',
                # ISO format (YYYY-MM-DD)
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                # Text format (Month DD, YYYY)
                r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{4})',
            ]
            
            # Month name to number mapping
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            
            # Process date
            for pattern in date_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    try:
                        groups = match.groups()
                        
                        if len(groups) == 2:  # Text format
                            month_text = text_lower[match.start():].split()[0][:3]
                            month = month_map.get(month_text, '01')
                            day, year = groups
                            result['date'] = f"{year}-{month}-{day.zfill(2)}"
                        else:
                            if groups[0].startswith('20'):  # ISO format
                                year, month, day = groups
                            else:  # US/EU format
                                month, day, year = groups
                                if int(month) > 12:  # Swap if day/month are reversed
                                    day, month = month, day
                            
                            result['date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        
                        self.logger.info(f"Date found: {result['date']}")
                        break
                    except (ValueError, IndexError) as e:
                        self.logger.error(f"Error parsing date: {str(e)}")
                        continue
                if result['date'] is not None:
                    break
            
            self.logger.info(f"Final OCR Results: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in _process_image: {str(e)}")
            raise 
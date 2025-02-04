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
        # Set logging level to DEBUG
        self.logger.setLevel(logging.DEBUG)
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def process_receipt(self, image_path):
        try:
            # Log the start of processing
            self.logger.debug(f"Starting to process receipt: {image_path}")

            # Handle PDF files
            if image_path.lower().endswith('.pdf'):
                # Log PDF processing
                self.logger.debug("Processing PDF file")
                # Convert PDF to image
                pages = convert_from_path(image_path)
                if pages:
                    # Save first page as temporary image
                    temp_image_path = image_path.replace('.pdf', '_temp.jpg')
                    self.logger.debug(f"Converting PDF to temporary image: {temp_image_path}")
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
            self.logger.error(f"Error in process_receipt: {str(e)}", exc_info=True)
            raise

    def _process_image(self, image_path):
        try:
            self.logger.debug(f"Processing image at path: {image_path}")
            
            # Extract text with specific language support
            text = pytesseract.image_to_string(
                Image.open(image_path),
                lang='eng+deu+nor+spa+nld'  # English, German, Norwegian, Spanish, Dutch
            )
            
            self.logger.debug("=== RAW OCR OUTPUT START ===")
            self.logger.debug(text)
            self.logger.debug("=== RAW OCR OUTPUT END ===")
            
            text_lower = text.lower()
            
            result = {
                'total': None,
                'date': None,
                'currency': None
            }

            # Currency detection for specific countries
            currency_patterns = {
                'USD': [
                    r'(?:us)?[\$]',      # $, US$
                    r'\busd\b',           # USD
                    r'\bdollar',          # dollar
                    r'\$\s*\d'            # $ followed by number
                ],
                'EUR': [
                    r'€',                 # €
                    r'\beur\b',           # EUR
                    r'\beuro',            # euro
                    r'\d\s*€',            # number followed by €
                    r'eur\s*\d'           # EUR followed by number
                ],
                'NOK': [
                    r'\bnok\b',           # NOK
                    r'kr',                # kr
                    r'krone',             # krone
                    r'\d\s*kr',           # number followed by kr
                    r'kr\s*\d'            # kr followed by number
                ]
            }

            # Detect currency
            for curr, patterns in currency_patterns.items():
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    result['currency'] = curr
                    self.logger.info(f"Currency detected: {curr}")
                    break

            # Total amount patterns in multiple languages
            total_patterns = [
                # Add these new patterns at the start
                r'-(\d+[.,]\d{2})\s*(?:EUR|€)',     # Matches "-24,90 EUR"
                r'(?:EUR|€)\s*-(\d+[.,]\d{2})',     # Matches "EUR -24,90"
                # English
                r'\btotal\b.*?(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2}).*?\btotal\b',
                # German
                r'\bgesamtbetrag\b.*?(\d+[.,]\d{2})',
                r'\bsumme\b.*?(\d+[.,]\d{2})',
                # Spanish
                r'\btotal\b.*?(\d+[.,]\d{2})',
                r'\bimporte\b.*?(\d+[.,]\d{2})',
                # Dutch
                r'\btotaal\b.*?(\d+[.,]\d{2})',
                r'\bbedrag\b.*?(\d+[.,]\d{2})',
                # Norwegian
                r'\btotal\b.*?(\d+[.,]\d{2})',
                r'\bsum\b.*?(\d+[.,]\d{2})',
                # Generic patterns
                r'(?:[\$€]\s*(\d+[.,]\d{2}))',
                r'(\d+[.,]\d{2})\s*(?:[\$€])',
                r'(?:kr)\s*(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*(?:kr)'
            ]

            # Process total amount
            total_found = False
            for pattern in total_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    try:
                        amount_str = match.group(1).replace(',', '.')
                        amount = float(amount_str)
                        if 'total' in pattern.lower() or 'gesamtbetrag' in pattern.lower():
                            result['total'] = amount
                            self.logger.info(f"Total amount found (from total line): {amount}")
                            total_found = True
                            break
                    except (ValueError, IndexError):
                        continue
                if total_found:
                    break

            # Date patterns for multiple formats
            date_patterns = [
                # Add this new pattern at the start
                r'(\d{1,2})\.\s*(?:januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember)\s*(\d{4})',
                # US format (prioritized for US receipts)
                r'(\d{1,2})/(\d{1,2})/(\d{4})',          # MM/DD/YYYY
                # European format
                r'(\d{1,2})[.-](\d{1,2})[.-](\d{4})',    # DD.MM.YYYY or DD-MM-YYYY
                # ISO format
                r'(\d{4})-(\d{1,2})-(\d{1,2})',          # YYYY-MM-DD
                # Text month format (multi-language)
                r'(\d{1,2})\s*(?:jan|feb|mar|apr|may|mai|jun|jul|aug|sep|oct|okt|nov|dec|dez)[a-z]*\s*(\d{4})',  # DD Month YYYY
                r'(?:jan|feb|mar|apr|may|mai|jun|jul|aug|sep|oct|okt|nov|dec|dez)[a-z]*\s*(\d{1,2})\s*,?\s*(\d{4})'  # Month DD YYYY
            ]

            # Month name mappings (multi-language)
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'mai': '05', 'jun': '06', 'jul': '07',
                'aug': '08', 'sep': '09', 'oct': '10', 'okt': '10',
                'nov': '11', 'dec': '12', 'dez': '12',
                # Add German months
                'januar': '01',
                'februar': '02',
                'märz': '03',
                'april': '04',
                'mai': '05',
                'juni': '06',
                'juli': '07',
                'august': '08',
                'september': '09',
                'oktober': '10',
                'november': '11',
                'dezember': '12'
            }

            # Process date
            for pattern in date_patterns:
                matches = list(re.finditer(pattern, text_lower))
                for match in matches:
                    try:
                        if 'jan|feb|mar' in pattern:  # Text month format
                            text_before = text_lower[max(0, match.start() - 20):match.end()]
                            for month_name in month_map:
                                if month_name in text_before:
                                    if len(match.groups()) == 2:  # DD Month YYYY
                                        day, year = match.groups()
                                        month = month_map[month_name]
                                    else:
                                        continue
                                    break
                        else:  # Numeric format
                            if match.group(1).startswith('20'):  # YYYY-MM-DD
                                year, month, day = match.groups()
                            else:
                                # Check for US format indicators
                                is_us_format = False
                                if result['currency'] == 'USD' or 'US' in text or ', IL' in text:
                                    is_us_format = True
                                
                                if is_us_format:  # MM/DD/YYYY
                                    month, day, year = match.groups()
                                else:  # DD.MM.YYYY
                                    day, month, year = match.groups()
                                
                        # Validate and format date
                        day = str(int(day)).zfill(2)  # Remove leading zeros first
                        month = str(int(month)).zfill(2)
                        
                        # Additional date validation
                        month_int = int(month)
                        day_int = int(day)
                        year_int = int(year)
                        
                        if (1 <= month_int <= 12 and 
                            1 <= day_int <= 31 and 
                            1900 <= year_int <= 2100):  # Basic sanity check for year
                            
                            # Additional validation for days in month
                            days_in_month = {
                                1: 31, 2: 29 if year_int % 4 == 0 else 28,  # Simplified leap year check
                                3: 31, 4: 30, 5: 31, 6: 30,
                                7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
                            }
                            
                            if day_int <= days_in_month[month_int]:
                                result['date'] = f"{year}-{month}-{day}"
                                self.logger.info(f"Date found: {result['date']}")
                                break
                            
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Error parsing date: {str(e)}")
                        continue
                if result['date'] is not None:
                    break

            self.logger.info(f"Final OCR Results: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in _process_image: {str(e)}")
            raise 
import logging
import re
from PIL import Image
import pytesseract
from datetime import datetime
from pdf2image import convert_from_path
import os

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

    def process_receipt(self, image_path):
        """
        Main entry point for receipt processing. Handles both PDF and image files.
        Args:
            image_path (str): Path to the receipt file (PDF or image)
        Returns:
            dict: Extracted receipt information (total, date, currency)
        """
        try:
            if not os.path.exists(image_path):
                self.logger.error(f"File not found: {image_path}")
                return {"error": "Receipt file not found", "total": None, "date": None, "currency": None}
            
            if image_path.lower().endswith('.pdf'):
                return self._process_pdf(image_path)
            else:
                return self._process_image(image_path)
        except Exception as e:
            self.logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
            return {"error": f"Receipt processing failed: {str(e)}", "total": None, "date": None, "currency": None}

    def _process_image(self, image_path):
        """
        Process an image file to extract receipt information.
        Args:
            image_path (str): Path to the image file
        Returns:
            dict: Extracted receipt information
        """
        try:
            self.logger.debug(f"Processing image at path: {image_path}")
            
            # 1. OCR Text Extraction
            text = pytesseract.image_to_string(
                Image.open(image_path),
                lang='eng+deu+nor+spa+nld+dan+swe+hun+ara'  # English, German, Norwegian, Spanish, Dutch, Danish, Swedish, Hungarian, Arabic
            )
            
            self.logger.debug("=== RAW OCR OUTPUT START ===")
            self.logger.debug(text)
            self.logger.debug("=== RAW OCR OUTPUT END ===")
            
            text_lower = text.lower()
            result = {'total': None, 'date': None, 'currency': None}

            # 2. Currency Detection
            currency_patterns = {
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
                ],
                'USD': [
                    r'(?:us)?[\$]',       # $, US$
                    r'\busd\b',           # USD
                    r'\bdollar',          # dollar
                    r'\$\s*\d'            # $ followed by number
                ],
                'GBP': [
                    r'£',                 # £
                    r'\bgbp\b',           # GBP
                    r'\bpound',           # pound
                    r'\d\s*£',            # number followed by £
                    r'gbp\s*\d'           # GBP followed by number
                ],
                'CHF': [
                    r'\bchf\b',           # CHF
                    r'fr\.',              # Fr.
                    r'franken',           # franken
                    r'\d\s*chf',          # number followed by CHF
                    r'chf\s*\d'           # CHF followed by number
                ],
                'DKK': [
                    r'\bdkk\b',           # DKK
                    r'danske\s*kr',       # danske kr
                    r'\d\s*dkk',          # number followed by DKK
                    r'dkk\s*\d'           # DKK followed by number
                ],
                'SEK': [
                    r'\bsek\b',           # SEK
                    r'svenska\s*kr',      # svenska kr
                    r'\d\s*sek',          # number followed by SEK
                    r'sek\s*\d'           # SEK followed by number
                ],
                'HUF': [
                    r'\bhuf\b',           # HUF
                    r'ft',                # Ft
                    r'forint',            # forint
                    r'\d\s*ft',           # number followed by Ft
                    r'huf\s*\d'           # HUF followed by number
                ],
                'AED': [
                    r'\baed\b',           # AED
                    r'د\.إ',              # د.إ
                    r'dirham',            # dirham
                    r'\d\s*aed',          # number followed by AED
                    r'aed\s*\d'           # AED followed by number
                ]
            }

            # Detect currency
            for curr, patterns in currency_patterns.items():
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    result['currency'] = curr
                    self.logger.info(f"Currency detected: {curr}")
                    break

            # 3. Total Amount Detection
            # Total amount patterns in multiple languages
            total_patterns = [
                # Add these new patterns at the start
                r'^[^\d]*?(-?\d+[.,]\d{2})\s*(?:EUR|€)',     # Matches amounts at start of text with currency
                r'^[^\d]*?(?:EUR|€)\s*(-?\d+[.,]\d{2})',     # Matches currency then amount at start of text
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

            # Process total amount using two strategies:
            # Strategy 1: Find explicit total line
            total_found = False
            lines = text_lower.split('\n')
            
            for line in lines:
                line = line.strip()
                if ('total' in line.lower()) and ('sub' not in line.lower()):  # Exclude subtotal
                    amount_matches = re.findall(r'-?(\d+[.,]\d{2})', line)
                    if amount_matches:
                        try:
                            amount_str = amount_matches[0].replace(',', '.')
                            amount = abs(float(amount_str))
                            result['total'] = amount
                            self.logger.info(f"Total amount found from total line: {amount}")
                            total_found = True
                            break
                        except (ValueError, IndexError):
                            continue

            # Strategy 2: Fall back to prominent amount
            if not total_found:
                for line in lines:
                    line = line.strip()
                    if 'eur' in line or '€' in line:
                        amount_matches = re.findall(r'-?(\d+[.,]\d{2})', line)
                        if amount_matches:
                            try:
                                amount_str = amount_matches[0].replace(',', '.')
                                amount = abs(float(amount_str))
                                result['total'] = amount
                                self.logger.info(f"Amount found from prominent position: {amount}")
                                total_found = True
                                break
                            except (ValueError, IndexError):
                                continue

            # 4. Date Detection
            # Define date patterns for multiple formats
            date_patterns = [
                # German format
                r'(\d{1,2})\.\s*(?:januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember)\s*(\d{4})',
                # US format
                r'(\d{1,2})/(\d{1,2})/(\d{4})',          # MM/DD/YYYY
                # European format
                r'(\d{1,2})[.-](\d{1,2})[.-](\d{4})',    # DD.MM.YYYY or DD-MM-YYYY
                # ISO format
                r'(\d{4})-(\d{1,2})-(\d{1,2})',          # YYYY-MM-DD
                # Text month formats
                r'(\d{1,2})\s*(?:jan|feb|mar|apr|may|mai|jun|jul|aug|sep|oct|okt|nov|dec|dez)[a-z]*\s*(\d{4})',
                r'(?:jan|feb|mar|apr|may|mai|jun|jul|aug|sep|oct|okt|nov|dec|dez)[a-z]*\s*(\d{1,2})\s*,?\s*(\d{4})'
            ]

            # Month name mappings for multiple languages
            month_map = {
                # English/Common
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'mai': '05', 'jun': '06', 'jul': '07',
                'aug': '08', 'sep': '09', 'oct': '10', 'okt': '10',
                'nov': '11', 'dec': '12', 'dez': '12',
                # German
                'januar': '01', 'februar': '02', 'märz': '03',
                'april': '04', 'mai': '05', 'juni': '06',
                'juli': '07', 'august': '08', 'september': '09',
                'oktober': '10', 'november': '11', 'dezember': '12'
            }

            # Process date
            for pattern in date_patterns:
                matches = list(re.finditer(pattern, text_lower))
                for match in matches:
                    try:
                        if 'januar|februar|märz' in pattern:  # German text month format
                            day = match.group(1)
                            year = match.group(2)
                            # Map German month names to numbers
                            text_before = text_lower[max(0, match.start() - 20):match.end()]
                            for month_name in month_map:
                                if month_name in text_before:
                                    month = month_map[month_name]
                                    break
                        elif 'jan|feb|mar' in pattern:  # English text month format
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
            self.logger.error(f"Error in _process_image: {str(e)}", exc_info=True)
            return {"error": f"Image processing failed: {str(e)}", "total": None, "date": None, "currency": None}

    def _process_pdf(self, pdf_path):
        """
        Process a PDF file to extract receipt information.
        Args:
            pdf_path (str): Path to the PDF file
        Returns:
            dict: Extracted receipt information
        """
        try:
            self.logger.debug(f"Processing PDF at path: {pdf_path}")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            if not images:
                self.logger.error("Failed to convert PDF to images")
                return {"error": "Failed to convert PDF", "total": None, "date": None, "currency": None}
            
            # Process the first page of the PDF
            first_page = images[0]
            
            # Save the image temporarily
            temp_image_path = f"{pdf_path}_temp.jpg"
            first_page.save(temp_image_path, 'JPEG')
            
            # Process the image
            result = self._process_image(temp_image_path)
            
            # Clean up the temporary file
            try:
                os.remove(temp_image_path)
            except Exception as e:
                self.logger.warning(f"Failed to remove temporary file: {str(e)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in _process_pdf: {str(e)}")
            return {"error": f"PDF processing failed: {str(e)}", "total": None, "date": None, "currency": None}
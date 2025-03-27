import logging
import re
from datetime import datetime
from .ocr_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)

def extract_currency(text_lower):
    """
    Extract currency from OCR text.
    Args:
        text_lower (str): Lowercase OCR text
    Returns:
        str: Detected currency code or None
    """
    # Currency patterns
    currency_patterns = {
        'EUR': [
            r'€',                 # €
            r'\beur\b',           # EUR
            r'\beuro',            # euro
            r'\d\s*€',            # number followed by €
            r'eur\s*\d'           # EUR followed by number
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
        'NOK': [
            r'\bnok\b',           # NOK
            r'kr',                # kr
            r'krone',             # krone
            r'\d\s*kr',           # number followed by kr
            r'kr\s*\d'            # kr followed by number
        ],
        'CHF': [
            r'\bchf\b',           # CHF
            r'fr\.',              # Fr.
            r'franken',           # franken
            r'\d\s*chf',          # number followed by CHF
            r'chf\s*\d'           # CHF followed by number
        ]
    }
    
    for curr, patterns in currency_patterns.items():
        if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in patterns):
            logger.info(f"Currency detected: {curr}")
            return curr
    
    return None

def extract_amount(text_lower, lines, currency=None):
    """
    Extract total amount from OCR text.
    Args:
        text_lower (str): Lowercase OCR text
        lines (list): List of text lines
        currency (str): Detected currency code
    Returns:
        float: Extracted amount or None
    """
    # Strategy 1: Find explicit total line
    for line in lines:
        line = line.strip().lower()
        if ('total' in line) and ('sub' not in line):  # Exclude subtotal
            amount_matches = re.findall(r'-?(\d+[.,]\d{2})', line)
            if amount_matches:
                try:
                    amount_str = amount_matches[-1].replace(',', '.')  # Use last match as it's likely the final total
                    amount = abs(float(amount_str))
                    logger.info(f"Total amount found from total line: {amount}")
                    return amount
                except (ValueError, IndexError):
                    continue

    # Strategy 2: Look for currency-specific patterns
    if currency:
        currency_patterns = {
            'EUR': [r'(\d+[.,]\d{2})\s*€', r'€\s*(\d+[.,]\d{2})'],
            'USD': [r'(\d+[.,]\d{2})\s*\$', r'\$\s*(\d+[.,]\d{2})'],
            'GBP': [r'(\d+[.,]\d{2})\s*£', r'£\s*(\d+[.,]\d{2})'],
            'NOK': [r'(\d+[.,]\d{2})\s*kr', r'kr\s*(\d+[.,]\d{2})'],
            'CHF': [r'(\d+[.,]\d{2})\s*chf', r'chf\s*(\d+[.,]\d{2})']
        }
        
        if currency in currency_patterns:
            for pattern in currency_patterns[currency]:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    try:
                        amount_str = matches[-1].replace(',', '.')  # Use last match
                        amount = abs(float(amount_str))
                        logger.info(f"Amount found with currency pattern: {amount}")
                        return amount
                    except (ValueError, IndexError):
                        continue

    # Strategy 3: Fall back to prominent amount
    # Look for the last amount in the text that has 2 decimal places
    amount_matches = re.findall(r'-?(\d+[.,]\d{2})', text_lower)
    if amount_matches:
        try:
            amount_str = amount_matches[-1].replace(',', '.')  # Use last match
            amount = abs(float(amount_str))
            logger.info(f"Amount found from prominent position: {amount}")
            return amount
        except (ValueError, IndexError):
            pass
    
    return None

def extract_date(text_lower):
    """
    Extract date from OCR text.
    Args:
        text_lower (str): Lowercase OCR text
    Returns:
        str: Extracted date in ISO format (YYYY-MM-DD) or None
    """
    # Define date patterns for multiple formats
    date_patterns = [
        # German format
        (r'(\d{1,2})[.-](\d{1,2})[.-](\d{4})', '%d/%m/%Y'),  # DD.MM.YYYY or DD-MM-YYYY
        # US format
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),        # MM/DD/YYYY
        # ISO format
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y/%m/%d'),        # YYYY-MM-DD
        # Short year format
        (r'(\d{1,2})[.-](\d{1,2})[.-](\d{2})', '%d/%m/%y'),  # DD.MM.YY
        # Text month formats
        (r'(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})', 'text_month'),
        (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{1,2})[,]?\s*(\d{4})', 'month_text')
    ]

    # Month name mappings for multiple languages
    month_map = {
        # English/Common
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
        # German
        'januar': '01', 'februar': '02', 'märz': '03',
        'april': '04', 'mai': '05', 'juni': '06',
        'juli': '07', 'august': '08', 'september': '09',
        'oktober': '10', 'november': '11', 'dezember': '12',
        # Norwegian
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'mai': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'okt': '10', 'nov': '11', 'des': '12'
    }

    # Process date
    for pattern, format_str in date_patterns:
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            try:
                if format_str in ('text_month', 'month_text'):
                    if format_str == 'text_month':
                        day = match.group(1)
                        month_name = match.group(2).lower()
                        year = match.group(3)
                    else:
                        month_name = match.group(1).lower()
                        day = match.group(2)
                        year = match.group(3)
                    month = month_map.get(month_name[:3], '01')  # Default to January if not found
                else:
                    if format_str == '%d/%m/%Y':
                        day, month, year = match.groups()
                    elif format_str == '%Y/%m/%d':
                        year, month, day = match.groups()
                    elif format_str == '%m/%d/%Y':
                        month, day, year = match.groups()
                    elif format_str == '%d/%m/%y':
                        day, month, year = match.groups()
                        year = '20' + year  # Assume 20xx for two-digit years
                
                # Convert to integers for validation
                day_int = int(day)
                month_int = int(month)
                year_int = int(year)
                
                # Basic validation
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
                        # Format as ISO date
                        iso_date = f"{year_int:04d}-{month_int:02d}-{day_int:02d}"
                        logger.info(f"Date found: {iso_date}")
                        return iso_date
            except (ValueError, IndexError) as e:
                logger.debug(f"Error parsing date: {str(e)}")
                continue
    
    return None 
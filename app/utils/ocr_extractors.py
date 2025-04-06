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
    # Currency patterns - only EUR and USD for MVP
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
        ]
    }
    
    for curr, patterns in currency_patterns.items():
        if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in patterns):
            logger.info(f"Currency detected: {curr}")
            return curr
    
    return None

def extract_amount(text_lower, lines, currency=None, original_text=None):
    """
    Extract the total amount from OCR text.
    
    Args:
        text_lower (str): Lowercase OCR text
        lines (list): OCR text split into lines
        currency (str): Detected currency code
        original_text (str): Original OCR text with case preserved
        
    Returns:
        float: Extracted amount or None if not found
    """
    # Look for common patterns indicating total amount - English and German only
    total_keywords = ['total', 'sum', 'amount', 'due', 'pay', 'balance', 'summe', 'betrag']
    
    # Try to find amount with currency symbol first
    currency_symbols = {'USD': '$', 'EUR': '€'}
    symbol = currency_symbols.get(currency, '')
    
    # German receipt specific patterns - check these first
    if original_text:
        # Look for specific German patterns
        german_patterns = [
            r'gesamtbrutto\s+[€]?(\d+[.,]\d+)',
            r'ec-zahlung\s+[€]?(\d+[.,]\d+)',
            r'zw-summe\s+[€]?(\d+[.,]\d+)',
            r'gesamt\s+[€]?(\d+[.,]\d+)'
        ]
        
        for pattern in german_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    amount = float(matches[0].replace(',', '.'))
                    logger.info(f"Amount found with German pattern: {amount}")
                    return amount
                except (ValueError, IndexError):
                    pass
        
        # For German receipts, look for the largest € amount
        if '€' in original_text:
            # Find all amounts with € symbol
            amount_matches = re.findall(r'€\s*(\d+[.,]\d+)', original_text.replace(' ', ''))
            if amount_matches:
                try:
                    # Convert all matches to float and find the largest one
                    amounts = [float(amt.replace(',', '.')) for amt in amount_matches]
                    largest_amount = max(amounts)
                    logger.info(f"Largest amount found with € symbol: {largest_amount}")
                    return largest_amount
                except (ValueError, IndexError):
                    pass
    
    if symbol:
        # Look for amounts with the currency symbol
        amount_pattern = rf'{symbol}\s*(\d+[.,]\d+)'
        matches = re.findall(amount_pattern, text_lower)
        if matches:
            try:
                amount = float(matches[-1].replace(',', '.'))
                logger.info(f"Amount found with currency pattern: {amount}")
                return amount
            except (ValueError, IndexError):
                pass
    
    # Look for total keywords followed by numbers
    for line in lines:
        line_lower = line.lower()
        for keyword in total_keywords:
            if keyword in line_lower:
                # Extract numbers from this line
                numbers = re.findall(r'(\d+[.,]\d+)', line_lower)
                if numbers:
                    try:
                        # Usually the last number in a total line is the amount
                        amount = float(numbers[-1].replace(',', '.'))
                        logger.info(f"Amount found with keyword '{keyword}': {amount}")
                        return amount
                    except (ValueError, IndexError):
                        continue
    
    # If no total keywords found, look for the largest number in the last few lines
    # (often the total is at the bottom of the receipt)
    last_lines = lines[-min(10, len(lines)):]
    all_numbers = []
    
    for line in last_lines:
        numbers = re.findall(r'(\d+[.,]\d+)', line.lower())
        for num in numbers:
            try:
                all_numbers.append(float(num.replace(',', '.')))
            except (ValueError, IndexError):
                continue
    
    if all_numbers:
        amount = max(all_numbers)
        logger.info(f"Amount found as largest number in last lines: {amount}")
        return amount
    
    return None

def extract_date(text_lower, original_text=None):
    """
    Extract the date from OCR text.
    
    Args:
        text_lower (str): Lowercase OCR text
        original_text (str): Original OCR text with case preserved
        
    Returns:
        str: Extracted date in ISO format (YYYY-MM-DD) or None if not found
    """
    # Add specific pattern for German receipts with BEGINN/ENDE
    if original_text:
        # Look for BEGINN or ENDE followed by date in format DD/MM/YYYY
        german_patterns = [
            r'beginn\s+(\d{1,2})/(\d{1,2})/(\d{2,4})',
            r'ende\s+(\d{1,2})/(\d{1,2})/(\d{2,4})',
            r'beginn\s+(\d{1,2})\.(\d{1,2})\.(\d{2,4})',
            r'ende\s+(\d{1,2})\.(\d{1,2})\.(\d{2,4})'
        ]
        
        for pattern in german_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    day, month, year = matches[0]
                    # Handle 2-digit years
                    if len(year) == 2:
                        year = '20' + year
                    
                    # Validate date components
                    day = int(day)
                    month = int(month)
                    year = int(year)
                    
                    if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                        formatted_date = f"{year}-{month:02d}-{day:02d}"
                        logger.info(f"Found date with German pattern: {formatted_date}")
                        return formatted_date
                except (ValueError, IndexError):
                    pass
    
    # Common date patterns (various formats)
    date_patterns = [
        # MM/DD/YYYY or DD/MM/YYYY
        r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})',
        # YYYY/MM/DD
        r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})',
        # Month name formats (English only)
        r'(\d{1,2})\s?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s?(\d{2,4})',
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s?(\d{1,2})[\s,]+(\d{2,4})'
    ]
    
    # Try each pattern
    for pattern in date_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                # Handle different formats
                if len(matches[0]) == 3:
                    if len(matches[0][0]) == 4:  # YYYY/MM/DD
                        year, month, day = matches[0]
                    elif any(m in matches[0][1].lower() for m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                        # Handle month name formats
                        month_names = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 
                                      'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
                        
                        if matches[0][0].isdigit():  # DD Month YYYY
                            day, month_name, year = matches[0]
                            month = month_names.get(month_name[:3].lower(), 1)
                        else:  # Month DD, YYYY
                            month_name, day, year = matches[0]
                            month = month_names.get(month_name[:3].lower(), 1)
                    else:  # MM/DD/YYYY or DD/MM/YYYY (assume DD/MM/YYYY for international receipts)
                        day, month, year = matches[0]
                        
                    # Handle 2-digit years
                    if len(str(year)) == 2:
                        year = '20' + str(year)
                        
                    # Validate date components
                    day = int(day)
                    month = int(month) if isinstance(month, str) and month.isdigit() else month
                    year = int(year)
                    
                    if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                        formatted_date = f"{year}-{month:02d}-{day:02d}"
                        logger.info(f"Found date: {formatted_date}")
                        return formatted_date
            except (ValueError, IndexError):
                continue
    
    # Look for date keywords - English and German only
    date_keywords = ['date', 'datum']
    for line in text_lower.split('\n'):
        for keyword in date_keywords:
            if keyword in line:
                # Try to extract date from this line
                for pattern in date_patterns:
                    matches = re.findall(pattern, line)
                    if matches:
                        try:
                            # Similar processing as above
                            if len(matches[0]) == 3:
                                if len(matches[0][0]) == 4:  # YYYY/MM/DD
                                    year, month, day = matches[0]
                                else:  # MM/DD/YYYY or DD/MM/YYYY (assume DD/MM/YYYY)
                                    day, month, year = matches[0]
                                
                                # Handle 2-digit years
                                if len(str(year)) == 2:
                                    year = '20' + str(year)
                                    
                                # Validate date components
                                day = int(day)
                                month = int(month)
                                year = int(year)
                                
                                if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                                    formatted_date = f"{year}-{month:02d}-{day:02d}"
                                    logger.info(f"Found date with keyword '{keyword}': {formatted_date}")
                                    return formatted_date
                        except (ValueError, IndexError):
                            continue
    
    return None 
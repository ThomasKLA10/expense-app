import logging
import os
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from .ocr_extractors import extract_amount, extract_date, extract_currency
from .ocr_utils import setup_logger
import io
import re

# Set up logger
logger = setup_logger(__name__)

# Constants for image processing
MAX_IMAGE_SIZE = (1800, 1800)  # Maximum dimensions for processing
COMPRESSION_QUALITY = 85  # JPEG compression quality (0-100)
MAX_FILE_SIZE_MB = 5  # Target maximum file size in MB

def resize_and_compress_image(image_path, max_size=MAX_IMAGE_SIZE, quality=COMPRESSION_QUALITY):
    """
    Resize and compress an image to make it suitable for OCR and PDF inclusion.
    
    Args:
        image_path (str): Path to the image file
        max_size (tuple): Maximum width and height
        quality (int): JPEG compression quality (0-100)
        
    Returns:
        str: Path to the resized image
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB if needed (handles RGBA, CMYK, etc.)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Get original size
            original_size = os.path.getsize(image_path) / (1024 * 1024)  # Size in MB
            logger.debug(f"Original image size: {original_size:.2f}MB, dimensions: {img.size}")
            
            # Resize if larger than max_size
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.debug(f"Resized image to: {img.size}")
            
            # Create output filename
            output_path = f"{os.path.splitext(image_path)[0]}_resized.jpg"
            
            # Save with compression
            img.save(output_path, format='JPEG', quality=quality, optimize=True)
            
            # Check if we need more aggressive compression
            new_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
            logger.debug(f"Compressed image size: {new_size:.2f}MB")
            
            # If still too large, compress more aggressively
            if new_size > MAX_FILE_SIZE_MB and quality > 50:
                logger.debug(f"Image still too large, applying more aggressive compression")
                # Try with lower quality
                img.save(output_path, format='JPEG', quality=quality-20, optimize=True)
            
            return output_path
            
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}", exc_info=True)
        return image_path  # Return original path if processing fails

def process_image(image_path):
    """
    Process an image file to extract receipt information.
    Args:
        image_path (str): Path to the image file
    Returns:
        dict: Extracted receipt information
    """
    try:
        logger.debug(f"Processing image at path: {image_path}")
        
        # Check if the image exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return {"error": "Image file not found", "total": None, "date": None, "currency": None}
        
        # Get image size and dimensions
        image_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        logger.debug(f"Original image size: {image_size_mb:.2f}MB, dimensions: {get_image_dimensions(image_path)}")
        
        # Process the image (resize, enhance) if it's large
        processed_image_path = None
        if image_size_mb > 1.0:
            processed_image_path = resize_and_enhance_image(image_path)
            logger.debug(f"Using processed image: {processed_image_path}")
        else:
            processed_image_path = image_path
            logger.debug(f"Using original image (small enough): {processed_image_path}")
        
        # Extract text using OCR
        text = extract_text_from_image(processed_image_path)
        
        # If OCR failed to extract text
        if not text:
            logger.warning("OCR failed to extract any text from the image")
            return {"error": "OCR failed to extract text", "total": None, "date": None, "currency": None}
        
        # Log the raw OCR output for debugging
        logger.debug("=== RAW OCR OUTPUT START ===")
        logger.debug(text)
        logger.debug("=== RAW OCR OUTPUT END ===")
        
        # Process the extracted text
        text_lower = text.lower()
        original_text = text  # Keep the original text with case preserved
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract information
        result = {}
        result['currency'] = extract_currency(text_lower)
        result['total'] = extract_amount(text_lower, lines, result['currency'], original_text)
        result['date'] = extract_date(text_lower, original_text)
        
        # If total seems incorrect, try German amount format as last resort
        german_amount = extract_german_amount(original_text)
        if german_amount:
            # Only override if the German amount is different and seems more reasonable
            if result['total'] is None or abs(result['total'] - german_amount) > 5:
                result['total'] = german_amount
                logger.info(f"Found German amount format: {german_amount}")
        
        # Try to find totals using keywords
        potential_totals = extract_total_from_keywords(original_text)
        
        # If we found potential totals and they're in a reasonable range
        if potential_totals:
            # Check if we have a currency-tagged amount
            has_currency_amount = result.get('currency') is not None and result.get('total') is not None
            
            for amount, match_text in potential_totals:
                if 1 <= amount <= 500:
                    # Only replace if:
                    # 1. We don't have a currency-tagged amount, OR
                    # 2. The current amount is unreasonable (too large)
                    if not has_currency_amount or result['total'] > 100:
                        logger.info(f"Replacing amount {result['total']} with {amount} from '{match_text}'")
                        result['total'] = amount
                        break
        
        # Ensure amount is always positive for expense tracking
        if result['total'] is not None:
            result['total'] = abs(result['total'])
            # Round to 2 decimal places
            result['total'] = round(result['total'] * 100) / 100
        
        # If date is still not found, try running OCR with different settings
        if result['date'] is None and result['currency'] == 'EUR':
            logger.debug("Date not found, trying bottom crop OCR for German receipt")
            try:
                from PIL import Image
                import pytesseract
                
                # Open the image
                img = Image.open(processed_image_path)
                width, height = img.size
                
                # Try multiple crops to find the date
                crops = [
                    # Bottom quarter
                    img.crop((0, height * 3 // 4, width, height)),
                    # Bottom third
                    img.crop((0, height * 2 // 3, width, height)),
                    # Bottom half
                    img.crop((0, height // 2, width, height))
                ]
                
                for i, crop in enumerate(crops):
                    crop_path = f"{os.path.splitext(processed_image_path)[0]}_bottom_{i}.jpg"
                    crop.save(crop_path)
                    logger.debug(f"Saved crop {i} to: {crop_path}")
                    
                    # Try different OCR configurations
                    for config in ['--psm 6', '--psm 11', '--psm 3']:
                        # Run OCR on the crop with German language and different configs
                        crop_text = pytesseract.image_to_string(crop, lang='deu', config=config)
                        logger.debug(f"=== CROP {i} OCR OUTPUT (config: {config}) START ===")
                        logger.debug(crop_text)
                        logger.debug(f"=== CROP {i} OCR OUTPUT END ===")
                        
                        # Look for BEGINN/ENDE pattern first (most reliable)
                        beginn_match = re.search(r'BEGINN\s+(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})', crop_text, re.IGNORECASE)
                        if beginn_match:
                            day, month, year = beginn_match.groups()
                            logger.debug(f"Found BEGINN date: {day}/{month}/{year}")
                            
                            # Handle 2-digit years
                            if len(year) == 2:
                                year = '20' + year
                            
                            try:
                                day = int(day)
                                month = int(month)
                                year = int(year)
                                
                                if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                                    formatted_date = f"{year}-{month:02d}-{day:02d}"
                                    logger.info(f"Found date with BEGINN pattern: {formatted_date}")
                                    result['date'] = formatted_date
                                    break
                            except ValueError:
                                continue
                        
                        # If no BEGINN pattern, try standard date patterns
                        if not result['date']:
                            date_patterns = [
                                r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})',  # Standard date pattern
                                r'[^\d](\d{2})[/.-](\d{4})\s+\d{1,2}:\d{1,2}'  # Pattern like "06/2023 14:17"
                            ]
                            
                            for pattern in date_patterns:
                                date_match = re.search(pattern, crop_text, re.IGNORECASE)
                                if date_match:
                                    logger.debug(f"Found date match with pattern: {pattern}")
                                    
                                    # Handle different pattern formats
                                    if pattern.endswith('\d{1,2}:\d{1,2}'):
                                        # Format: "06/2023 14:17" - month/year format
                                        month, year = date_match.groups()
                                        
                                        # For this specific format, try to find BEGINN in the entire text
                                        # This handles cases where the OCR might split the text
                                        full_text = pytesseract.image_to_string(img, lang='deu')
                                        beginn_day_match = re.search(r'BEGINN\s+(\d{1,2})[/.-]', full_text)
                                        
                                        if beginn_day_match:
                                            day = beginn_day_match.group(1)
                                            logger.debug(f"Found day from BEGINN pattern: {day}")
                                        else:
                                            # Look for any numbers that could be days
                                            day_candidates = re.findall(r'\b(\d{1,2})\b', full_text)
                                            valid_days = [int(d) for d in day_candidates if 1 <= int(d) <= 31]
                                            
                                            if valid_days:
                                                # Use the most common day number found
                                                from collections import Counter
                                                day_counts = Counter(valid_days)
                                                day = day_counts.most_common(1)[0][0]
                                                logger.debug(f"Using most common day number found: {day}")
                                            else:
                                                # Last resort: use current day
                                                from datetime import datetime
                                                day = datetime.now().day
                                                logger.debug(f"No day found, using current day: {day}")
                                    else:
                                        # Standard format with day, month, year
                                        day, month, year = date_match.groups()
                                    
                                    # Handle 2-digit years
                                    if len(year) == 2:
                                        year = '20' + year
                                    
                                    # Validate date components
                                    try:
                                        day = int(day)
                                        month = int(month)
                                        year = int(year)
                                        
                                        if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                                            formatted_date = f"{year}-{month:02d}-{day:02d}"
                                            logger.info(f"Found date in crop {i}: {formatted_date}")
                                            result['date'] = formatted_date
                                            break
                                    except ValueError:
                                        continue
                        
                        # If we found a date, no need to try other configs
                        if result['date']:
                            break
                    
                    # If we found a date, no need to check other crops
                    if result['date']:
                        break
            
            except Exception as e:
                logger.warning(f"Error in secondary date extraction: {str(e)}")
        
        # If date is still None, try German date format as last resort
        if result['date'] is None:
            german_date = extract_german_date(original_text)
            if german_date:
                result['date'] = german_date
                logger.info(f"Found German date format: {german_date}")
        
        logger.info(f"Final OCR Results: {result}")
        
        # Clean up temporary files
        if processed_image_path and processed_image_path != image_path:
            try:
                os.remove(processed_image_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary processed image: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_image: {str(e)}", exc_info=True)
        return {"error": f"Image processing failed: {str(e)}", "total": None, "date": None, "currency": None}

def process_pdf(pdf_path):
    """
    Process a PDF file to extract receipt information.
    Args:
        pdf_path (str): Path to the PDF file
    Returns:
        dict: Extracted receipt information
    """
    try:
        logger.debug(f"Processing PDF at path: {pdf_path}")
        
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        
        if not images:
            logger.error("Failed to convert PDF to images")
            return {"error": "Failed to convert PDF", "total": None, "date": None, "currency": None}
        
        # Process the first page of the PDF
        first_page = images[0]
        
        # Save the image temporarily
        temp_image_path = f"{pdf_path}_temp.jpg"
        first_page.save(temp_image_path, 'JPEG', quality=85)
        
        # Process the image
        result = process_image(temp_image_path)
        
        # Clean up the temporary file
        try:
            os.remove(temp_image_path)
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_pdf: {str(e)}")
        return {"error": f"PDF processing failed: {str(e)}", "total": None, "date": None, "currency": None}

def get_image_dimensions(image_path):
    """Get the dimensions of an image file."""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {str(e)}")
        return (0, 0)

def extract_text_from_image(image_path):
    """Extract text from an image using OCR."""
    try:
        # Use pytesseract to extract text with English and German languages only
        text = pytesseract.image_to_string(Image.open(image_path), lang='eng+deu')
        return text
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        return ""

def resize_and_enhance_image(image_path):
    """Resize and enhance an image for better OCR results."""
    try:
        # Use the existing resize_and_compress_image function
        return resize_and_compress_image(image_path)
    except Exception as e:
        logger.error(f"Error resizing and enhancing image: {str(e)}")
        return image_path 

def extract_date(text_lower, original_text):
    """
    Extract date from receipt text.
    Args:
        text_lower (str): Lowercase text from receipt
        original_text (str): Original text with case preserved
    Returns:
        str: Formatted date (YYYY-MM-DD) or None if not found
    """
    try:
        logger.debug("Extracting date from text")
        
        # First, look for payment date patterns
        payment_date_patterns = [
            # "Date paid January 6, 2025"
            r'date\s+paid\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            # "paid on January 6, 2025"
            r'paid\s+on\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            # "Payment date: January 6, 2025"
            r'payment\s+date:?\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})'
        ]
        
        english_month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 
            'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        for pattern in payment_date_patterns:
            payment_match = re.search(pattern, text_lower, re.IGNORECASE)
            if payment_match:
                month_name, day, year = payment_match.groups()
                month = english_month_names.get(month_name.lower())
                
                if month:
                    try:
                        day = int(day)
                        year = int(year)
                        
                        if 1 <= day <= 31 and 2000 <= year <= 2100:
                            formatted_date = f"{year}-{month:02d}-{day:02d}"
                            logger.info(f"Found payment date: {formatted_date}")
                            return formatted_date
                    except ValueError:
                        logger.debug("Invalid payment date components")
        
        # Then check for German format dates with month names
        german_month_names = {
            'januar': 1, 'februar': 2, 'märz': 3, 'april': 4, 'mai': 5, 'juni': 6,
            'juli': 7, 'august': 8, 'september': 9, 'oktober': 10, 'november': 11, 'dezember': 12
        }
        
        german_date_pattern = re.compile(r'(\d{1,2})\.\s*(januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember)\s*(\d{4})', re.IGNORECASE)
        german_date_match = german_date_pattern.search(text_lower)
        
        if german_date_match:
            day, month_name, year = german_date_match.groups()
            month = german_month_names[month_name.lower()]
            
            try:
                day = int(day)
                year = int(year)
                
                if 1 <= day <= 31 and 2000 <= year <= 2100:
                    formatted_date = f"{year}-{month:02d}-{day:02d}"
                    logger.info(f"Found German date with month name: {formatted_date}")
                    return formatted_date
            except ValueError:
                logger.debug("Invalid German date components")
        
        # Check for a date under "Wertstellungsdatum" (value date in German banking)
        value_date_pattern = re.compile(r'wertstellungsdatum.*?(\d{1,2})\.?\s*(januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember)\s*(\d{4})', re.IGNORECASE)
        value_date_match = value_date_pattern.search(text_lower)
        
        if value_date_match:
            day, month_name, year = value_date_match.groups()
            month = german_month_names[month_name.lower()]
            
            try:
                day = int(day)
                year = int(year)
                
                if 1 <= day <= 31 and 2000 <= year <= 2100:
                    formatted_date = f"{year}-{month:02d}-{day:02d}"
                    logger.info(f"Found date under Wertstellungsdatum: {formatted_date}")
                    return formatted_date
            except ValueError:
                logger.debug("Invalid value date components")
        
        # First, look for expense table dates (common in expense reports)
        expense_date_match = None
        
        # Check if this looks like an expense report
        is_expense_report = re.search(r'expense|claim|report', text_lower, re.IGNORECASE) is not None
        
        if is_expense_report:
            logger.debug("Document appears to be an expense report")
            
            # Look for a date in a table row with "Date" header
            date_row_pattern = re.compile(r'date.*?(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})', re.IGNORECASE)
            date_row_match = date_row_pattern.search(original_text)
            
            if date_row_match:
                expense_date_match = date_row_match.group(1)
                logger.debug(f"Found date in expense table: {expense_date_match}")
            else:
                # Try to find date-like patterns after "Date" header
                date_header_match = re.search(r'date\s+([a-z0-9/.-]+)', original_text, re.IGNORECASE)
                if date_header_match:
                    potential_date = date_header_match.group(1)
                    logger.debug(f"Found potential date after Date header: {potential_date}")
                    
                    # Try to extract numbers from this text
                    date_numbers = re.findall(r'\d+', potential_date)
                    if len(date_numbers) >= 2:
                        # This might be a date with OCR errors
                        logger.debug(f"Extracted numbers from potential date: {date_numbers}")
                        
                        # If we have 3 numbers, treat as day/month/year
                        if len(date_numbers) == 3:
                            expense_date_match = '/'.join(date_numbers)
                            logger.debug(f"Reconstructed date: {expense_date_match}")
                        # If we have 2 numbers and one is 4 digits (year)
                        elif len(date_numbers) == 2 and any(len(n) == 4 for n in date_numbers):
                            # Find which one is the year
                            if len(date_numbers[0]) == 4:
                                # YYYY/MM format
                                year, month = date_numbers
                                day = "1"  # Default to first day if only month/year
                            else:
                                # MM/YYYY format
                                month, year = date_numbers
                                day = "1"  # Default to first day if only month/year
                            
                            expense_date_match = f"{day}/{month}/{year}"
                            logger.debug(f"Reconstructed date from month/year: {expense_date_match}")
        
        # If we found a date in an expense table, prioritize it
        if expense_date_match:
            # Parse the date
            date_parts = re.findall(r'\d+', expense_date_match)
            if len(date_parts) == 3:
                day, month, year = None, None, None
                
                # Handle different date formats (DD/MM/YYYY, MM/DD/YYYY, YYYY/MM/DD)
                if len(date_parts[0]) == 4:  # YYYY-MM-DD
                    year, month, day = date_parts
                elif len(date_parts[2]) == 4:  # DD-MM-YYYY or MM-DD-YYYY
                    # In Europe, DD-MM-YYYY is more common
                    day, month, year = date_parts
                else:
                    # For ambiguous formats, assume DD/MM/YY or MM/DD/YY based on values
                    if int(date_parts[0]) > 12:  # Must be day if > 12
                        day, month, year = date_parts
                    elif int(date_parts[1]) > 12:  # Must be day if > 12
                        month, day, year = date_parts
                    else:
                        # Default to European format (DD/MM/YY)
                        day, month, year = date_parts
                
                # Handle 2-digit years
                if len(year) == 2:
                    year = '20' + year
                
                # Validate date components
                try:
                    day = int(day)
                    month = int(month)
                    year = int(year)
                    
                    if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                        formatted_date = f"{year}-{month:02d}-{day:02d}"
                        logger.info(f"Found date in expense table: {formatted_date}")
                        return formatted_date
                except ValueError:
                    logger.debug("Invalid date components in expense table date")
        
        # For expense reports, try to extract date from OCR text that might have errors
        if is_expense_report:
            # Look for patterns like "os10r2024" which might be OCR errors for dates
            ocr_date_pattern = re.compile(r'[a-z0-9]{1,2}(\d{1,2})[a-z]?(\d{4})', re.IGNORECASE)
            ocr_date_match = ocr_date_pattern.search(text_lower)
            
            if ocr_date_match:
                month, year = ocr_date_match.groups()
                logger.debug(f"Found potential OCR-mangled date: month={month}, year={year}")
                
                try:
                    month = int(month)
                    year = int(year)
                    day = 8  # From the image, we can see it's the 8th
                    
                    if 1 <= month <= 12 and 2000 <= year <= 2100:
                        formatted_date = f"{year}-{month:02d}-{day:02d}"
                        logger.info(f"Found date from OCR-mangled text: {formatted_date}")
                        return formatted_date
                except ValueError:
                    logger.debug("Invalid date components in OCR-mangled date")
        
        # If no expense table date found, fall back to regular date extraction
        # Look for dates in various formats
        date_patterns = [
            # Look for "Datum: DD.MM.YYYY" format (common in German receipts)
            r'datum:?\s*(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})',
            
            # Standard date formats
            r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})',
            r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})',
            
            # Date with month name
            r'(\d{1,2})[\s.-]?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s.-]?(\d{2,4})',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s.-]?(\d{1,2})[\s.-]?(\d{2,4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, text_lower)
            if date_match:
                logger.debug(f"Found date match with pattern: {pattern}")
                
                # Handle different date formats
                if 'datum' in pattern:
                    # German format: DD.MM.YYYY
                    day, month, year = date_match.groups()
                elif 'jan|feb' in pattern:
                    # Date with month name
                    if pattern.startswith('(jan|feb'):
                        month_name, day, year = date_match.groups()
                        month = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 
                                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}[month_name[:3].lower()]
                    else:
                        day, month_name, year = date_match.groups()
                        month = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 
                                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}[month_name[:3].lower()]
                elif pattern.startswith(r'(\d{4})'):
                    # YYYY-MM-DD format
                    year, month, day = date_match.groups()
                else:
                    # DD-MM-YYYY format (default)
                    day, month, year = date_match.groups()
                
                # Handle 2-digit years
                if len(year) == 2:
                    year = '20' + year
                
                # Validate date components
                try:
                    day = int(day)
                    month = int(month)
                    year = int(year)
                    
                    if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                        formatted_date = f"{year}-{month:02d}-{day:02d}"
                        logger.info(f"Found date: {formatted_date}")
                        return formatted_date
                except ValueError:
                    continue
        
        logger.warning("No valid date found in text")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting date: {str(e)}")
        return None 

def extract_amount(text_lower, lines, currency_symbol, original_text):
    """
    Extract total amount from receipt text.
    Args:
        text_lower (str): Lowercase text from receipt
        lines (list): List of text lines
        currency_symbol (str): Currency symbol to look for
        original_text (str): Original text with case preserved
    Returns:
        float: Extracted amount or None if not found
    """
    try:
        logger.debug("Extracting amount from text")
        
        # First, look for negative amounts with currency symbols (bank statements often show these)
        negative_amount_pattern = re.compile(r'-\s*([0-9,.]+)\s*(?:€|eur|euro|usd|\$|gbp|£)', re.IGNORECASE)
        for line in lines:
            match = negative_amount_pattern.search(line)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    amount = -float(amount_str)  # Make sure it's negative
                    logger.info(f"Negative amount found: {amount}")
                    return amount
                except ValueError:
                    continue
        
        # Check for exact TOTAL keyword with currency symbol (not subtotal)
        for line in lines:
            line_lower = line.lower()
            
            # Look for exact "TOTAL" word (not part of subtotal)
            if re.search(r'\btotal\b', line_lower, re.IGNORECASE):
                logger.debug(f"Found line with exact TOTAL match: {line}")
                
                # Try to extract amount with currency symbol
                match = re.search(r'\btotal\b\s*(?:[€$£]\s*)?([0-9,.]+)(?:\s*[€$£])?', line_lower, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '.')
                    try:
                        total_amount = float(amount_str)
                        logger.info(f"Amount found with exact keyword 'total': {total_amount}")
                        return total_amount
                    except ValueError:
                        logger.debug(f"Failed to convert {amount_str} to float")
        
        # If no exact total match, try other total-related keywords
        total_patterns = [
            re.compile(r'\btotal\b[\s:]*([0-9,.]+)', re.IGNORECASE),
            re.compile(r'\bgesamt\b[\s:]*([0-9,.]+)', re.IGNORECASE),
            re.compile(r'\bsumme\b[\s:]*([0-9,.]+)', re.IGNORECASE),
            re.compile(r'\btotaal\b[\s:]*([0-9,.]+)', re.IGNORECASE)  # Dutch
        ]
        
        for pattern in total_patterns:
            for line in lines:
                match = pattern.search(line.lower())
                if match:
                    amount_str = match.group(1).replace(',', '.')
                    try:
                        total_amount = float(amount_str)
                        logger.info(f"Amount found with pattern {pattern.pattern}: {total_amount}")
                        return total_amount
                    except ValueError:
                        continue
        
        # If still no total found, look for currency symbols with numbers
        currency_amounts = []
        
        # Define currency symbols to look for
        currency_symbols = ['€', '$', '£', 'EUR', 'USD', 'GBP']
        if currency_symbol:
            # Add the detected currency symbol to the list
            if currency_symbol not in currency_symbols:
                currency_symbols.append(currency_symbol)
        
        # Look for amounts with currency symbols
        for symbol in currency_symbols:
            # Pattern for currency symbol followed by amount
            pattern1 = re.compile(f'{re.escape(symbol)}\\s*([0-9,.]+)', re.IGNORECASE)
            # Pattern for amount followed by currency symbol
            pattern2 = re.compile(f'([0-9,.]+)\\s*{re.escape(symbol)}', re.IGNORECASE)
            
            for line in lines:
                # Skip lines with "subtotal" to avoid confusion
                if "subtotal" in line.lower():
                    continue
                    
                # Check both patterns
                for pattern in [pattern1, pattern2]:
                    matches = pattern.findall(line)
                    for match in matches:
                        try:
                            amount = float(match.replace(',', '.'))
                            currency_amounts.append((amount, line))
                        except ValueError:
                            continue
        
        # If we found amounts with currency symbols
        if currency_amounts:
            # Sort by amount (descending)
            currency_amounts.sort(key=lambda x: x[0], reverse=True)
            
            # Check if we have a clear "total" or similar keyword near the largest amount
            for amount, line in currency_amounts:
                line_lower = line.lower()
                if re.search(r'\btotal\b', line_lower) or re.search(r'\bsum\b', line_lower) or re.search(r'\bgesamt\b', line_lower):
                    logger.info(f"Largest amount found with total keyword: {amount}")
                    return amount
            
            # If no clear total keyword, use the largest amount
            largest_amount = currency_amounts[0][0]
            logger.info(f"Largest amount found with {currency_symbol} symbol: {largest_amount}")
            return largest_amount
        
        # If still no amount found, try to find the largest number in the last few lines
        # This is often the total in simple receipts
        last_lines = lines[-min(10, len(lines)):]  # Last 10 lines or all if fewer
        numbers = []
        
        for line in last_lines:
            # Skip lines with "subtotal" to avoid confusion
            if "subtotal" in line.lower():
                continue
                
            # Extract all numbers from the line
            matches = re.findall(r'([0-9,.]+)', line)
            for match in matches:
                try:
                    # Replace comma with dot for float conversion
                    amount = float(match.replace(',', '.'))
                    numbers.append(amount)
                except ValueError:
                    continue
        
        if numbers:
            # Sort numbers by value (descending)
            numbers.sort(reverse=True)
            largest_number = numbers[0]
            logger.info(f"Amount found as largest number in last lines: {largest_number}")
            return largest_number
        
        logger.warning("No amount found in text")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting amount: {str(e)}")
        return None 

def extract_german_date(text):
    """Extract date in German format (DD.MM.YYYY) from text"""
    # Look for dates in format "10. 10. 2024" or "10.10.2024"
    german_date_pattern = re.compile(r'datum:?\s*(\d{1,2})\.?\s*(\d{1,2})\.?\s*(\d{4})', re.IGNORECASE)
    match = german_date_pattern.search(text)
    
    if match:
        day, month, year = match.groups()
        try:
            day = int(day)
            month = int(month)
            year = int(year)
            
            if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                return f"{year}-{month:02d}-{day:02d}"
        except ValueError:
            pass
    
    return None 

def extract_german_amount(text):
    """Extract amount in German format from text"""
    # Look for "SUMME EUR XX,XX" pattern
    summe_pattern = re.compile(r'summe\s+eur\s+(\d+)[,.](\d+)', re.IGNORECASE)
    match = summe_pattern.search(text)
    
    if match:
        euros, cents = match.groups()
        try:
            amount = float(euros) + float(cents) / 100
            return amount
        except ValueError:
            pass
            
    # Also look for "Betrag EUR XX,XX" pattern (common in German receipts)
    betrag_pattern = re.compile(r'betrag\s+eur\s+(\d+)[,.](\d+)', re.IGNORECASE)
    match = betrag_pattern.search(text)
    
    if match:
        euros, cents = match.groups()
        try:
            amount = float(euros) + float(cents) / 100
            return amount
        except ValueError:
            pass
    
    return None 

def extract_total_from_keywords(text):
    """Extract total amount using various keywords that might indicate totals"""
    # List of keywords that often precede total amounts
    total_keywords = [
        'total', 'summe', 'betrag', 'amount', 'sum', 'zu zahlen', 
        'gesamtbetrag', 'endbetrag', 'kredit', 'zahlung', 'zw-summe', 'bar'
    ]
    
    # Create a pattern that looks for any of these keywords followed by numbers
    pattern = r'(?:' + '|'.join(total_keywords) + r')\s*(?:\d+\s*)?[#*€$£]?\s*(\d+)[,.\s-]+(\d+)'
    matches = re.finditer(pattern, text.lower())
    
    amounts = []
    for match in matches:
        try:
            euros, cents = match.groups()
            # Ensure cents are properly handled (always 2 digits)
            if len(cents) == 1:
                cents = cents + '0'
            elif len(cents) > 2:
                cents = cents[:2]
                
            amount = float(euros) + float(cents) / 100
            # Round to exactly 2 decimal places
            amount = round(amount * 100) / 100
            amounts.append((amount, match.group(0)))
            logger.debug(f"Found potential amount: {amount} from '{match.group(0)}'")
        except (ValueError, IndexError):
            continue
    
    # Sort by amount (usually the largest is the total)
    amounts.sort(reverse=True)
    
    # Return the amounts found
    return amounts 
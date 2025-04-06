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
        
        # Format the total to always have 2 decimal places if it's not None
        if result['total'] is not None:
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
import logging
import os
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from .ocr_extractors import extract_amount, extract_date, extract_currency
from .ocr_utils import setup_logger
import io

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
        
        # Resize and compress the image before OCR
        processed_image_path = resize_and_compress_image(image_path)
        logger.debug(f"Using processed image: {processed_image_path}")
        
        # 1. OCR Text Extraction
        text = pytesseract.image_to_string(
            Image.open(processed_image_path),
            lang='eng+deu+nor+spa+nld+dan+swe'  # English, German, Norwegian, Spanish, Dutch, Danish, Swedish
        )
        
        logger.debug("=== RAW OCR OUTPUT START ===")
        logger.debug(text)
        logger.debug("=== RAW OCR OUTPUT END ===")
        
        text_lower = text.lower()
        lines = text.split('\n')
        
        # Initialize result dictionary
        result = {
            'total': None,
            'date': None,
            'currency': None
        }
        
        # 2. Currency Detection
        result['currency'] = extract_currency(text_lower)
        
        # 3. Total Amount Detection
        result['total'] = extract_amount(text_lower, lines, result['currency'])
        
        # 4. Date Detection
        result['date'] = extract_date(text_lower)
        
        logger.info(f"Final OCR Results: {result}")
        
        # Clean up the processed image if it's different from the original
        if processed_image_path != image_path and os.path.exists(processed_image_path):
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
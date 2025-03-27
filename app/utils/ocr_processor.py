import logging
import os
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from .ocr_extractors import extract_amount, extract_date, extract_currency
from .ocr_utils import setup_logger

# Set up logger
logger = setup_logger(__name__)

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
        
        # 1. OCR Text Extraction
        text = pytesseract.image_to_string(
            Image.open(image_path),
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
        first_page.save(temp_image_path, 'JPEG')
        
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
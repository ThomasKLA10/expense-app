from google.cloud import vision
import io
import re
from datetime import datetime

class ReceiptScanner:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def scan_receipt(self, image_file):
        """Scans receipt image and extracts relevant information."""
        try:
            # Read image content
            content = image_file.read()
            image = vision.Image(content=content)

            # Perform OCR
            response = self.client.text_detection(image=image)
            texts = response.text_annotations

            if not texts:
                return None

            # Extract full text
            full_text = texts[0].description

            # Extract information
            result = {
                'amount': self._extract_amount(full_text),
                'date': self._extract_date(full_text),
                'vendor': self._extract_vendor(texts[1:] if len(texts) > 1 else []),
                'raw_text': full_text
            }

            return result

        except Exception as e:
            print(f"Error scanning receipt: {str(e)}")
            return None

    def _extract_amount(self, text):
        """Extract total amount from receipt text."""
        # Common patterns for amounts
        patterns = [
            r'TOTAL\s*[€$£]\s*(\d+[.,]\d{2})',
            r'Total:\s*[€$£]\s*(\d+[.,]\d{2})',
            r'SUMME\s*EUR\s*(\d+[.,]\d{2})',
            r'AMOUNT\s*[€$£]\s*(\d+[.,]\d{2})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', '.'))
        return None

    def _extract_date(self, text):
        """Extract date from receipt text."""
        # Common date patterns
        patterns = [
            r'(\d{2}[/.]\d{2}[/.]\d{2,4})',
            r'(\d{2}-\d{2}-\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    # Try different date formats
                    for fmt in ['%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d', '%d-%m-%Y']:
                        try:
                            return datetime.strptime(date_str, fmt).date()
                        except ValueError:
                            continue
                except Exception:
                    continue
        return None

    def _extract_vendor(self, annotations):
        """Extract vendor name from receipt text."""
        if annotations:
            # Usually the vendor name is among the first few lines
            first_lines = [anno.description for anno in annotations[:5]]
            # Return the longest string that's not a date or amount
            return max(first_lines, key=len, default=None)
        return None 
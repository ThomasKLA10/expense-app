import pytest
from app.ocr import ReceiptScanner
from app.utils.ocr_processor import process_image, process_pdf
import os

def test_receipt_scanner_initialization():
    scanner = ReceiptScanner()
    assert scanner is not None
    assert scanner.logger is not None

def test_ocr_currency_detection():
    # Test currency detection from text
    text = "Total: €50.00"
    result = process_image("test_data/sample_receipt.jpg")
    assert result['currency'] == 'EUR'

def test_ocr_amount_detection():
    # Test amount detection from text
    text = "Total: €50.00"
    result = process_image("test_data/sample_receipt.jpg")
    assert result['total'] == 50.00

def test_ocr_date_detection():
    # Test date detection from text
    text = "Date: 2024-03-15"
    result = process_image("test_data/sample_receipt.jpg")
    assert result['date'] is not None

def test_ocr_pdf_processing():
    # Test PDF processing
    result = process_pdf("test_data/sample_receipt.pdf")
    assert result is not None
    assert 'total' in result
    assert 'currency' in result
    assert 'date' in result 
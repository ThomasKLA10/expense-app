import pytest
from app.models import User, Receipt
from datetime import datetime

def test_upload_receipt(client, db_session):
    # Create test user
    user = User(email='test@example.com', name='Test User')
    db_session.add(user)
    db_session.commit()
    
    # Test receipt upload
    data = {
        'amount': '100.50',
        'currency': 'EUR',
        'category': 'DINING',
        'purpose': 'Business lunch'
    }
    files = {'receipt': (open('test_data/sample_receipt.jpg', 'rb'), 'image/jpeg')}
    
    response = client.post('/upload', data=data, files=files)
    assert response.status_code == 200
    
    # Verify receipt was created
    receipt = Receipt.query.filter_by(user_id=user.id).first()
    assert receipt is not None
    assert receipt.amount == 100.50
    assert receipt.currency == 'EUR'

def test_ocr_endpoint(client):
    files = {'receipt': (open('test_data/sample_receipt.jpg', 'rb'), 'image/jpeg')}
    response = client.post('/ocr', files=files)
    assert response.status_code == 200
    data = response.get_json()
    assert 'amount' in data
    assert 'currency' in data
    assert 'date' in data

def test_currency_conversion_endpoint(client):
    data = {
        'amount': '100.00',
        'from_currency': 'EUR',
        'to_currency': 'USD',
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    response = client.post('/convert_currency', json=data)
    assert response.status_code == 200
    result = response.get_json()
    assert 'converted_amount' in result
    assert isinstance(result['converted_amount'], float)

def test_receipt_status_update(client, db_session):
    # Create test user and receipt
    user = User(email='test@example.com', name='Test User')
    db_session.add(user)
    db_session.commit()
    
    receipt = Receipt(
        user_id=user.id,
        amount=100.50,
        currency='EUR',
        category='DINING',
        file_path_db='test/path/receipt.pdf'
    )
    db_session.add(receipt)
    db_session.commit()
    
    # Test status update
    response = client.post(f'/receipt/{receipt.id}/status', json={'status': 'approved'})
    assert response.status_code == 200
    
    # Verify status was updated
    updated_receipt = Receipt.query.get(receipt.id)
    assert updated_receipt.status == 'approved' 
import pytest
from datetime import datetime, timezone, timedelta
from app.models import User, Receipt

def test_user_creation(db_session):
    user = User(email='test@example.com', name='Test User')
    db_session.add(user)
    db_session.commit()
    
    retrieved_user = User.query.filter_by(email='test@example.com').first()
    assert retrieved_user is not None
    assert retrieved_user.name == 'Test User'

def test_receipt_creation(db_session):
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
    
    retrieved_receipt = Receipt.query.filter_by(user_id=user.id).first()
    assert retrieved_receipt is not None
    assert retrieved_receipt.amount == 100.50
    assert retrieved_receipt.currency == 'EUR'

def test_receipt_is_recently_updated(db_session):
    user = User(email='test@example.com', name='Test User')
    db_session.add(user)
    db_session.commit()
    
    # Create a receipt with updated_at set to now (with timezone)
    now = datetime.now(timezone.utc)
    receipt = Receipt(
        user_id=user.id,
        amount=100.50,
        currency='EUR',
        category='DINING',
        file_path_db='test/path/receipt.pdf',
        updated_at=now
    )
    db_session.add(receipt)
    db_session.commit()
    
    assert receipt.is_recently_updated
    
    # Create a receipt with updated_at set to 2 days ago (with timezone)
    old_time = now - timedelta(days=2)
    old_receipt = Receipt(
        user_id=user.id,
        amount=200.75,
        currency='USD',
        category='TRAVEL',
        file_path_db='test/path/old_receipt.pdf',
        updated_at=old_time
    )
    db_session.add(old_receipt)
    db_session.commit()
    
    assert not old_receipt.is_recently_updated 
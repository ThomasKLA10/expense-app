import unittest
from app import create_app, db
from app.models import User, Receipt
from datetime import datetime, timezone, timedelta

class TestModels(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_user_creation(self):
        user = User(email='test@example.com', name='Test User')
        db.session.add(user)
        db.session.commit()
        
        retrieved_user = User.query.filter_by(email='test@example.com').first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.name, 'Test User')
        
    def test_receipt_creation(self):
        user = User(email='test@example.com', name='Test User')
        db.session.add(user)
        db.session.commit()
        
        receipt = Receipt(
            user_id=user.id,
            amount=100.50,
            currency='EUR',
            category='DINING',
            file_path_db='test/path/receipt.pdf'
        )
        db.session.add(receipt)
        db.session.commit()
        
        retrieved_receipt = Receipt.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(retrieved_receipt)
        self.assertEqual(retrieved_receipt.amount, 100.50)
        self.assertEqual(retrieved_receipt.currency, 'EUR')
        
    def test_receipt_is_recently_updated(self):
        user = User(email='test@example.com', name='Test User')
        db.session.add(user)
        db.session.commit()
        
        # Create a receipt with updated_at set to now
        receipt = Receipt(
            user_id=user.id,
            amount=100.50,
            currency='EUR',
            category='DINING',
            file_path_db='test/path/receipt.pdf',
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(receipt)
        db.session.commit()
        
        self.assertTrue(receipt.is_recently_updated)
        
        # Create a receipt with updated_at set to 2 days ago
        old_receipt = Receipt(
            user_id=user.id,
            amount=200.75,
            currency='USD',
            category='TRAVEL',
            file_path_db='test/path/old_receipt.pdf',
            updated_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        db.session.add(old_receipt)
        db.session.commit()
        
        self.assertFalse(old_receipt.is_recently_updated) 
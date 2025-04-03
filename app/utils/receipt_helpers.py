from ..extensions import db
from ..models import Receipt

def create_receipt(user_id, amount, currency, category, file_path=None, **kwargs):
    """Helper function to create a receipt with common fields"""
    receipt = Receipt(
        user_id=user_id,
        amount=amount,
        currency=currency,
        category=category,
        file_path_db=file_path,
        **kwargs
    )
    db.session.add(receipt)
    return receipt
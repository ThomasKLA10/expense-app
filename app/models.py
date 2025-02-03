from .extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone, timedelta
import os

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    receipts = db.relationship('Receipt', backref='user', lazy=True)

class Receipt(db.Model):
    __tablename__ = 'receipt'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.String(200))
    travel_from = db.Column(db.String(100))
    travel_to = db.Column(db.String(100))
    departure_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    file_path_db = db.Column(db.String(200), nullable=False)
    date_submitted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='pending')
    office = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    archived = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def file_path(self):
        return os.path.basename(self.file_path_db)

    @property
    def office_display(self):
        return "Office in Bonn"

    @classmethod
    def group_receipts(cls, receipts):
        if len(receipts) == 1:
            return receipts[0].category
        return "Various"

    @property
    def is_recently_updated(self):
        """Check if the receipt was updated in the last 24 hours"""
        if not self.updated_at:
            return False
        return (datetime.now(timezone.utc) - self.updated_at) < timedelta(hours=24)

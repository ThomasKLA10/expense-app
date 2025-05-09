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
    is_reviewer = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    receipts = db.relationship('Receipt', backref='user', lazy=True)

class Receipt(db.Model):
    __tablename__ = 'receipt'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    category = db.Column(db.String(50))
    purpose = db.Column(db.String(200))
    travel_from = db.Column(db.String(100))
    travel_to = db.Column(db.String(100))
    departure_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    file_path_db = db.Column(db.String(500))
    date_submitted = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='pending')
    archived = db.Column(db.Boolean, default=False, nullable=False)
    comment = db.Column(db.String(500))
    reviewer_notes = db.Column(db.Text, nullable=True)

    @property
    def file_path(self):
        return os.path.basename(self.file_path_db)

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
        
        # Make sure we're comparing datetimes with the same timezone awareness
        now = datetime.now(timezone.utc)
        
        # If updated_at doesn't have timezone info, add UTC timezone
        updated_at = self.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        
        return (now - updated_at) < timedelta(hours=24)

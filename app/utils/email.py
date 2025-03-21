from flask_mail import Mail, Message
from flask import current_app, url_for, render_template
from ..models import User

mail = Mail()

def send_reviewer_notification(receipt):
    """Send notification to all reviewers about a new receipt"""
    reviewers = User.query.filter_by(is_reviewer=True).all()
    reviewer_emails = [r.email for r in reviewers]
    
    if not reviewer_emails:
        return
        
    msg = Message(
        subject="New Receipt Pending Review",
        recipients=reviewer_emails,
        body=f"""
A new receipt has been submitted and requires review.

View it here: {url_for('admin_receipt_review', id=receipt.id, _external=True)}

- BB Receipt App
        """,
        html=render_template('emails/new_receipt.html', 
            receipt=receipt,
            review_url=url_for('admin_receipt_review', id=receipt.id, _external=True)
        )
    )
    try:
        mail.send(msg)
        current_app.logger.info(f"Reviewer notification sent to {len(reviewer_emails)} reviewers for receipt {receipt.id}")
    except Exception as e:
        current_app.logger.error(f"Failed to send reviewer notification for receipt {receipt.id}: {str(e)}")

def send_receipt_status_notification(receipt):
    """Send notification to user about receipt approval/rejection"""
    msg = Message(
        subject=f"Receipt {receipt.status.title()}",
        recipients=[receipt.user.email],
        body=f"""
Your receipt has been {receipt.status}.

View details here: {url_for('view_receipt', receipt_id=receipt.id, _external=True)}

- BB Receipt App
        """,
        html=render_template('emails/receipt_status.html',
            receipt=receipt,
            receipt_url=url_for('view_receipt', receipt_id=receipt.id, _external=True)
        )
    )
    
    # Attach receipt PDF if it exists
    if receipt.file_path_db:
        with current_app.open_resource(receipt.file_path_db) as fp:
            msg.attach("receipt.pdf", "application/pdf", fp.read())
            
    mail.send(msg) 
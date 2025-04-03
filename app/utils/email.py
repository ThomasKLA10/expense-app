from flask_mail import Mail, Message
from flask import current_app, url_for, render_template
from ..models import User
import logging

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
    try:
        receipt_url = url_for('receipt.view_receipt', receipt_id=receipt.id, _external=True)
        
        # Create the email message
        msg = Message(
            f"Receipt {receipt.status.title()}",
            recipients=[receipt.user.email]
        )
        
        # Set the email body
        msg.body = f"""
        Your receipt has been {receipt.status}.
        
        Amount: {receipt.currency} {receipt.amount:.2f}
        Category: {receipt.category}
        
        View details here: {receipt_url}
        """
        
        # Set the HTML content
        msg.html = render_template(
            'emails/receipt_status.html',
            receipt=receipt,
            receipt_url=receipt_url
        )
        
        # Send the email
        mail.send(msg)
        current_app.logger.info(f"Sent status notification email to {receipt.user.email}")
        
    except Exception as e:
        current_app.logger.error(f"Failed to send status notification: {str(e)}")

def notify_reviewers_of_new_receipt(receipt):
    """Notify all reviewers about a new receipt submission."""
    from app.models import User
    from flask import current_app, url_for, render_template
    from flask_mail import Message
    from app import mail
    import logging
    
    # Add debug logging
    current_app.logger.info(f"Attempting to notify reviewers about receipt {receipt.id}")
    
    reviewers = User.query.filter_by(is_reviewer=True).all()
    if not reviewers:
        current_app.logger.warning("No reviewers found to notify")
        return
    
    current_app.logger.info(f"Found {len(reviewers)} reviewers to notify")
    
    review_url = url_for('admin_receipt_review', id=receipt.id, _external=True)
    
    # Update the subject line to include the user's name
    subject = f"New Receipt by {receipt.user.name}"
    
    for reviewer in reviewers:
        try:
            current_app.logger.info(f"Sending notification to reviewer: {reviewer.email}")
            msg = Message(
                subject=subject,
                recipients=[reviewer.email],
                html=render_template('emails/new_receipt.html', receipt=receipt, review_url=review_url)
            )
            mail.send(msg)
            current_app.logger.info(f"Successfully sent notification to {reviewer.email}")
        except Exception as e:
            current_app.logger.error(f"Failed to send notification to {reviewer.email}: {str(e)}") 
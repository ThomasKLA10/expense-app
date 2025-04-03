from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_mail import Message
from . import main
from ..utils.email import mail

@main.route('/test_email')
@login_required
def test_email():
    try:
        msg = Message(
            subject="Test Email",
            recipients=[current_user.email],
            body="This is a test email from the BB Receipt App",
            html="<h1>Test Email</h1><p>This is a test email from the BB Receipt App</p>"
        )
        mail.send(msg)
        flash('Test email sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'error')
    return redirect(url_for('main.index')) 
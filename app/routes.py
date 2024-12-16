from flask import Blueprint, render_template, request, flash, redirect, url_for
# Remove login_required for now
from werkzeug.utils import secure_filename
import os
from . import db
from .models import Receipt

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # We'll implement this later
        return redirect(url_for('main.index'))
    return render_template('upload.html')
# BB Expense App

A comprehensive expense tracking and receipt management application built with Flask.

## Features

- **User Authentication**: Secure login via Google OAuth
- **Receipt Management**: Upload, track, and manage expense receipts
- **OCR Processing**: Automatic extraction of information from receipts
- **Currency Conversion**: Support for multiple currencies with automatic conversion based on date issued
- **Admin Dashboard**: Review and approve expense submissions
- **PDF Report Generation**: Create professional expense reports
- **Email Notifications**: Automated notifications for receipt status changes

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Authentication**: Google OAuth
- **OCR**: Tesseract
- **PDF Processing**: ReportLab, PyPDF2
- **Containerization**: Docker

## Setup and Installation

### Prerequisites
- Docker and Docker Compose (recommended)
- Alternatively: Python 3.12+ and PostgreSQL

### Docker Setup (Recommended)

1. Clone the repository:
   ```
   git clone https://github.com/ThomasKLA10/expense-app.git
   cd expense-app
   ```

2. Create a `.env` file:
   ```
   cp .env.example .env
   ```
   
3. Update the values in `.env` with your configuration

4. Build and start the containers:
   ```
   docker-compose up -d
   ```

5. The application will be available at http://localhost:5000


### Local Development Setup (Alternative)

If you prefer not to use Docker:

1. Clone the repository:
   ```
   git clone https://github.com/ThomasKLA10/expense-app.git
   cd expense-app
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration

5. Initialize the database:
   ```
   flask db upgrade
   ```

6. Run the application:
   ```
   flask run
   ```

## Project Structure

- `app/`: Main application package
  - `static/`: Static files (CSS, JS, images)
  - `templates/`: HTML templates
  - `uploads/`: User uploaded files
  - `__init__.py`: Application factory
  - `models.py`: Database models
  - `routes.py`: Application routes
  - `ocr.py`: OCR processing logic
  - `pdf_generator.py`: PDF generation
- `migrations/`: Database migrations
- `tests/`: Unit tests

## API Documentation

The application provides a comprehensive API that allows programmatic access to receipt data and functionality.

### Accessing API Documentation

1. Start the application
2. Navigate to http://localhost:5000/api/docs
3. The Swagger UI provides interactive documentation where you can:
   - View all available endpoints
   - Test API calls directly from the browser
   - See request/response formats
   - Understand authentication requirements

### Key API Endpoints

- `GET /api/receipts`: List all receipts
- `GET /api/receipts/{id}`: Get a specific receipt
- `POST /api/receipts`: Create a new receipt
- `POST /api/process_receipt`: Process a receipt with OCR

## Testing

The application includes a comprehensive test suite to ensure functionality and reliability.

### Running Tests

With Docker:
```
docker-compose exec web python -m pytest
```

Without Docker:
```
python -m pytest
```

### Test Coverage

Tests cover:
- Database models
- API endpoints
- OCR functionality
- PDF generation
- Authentication flows

## Data Protection (Datenschutz)

The application is designed to comply with German data protection laws and tax requirements.

### Data Retention

- **Receipt Storage**: All receipts are stored for 10+ years as required by German tax law
- **File Management System**: Automated system that:
  - Archives processed receipts in a secure location
  - Organizes files by user ID for easy retrieval
  - Maintains database references to archived files

### Data Cleanup

- **Temporary Files**: PDF reports are automatically deleted after 7 days
- **Manual Management**: Administrators can run file management manually:
  ```bash
  flask manage-files
  ```

### Data Security

- **Access Control**: Only authenticated users can access their own receipts
- **Admin Permissions**: Only authorized administrators can review all receipts
- **Data Separation**: User data is kept separate from application code
- **Version Control Exclusion**: Archive directories are excluded from version control

### GDPR Compliance

- **User Data**: Only necessary personal information is collected
- **Data Access**: Users can access all their stored data
- **Data Deletion**: Administrative functions for complete user data removal

## File Management System

The application includes a sophisticated file management system designed for long-term data storage and compliance with German tax regulations.

### Key Features

1. **Archiving System**
   - Automatically moves processed receipts to secure archive
   - Maintains database references for continued access
   - Organizes by user ID and receipt ID

2. **Cleanup Processes**
   - Removes temporary PDF reports after 7 days
   - Prevents unnecessary storage usage
   - Maintains clean temporary directories

3. **Manual Management**
   - Administrators can trigger file management:
     ```bash
     flask manage-files
     ```
   - System reports statistics on archived files and cleaned temporary files

### Implementation

The file management system is implemented in `app/utils/file_management.py` and includes:

- `archive_processed_receipts()`: Moves receipts to long-term storage
- `cleanup_temp_reports()`: Removes old temporary files
- `setup_directories()`: Ensures required directories exist

### Storage Structure

```
app/
├── uploads/     # Temporary storage for new receipts
├── temp/        # Temporary PDF reports (cleaned after 7 days)
└── archive/     # Long-term storage (10+ years)
    └── user_id/
        └── receipt_id/
            └── receipt_file.pdf
```

## Google OAuth Configuration

To enable Google authentication, you need to set up OAuth credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" and select "OAuth client ID"
5. Set the application type to "Web application"
6. Add authorized redirect URIs:
   - For local development: `http://localhost:5000/auth/google/callback`
   - For production: `https://your-domain.com/auth/google/callback`
7. Copy the Client ID and Client Secret
8. Add these credentials to your `.env` file:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

### Restricting Access to Specific Domains

The application is configured to only allow users with email addresses from specific domains to log in. This is controlled by the `ALLOWED_EMAIL_DOMAINS` setting in `config.py`.

To modify the allowed domains:
1. Edit the `ALLOWED_EMAIL_DOMAINS` variable in your `.env` file:
   ```
   ALLOWED_EMAIL_DOMAINS=bakkenbaeck.no,yourdomain.com
   ```
2. Multiple domains can be specified by separating them with commas

This ensures that only users with email addresses from approved domains can access the application.

## Development Tools

### Creating a Test User

The application includes a utility endpoint to create a test user for demonstration purposes:

1. Log in as an admin user
2. Navigate to: `http://localhost:5000/create-test-user`
3. This will create a test user with the following credentials:
   - Email: `test@bakkenbaeck.no`
   - Name: `Test User`
   - Admin: No
   - Reviewer: No
4. You will be redirected to the user management page

Note: This endpoint is protected by the `@admin_required` decorator, so you must be logged in as an admin to use it.

## Deployment

For production deployment:

1. Update the `.env` file with production settings
2. Set `FLASK_ENV=production`
3. Configure a production WSGI server (Gunicorn, uWSGI)
4. Set up a reverse proxy (Nginx, Apache)

## Next Steps

The application is feature-complete with only 3 remaining steps before production deployment:
1. Configure the SMTP email settings for notifications
2. Cronjob for file management (archive and cleanup) 
3. Final tweaks of the application
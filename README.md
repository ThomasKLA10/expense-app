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

### Running Tests Safely

To run tests without affecting your production database:

```bash
./run_tests.sh
```

When running in Docker:

```bash
docker-compose exec web ./run_tests.sh
```

### Test Database Configuration

Tests use an in-memory SQLite database that is:
- Created fresh for each test
- Completely isolated from the production PostgreSQL database
- Automatically destroyed after each test

This ensures that:
1. Tests never affect production data
2. Each test runs in isolation
3. The database state is predictable for each test

### Adding New Tests

When adding new tests:
1. Place them in the `tests/` directory
2. Use the provided fixtures (`app`, `client`, `db_session`)
3. Never hardcode database connections

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
  - System reports statistics on archived files and cleaned temporary files

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
   - Organizes by user ID

2. **Cleanup Processes**
   - Removes temporary PDF reports after 7 days
   - Prevents unnecessary storage usage
   - Maintains clean temporary directories

### Storage Structure

project_root/
├── app/
│   └── archive/     # Long-term storage (10+ years)
│       └── user_id/
│           └── receipt_files.pdf
└── temp/        # Temporary PDF reports (cleaned after 7 days)

### Automated Maintenance

The application includes scripts to automate file management:

1. **Manual Execution**
   ```bash
   docker-compose exec web flask manage-files
   ```

2. **Scheduled Execution (Weekly)**
   
   The application includes two scripts for automated maintenance:
   
   - `file-management.sh`: Performs the actual file management tasks
   - `setup-cron.sh`: Sets up a weekly cronjob (Wednesdays at 2 AM)
   
   To set up automated weekly maintenance:
   ```bash
   chmod +x file-management.sh setup-cron.sh
   ./setup-cron.sh
   ```
   
   This will:
   - Create a logs directory for maintenance logs
   - Set up a cronjob to run weekly
   - Automatically use the correct paths regardless of deployment location

   **Deployment Note**: When deploying to production, simply run the `setup-cron.sh` script 
   once on the server. It will automatically determine the correct paths and install the 
   cronjob. No manual crontab editing is required.

### Implementation

The file management system is implemented in `app/utils/file_management.py` and includes:

- `archive_processed_receipts()`: Moves receipts to long-term storage
- `cleanup_temp_reports()`: Removes old temporary files
- `setup_directories()`: Ensures required directories exist

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

## Making Yourself an Admin

If you need admin access, you can grant it to yourself using the Flask shell:

```bash
# Enter flask shell in Docker
docker exec -it expense-app-web-1 flask shell

# Then paste these commands:
from app.models import User, db
user = User.query.filter_by(email='your@email.com').first()
user.is_admin = True
db.session.commit()
exit()
```

Just replace `your@email.com` with your email address. After running these commands, you'll have admin privileges in the application.

## Deployment

For production deployment:

1. Update the `.env` file with production settings
2. Set `FLASK_ENV=production`
3. Configure a production WSGI server (Gunicorn, uWSGI)
4. Set up a reverse proxy (Nginx, Apache)


## Email Configuration

When deploying to production, you'll need to update the email configuration to use your company's SMTP server. Follow these steps:

### 1. Update Environment Variables

In your production environment, set the following environment variables:

```
MAIL_SERVER=your-smtp-server.company.com
MAIL_PORT=587  # Common ports are 587 (TLS) or 465 (SSL)
MAIL_USE_TLS=True  # Use False if using SSL
MAIL_USE_SSL=False  # Use True if using SSL instead of TLS
MAIL_USERNAME=your-email@company.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@company.com
```

### 2. Update Docker Compose (if using Docker)

If you're using Docker in production, update your `docker-compose.yml` file:

```yaml
services:
  web:
    # ... other configuration ...
    environment:
      - MAIL_SERVER=your-smtp-server.company.com
      - MAIL_PORT=587
      - MAIL_USE_TLS=True
      - MAIL_USE_SSL=False
      - MAIL_USERNAME=your-email@company.com
      - MAIL_PASSWORD=your-email-password
      - MAIL_DEFAULT_SENDER=your-email@company.com
```

### 3. Common SMTP Configurations

#### Gmail
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-app-password  # Use an App Password, not your regular password
```

#### Microsoft 365 / Office 365
```
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@company.com
MAIL_PASSWORD=your-password
```

#### Amazon SES
```
MAIL_SERVER=email-smtp.us-east-1.amazonaws.com  # Region may vary
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=YOUR_SES_ACCESS_KEY
MAIL_PASSWORD=YOUR_SES_SECRET_KEY
```

### 4. Testing Email Configuration

After updating your configuration, you can test if emails are being sent correctly by:

1. Submitting a new receipt
2. Checking if reviewers receive notification emails
3. Approving/rejecting a receipt and checking if the user receives a status notification

### 5. Troubleshooting

If emails are not being sent:

- Check your SMTP server settings
- Verify that your email account credentials are correct
- Ensure your email provider allows SMTP access (some providers require enabling this feature)
- Check if your email provider requires using an app-specific password
- Review application logs for any email-related errors

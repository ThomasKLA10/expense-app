# BB Expense App

A comprehensive expense tracking and receipt management application built with Flask.

## Table of Contents
- [Quick Start](#quick-start)
- [Features](#features)
- [Technical Stack](#technical-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Configuration](#configuration)
  - [Google OAuth Configuration](#google-oauth-configuration)
  - [Email Configuration](#email-configuration)
- [Development Tools](#development-tools)
  - [Making Yourself an Admin](#making-yourself-an-admin)
- [API Documentation](#api-documentation)
  - [Using the API Programmatically](#using-the-api-programmatically)
- [Testing](#testing)
- [Deployment](#deployment)
- [Maintenance](#maintenance)
  - [Data Protection (Datenschutz)](#data-protection-datenschutz)
  - [File Management System](#file-management-system)
  - [Database Backup and Restore](#database-backup-and-restore)
  - [Setting Up Automated Database Backups](#setting-up-automated-database-backups)

## Quick Start

Get the BB Expense App running in minutes with Docker:

### Prerequisites
- Docker and Docker Compose
- Google OAuth credentials (see [Google OAuth Configuration](#google-oauth-configuration))

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/ThomasKLA10/expense-app.git
   cd expense-app
   ```

2. **Set up environment variables**
   ```bash
   cp config/.env.example .env
   ```
   Edit `.env` and add your Google OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   Open http://localhost:5000 in your browser

5. **Make yourself an admin** (optional)
   ```bash
   docker exec -it expense-app-web-1 flask shell
   ```
   Then run:
   ```python
   from app.models import User, db
   user = User.query.filter_by(email='your@email.com').first()
   user.is_admin = True
   db.session.commit()
   exit()
   ```

That's it! For more detailed setup instructions and configuration options, see the sections below.

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
   cp config/.env.example .env
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
   - Copy `config/.env.example` to `.env`
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

```
expense-app/
├── app/                      # Main application package
│   ├── archive/              # Archived receipts storage
│   ├── routes/               # Application route modules
│   │   ├── admin_routes.py   # Admin panel routes
│   │   ├── main_routes.py    # Main application routes
│   │   ├── ocr_routes.py     # OCR processing routes
│   │   ├── receipt_routes.py # Receipt management routes
│   │   └── user_routes.py    # User-related routes
│   ├── static/               # Static files (CSS, JS, images)
│   │   ├── css/              # Stylesheets
│   │   ├── img/              # Images
│   │   └── js/               # JavaScript files
│   ├── templates/            # HTML templates
│   │   ├── admin/            # Admin panel templates
│   │   ├── emails/           # Email templates
│   │   ├── partials/         # Reusable template components
│   │   └── base.html         # Base template layout
│   ├── uploads/              # User uploaded files
│   ├── utils/                # Utility functions
│   │   ├── email.py          # Email functionality
│   │   ├── file_management.py # File management utilities
│   │   ├── ocr_extractors.py # OCR data extraction
│   │   ├── ocr_processor.py  # OCR processing
│   │   └── patches.py        # Dependency patches
│   ├── __init__.py           # Application factory
│   ├── auth.py               # Authentication logic
│   ├── extensions.py         # Flask extensions
│   ├── models.py             # Database models
│   ├── oauth.py              # OAuth implementation
│   ├── ocr.py                # OCR main module
│   ├── pdf_generator.py      # PDF generation
│   └── swagger.py            # API documentation
├── config/                   # Configuration files
│   ├── __init__.py           # Package initialization
│   └── settings.py           # Application configuration
├── data/                     # Data storage
│   ├── db/                   # Database schemas and backups
│   └── postgres/             # PostgreSQL data files
├── docker/                   # Docker configuration
│   ├── Dockerfile            # Container definition
│   └── docker-compose.yml    # Multi-container setup
├── logs/                     # Application logs
├── migrations/               # Database migrations
│   └── versions/             # Migration versions
├── scripts/                  # Utility scripts
│   ├── db_backup.sh          # Database backup script
│   ├── db_restore.sh         # Database restore script
│   ├── file-management.sh    # File management utilities
│   ├── run_tests.sh          # Test runner
│   └── setup-cron.sh         # Cron job setup
├── temp/                     # Temporary files storage
├── tests/                    # Unit tests
├── .env                      # Environment variables (not in version control)
├── docker-compose.yml        # Symlink to docker/docker-compose.yml
├── Dockerfile                # Symlink to docker/Dockerfile
├── requirements.txt          # Python dependencies
└── run.py                    # Application entry point
```

### Key Components

- **app/**: Core application code
  - **routes/**: Organized route handlers by function
  - **utils/**: Helper functions for OCR, email, and file management
  - **templates/**: Jinja2 HTML templates
  - **static/**: Frontend assets

- **config/**: Configuration and environment settings

- **docker/**: Container definitions for development and deployment

- **scripts/**: Maintenance, backup, and utility scripts

- **migrations/**: Database schema version control

- **temp/**: Storage for temporary files like generated PDFs

This structure follows the Flask application factory pattern with clear separation of concerns.

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

### Using the API Programmatically

The API can be accessed using standard HTTP clients. Here are some examples:

#### Listing Receipts with curl

```bash
curl -X GET "http://localhost:5000/api/receipts" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### Creating a New Receipt with Python

```python
import requests
import json

url = "http://localhost:5000/api/receipts"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}
data = {
    "description": "Office supplies",
    "amount": 42.50,
    "currency": "EUR",
    "category": "office"
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

#### Processing a Receipt with JavaScript

```javascript
const processReceipt = async (fileData) => {
  const formData = new FormData();
  formData.append('file', fileData);
  
  const response = await fetch('http://localhost:5000/api/process_receipt', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
    },
    body: formData
  });
  
  return await response.json();
};
```

## Testing

The application includes a comprehensive test suite to ensure functionality and reliability.

### Running Tests Safely

To run tests without affecting your production database:

```bash
./scripts/run_tests.sh
```

When running in Docker:

```bash
docker-compose exec web ./scripts/run_tests.sh
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

## Configuration

### Google OAuth Configuration

To enable Google authentication, you need to set up OAuth credentials in the Google Cloud Console:

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "BB Expense App")
5. Click "Create"

### 2. Enable the Google OAuth API

1. Select your project from the dashboard
2. Navigate to "APIs & Services" > "Library" from the left sidebar
3. Search for "Google OAuth2 API" or "Google Identity"
4. Click on the API and click "Enable"

### 3. Configure the OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" as the user type (unless you have Google Workspace)
3. Click "Create"
4. Fill in the required information:
   - App name: "BB Expense App"
   - User support email: Your email address
   - Developer contact information: Your email address
5. Click "Save and Continue"
6. Under "Scopes", add the following scopes:
   - `email`
   - `profile`
   - `openid`
7. Click "Save and Continue"
8. Add test users if needed (your email and any testers)
9. Click "Save and Continue"
10. Review your settings and click "Back to Dashboard"

### 4. Create OAuth Client ID

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" and select "OAuth client ID"
3. Set the application type to "Web application"
4. Name: "BB Expense App Web Client"
5. Add authorized JavaScript origins:
   - For local development: `http://localhost:5000`
   - For production: `https://your-domain.com`
6. Add authorized redirect URIs:
   - For local development: `http://localhost:5000/auth/google/callback`
   - For production: `https://your-domain.com/auth/google/callback`
7. Click "Create"
8. Note your Client ID and Client Secret (you'll need these for your app)

### 5. Configure Your Application

1. Add the Client ID and Client Secret to your `.env` file:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

2. If using Docker, update your `docker-compose.yml` file:
   ```yaml
   services:
     web:
       # ... other configuration ...
       environment:
         - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
         - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
   ```

### 6. Restricting Access to Specific Domains

The application is configured to only allow users with email addresses from specific domains to log in. This is controlled by the `ALLOWED_EMAIL_DOMAINS` setting.

To modify the allowed domains:
1. Edit the `ALLOWED_EMAIL_DOMAINS` variable in your `.env` file:
   ```
   ALLOWED_EMAIL_DOMAINS=bakkenbaeck.no
   ```
2. Multiple domains can be specified by separating them with commas if needed

### 7. Moving to Production

When moving to production:

1. Update the authorized origins and redirect URIs in the Google Cloud Console
2. If needed, publish your OAuth consent screen:
   - Go to "OAuth consent screen"
   - Click "Publish App" to move from testing to production
   - Note: This may require verification if you're allowing access to users outside your organization

### 8. Troubleshooting

If you encounter authentication issues:

- Verify that your redirect URIs exactly match what's configured in the Google Cloud Console
- Check that your Client ID and Client Secret are correctly set in your environment
- Ensure the OAuth API is enabled for your project
- Verify that the user's email domain is in your `ALLOWED_EMAIL_DOMAINS` list
- Check the application logs for specific error messages

### Email Configuration

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


## Maintenance

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

```
project_root/
├── app/
│   └── archive/     # Long-term storage (10+ years)
│       └── user_id/
│           └── receipt_files.pdf
└── temp/        # Temporary PDF reports (cleaned after 7 days)
```

### Automated Maintenance

The application includes scripts to automate file management:

1. **Manual Execution**

   Run the following command to manually execute the file management task:
   ```bash
   docker-compose exec web flask manage-files
   ```

2. **Scheduled Execution (Weekly)**
   
   The application includes two scripts for automated maintenance:
   
   - `scripts/file-management.sh`: Performs the actual file management tasks including:
     - Running the management command via Docker Compose
     - Creating timestamped log files
     - Rotating logs (keeping the last 10 log files)
     - Recording start and completion times
   
   - `scripts/setup-cron.sh`: Sets up a weekly cron job (Wednesdays at 2 AM)
   
   To set up automated weekly maintenance, run the following commands:
   ```bash
   chmod +x scripts/file-management.sh scripts/setup-cron.sh
   ./scripts/setup-cron.sh
   ```
   
   This will:
   - Create a logs directory for maintenance logs
   - Set up a cron job to run weekly
   - Automatically use the correct paths regardless of deployment location

   **Deployment Note**: When deploying to production, simply run the `

### Docker Container Names

When running commands that target specific containers, be aware of how Docker Compose names containers:

1. **Default Naming Convention**: Docker Compose uses the format `{project-name}_{service-name}_{instance-number}`

2. **Container Names in This Documentation**:
   - Web application: `expense-app-web-1` (or `expense-app_web_1` depending on Docker Compose version)
   - Database: `expense-app-db-1` (or `expense-app_db_1`)
   - Mail server: `expense-app-mailhog-1` (or `expense-app_mailhog_1`)

3. **Checking Actual Container Names**:
   ```bash
   docker-compose ps
   ```
   
4. **Adjusting Commands**:
   If your container names differ from those in the documentation, adjust commands accordingly:
   ```bash
   # Example in documentation
   docker exec -it expense-app-web-1 flask shell
   
   # Adjust to your actual container name
   docker exec -it your_actual_container_name flask shell
   ```
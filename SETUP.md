# Eviction Management System Setup Guide

This guide will help you set up and run the Eviction Management System in either full mode or simplified local mode.

## Prerequisites

- Python 3.9+ installed
- pip package manager
- Virtual environment (recommended)

## Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd eviction-management-system
   ```

2. **Create and Activate Virtual Environment**

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**

   Copy the `.env.example` file to `.env` and update the values as needed:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` with your preferred text editor to set your database URL, secret keys, and other configurations.

## Running the Application

### Simplified Local Mode

The simplified local mode uses an in-memory/file-based JSON database for evictions and doesn't require a database server. This is perfect for development, demonstrations, or quick testing.

```bash
python local_app.py
```

This will start the server at http://localhost:5000

Features in local mode:
- Eviction listing and management
- Timeline calculator
- Reports generation
- No user authentication required
- File-based JSON storage

### Full Mode

The full mode uses a PostgreSQL database and includes all features including user authentication, property management, tenant tracking, and more.

1. **Set up the database**

   Ensure your PostgreSQL database is running and the connection URL is set in your `.env` file.

2. **Initialize the database**

   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

3. **Run the application**

   ```bash
   python app.py
   ```

   This will start the server at http://localhost:5000

Features in full mode:
- User authentication and role-based access control
- Property and tenant management
- Lease management
- Eviction case management
- Document management
- Reporting and analytics
- Email notifications
- API endpoints

## Development Notes

### Models

The application uses SQLAlchemy for database models. The main models are:
- User - Authentication and user management
- Property - Property information 
- Tenant - Tenant information
- Lease - Lease agreements
- Eviction - Eviction cases and timeline
- Document - Document storage and management
- Report - Report generation and storage

### Routes

The application is organized into blueprint modules:
- auth_bp - Authentication and user management
- property_bp - Property management
- tenant_bp - Tenant management
- lease_bp - Lease management
- eviction_bp - Eviction management
- document_bp - Document management
- report_bp - Report generation
- api_bp - API endpoints

### Front-end

The application uses:
- Bootstrap 5 for UI components
- Font Awesome for icons
- Custom CSS for styling
- Vanilla JavaScript for interactivity

## Troubleshooting

If you encounter issues, check these common problems:

1. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string in `.env` file
   - Ensure database user has proper permissions

2. **Module Not Found Errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **Permission Errors**
   - Check file permissions for data directories

## Support

For questions or support, please contact the development team or open an issue on the repository. 
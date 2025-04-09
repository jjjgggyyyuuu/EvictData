# Eviction Management System [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

![Eviction Management System Logo](assets/logo.png)

A comprehensive platform for landlords and tenants to track eviction cases, calculate timelines, and stay informed throughout the eviction process.

## Features

- **CSV Import Tool**: Import eviction data from court CSV files with smart column mapping
- **Timeline Calculator**: Calculate eviction timelines based on filing dates and legal requirements
- **Eviction Management**: Track and manage all your eviction cases in one centralized system
- **Reports**: Generate comprehensive reports on eviction activities and outcomes
- **Financial Tracking**: Manage judgment amounts, payments, and outstanding balances

## Project Structure

```
eviction-management/
├── app.py                  # Main application file
├── csv_import_tools.py     # Utilities for importing CSV files
├── eviction_data/          # Data storage directory
├── reports/                # Generated reports storage
├── static/                 # Static assets
└── templates/              # HTML templates
    ├── base.html           # Base template
    ├── index.html          # Dashboard
    ├── import.html         # CSV import tool
    ├── mapping.html        # Column mapping for CSV imports
    ├── preview.html        # Preview CSV import
    ├── evictions.html      # Eviction cases listing
    ├── eviction_details.html # Individual eviction details
    ├── timeline_calculator.html # Eviction timeline calculator
    ├── timeline_result.html  # Timeline calculation results
    ├── reports.html        # Reports listing
    └── report_details.html # Individual report details
```

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python app.py
   ```
6. Open your browser and navigate to `http://127.0.0.1:5000`

## Dependencies

- Flask: Web framework
- Pandas: Data analysis and manipulation
- Bootstrap: UI framework (loaded via CDN)
- Font Awesome: Icons (loaded via CDN)

## Usage

### Importing CSV Files

1. Navigate to the Import Data page
2. Select a CSV file or enter the path to a CSV file
3. Map the CSV columns to the database fields
4. Preview the import data
5. Complete the import process

### Calculating Eviction Timelines

1. Navigate to the Timeline Calculator page
2. Enter the filing date and/or writ date
3. View the calculated timeline, including important dates and recommended actions

### Managing Eviction Cases

1. Navigate to the Evictions page to view all cases
2. Use filters to find specific eviction cases
3. Click on a case to view detailed information
4. Update status, add notes, and track progress

### Generating Reports

1. Navigate to the Reports page
2. Choose a report type or create a custom report
3. Apply filters as needed
4. Generate the report in your preferred format
5. View, download, or email the report

## Value for Landlords and Tenants

### For Landlords

- Track all eviction cases in one place
- Calculate accurate timelines
- Generate professional reports
- Import court data automatically
- Stay organized with notifications

### For Tenants

- Understand the eviction process
- Get accurate timeline information
- Access legal resources
- Track case progress
- Prepare necessary documentation

### For Property Managers

- Manage multiple properties efficiently
- Track case status for all units
- Generate portfolio-wide reports
- Save time with bulk imports
- Streamline your eviction workflow

## Contributing

We welcome contributions to improve the Eviction Management System. Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is provided for informational purposes only and does not constitute legal advice. Users should consult with a qualified attorney for specific legal guidance regarding eviction processes.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Getting Started

### Prerequisites

```bash
# Node.js 18.x or higher
node -v

# PostgreSQL 14.x or higher
psql --version

# Redis 6.x or higher
redis-cli --version
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/eviction-management.git
cd eviction-management
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
npm run db:migrate
npm run db:seed
```

5. Start the development server:
```bash
npm run dev
```

## Usage

### Quick Start Guide

1. **Login/Register**
   - Create an account as a landlord or tenant
   - Complete profile setup

2. **Property Management**
   - Add properties and units
   - Manage tenant relationships
   - Track lease agreements

3. **Eviction Process**
   - Initiate new eviction case
   - Upload required documents
   - Track timeline and status
   - Generate reports

4. **Document Management**
   - Upload and organize documents
   - Generate required forms
   - Track document status

### Advanced Features

1. **Reporting**
   - Generate custom reports
   - Export data in multiple formats
   - Schedule automated reports

2. **Analytics**
   - Track eviction trends
   - Monitor property performance
   - Analyze tenant history

## API Documentation

Comprehensive API documentation is available at `/api/docs` when running the server. The API follows RESTful principles and includes:

- Authentication endpoints
- Property management
- Eviction processing
- Document handling
- Reporting and analytics

For detailed API documentation, visit our [API Guide](docs/API.md).

## Security

Security is a top priority. We implement:

- Role-based access control
- Data encryption at rest and in transit
- Regular security audits
- Compliance with data protection regulations

Report security vulnerabilities to security@evictionmanagement.com

## Support

- Documentation: [docs/](docs/)
- Issue Tracker: [GitHub Issues](https://github.com/yourusername/eviction-management/issues)
- Email Support: support@evictionmanagement.com

## Roadmap

- [ ] Mobile application
- [ ] AI-powered document analysis
- [ ] Blockchain-based document verification
- [ ] Integration with court systems
- [ ] Multi-language support

## Acknowledgments

- Legal advisors who helped with compliance
- Open source community
- Beta testers and early adopters 
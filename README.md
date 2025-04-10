# Eviction Management System [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

![Eviction Management System Logo](static/img/logo.png)

A comprehensive platform for landlords and tenants to track eviction cases, calculate timelines, and manage the eviction process efficiently.

## Why Choose Our Eviction Management System?

Our system provides a centralized solution for tracking eviction cases, calculating timelines, and generating reports. It helps landlords, property managers, and tenants navigate the complex eviction process with clarity and transparency.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Value for Users](#value-for-users)
- [Stripe Integration](#stripe-integration)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

## Features

- **CSV Import Tool**: Import eviction data from CSV files with flexible column mapping
- **Timeline Calculator**: Calculate eviction timelines based on filing dates or writ dates
- **Eviction Management**: Track and update eviction cases through each stage of the process
- **Report Generation**: Create and export reports in various formats (JSON, Markdown, PDF)
- **Financial Tracking**: Monitor judgment amounts, payments, and balances
- **Email Notifications**: Send updates to landlords and tenants
- **Stripe Integration**: Process payments for subscription plans

## Project Structure

```
eviction-management-system/
├── app.py                  # Main application file
├── simplified_app.py       # Simplified version with core functionality
├── eviction_timeline_calculator.py # Timeline calculation logic
├── csv_import_tools.py     # CSV import utilities
├── models/                 # Database models
├── routes/                 # Route handlers
├── static/                 # Static assets (CSS, JS, images)
├── templates/              # HTML templates
├── uploads/                # Uploaded CSV files
├── reports/                # Generated reports
├── eviction_data/          # Eviction data storage
└── .env                    # Environment variables
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/eviction-management-system.git
   cd eviction-management-system
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_PUBLIC_KEY=your_stripe_public_key
   SECRET_KEY=your_flask_secret_key
   ```

5. **Run the application**
   ```bash
   python app.py
   # Or for the simplified version:
   # python simplified_app.py
   ```

6. **Access the application**
   Open your web browser and navigate to `http://localhost:5000`

## Dependencies

- Flask: Web framework
- Pandas: Data manipulation and analysis
- Stripe: Payment processing
- SQLAlchemy: ORM for database operations
- Flask-Login: User authentication
- Bootstrap: Front-end framework
- Font Awesome: Icons

## Usage

### Importing CSV Files

1. Navigate to the Import page
2. Upload your CSV file containing eviction data
3. Map the columns to the appropriate database fields
4. Review the preview and confirm the import

### Calculating Eviction Timelines

1. Navigate to the Timeline Calculator
2. Enter either a filing date or a writ date
3. The system will calculate and display the timeline

### Managing Eviction Cases

1. Navigate to the Evictions page to view all cases
2. Filter cases by status, date range, or search terms
3. Click on a case to view details
4. Update status, send notifications, or generate reports

### Setting Up Stripe Integration

1. Create a Stripe account at https://stripe.com
2. Obtain your API keys from the Stripe Dashboard
3. Add your Stripe API keys to the `.env` file
4. Configure your products and prices in the Stripe Dashboard
5. Update the `PRICE_IDS` dictionary in your application with your Stripe price IDs

## Value for Users

### For Landlords

- Track all eviction cases in one place
- Calculate accurate timelines for the eviction process
- Generate reports for financial and legal purposes
- Save time with CSV import functionality
- Process payments securely through Stripe

### For Tenants

- Understand the eviction process and timeline
- Receive notifications about case updates
- Access financial information about their case
- Stay informed about important dates

### For Property Managers

- Manage multiple properties and tenants
- Track eviction cases across all properties
- Generate reports for property owners
- Monitor financial aspects of eviction cases

## Stripe Integration

This application uses Stripe for processing subscription payments. To set up Stripe:

1. **Create a Stripe Account**
   Sign up at https://stripe.com and activate your account

2. **Get Your API Keys**
   - Go to Developers > API keys in your Stripe Dashboard
   - Use test keys for development and live keys for production

3. **Create Products and Prices**
   - Go to Products > Add Product in your Stripe Dashboard
   - Create products for your subscription plans (Basic, Pro, Enterprise)
   - Note the price IDs for each product

4. **Update Your Configuration**
   - Add your Stripe API keys to the `.env` file
   - Update the `PRICE_IDS` dictionary in your application with your price IDs

5. **Testing Payments**
   - Use Stripe's test cards to test the payment flow
   - Test card: 4242 4242 4242 4242, any future date, any CVC, any ZIP

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some feature'`)
5. Push to the branch (`git push origin feature/your-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for informational purposes only and does not constitute legal advice. Users should consult with an attorney for specific legal advice regarding eviction proceedings. 
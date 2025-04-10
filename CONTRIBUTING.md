# Contributing to Eviction Management System

Thank you for considering contributing to the Eviction Management System! This document outlines the process for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## How Can I Contribute?

### Reporting Bugs

- **Ensure the bug was not already reported** by searching on GitHub under [Issues](https://github.com/yourusername/eviction-management-system/issues).
- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/yourusername/eviction-management-system/issues/new). Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

### Suggesting Enhancements

- **Ensure the enhancement was not already suggested** by searching on GitHub under [Issues](https://github.com/yourusername/eviction-management-system/issues).
- If you're unable to find an open issue addressing the enhancement, [open a new one](https://github.com/yourusername/eviction-management-system/issues/new). Be sure to include a **title and clear description**, as much relevant information as possible, and **examples of how the enhancement would be used**.

### Pull Requests

1. **Fork the repository** and create your branch from `main`.
2. **Clone your fork** to your local machine.
3. **Install development dependencies** using `pip install -r requirements.txt`.
4. **Make your changes** and add tests if applicable.
5. **Run the tests** to ensure they pass.
6. **Commit your changes** with a clear and descriptive commit message.
7. **Push to your fork** and [submit a pull request](https://github.com/yourusername/eviction-management-system/compare).

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/eviction-management-system.git
   cd eviction-management-system
   ```

2. **Create a virtual environment**
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
   STRIPE_SECRET_KEY=sk_test_51QxEvPFM2CXXOJ1example000000000000000000000000000000000000000000
   STRIPE_PUBLIC_KEY=pk_test_51QxEvPFM2CXXOJ1example000000000000000000000000000000000000000000
   SECRET_KEY=dev-key-for-development
   ```
   
   Note: Use Stripe test keys, not production keys, for development.

5. **Run the application**
   ```bash
   python app.py
   ```

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines for Python code.
- Use meaningful variable and function names.
- Write docstrings for functions and classes.
- Include comments where necessary to explain complex logic.
- Write unit tests for new features.

## Git Workflow

1. **Create a branch** for your feature or bugfix.
   ```bash
   git checkout -b feature/your-feature-name
   ```
   or
   ```bash
   git checkout -b fix/your-bugfix-name
   ```

2. **Make your changes** and commit them with a descriptive message.
   ```bash
   git commit -m "Add feature: description of your feature"
   ```

3. **Push your branch** to your fork.
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a pull request** to the main repository.

## Pull Request Guidelines

- Ensure your code follows the coding standards.
- Update the documentation if necessary.
- Include tests for new features.
- Ensure all tests pass.
- Keep pull requests focused on a single change.
- Link any relevant issues in the pull request description.

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Stripe API Documentation](https://stripe.com/docs/api)

## Questions?

If you have any questions or need help, please feel free to open an issue with the "question" label. 
# Family Recipe Sharing Application

A secure, private web application designed for sharing family recipes and photos. Built with Flask, SQLite, and Bootstrap.

## Features

- 🔒 Secure user authentication
- 📝 Create, edit, and delete recipes
- 📸 Upload photos for recipes and family memories
- 🔍 Search and filter recipes by category
- 👨‍👩‍👧‍👦 Family-only photo section
- 🌍 Hungarian language support

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional)

### Setup Instructions

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd recipe-app
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   python setup.py
   ```
   Follow the prompts to create user accounts.

5. **Configure environment variables**
   
   In production, set the SECRET_KEY environment variable:
   ```bash
   export SECRET_KEY="your-secure-random-key"
   # On Windows: set SECRET_KEY=your-secure-random-key
   ```

6. **Create protected upload directories**
   ```bash
   mkdir -p protected_uploads/family
   chmod 700 protected_uploads  # Set proper permissions (Unix-like systems)
   ```

7. **Run the application**
   ```bash
   python app.py
   ```
   The application will be available at http://localhost:5000

## Security Features

- Password hashing using secure methods
- Protected media routes - images are not directly accessible
- Authentication and authorization for all sensitive operations
- Family-only content protection
- Secure file handling

## User Management

To reset a user's password:
```bash
python reset_password.py username
```

## Project Structure

- `app.py` - Main application file
- `auth.py` - Authentication functionality
- `database.py` - Database models
- `utils.py` - Utility functions
- `templates/` - HTML templates
- `static/` - Static files (CSS, JavaScript)
- `protected_uploads/` - Protected media files
- `translations/` - Language files

## Deployment Recommendations

- Use HTTPS in production
- Set restrictive file permissions (especially on database)
- Run behind a reverse proxy (Nginx/Apache)
- Set up regular backups
- Update SECRET_KEY for production

## License

[MIT License](LICENSE)
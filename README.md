# Django App

## Overview

This is a Django-based web application designed to create an ecommerce website with payment integration and user authorization efficiently and securely. The app leverages Django's robust framework to offer scalable and maintainable features.

## Features

- User authentication and payment authorization 
- REST API and forms to interact to allow 
- Interactive admin dashboard to monitor user activity
- Database structured to allow communication between different tables
- Allow users to see saved payments, locations and orders
- Session based storage for both returning customers and guest users

## Installation

### Prerequisites

Ensure you have the following installed:

- Python 3.8+
- pip
- Virtualenv (optional but recommended)
- PostgreSQL (or your database of choice)

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/Jtolen543/ecommerce-app.git
   cd ecommerce-app
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Create a `.env` file in the project root and set the required variables:

   ```env
    DJANGO_FORM_KEY = "your-secret-form-key"
    DJANGO_EMAIL_ADDRESS="your-django-email"
    DJANGO_EMAIL_PASSWORD="your-django-password"
    HASHING_SEQUENCE="hash-sequence"
    GOOGLE_MAPS_KEY="your-googlemaps-key"
    STRIPE_SECRET_KEY="your-stripe-secret-key"
    STRIPE_PUBLISHABLE_KEY="your-stripe-publishable-key"
    DATABASE_URI=postgres://username:password@localhost:5432/dbname
   ```
   Set DEBUG to True in settings.py

5. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

6. Start the development server:

   ```bash
   python manage.py runserver
   ```

7. Access the application at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Usage

- [Add details about how to use your app, such as "Log in as an admin to manage content"]
- [Add steps for testing or interacting with key features]

## Project Structure

```
project-name/
├── app_name/           # Django app containing models, views, templates
    ├── static/         # Static files (CSS, JS, images)  
    ├── templates/      # HTML templates  
├── project_name/       # Project configuration files (settings, URLs)
    ├── settings.py     # Configure Django settings
    ├── urls.py/        # Add URLs and webhooks to project
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## Testing

Run tests with:

```bash
python manage.py test
```

## Deployment

1. Update settings for production:

   - Set `DEBUG=False`
   - Configure `ALLOWED_HOSTS`

2. Collect static files:

   ```bash
   python manage.py collectstatic
   ```

3. Use a WSGI server (e.g., Gunicorn) and set up a reverse proxy (e.g., Nginx).

4. Apply database migrations and run the server in production mode.

## Contributing

Contributions are welcome! Follow these steps:

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit changes:
   ```bash
   git commit -m "Add your feature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/your-feature
   ```
5. Open a pull request.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For questions or feedback, contact:

- Name: Jason Tolen
- Email: [Jtolen543@gmail.com](mailto\:Jtolen543@gmail.com)
- GitHub: [Jtolen543](https://github.com/Jtolen543)

---

Thank you for using the Django App!

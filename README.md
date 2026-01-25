# Electronic Diary System

A modern web application for teachers and students to manage grades and assignments.

## Features

### For Teachers
- Create and manage classes
- Assign homework and projects
- Grade student assignments
- Track student progress
- Enroll students in classes

### For Students
- View all grades and assignments
- See upcoming deadlines
- Track academic progress
- Access class information

## Technologies Used

- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Authentication**: Flask-Login
- **ORM**: Flask-SQLAlchemy
- **Deployment**: Docker, Docker Compose

## Installation and Setup

### Prerequisites
- Docker
- Docker Compose

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/electronic-diary.git
cd electronic-diary
```

2. Build and start the containers:
```bash
docker compose up --build
```

3. Access the application at:
```
http://localhost:5000
```

### Manual Setup (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (create `.env` file):
```
DATABASE_URL=postgresql://diary_user:diary_password@localhost:5432/diarydb
SECRET_KEY=your-secret-key-change-in-production
```

3. Run the application:
```bash
python app.py
```

## Usage

### Registration
1. Go to the registration page
2. Choose your role (Teacher or Student)
3. Fill in your details and create an account

### For Teachers
1. Login to your account
2. Create classes for different subjects
3. Add assignments with due dates
4. Enroll students in your classes
5. Grade student assignments

### For Students
1. Login to your account
2. View your enrolled classes
3. Check your grades and assignments
4. See upcoming deadlines

## Project Structure

```
electronic-diary/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── static/
│   ├── css/
│   │   └── style.css       # Custom CSS styles
│   └── uploads/            # File uploads directory
├── templates/
│   ├── base.html           # Base template
│   ├── index.html          # Home page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── teacher_dashboard.html  # Teacher dashboard
│   ├── student_dashboard.html  # Student dashboard
│   ├── create_class.html   # Create class form
│   ├── view_class.html     # View class details
│   ├── create_assignment.html  # Create assignment form
│   └── grade_students.html # Grade students interface
└── README.md               # This file
```

## Database Schema

The application uses the following database models:

- **User**: Stores user information (teachers and students)
- **Class**: Represents classes/subjects
- **StudentClass**: Many-to-many relationship between students and classes
- **Assignment**: Homework and projects assigned to classes
- **Grade**: Student grades for assignments

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://diary_user:diary_password@db:5432/diarydb` |
| `SECRET_KEY` | Flask secret key for sessions | `your-secret-key-change-in-production` |
| `FLASK_APP` | Flask application entry point | `app.py` |

### Security

- Change the `SECRET_KEY` in production
- Use strong passwords for database credentials
- Consider using HTTPS in production

## Development

### Running Tests

```bash
# Run the application in development mode
python app.py
```

### Database Migrations

The application automatically creates tables on startup. For production, consider using Flask-Migrate.

## Deployment

### Production with Docker

```bash
# Build and start in detached mode
docker compose up --build -d

# Stop the containers
docker compose down
```

### Scaling

The application can be scaled by:
1. Increasing Gunicorn workers
2. Using a production WSGI server
3. Adding a reverse proxy (Nginx)
4. Implementing caching

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions, please contact:
- Email: support@diary.com
- GitHub Issues: [https://github.com/yourusername/electronic-diary/issues](https://github.com/yourusername/electronic-diary/issues)

---

**Electronic Diary System** - Modern education management solution
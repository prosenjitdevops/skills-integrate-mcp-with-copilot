# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Allow teachers to register and unregister students after logging in
- Allow students to view activities and their participants without logging in

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Configure the teacher login before starting the application:

   ```
   export TEACHER_USERNAME=teacher
   export TEACHER_PASSWORD='use-a-unique-secret'
   ```

   Do not commit teacher credentials to the repository. Use HTTPS outside
   local development, and set `COOKIE_SECURE=true` so the session cookie is
   sent only over HTTPS.

3. Run the application:

   ```
   python app.py
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                     | Start a teacher session                                             |
| GET    | `/auth/session`                                                   | Check whether the current browser has a teacher session              |
| POST   | `/auth/logout`                                                    | End the current teacher session                                     |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher session required)                       |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher session required)                  |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All activity and teacher-session data is stored in memory, which means it is
reset when the server restarts. Teacher credentials are provided through
environment variables and must not be stored in the repository.

"""
High School Management System API

A super simple FastAPI application that lets students view activities and
teachers manage extracurricular registrations.
"""

from fastapi import FastAPI, HTTPException
from fastapi import Depends, Request, Response
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import hmac
import os
from pathlib import Path
import secrets
import time

app = FastAPI(title="Mergington High School API",
              description="API for viewing activities and managing student registrations")

SESSION_COOKIE = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60
teacher_sessions: dict[str, float] = {}


class TeacherCredentials(BaseModel):
    username: str
    password: str


def secure_cookies_enabled() -> bool:
    return os.getenv("COOKIE_SECURE", "false").lower() in {"true", "1", "yes"}


def is_teacher_session_valid(session_token: str | None) -> bool:
    if session_token is None:
        return False

    expires_at = teacher_sessions.get(session_token)
    if expires_at is None:
        return False
    if expires_at <= time.time():
        teacher_sessions.pop(session_token, None)
        return False
    return True


def require_teacher(request: Request) -> None:
    if not is_teacher_session_valid(request.cookies.get(SESSION_COOKIE)):
        raise HTTPException(status_code=401, detail="Teacher login required")


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(credentials: TeacherCredentials, response: Response):
    """Create a short-lived teacher session using credentials from the environment."""
    teacher_username = os.getenv("TEACHER_USERNAME")
    teacher_password = os.getenv("TEACHER_PASSWORD")
    if not teacher_username or not teacher_password:
        raise HTTPException(
            status_code=503,
            detail="Teacher login is not configured on the server"
        )

    username_matches = hmac.compare_digest(
        credentials.username.encode("utf-8"),
        teacher_username.encode("utf-8")
    )
    password_matches = hmac.compare_digest(
        credentials.password.encode("utf-8"),
        teacher_password.encode("utf-8")
    )
    if not username_matches or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    now = time.time()
    for token, expires_at in list(teacher_sessions.items()):
        if expires_at <= now:
            teacher_sessions.pop(token, None)

    session_token = secrets.token_urlsafe(32)
    teacher_sessions[session_token] = now + SESSION_DURATION_SECONDS
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=secure_cookies_enabled(),
        samesite="strict",
        path="/"
    )
    return {"authenticated": True}


@app.get("/auth/session")
def get_auth_session(request: Request):
    """Report whether the browser has a valid teacher session."""
    return {
        "authenticated": is_teacher_session_valid(
            request.cookies.get(SESSION_COOKIE)
        )
    }


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    """Revoke the current teacher session."""
    session_token = request.cookies.get(SESSION_COOKIE)
    if session_token is not None:
        teacher_sessions.pop(session_token, None)
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=secure_cookies_enabled(),
        samesite="strict",
        path="/"
    )
    return {"authenticated": False}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _: None = Depends(require_teacher)
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _: None = Depends(require_teacher)
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)

def test_root_redirect():
    """Test that the root endpoint redirects to index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"

def test_get_activities():
    """Test getting the list of activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    assert response.json() == activities

def test_signup_success():
    """Test successful activity signup"""
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    
    # Make sure the student isn't already signed up
    assert email not in activities[activity_name]["participants"]
    
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}

def test_signup_already_registered():
    """Test signing up a student who is already registered"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # This email is already in the participants list
    
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"

def test_signup_nonexistent_activity():
    """Test signing up for a non-existent activity"""
    activity_name = "Non-existent Club"
    email = "student@mergington.edu"
    
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

def test_activity_capacity():
    """Test signing up when an activity is at maximum capacity"""
    activity_name = "Chess Club"
    activity = activities[activity_name]
    original_participants = activity["participants"].copy()
    
    # Fill up the activity to max capacity
    while len(activity["participants"]) < activity["max_participants"]:
        email = f"student{len(activity['participants'])}@mergington.edu"
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
    
    # Try to add one more student
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "onemore@mergington.edu"}
    )
    assert response.status_code == 400
    assert "Activity is full" in response.json()["detail"]
    
    # Reset participants
    activity["participants"] = original_participants

@pytest.mark.parametrize("invalid_email", [
    "not-an-email",
    "missing@domain",
    "@incomplete.com",
    "spaces in@email.com",
])
def test_signup_invalid_email(invalid_email):
    """Test signing up with invalid email formats"""
    activity_name = "Chess Club"
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": invalid_email}
    )
    assert response.status_code == 422  # Unprocessable Entity
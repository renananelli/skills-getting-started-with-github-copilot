import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def api_client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            "Chess Club": {
                "description": "Learn chess",
                "schedule": "Fridays",
                "max_participants": 2,
                "participants": ["current@example.com"],
            },
            "Full Activity": {
                "description": "No open spots",
                "schedule": "Mondays",
                "max_participants": 1,
                "participants": ["current@example.com"],
            },
        },
    )
    with TestClient(app_module.app) as client:
        yield client


def test_get_activities_returns_activity_data(api_client):
    # Arrange
    expected_participants = ["current@example.com"]

    # Act
    response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == expected_participants


def test_signup_adds_participant(api_client):
    # Arrange
    email = "new@example.com"

    # Act
    response = api_client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    activities_response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@example.com for Chess Club"}
    assert email in activities_response.json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(api_client):
    # Arrange
    email = "current@example.com"

    # Act
    response = api_client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    activities_response = api_client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities_response.json()["Chess Club"]["participants"] == [email]


def test_signup_rejects_full_activity(api_client):
    # Arrange
    email = "new@example.com"

    # Act
    response = api_client.post(
        "/activities/Full Activity/signup", params={"email": email}
    )
    activities_response = api_client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert activities_response.json()["Full Activity"]["participants"] == [
        "current@example.com"
    ]


def test_signup_rejects_unknown_activity(api_client):
    # Arrange
    email = "new@example.com"

    # Act
    response = api_client.post(
        "/activities/Unknown Activity/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_unregisters_student(api_client):
    # Arrange
    email = "current@example.com"

    # Act
    response = api_client.delete(
        "/activities/Chess Club/participants", params={"email": email}
    )
    activities_response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Removed current@example.com from Chess Club"}
    assert activities_response.json()["Chess Club"]["participants"] == []


def test_remove_participant_rejects_unknown_activity(api_client):
    # Arrange
    email = "current@example.com"

    # Act
    response = api_client.delete(
        "/activities/Unknown Activity/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_rejects_unregistered_student(api_client):
    # Arrange
    email = "missing@example.com"

    # Act
    response = api_client.delete(
        "/activities/Chess Club/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
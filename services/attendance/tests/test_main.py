import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"name": "Test User", "qr_code": "QR123", "password": "testpass", "nfc_tag": "NFC123", "role": "employee"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test User"

def test_record_attendance():
    response = client.post("/attendance/", json={"user_id": 1, "is_entry": True})
    assert response.status_code == 200
    assert response.json()["status"] == "recorded"

def test_request_leave():
    response = client.post("/leaves/", json={"user_id": 1, "start_date": "2025-04-20T00:00:00", "end_date": "2025-04-21T00:00:00"})
    assert response.status_code == 200
    assert response.json()["status"] == "requested"

def test_approve_leave():
    response = client.post("/leaves/approve/", json={"leave_id": 1, "role": "manager"})
    assert response.status_code == 200
    assert response.json()["status"] == "pending"  # Needs HR approval

def test_emergency_shift():
    response = client.post("/shifts/emergency/", json={"user_id": 1})
    assert response.status_code == 200
    assert response.json()["status"] == "adjusted"
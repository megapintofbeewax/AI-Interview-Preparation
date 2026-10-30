import sys
import os

# Add parent directory to path so app modules can be loaded
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

# Ensure clean tables for test
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_full_auth_flow():
    print(">>> 1. Testing health check...")
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    assert resp.json()["status"] == "healthy"
    print("[PASS] Health check passed")

    print("\n>>> 2. Testing user registration with valid data...")
    user_payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "securepassword123",
        "confirm_password": "securepassword123"
    }
    resp = client.post("/api/auth/register", json=user_payload)
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data, "No access token in response"
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["name"] == "Jane Doe"
    token = data["access_token"]
    print("[PASS] Registration successful with token and user details")

    print("\n>>> 3. Testing duplicate email registration prevention...")
    resp = client.post("/api/auth/register", json=user_payload)
    assert resp.status_code == 400, f"Expected 400 for duplicate email, got: {resp.status_code}"
    print(f"[PASS] Duplicate prevented correctly: {resp.json()['detail']}")

    print("\n>>> 4. Testing password mismatch rejection...")
    mismatch_payload = {
        "name": "Another User",
        "email": "another@example.com",
        "password": "password123",
        "confirm_password": "differentpassword"
    }
    resp = client.post("/api/auth/register", json=mismatch_payload)
    assert resp.status_code == 422, f"Expected 422 validation error for password mismatch, got: {resp.status_code}"
    print("[PASS] Password mismatch rejected by schema validation")

    print("\n>>> 5. Testing short password rejection...")
    short_pwd_payload = {
        "name": "Short Pwd",
        "email": "short@example.com",
        "password": "123",
        "confirm_password": "123"
    }
    resp = client.post("/api/auth/register", json=short_pwd_payload)
    assert resp.status_code == 422, f"Expected 422 for short password, got: {resp.status_code}"
    print("[PASS] Short password rejected")

    print("\n>>> 6. Testing login with valid credentials...")
    login_payload = {
        "email": "jane@example.com",
        "password": "securepassword123"
    }
    resp = client.post("/api/auth/login", json=login_payload)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    login_data = resp.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == "jane@example.com"
    print("[PASS] Login successful")

    print("\n>>> 7. Testing login with invalid password...")
    bad_login_payload = {
        "email": "jane@example.com",
        "password": "wrongpassword"
    }
    resp = client.post("/api/auth/login", json=bad_login_payload)
    assert resp.status_code == 401, f"Expected 401 for wrong password, got: {resp.status_code}"
    print(f"[PASS] Invalid credentials rejected correctly: {resp.json()['detail']}")

    print("\n>>> 8. Testing /api/auth/me with valid Bearer token...")
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, f"Failed to get current user: {resp.text}"
    me_data = resp.json()
    assert me_data["email"] == "jane@example.com"
    assert me_data["name"] == "Jane Doe"
    print("[PASS] /api/auth/me verified successfully")

    print("\n>>> 9. Testing /api/auth/me with invalid/missing token...")
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken123"})
    assert resp.status_code == 401
    print("[PASS] Unauthenticated access rejected correctly")

    print("\n=========================================")
    print("ALL AUTHENTICATION TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_full_auth_flow()

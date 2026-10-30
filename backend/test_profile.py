import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_profile_flow():
    print(">>> 1. Registering user for profile testing...")
    user_payload = {
        "name": "John Doe",
        "email": "john.profile@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    resp = client.post("/api/auth/register", json=user_payload)
    if resp.status_code == 400: # If user already registered in previous run
        resp = client.post("/api/auth/login", json={"email": "john.profile@example.com", "password": "password123"})
    assert resp.status_code in [200, 201], f"Auth failed: {resp.text}"
    token = resp.json()["access_token"]
    print("[PASS] User authenticated, token received")

    headers = {"Authorization": f"Bearer {token}"}

    print("\n>>> 2. Fetching initial profile (GET /api/profile)...")
    resp = client.get("/api/profile", headers=headers)
    assert resp.status_code == 200, f"Get profile failed: {resp.text}"
    data = resp.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john.profile@example.com"
    print("[PASS] Initial profile fetched correctly:", data)

    print("\n>>> 3. Updating profile (PUT /api/profile)...")
    update_payload = {
        "name": "John Doe",
        "education": "B.Tech Computer Science",
        "target_role": "Software Developer",
        "skills": "Python, Java, SQL, Flask"
    }
    resp = client.put("/api/profile", json=update_payload, headers=headers)
    assert resp.status_code == 200, f"Update profile failed: {resp.text}"
    updated_data = resp.json()
    assert updated_data["education"] == "B.Tech Computer Science"
    assert updated_data["target_role"] == "Software Developer"
    assert updated_data["skills"] == "Python, Java, SQL, Flask"
    print("[PASS] Profile updated successfully:", updated_data)

    print("\n>>> 4. Verifying persistence with fresh GET /api/profile...")
    resp = client.get("/api/profile", headers=headers)
    assert resp.status_code == 200
    persisted = resp.json()
    assert persisted["education"] == "B.Tech Computer Science"
    assert persisted["target_role"] == "Software Developer"
    assert persisted["skills"] == "Python, Java, SQL, Flask"
    print("[PASS] Profile changes verified persistent")

    print("\n>>> 5. Testing unauthenticated profile access...")
    resp = client.get("/api/profile")
    assert resp.status_code == 401
    print("[PASS] Unauthenticated access blocked correctly")

    print("\n=========================================")
    print("ALL PROFILE TESTS PASSED!")
    print("=========================================")

if __name__ == "__main__":
    test_profile_flow()

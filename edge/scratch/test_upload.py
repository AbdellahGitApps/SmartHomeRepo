import os
import json
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

# Adjust python path to include edge directory
import sys
edge_dir = Path(__file__).resolve().parents[1] / "edge"
sys.path.insert(0, str(edge_dir))

from main import app
from database.connection.database import SessionLocal
from database.models.device import Device
from database.models.home import Home

client = TestClient(app)

def run_tests():
    print("--- STARTING ESP32-CAM INTEGRATION TESTS ---")
    
    db = SessionLocal()
    try:
        # 1. Create a dummy home and device for testing
        test_home = db.query(Home).filter(Home.name == "Integration Test Home").first()
        if not test_home:
            test_home = Home(
                name="Integration Test Home",
                home_code="HME-TEST-1234",
                owner_name="Test Owner",
                owner_email="test@owner.com",
                apartment_number="404"
            )
            db.add(test_home)
            db.commit()
            db.refresh(test_home)
        
        test_device = db.query(Device).filter(Device.device_name == "Test ESP32-CAM").first()
        if not test_device:
            test_device = Device(
                home_id=test_home.id,
                device_id="CAM-TEST-999",
                device_name="Test ESP32-CAM",
                device_type="smart_door",
                device_token="tok_test_secure_token_12345",
                mqtt_topic="home/HME-TEST-1234/smart_door/CAM-TEST-999",
                status="offline",
                enabled=True
            )
            db.add(test_device)
            db.commit()
            db.refresh(test_device)

        print(f"Created/Resolved Test Home: ID={test_home.id}, Name={test_home.name}")
        print(f"Created/Resolved Test Device: ID={test_device.device_id}, Token={test_device.device_token}")

        # Create a dummy image file
        dummy_img_path = Path("dummy_capture.jpg")
        dummy_img_path.write_bytes(b"MOCK_JPEG_IMAGE_DATA")

        # 2. Test Invalid Token
        print("\nTesting: Upload with invalid token...")
        with open(dummy_img_path, "rb") as f:
            response = client.post(
                "/api/device/upload-image",
                data={"device_token": "tok_invalid_and_fake"},
                files={"file": ("test.jpg", f, "image/jpeg")}
            )
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.json()}")
        assert response.status_code == 401
        
        # 3. Test Missing Token
        print("\nTesting: Upload with missing token...")
        with open(dummy_img_path, "rb") as f:
            response = client.post(
                "/api/device/upload-image",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.json()}")
        assert response.status_code == 400

        # 4. Test Valid Upload (Form Param)
        print("\nTesting: Upload with valid token (Form field)...")
        with open(dummy_img_path, "rb") as f:
            response = client.post(
                "/api/device/upload-image",
                data={"device_token": test_device.device_token},
                files={"file": ("test.jpg", f, "image/jpeg")}
            )
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["device_id"] == test_device.device_id
        assert int(data["home_id"]) == test_home.id
        
        saved_img_path = edge_dir / data["image_path"]
        print(f"Checking if file exists at: {saved_img_path}")
        assert saved_img_path.exists()
        print("File verified to exist!")

        # 5. Test Valid Upload (Query Param fallback)
        print("\nTesting: Upload with valid token (Query parameter)...")
        with open(dummy_img_path, "rb") as f:
            response = client.post(
                f"/api/device/upload-image?token={test_device.device_token}",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.json()}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 6. Verify Log entry was written to DB
        print("\nTesting: Verifying log insertion in system_logs...")
        conn = sqlite3.connect(edge_dir / "database" / "smart_home_edge.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query the latest log entry
        row = cursor.execute(
            "SELECT * FROM system_logs WHERE event_type = 'IMAGE_RECEIVED' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        assert row is not None
        print("Log Record Found:")
        for col in row.keys():
            print(f"  {col}: {row[col]}")
            
        details = json.loads(row["details"])
        assert details["device_id"] == test_device.device_id
        assert details["home_id"] == test_home.id
        print("Log entry validation: PASSED!")

        # Cleanup dummy local file
        if dummy_img_path.exists():
            dummy_img_path.unlink()
            
        print("\n--- ALL TESTS COMPLETED SUCCESSFULLY! ---")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()

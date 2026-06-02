import os
import json
import sqlite3
from pathlib import Path
from fastapi import UploadFile

# Adjust python path to include edge directory
import sys
edge_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(edge_dir))


from database.connection.database import SessionLocal
from database.models.device import Device
from database.models.home import Home
from services.image_upload_service import ImageUploadService
from services.device_service import validate_device_token, get_device_from_token

def run_tests():
    print("--- STARTING DIRECT ESP32-CAM SERVICE TESTS ---")
    
    db = SessionLocal()
    try:
        # 1. Create a dummy home and device for testing
        test_home = db.query(Home).filter(Home.name == "Direct Test Home").first()
        if not test_home:
            test_home = Home(
                name="Direct Test Home",
                home_code="HME-DIRECT-1234",
                owner_name="Direct Owner",
                owner_email="direct@owner.com",
                apartment_number="505"
            )
            db.add(test_home)
            db.commit()
            db.refresh(test_home)
        
        test_device = db.query(Device).filter(Device.device_name == "Direct ESP32-CAM").first()
        if not test_device:
            test_device = Device(
                home_id=test_home.id,
                device_id="CAM-DIRECT-999",
                device_name="Direct ESP32-CAM",
                device_type="smart_door",
                device_token="tok_direct_secure_token_12345",
                mqtt_topic="home/HME-DIRECT-1234/smart_door/CAM-DIRECT-999",
                status="offline",
                enabled=True
            )
            db.add(test_device)
            db.commit()
            db.refresh(test_device)

        print(f"Resolved Test Home: ID={test_home.id}, Name={test_home.name}")
        print(f"Resolved Test Device: ID={test_device.device_id}, Token={test_device.device_token}")

        # 2. Test Device Service Authentication Methods
        print("\nTesting: Service token validation...")
        is_valid = validate_device_token(db, test_device.device_token)
        print(f"validate_device_token: {is_valid}")
        assert is_valid is True

        is_invalid = validate_device_token(db, "tok_fake_token")
        print(f"validate_device_token (fake): {is_invalid}")
        assert is_invalid is False

        device_fetched = get_device_from_token(db, test_device.device_token)
        print(f"get_device_from_token returned device: {device_fetched.device_id if device_fetched else None}")
        assert device_fetched is not None
        assert device_fetched.id == test_device.id

        # 3. Create dummy file to upload
        dummy_img_path = Path("direct_dummy.jpg")
        dummy_img_path.write_bytes(b"MOCK_DIRECT_JPEG_DATA")

        # 4. Invoke ImageUploadService directly
        print("\nTesting: Uploading image via ImageUploadService...")
        with open(dummy_img_path, "rb") as f:
            upload_file = UploadFile(file=f, filename="direct_dummy.jpg")
            
            result = ImageUploadService.upload_image(
                db=db,
                token=test_device.device_token,
                file=upload_file
            )

        print(f"Upload Result: {result}")
        assert result["success"] is True
        assert result["device_id"] == test_device.device_id
        assert int(result["home_id"]) == test_home.id

        saved_img_path = edge_dir / result["image_path"]
        print(f"Verifying saved file at: {saved_img_path}")
        assert saved_img_path.exists()
        print("Image file successfully stored on disk!")

        # 5. Verify system_logs record in database
        print("\nTesting: Verifying database system_logs record...")
        conn = sqlite3.connect(edge_dir / "database" / "smart_home_edge.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        row = cursor.execute(
            "SELECT * FROM system_logs WHERE event_type = 'IMAGE_RECEIVED' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        assert row is not None
        print("Latest Event Log found in database:")
        for col in row.keys():
            print(f"  {col}: {row[col]}")
            
        details = json.loads(row["details"])
        assert details["device_id"] == test_device.device_id
        assert details["home_id"] == test_home.id
        print("Direct Service and Database tests: ALL PASSED!")

        # Cleanup dummy files
        if dummy_img_path.exists():
            dummy_img_path.unlink()
        if saved_img_path.exists():
            saved_img_path.unlink()

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.face_ai_service import FaceAIService

IMAGE_PATH = BASE_DIR / "test.jpg"

print("Loading Face AI Service...")

service = FaceAIService()

print("Running recognition...")

result = service.recognize_image(str(IMAGE_PATH))

print("\nRESULT:")
print(result)

print("\nDONE")
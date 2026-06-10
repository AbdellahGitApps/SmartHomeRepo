from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai.face_model.enroll import collect_embeddings_from_camera

print("Starting camera...")

vectors, images = collect_embeddings_from_camera(
    seconds=7,
    max_samples=12
)

print(f"Embeddings collected: {len(vectors)}")
print(f"Images collected: {len(images)}")
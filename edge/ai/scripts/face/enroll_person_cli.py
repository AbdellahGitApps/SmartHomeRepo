import re
import os
import cv2

from app.core.db import Base, engine, SessionLocal
from app.core.models import Person, FaceEmbedding
from app.core.config import PERSONS_DIR

from app.face_model.enroll import collect_embeddings_from_camera, average_embedding
from app.face_model.emb_utils import emb_to_json

def slugify_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_\u0600-\u06FF]+", "", name)
    return name

def save_person_images(person_id: int, person_name: str, face_images: list):
    safe_name = slugify_name(person_name)
    person_dir = PERSONS_DIR / f"{person_id}_{safe_name}"
    os.makedirs(person_dir, exist_ok=True)

    for idx, img in enumerate(face_images, start=1):
        path = str(person_dir / f"enroll_{idx:03d}.jpg")
        cv2.imwrite(path, img)

def main():
    Base.metadata.create_all(bind=engine)

    name = input("Name: ").strip()
    role = input("Role (resident/friend/blocked) [resident]: ").strip() or "resident"

    print("Stand in front of the camera for 7 seconds. Move your head slightly...")
    vectors, face_images = collect_embeddings_from_camera(seconds=7, max_samples=12)

    if len(vectors) < 5:
        print("Not enough good samples. Improve lighting / get closer.")
        return

    avg = average_embedding(vectors)

    db = SessionLocal()

    p = Person(name=name, role=role)
    db.add(p)
    db.commit()
    db.refresh(p)

    person_id = p.id

    save_person_images(person_id, name, face_images)

    db.add(FaceEmbedding(person_id=person_id, embedding_json=emb_to_json(avg)))
    db.add(FaceEmbedding(person_id=person_id, embedding_json=emb_to_json(vectors[0])))
    db.add(FaceEmbedding(person_id=person_id, embedding_json=emb_to_json(vectors[-1])))

    db.commit()
    db.close()

    print(f"Saved person id={person_id} embeddings=3 samples_collected={len(vectors)}")
    print(f"Saved face images in: {PERSONS_DIR / f'{person_id}_{slugify_name(name)}'}")

if __name__ == "__main__":
    main()
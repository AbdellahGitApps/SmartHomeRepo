from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection.database import SessionLocal
from database.models.ai_face import Person, FaceEmbedding

from ai.face_model.enroll import (
    collect_embeddings_from_camera,
    average_embedding,
)

from ai.face_model.emb_utils import emb_to_json


HOME_ID = 1
PERSON_NAME = "Omar"
ROLE = "resident"


print("Starting enrollment...")
print("Look at the camera for 7 seconds and move your head slightly.")

vectors, images = collect_embeddings_from_camera(
    seconds=7,
    max_samples=12
)

print(f"Collected {len(vectors)} embeddings")

if len(vectors) < 5:
    raise Exception(
        f"Not enough samples collected: {len(vectors)}"
    )

avg_embedding = average_embedding(vectors)

db = SessionLocal()

try:

    person = Person(
        home_id=HOME_ID,
        name=PERSON_NAME,
        role=ROLE
    )

    db.add(person)
    db.commit()
    db.refresh(person)

    db.add(
        FaceEmbedding(
            person_id=person.id,
            embedding_json=emb_to_json(avg_embedding)
        )
    )

    db.add(
        FaceEmbedding(
            person_id=person.id,
            embedding_json=emb_to_json(vectors[0])
        )
    )

    db.add(
        FaceEmbedding(
            person_id=person.id,
            embedding_json=emb_to_json(vectors[-1])
        )
    )

    db.commit()

    print()
    print("Enrollment successful")
    print(f"Person ID: {person.id}")
    print(f"Name: {person.name}")

finally:
    db.close()
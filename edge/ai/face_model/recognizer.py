from typing import Optional, Tuple, List

import numpy as np

from config.settings import settings

from database.connection.database import SessionLocal
from database.models.ai_face import (
    FaceEmbedding,
    Person,
)

from .emb_utils import json_to_emb, cosine_sim


class FaceRecognizer:

    def __init__(self):
        self.threshold = settings.SIM_THRESHOLD

    def load_gallery(
        self
    ) -> List[Tuple[int, np.ndarray]]:

        db = SessionLocal()

        try:

            rows = db.query(
                FaceEmbedding
            ).all()

            gallery = [
                (
                    row.person_id,
                    json_to_emb(
                        row.embedding_json
                    )
                )
                for row in rows
            ]

            return gallery

        finally:
            db.close()

    def match(
        self,
        emb: np.ndarray,
        gallery: List[
            Tuple[
                int,
                np.ndarray
            ]
        ]
    ) -> Tuple[
        Optional[int],
        float
    ]:

        best_id = None
        best_score = -1.0

        for person_id, gemb in gallery:

            score = cosine_sim(
                emb,
                gemb
            )

            if score > best_score:

                best_score = score
                best_id = person_id

        if best_score >= self.threshold:

            return (
                best_id,
                best_score
            )

        return (
            None,
            best_score
        )

    def get_person(
        self,
        person_id: int
    ) -> Optional[Person]:

        db = SessionLocal()

        try:

            return (
                db.query(Person)
                .filter(
                    Person.id == person_id
                )
                .first()
            )

        finally:
            db.close()
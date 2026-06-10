from sqlalchemy.orm import Session

from database.models.ai_face import FaceEvent


class FaceEventRepository:

    @staticmethod
    def create(
        db: Session,
        home_id: int,
        event_type: str,
        person_id: int | None = None,
        score: float | None = None,
        snapshot_path: str | None = None,
    ):

        event = FaceEvent(
            home_id=home_id,
            event_type=event_type,
            person_id=person_id,
            score=score,
            snapshot_path=snapshot_path,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event
from sqlalchemy.orm import Session

from database.models.home import Home


class HomeRepository:

    @staticmethod
    def create(db: Session, home: Home):
        db.add(home)
        db.commit()
        db.refresh(home)
        return home

    @staticmethod
    def get_by_id(db: Session, home_id: int):
        return (
            db.query(Home)
            .filter(Home.id == home_id)
            .first()
        )

    @staticmethod
    def get_all(db: Session):
        return db.query(Home).all()

    @staticmethod
    def get_by_home_code(db: Session, home_code: str):
        return (
            db.query(Home)
            .filter(Home.home_code == home_code)
            .first()
        )
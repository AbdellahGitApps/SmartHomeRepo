import random
import string
from sqlalchemy.orm import Session
from database.models.home import Home


def generate_home_code(apartment_number: str) -> str:
    """
    Generate home_code automatically in the format HOME-XXX (e.g., HOME-036).
    Pads the apartment number to at least 3 digits.
    """
    try:
        num = int(apartment_number)
        padded = f"{num:03d}"
    except ValueError:
        padded = apartment_number.zfill(3)
    return f"HOME-{padded}"


def create_home(
    db: Session,
    name: str,
    owner_name: str,
    owner_email: str,
    apartment_number: str,
) -> Home:
    """
    Create a new Home in the database, automatically generating a unique home_code.
    """
    home_code = generate_home_code(apartment_number)

    # Ensure uniqueness of the home_code
    exists = db.query(Home).filter(Home.home_code == home_code).first()
    if exists:
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        home_code = f"{home_code}-{suffix}"

    db_home = Home(
        name=name,
        owner_name=owner_name,
        owner_email=owner_email,
        apartment_number=apartment_number,
        home_code=home_code,
    )
    db.add(db_home)
    db.commit()
    db.refresh(db_home)
    return db_home


def get_all_homes(db: Session):
    from database.repositories.home_repository import HomeRepository
    return HomeRepository.get_all(db)


def get_home_by_id(db: Session, home_id: int):
    from database.repositories.home_repository import HomeRepository
    return HomeRepository.get_by_id(db, home_id)


def delete_home(db: Session, home_id: int):
    """
    Delete a Home and all its associated devices.
    """
    from database.models.device import Device
    
    # 1. Query home by id
    home = db.query(Home).filter(Home.id == home_id).first()
    
    # 2. If not found → raise error
    if not home:
        raise ValueError(f"Home with id {home_id} not found")
        
    # 3. Delete all devices where device.home_id == home_id
    db.query(Device).filter(Device.home_id == home_id).delete()
    
    # 4. Delete home
    db.delete(home)
    
    # 5. Commit transaction safely
    db.commit()


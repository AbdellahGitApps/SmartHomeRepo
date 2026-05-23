from sqlalchemy import Column, Integer, String
from database.connection.database import Base

class Home(Base):
    __tablename__ = "homes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    home_code = Column(String, unique=True, index=True, nullable=False)
    owner_name = Column(String, nullable=True)
    owner_email = Column(String, nullable=True)
    apartment_number = Column(String, nullable=True)
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from src.utils.db_utils import Base
from sqlalchemy.orm import relationship

class Books(Base):
    __tablename__ = "books"  

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=False, index=True)
    published_year = Column(Integer, nullable=False)
    publisher = Column(String, nullable=True)

    isbn = Column(String, nullable=True, unique=True, index=True)
    image_url_s = Column(String, nullable=True)
    image_url_m = Column(String, nullable=True)
    image_url_l = Column(String, nullable=True)

    total_copies = Column(Integer, nullable=False, default=1)
    available_copies = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    rentals = relationship("Rental", back_populates="book", cascade="all, delete-orphan")

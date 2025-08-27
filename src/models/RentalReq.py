from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from src.utils.db_utils import Base
from sqlalchemy.orm import relationship

class Rental(Base):
    __tablename__ = "rentals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity = Column(Integer, nullable=False, default=1)

    # lifecycle
    rented_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    due_date = Column(Date, nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)

    # relationships
    book = relationship("Books", back_populates="rentals")
    user = relationship("Users", back_populates="rentals")

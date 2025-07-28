from sqlalchemy import Column, UUID, String

from src.utils.db_utils import Base


class SampleModel(Base):
    __tablename__ = "sample_model"

    id: Column = Column(UUID, primary_key=True)
    name: Column = Column(String, nullable=False)
    description: Column = Column(String, nullable=True)

    def __repr__(self):
        return f"<SampleModel(id={self.id}, name={self.name}, description={self.description})>"

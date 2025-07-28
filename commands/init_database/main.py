from src.models.sample_models import *
from src.utils.db_utils import Base, get_database_url

from sqlalchemy import create_engine


def init_database():
    database_url = get_database_url()
    engine = create_engine(database_url, echo=True)

    # Create all tables in the database
    Base.metadata.create_all(engine)
    print("Database initialized successfully.")

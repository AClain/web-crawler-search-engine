import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

load_dotenv()

engine = create_engine(f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOSTNAME')}:{os.getenv('POSTGRES_FORWARD_PORT')}/{os.getenv('POSTGRES_DATABASE')}")
session = Session(engine)

class BaseModel(DeclarativeBase):
    pass
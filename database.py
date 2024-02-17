from sqlmodel import SQLModel, create_engine, Session, select
from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv())
DATABASE_URL = os.getenv("DATABASE_URL")


if DATABASE_URL is None:
    print("DATABASE_URL not set")
else:
    engine = create_engine(DATABASE_URL, echo=True)

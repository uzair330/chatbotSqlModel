from typing import Optional

from sqlmodel import Field, SQLModel, create_engine


class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str


class Assistant(SQLModel, table=True):
    assistant_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: [int] = Field(default=None, foreign_key="user.user_id")
    assistant: str


class Thread(SQLModel, table=True):
    thread_id: [int] = Field(default=None, primary_key=True)
    threads: str
    user_id: [int] = Field(default=None, foreign_key="user.user_id")
    assistant_id: [int] = Field(default=None, foreign_key="assistant.assistant_id")


def create_all_tables():
    SQLModel.metadata.create_all(engine)
    print("Tables created")


create_all_tables()

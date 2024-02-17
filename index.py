from typing import List, Optional
from openai import OpenAI
from sqlmodel import SQLModel, create_engine, Session, select, Field
from dotenv import load_dotenv, find_dotenv
import os
import requests
from typing import Union

from fastapi import FastAPI

app = FastAPI()


load_dotenv(find_dotenv())
DATABASE_URL = os.getenv("DATABASE_URL")

client = OpenAI()

engine = create_engine(DATABASE_URL, echo=True)


# Creating user table having id primary key and user_id unique key and assistant_id
class User(SQLModel, table=True):
    # id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    email: str


class Assistant(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    assistant_id: Optional[str] = Field(default=None, unique=True)
    user_id: str = Field(default=None, foreign_key="user.user_id")
    assistant: str


class Thread(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    thread_id: Optional[str] = Field(default=None, unique=True)
    user_id: str = Field(default=None, foreign_key="user.user_id")
    assistant_id: str = Field(default=None, foreign_key="assistant.assistant_id")
    thread: str


# Chat completion using open ai
@app.post("/api/chat")
def chat(prompt: str):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo-1106",
    )

    data: str = response.choices[0].message.content

    return {"Prompt": prompt, "System_Response": data}  # Return API


# chat completion using code interpreter
@app.post("/api/code")
async def code(text: str):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a code generator. Your responses should be exclusively in markdown code snippets, with code comments used for explanations.",
            },
            {"role": "user", "content": text},
        ],
        model="gpt-3.5-turbo-1106",
    )
    code_data = response.choices[0].message.content  # Return API
    return {"prompt": text, "message": code_data}


# Connection to api
@app.get("/api/connection")
async def connection():
    # send a GET request to the list models endpoint
    response = requests.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {client.api_key}"},
    )
    # check the status code of the response
    if response.status_code == 200:
        # if the status code is 200, the connection is successful
        return True
    else:
        # if the status code is not 200, the connection is unsuccessful
        return False


@app.post("/create_user")
def create_user(user: str, name: str, email: str):
    with Session(engine) as session:
        check_user = select(User).where(User.user_id == user)
        user_exist = session.exec(check_user).first()
        check_email = select(User).where(User.email == email)
        email_exist = session.exec(check_email).first()
        if user_exist or email_exist:
            return {"error": "User id or Email already exists"}
            raise HTTPException(status_code=400, detail="User already exists")
            return {"error": "User already exists"}
        else:
            user1 = User(user_id=user, name=name, email=email)
            session.add(user1)
            session.commit()
            session.refresh(user1)
            print("User Created")
            return {"created": "user created"}


def get_user():
    with Session(engine) as session:
        user = select(User).where(User.user_id == "user_1")
        result = session.exec(user).first()
        print(result.user_id)
        return result.user_id


@app.post("/create_assistant")
def create_assistant(user_id: str, assistant_name: str):
    def assistant():
        assistant = client.beta.assistants.create(
            name="NextGenius",
            instructions="Chat with in a helpful, positive, polite, empathetic, interesting, entertaining, and engaging way.",
            model="gpt-3.5-turbo-1106",
        )
        thread = client.beta.threads.create()

        return assistant.id

    assistant = assistant()
    with Session(engine) as session:
        check_assistant = select(Assistant).where(Assistant.assistant_id == assistant)
        assistant_exist = session.exec(check_assistant).first()
        if assistant_exist:
            return {"error": "Assistant already exists"}
        else:
            assistant_created = Assistant(
                assistant_id=assistant, user_id=user_id, assistant=assistant_name
            )
            session.add(assistant_created)
            session.commit()
            session.refresh(assistant_created)
            return {"created": "assistant created"}


# def get_assistant():
#     with Session(engine) as session:
#         assistant = select(Assistant).where(Assistant.assistant_id == "assistant123")
#         result = session.exec(assistant).first()
#         print(result.assistant_id)
#         return result.assistant_id


# def create_thread():
#     with Session(engine) as session:
#         thread1 = Thread(
#             thread_id="thread123",
#             user_id=get_user(),
#             assistant_id=get_assistant(),
#             thread="Thread 1",
#         )
#         session.add(thread1)
#         session.commit()
#         session.refresh(thread1)
#         print("Thread Created")


def thread_created():
    thread = client.beta.threads.create()
    return thread.id


# Creating thread route
@app.post("/create_thread")
def create_thread(user_id: str, thread: str):

    with Session(engine) as session:
        assistant = select(Assistant).where(Assistant.user_id == user_id)
        result = session.exec(assistant).first()
        thread_id: str = thread_created()
        thread1 = Thread(
            thread_id=thread_id,
            user_id=user_id,
            assistant_id=result.assistant_id,
            thread=thread,
        )
        session.add(thread1)
        session.commit()
        session.refresh(thread1)
        return {"created": "thread created"}


# end point for chat with ai with assistant
@app.post("/chat_with_memory")
def chat_with_memory(user_id: str, prompt: str):
    with Session(engine) as session:
        thread = select(Thread).where(Thread.user_id == user_id)
        result = session.exec(thread).first()
        assistant_id = result.assistant_id
        thread_id = result.thread_id

    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=assistant_id
    )
    return run


@app.get("/messages_with_memory")
def messages_with_memory(user_id: str):
    with Session(engine) as session:
        thread = select(Thread).where(Thread.user_id == user_id)
        result = session.exec(thread).first()
        assistant_id = result.assistant_id
        thread_id = result.thread_id

        messages = client.beta.threads.messages.list(thread_id=thread_id, order="asc")
        formatted_messages = []
        for m in reversed(messages.data):
            formatted_messages.append(
                {"role": m.role, "content": m.content[0].text.value}
            )
        print(formatted_messages)

        return formatted_messages


def create_all_tables():

    SQLModel.metadata.create_all(engine)
    print("Tables created")


def thread():
    thread = client.beta.threads.create()
    print(thread.id)
    return thread.id


if __name__ == "__main__":
    create_all_tables()  #
    thread()

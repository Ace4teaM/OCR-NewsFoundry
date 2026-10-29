import os
from models import User
from sqlmodel import SQLModel, Session, create_engine, select
import bcrypt

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)
    print("Database initialized successfully")

    users = [
        {"email": "test@test.com", "password": "test"},
        {"email": "foo@test.com", "password": "foo"},
        {"email": "bar@test.com", "password": "bar"},
    ]

    with Session(engine) as session:
        for user_data in users:
            statement = select(User).where(User.email == user_data["email"])
            user = session.exec(statement).first()

            if not user:
                session.add(
                    User(
                        email=user_data["email"],
                        hashed_password=bcrypt.hashpw(
                            user_data["password"].encode("utf-8"), bcrypt.gensalt()
                        ).decode("utf-8"),
                    )
                )
                session.commit()


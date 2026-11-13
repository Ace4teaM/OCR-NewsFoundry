from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()


class Chat(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str = Field()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: str = Field()

class Revue(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    theme: str = Field()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content: str = Field()

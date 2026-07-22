from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    ForeignKey,
    Index,
    Text,
    create_engine,
    event
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker
)


from datetime import datetime, UTC
from pathlib import Path
from app.config import settings
import sqlite3

def utc_now() -> datetime:
    return datetime.now(UTC)
from app.config import settings

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__= "users"

    id: Mapped[int]= mapped_column(primary_key=True)
    name: Mapped[str]= mapped_column(String(80))
    email: Mapped[str]= mapped_column(
        String(255, collation="NOCASE"),
        unique=True
    )
    password_hash: Mapped[str]= mapped_column(String(255))
    created_at: Mapped[datetime]= mapped_column(
        DateTime(timezone=True),
        default=datetime.now()
    )

    chats: Mapped[list["Chat"]]= relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

class Chat(Base):
    __tablename__= "chats"
    __table_args__= (
        Index("idx_chats_user_update", "user_id", "updated_at"),
    )

    id: Mapped[int]= mapped_column(primary_key=True)
    user_id: Mapped[int]= mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    title: Mapped[str]= mapped_column(String(120), default="Новый чат")
    created_at: Mapped[datetime]= mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime]= mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    user: Mapped["User"]= relationship(back_populates="chats")
    messages: Mapped[list["Message"]]= relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.creted_at"
    )



    class Message(Base):
        __tablename__= "messages"
        __table_args__= (
            CheckConstraint("role IN ('user', 'assistant')"),
            Index("idx_messages_chat_created", "chat_id", "created_at")
        )

        id: Mapped[int]= mapped_column(primary_key=True)
        chat_id: Mapped[int]= mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
        role: Mapped[str]= mapped_column(String(20))
        content: Mapped[str]= mapped_column(Text)
        model_id: Mapped[str | None]= mapped_column(String(255))
        created_at: Mapped[datetime]= mapped_column(DateTime(timezone=True), default=utc_now)

        chat: Mapped["Chat"]= relationship(back_populates="massages")

if settings.database_url.startswith("sqlite:///"):
    Path(settings.database_url.removeprefix("sqlite:///")).parent.mkdir(
        parents=True, exist_ok=True
    )

engine= create_engine(
    settings.database_url
)

@event.listens_for(engine, "connect")
def enable_sqlite_foreigin_key(connection, _)->None:
    if isinstance (connection, sqlite3.Connection):
        cursor= connection.cursor()
        cursor.execute("PRAGMA foreigin_keys= ON")
        cursor.close

SessionLocal= sessionmaker(bind=engine, autoflush=False)

def get_db():
    with SessionLocal() as sesion:
        yield sesion

def init_db()->None:
    Base.metadata.create_all(engine)
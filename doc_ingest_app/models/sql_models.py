from typing import List, Optional
from sqlalchemy import ForeignKey, String, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from uuid import UUID
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)
    username: Mapped[str] = mapped_column(String(30))
    email: Mapped[str]
    organization_id: Mapped[Optional[UUID]] = mapped_column(types.UUID, ForeignKey("organization.id"))
    organization: Mapped[Optional["Organization"]] = relationship(back_populates="users")  # Add this line
    conversations: Mapped[List["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.username!r})"

class Conversation(Base):
    __tablename__ = "conversation"
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(types.UUID, ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    created_at: Mapped[datetime] = mapped_column(types.DateTime, default=datetime.now(timezone.utc))
    document_ids: Mapped[List[UUID]] = mapped_column(types.ARRAY(types.UUID), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(128))
    def __repr__(self) -> str:
        return f"Conversation(id={self.id!r})"

class Message(Base):
    __tablename__ = "message"
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)
    conversation_id: Mapped[UUID] = mapped_column(types.UUID, ForeignKey("conversation.id"))
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    query: Mapped[str]
    response: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(types.DateTime, default=datetime.now(timezone.utc))
    response_at: Mapped[Optional[datetime]] = mapped_column(types.DateTime)
    def __repr__(self) -> str:
        return f"Message(id={self.id!r}, content={self.content!r})"

class Document(Base):
    __tablename__ = "document"
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(types.UUID, ForeignKey("user_account.id"), nullable=True)
    organization_id: Mapped[Optional[UUID]] = mapped_column(types.UUID, ForeignKey("organization.id"), nullable=True)
    user: Mapped[Optional["User"]] = relationship(back_populates="documents")
    organization: Mapped[Optional["Organization"]] = relationship(back_populates="documents")
    file_name: Mapped[str]
    chunks: Mapped[List["Chunks"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"Document(id={self.id!r}, file_name={self.file_name!r})"

class Chunks(Base):
    __tablename__ = "chunks"
    id: Mapped[UUID] = mapped_column(types.UUID, primary_key=True)
    document_id: Mapped[UUID] = mapped_column(types.UUID, ForeignKey("document.id"))
    document: Mapped["Document"] = relationship(back_populates="chunks")
    chunk: Mapped[str]
    embedding: Mapped[Vector] = mapped_column(Vector(384))
    def __repr__(self) -> str:
        return f"Chunks(id={self.id!r}, chunk={self.chunk!r})"
    

class Organization(Base):
    __tablename__ = "organization"
    id: Mapped[UUID] = mapped_column(primary_key=True,)
    name: Mapped[str]
    users: Mapped[List["User"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"Organization(id={self.id!r}, name={self.name!r})"
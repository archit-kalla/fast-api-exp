from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from .models.sql_models import Conversation, Organization, User


url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="admin",
    host="localhost",
    port=5432,
    database="postgres"
)
engine = create_engine(url, echo=True)

async def get_user(user_id: UUID):
    with Session(engine) as session:
        user = session.scalar(
            select(User).where(User.id == user_id)
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

async def get_organization(org_id: UUID):
    with Session(engine) as session:
        org = session.scalar(
            select(Organization).where(Organization.id == org_id)
            .options(joinedload(Organization.users),  # Eager load users
                     joinedload(Organization.documents))  # Eager load documents
        )
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org

def get_session():
    with Session(engine) as session:
        yield session

async def get_conversation(conversation_id: UUID):
    with Session(engine) as session:
        conversation = session.scalar(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation


SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[User, Depends(get_user)]
OrganizationDep = Annotated[Organization, Depends(get_organization)]
ConversationDep = Annotated[Conversation, Depends(get_conversation)]
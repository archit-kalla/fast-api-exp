from typing import Annotated, List, Optional
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from .models.sql_models import Conversation, Document, Organization, User


url = URL.create(
    drivername="postgresql+asyncpg",
    username="postgres",
    password="admin",
    host="localhost",
    port=5432,
    database="postgres"
)
engine = create_async_engine(url, echo=True)

async def get_session():
    async with AsyncSession(engine) as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

async def get_user(user_id: UUID, session: SessionDep) -> User:
    
    user = await session.scalar(
        select(User).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_organization(org_id: UUID, session: SessionDep) -> Organization:
    org = await session.scalar(
        select(Organization).where(Organization.id == org_id)
        .options(joinedload(Organization.users),  # Eager load users
                    joinedload(Organization.documents))  # Eager load documents
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org



async def get_conversation(conversation_id: UUID, session: SessionDep) -> Conversation:
    conversation = await session.scalar(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

async def validate_document_ids_for_user(
    document_ids: List[UUID],
    user_id: UUID,
    organization_id: Optional[UUID],
    session: AsyncSession
):
    """
    Validates the provided document IDs:
    - Ensures the documents exist.
    - Ensures the documents are associated with the user or their organization.
    """
    for doc_id in document_ids:
        document = await session.scalar(
            select(Document).where(
                Document.id == doc_id,
                (Document.user_id == user_id) |
                (Document.organization_id == organization_id)
            )
        )
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with id {doc_id} not found, or not associated with the user or organization"
            )



UserDep = Annotated[User, Depends(get_user)]
OrganizationDep = Annotated[Organization, Depends(get_organization)]
ConversationDep = Annotated[Conversation, Depends(get_conversation)]
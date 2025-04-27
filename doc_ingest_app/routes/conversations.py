from fastapi import APIRouter, Depends, HTTPException
from typing import List, Annotated
from sqlalchemy import select
from datetime import datetime, timezone
from uuid import UUID
import uuid


from ..dependencies import SessionDep, UserDep, ConversationDep
from ..models.sql_models import User, Conversation, Message
from ..models.api_models import ConversationEntry, ConversationEntryResponse, ConversationResponse

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)

@router.post("/{user_id}/entry")
async def start_conversation(user: UserDep, 
                             session: SessionDep, 
                             conversation_entry: ConversationEntry
                             ) -> ConversationEntryResponse:
    # creates a new conversation and sends first message
    session.merge(user)
    conversation_id = uuid.uuid4()
    new_conversation = Conversation(
        id=conversation_id,
        user_id=user.id,
        created_at= datetime.now(timezone.utc),
        document_ids=conversation_entry.document_ids,
    )
    session.add(new_conversation)

    new_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        query=conversation_entry.query,
        created_at=datetime.now(timezone.utc),
    )
    session.add(new_message)
    session.commit()
    session.refresh(new_conversation)
    session.refresh(new_message)
    return ConversationEntryResponse(
        id=new_conversation.id,
        created_at=new_message.created_at,
        document_ids=new_conversation.document_ids
    )

@router.put("/{conversation_id}/documents")
async def add_documents_to_conversation(conversation: UserDep,
                                        session: SessionDep,
                                        document_ids: List[UUID]
                                        )-> ConversationEntryResponse:
    """
    add_documents_to_conversation
    """
    # Check if the conversation exists
    conversation = session.merge(conversation)

    # Update the conversation with new document IDs
    conversation.document_ids = document_ids
    session.commit()
    session.refresh(conversation)
    return conversation

@router.get("/{conversation_id}")
async def get_conversation(conversation: ConversationDep, 
                           session: SessionDep) -> ConversationResponse:
    """
    get_conversation
    """
    # Check if the conversation exists
    conversation = session.merge(conversation)

    # Fetch messages associated with the conversation
    messages = session.scalars(
        select(Message).where(Message.conversation_id == conversation.id)
    ).all()
    #convert messages to MessageResponse
    messages = [
        {
            "id": message.id,
            "query": message.query,
            "response": message.response,
            "created_at": message.created_at,
            "response_at": message.response_at
        }
        for message in messages
    ]
    return ConversationResponse(
        id=conversation.id,
        created_at=conversation.created_at,
        messages=messages
    )


@router.get("/{user_id}/history")
async def get_conversation_history(user_id: str, session: SessionDep):
    """
    get_conversation_history
    """
    # Fetch all conversations associated with the user
    conversations = session.scalars(
        select(Conversation).where(Conversation.user_id == user_id)
    ).all()
    return conversations

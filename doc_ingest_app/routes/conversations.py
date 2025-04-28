from fastapi import APIRouter, Depends, HTTPException
from typing import List, Annotated
from sqlalchemy import select
from datetime import datetime, timezone
from uuid import UUID
import uuid


from ..dependencies import SessionDep, UserDep, ConversationDep, validate_document_ids_for_user
from ..models.sql_models import Document, User, Conversation, Message
from ..models.api_models import ConversationEntryCreate, ConversationEntryResponse, ConversationResponse, ConversationUpdate, ConversationUpdateResponse, MessageResponse

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)

@router.post("/{user_id}/entry")
async def start_conversation(user: UserDep, 
                             session: SessionDep, 
                             conversation_entry: ConversationEntryCreate
                             ) -> ConversationEntryResponse:
    # creates a new conversation and sends first message
    session.merge(user)
    conversation_id = uuid.uuid4()


    new_conversation = Conversation(
        id=conversation_id,
        user_id=user.id,
        created_at= datetime.now(timezone.utc)
    )
    if conversation_entry.document_ids:
        await validate_document_ids_for_user(
            document_ids=conversation_entry.document_ids,
            user_id=user.id,
            organization_id=user.organization_id,
            session=session
        )
        new_conversation.document_ids = conversation_entry.document_ids
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

    # send a celery task to process the message and produce a response

    return ConversationEntryResponse(
        id=new_conversation.id,
        created_at=new_message.created_at,
        document_ids=new_conversation.document_ids
    )

@router.post("/{conversation_id}/message")
async def add_message_to_conversation(conversation: ConversationDep,
                                        session: SessionDep,
                                        message_create: ConversationEntryCreate,
                                        ) -> MessageResponse:
    

    conversation = session.merge(conversation)
    # check if user is the owner of the conversation
    # if conversation.user_id != [somethinghere].user_id:
    #     raise HTTPException(status_code=403, detail="User not authorized to add message to this conversation")
    
    # add document ids to conversation
    if message_create.document_ids:
        await validate_document_ids_for_user(
            document_ids=message_create.document_ids,
            user_id=conversation.user.id,
            organization_id=conversation.user.organization_id,
            session=session
        )
        conversation.document_ids = message_create.document_ids


    #add message to conversation
    new_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        query=message_create.query,
        created_at=datetime.now(timezone.utc)
    )   
    session.add(new_message)
    session.commit()
    session.refresh(new_message)

    # send a celery task to process the message and produce a response

    return new_message


@router.put("/{conversation_id}")
async def update_conversation(conversation: ConversationDep,
                                        session: SessionDep,
                                        conversation_update: ConversationUpdate,
                                        )-> ConversationUpdateResponse:
    """
    add_documents_to_conversation
    """
    # Check if the conversation exists
    conversation = session.merge(conversation)

    #check if the documents are already in the conversation
    if conversation_update.document_ids:
        await validate_document_ids_for_user(
            document_ids=conversation_update.document_ids,
            user_id=conversation.user_id,
            organization_id=conversation.user.organization_id,
            session=session
        )
        conversation.document_ids = conversation_update.document_ids

    #update conversation title if provided
    if conversation_update.title:
        conversation.title = conversation_update.title  
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
        title=conversation.title,
        messages=messages,
        document_ids=conversation.document_ids
    )


@router.get("/{user_id}/history")
async def get_conversation_history(user_id: str, session: SessionDep) -> List[ConversationResponse]:
    """
    get_conversation_history
    """
    # Fetch all conversations associated with the user without
    conversations = session.scalars(
        select(Conversation.id,
               Conversation.created_at,
               Conversation.title).where(Conversation.user_id == user_id)
    ).all()
    return conversations

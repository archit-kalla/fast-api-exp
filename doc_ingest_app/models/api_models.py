from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


# Base User Model
class UserBase(BaseModel):
    username: str
    email: str
    organization_id: Optional[UUID] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    organization_id: Optional[UUID]


class UserResponse(UserBase):
    id: UUID


# Base Organization Model
class OrganizationBase(BaseModel):
    name: str


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    id: UUID
    name: Optional[str]


class OrganizationAddUsers(BaseModel):
    user_ids: List[UUID]


class OrganizationResponse(OrganizationBase):
    id: UUID
    users: Optional[List[UserResponse]]


# Base File Model
class FilesBase(BaseModel):
    file_name: str
    user_id: Optional[UUID]
    organization_id: Optional[UUID]


class FilesResponse(FilesBase):
    id: UUID


# Base Message Model
class MessageBase(BaseModel):
    query: str
    response: Optional[str]
    created_at: datetime
    response_at: Optional[datetime]


class MessageResponse(MessageBase):
    id: UUID


# Base Conversation Model
class ConversationBase(BaseModel):
    document_ids: Optional[List[UUID]] = None


class ConversationEntryCreate(ConversationBase):
    query: str


class ConversationUpdate(BaseModel):
    document_ids: Optional[List[UUID]] = None
    title: Optional[str] = None

class ConversationUpdateResponse(BaseModel):
    id: UUID
    document_ids: Optional[List[UUID]]
    title: Optional[str]


class ConversationEntryResponse(ConversationBase):
    id: UUID
    created_at: datetime


class ConversationResponse(BaseModel):
    id: UUID
    created_at: datetime
    title: Optional[str]
    document_ids: Optional[List[UUID]]
    messages: Optional[List[MessageResponse]]


# Enum for Ownership Type
class OwnershipType(str, Enum):
    user = "user"
    organization = "organization"


# Search Response Model
class SearchResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk: str
    similarity: float

class MessageBase(BaseModel):
    query: str
    response: Optional[str] = None
    created_at: datetime
    response_at: Optional[datetime] = None

class MessageResponse(MessageBase):
    id: UUID
    conversation_id: UUID
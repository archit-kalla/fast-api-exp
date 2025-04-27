from enum import Enum
from typing import List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from .sql_models import User

class User(BaseModel):
    id: UUID
    username: str
    email: str
    organization_id: UUID | None

class UserCreate(BaseModel):
    username: str
    email: str
    organization_id: UUID | None = Field(default=None)

class UserUpdate(BaseModel):
    username: str | None
    email: str | None
    organization_id: UUID | None

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    organization_id: UUID | None

class OwnershipType(str, Enum):
    user = "user"
    organization = "organization"


    
class OrganizationCreate(BaseModel):
    name: str

class OrganizationUpdate(BaseModel):
    id: UUID
    name: str | None

class OrganizationAddUsers(BaseModel):
    user_ids: List[UUID]

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    users: List[User] | None

class SearchResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk: str
    similarity: float

class FilesResponse(BaseModel):
    id: UUID
    file_name: str
    user_id: UUID | None
    organization_id: UUID | None

class MessageResponse(BaseModel):
    id: UUID
    query: str
    response: str | None
    created_at: datetime
    response_at: datetime | None

class ConversationEntry(BaseModel):
    query: str
    document_ids: List[UUID] | None

class ConversationEntryResponse(BaseModel):
    id: UUID
    created_at: datetime
    document_ids: List[UUID] | None

class ConversationResponse(BaseModel):
    id: UUID
    created_at: datetime
    messages: List[MessageResponse]



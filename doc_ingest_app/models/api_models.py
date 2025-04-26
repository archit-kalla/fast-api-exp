from enum import Enum
from typing import List
from pydantic import BaseModel, Field
from uuid import UUID
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




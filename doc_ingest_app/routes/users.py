import uuid

from fastapi import APIRouter
from typing import Annotated, List
from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from ..models.sql_models import Document, Organization, User
from ..models.api_models import FilesResponse, UserCreate, UserResponse, UserUpdate
from ..dependencies import get_user, SessionDep, UserDep

router = APIRouter(
    prefix="/users",
    tags=["Users"])

@router.get("/")
async def get_all_users(session: SessionDep) -> List[UserResponse]:
    users = session.scalars(
        select(User)
    ).all()
    return users

@router.get("/{user_id}")
async def get_user_by_id(user: UserDep) -> UserResponse:
    return user

@router.get("/{user_id}/getFiles")
async def get_user_files(existing_user: UserDep, 
                         session: SessionDep, 
                         include_org: bool = False
                         ) -> List[FilesResponse]:
    """
    Get all files associated with a user.
    If include_org is True, also include files from the user's organization.
    """
    if include_org:
        files = session.scalars(
            select(Document).where(
                (Document.user_id == existing_user.id) | 
                (Document.organization_id == existing_user.organization_id)
            )
        ).all()
    else:
        files = session.scalars(
            select(Document).where(Document.user_id == existing_user.id)
        ).all()
    
    return files

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, session: SessionDep) -> UserResponse:
    # Check if user already exists
    existing_user = session.scalar(
        select(User).where(User.username == user.username or User.email == user.email)
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Check if organization exists
    if user.organization_id:
        existing_org = session.scalar(
            select(Organization).where(Organization.id == user.organization_id)
        )
        if not existing_org:
            raise HTTPException(status_code=400, detail="Organization does not exist")
    new_user = User(
        username=user.username,
        email=user.email,
        id=uuid.uuid4(),
        organization_id=user.organization_id
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@router.put("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(existing_user: UserDep, 
                      user_data: UserUpdate, 
                      session: SessionDep) -> UserResponse:
    if user_data.username:
        existing_user.username = user_data.username
    if user_data.email:
        existing_user.email = user_data.email
    if user_data.organization_id:
        existing_user.organization_id = user_data.organization_id
    
    session.commit() 
    session.refresh(existing_user)
    return existing_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(existing_user: UserDep, 
                      session: SessionDep) -> None:
    session.delete(existing_user)
    session.commit()
    return None


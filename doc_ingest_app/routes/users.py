import uuid

from fastapi import APIRouter
from typing import Annotated, List
from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from ..models.sql_models import Organization, User
from ..models.api_models import UserCreate, UserResponse, UserUpdate
from ..dependencies import get_user, SessionDep

router = APIRouter(
    prefix="/users",
    tags=["Users"])

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
        id=str(uuid.uuid4()),
        organization_id=user.organization_id
    )
    session.add(new_user)
    session.commit()  # Commit the transaction
    return new_user

@router.get("/{user_id}")
async def get_user_by_id(user: Annotated[User, Depends(get_user)], session: SessionDep) -> UserResponse:
    return user

@router.put("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(existing_user: Annotated[User, Depends(get_user)], user_data: UserUpdate, session: SessionDep) -> UserResponse:
    if user_data.username:
        existing_user.username = user_data.username
    if user_data.email:
        existing_user.email = user_data.email
    if user_data.organization_id:
        existing_user.organization_id = user_data.organization_id
    session.refresh(existing_user)
    session.commit()  # Commit the transaction
    return existing_user

@router.get("/")
async def get_all_users(session: SessionDep) -> List[UserResponse]:
    users = session.scalars(
        select(User)
    ).all()
    return users
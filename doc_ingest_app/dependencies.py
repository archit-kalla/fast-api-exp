from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.orm import Session, joinedload

from .models.sql_models import Organization, User


url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="admin",
    host="localhost",
    port=5432,
    database="postgres"
)
engine = create_engine(url, echo=True)

async def get_user(user_id: str):
    with Session(engine) as session:
        user = session.scalar(
            select(User).where(User.id == user_id)
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

async def get_organization(org_id: str):
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


SessionDep = Annotated[Session, Depends(get_session)]
from typing import Annotated, List
import uuid
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from celery import Celery
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, text

from .tasks import proccess_file, fake_task_remote, celery

from sqlalchemy.engine import URL, create_engine
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


from .models.sql_models import Base, Organization, User, Conversation, Document, Chunks
from .models.api_models import OrganizationCreate, OrganizationResponse, OrganizationUpdate, SearchResponse, UserCreate, UserResponse, OwnershipType, OrganizationAddUsers, UserUpdate

from .scripts.create_db_schema import create_tables, drop_tables
from .dependencies import get_user, get_session, engine, SessionDep, url, get_organization

from .middleware.error_handler import ErrorHandlingMiddleware
from uuid import UUID
import os

app = FastAPI()
embedding_dim = 384
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

app.add_middleware(ErrorHandlingMiddleware)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred.",
                 "error": str(exc)},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred.",
                 "error": str(exc)},
    )
    
@app.on_event("startup")
def on_startup():
    create_tables()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.delete("/drop_tables", tags=["Admin"])
async def drop_all_tables():
    drop_tables()
    return {"message": "All tables dropped"}

@app.post("/create_tables", tags=["Admin"])
async def create_all_tables():
    create_tables()
    return {"message": "All tables created"}

@app.post("/user/create", status_code=status.HTTP_201_CREATED, tags=["User"])
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

@app.get("/user/{user_id}", tags=["User"])
async def get_user_by_id(user: Annotated[User, Depends(get_user)], session: SessionDep) -> UserResponse:
    return user

@app.put("/user/{user_id}", status_code=status.HTTP_200_OK, tags=["User"])
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

@app.get("/users", tags=["User"])
async def get_all_users(session: SessionDep) -> List[UserResponse]:
    users = session.scalars(
        select(User)
    ).all()
    return users

@app.post("/organization/create", status_code=status.HTTP_201_CREATED, tags=["Organization"])
async def create_organization(org: OrganizationCreate, session: SessionDep) -> OrganizationResponse:
    # Check if organization already exists
    existing_org = session.scalar(
        select(Organization).where(Organization.name == org.name)
    )
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization already exists")
    new_org = Organization(
        name=org.name,
        id=str(uuid.uuid4())
    )
    session.add(new_org)
    session.commit()  # Commit the transaction
    return new_org

@app.get("/organization/{org_id}", tags=["Organization"])
async def get_organization_by_id(org: Annotated[Organization, Depends(get_organization)], session: SessionDep) -> OrganizationResponse:
    return org

@app.put("/organization/{org_id}", status_code=status.HTTP_200_OK, tags=["Organization"])
async def update_organization(existing_org: Annotated[Organization, Depends(get_organization)], org_data: OrganizationUpdate, session: SessionDep) -> OrganizationResponse:
    # Ensure the organization instance is attached to the current session
    existing_org = session.merge(existing_org)
    if org_data.name:
        existing_org.name = org_data.name
    session.refresh(existing_org)
    session.commit()  # Commit the transaction
    return existing_org

@app.post("/organization/{org_id}/addUsers", status_code=status.HTTP_200_OK, tags=["Organization"])
async def add_user_to_organization(org: Annotated[Organization, Depends(get_organization)], user_data: OrganizationAddUsers, session: SessionDep) -> OrganizationResponse:
    org = session.merge(org)
    # Check if users exist and associate them with the organization
    for user_id in user_data.user_ids:
        existing_user = session.scalar(
            select(User).where(User.id == user_id)
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        existing_user.organization_id = org.id
        org.users.append(existing_user)
    session.commit()  # Commit the transaction
    return org

@app.get("/organizations", tags=["Organization"])
async def get_all_organizations(session: SessionDep) -> List[OrganizationResponse]:
    organizations = session.scalars(
        select(Organization)
    ).all()
    return organizations

@app.post("/tasks/fakeTask", tags=["Tasks"])
async def fake_task():
    task = fake_task_remote.delay()
    return {"status": task.status, "task_id": task.id}

@app.post("/{owner_id}/uploadFile", status_code=status.HTTP_201_CREATED)
async def upload_file(owner_id: UUID, owner_type: OwnershipType, session: SessionDep, file: UploadFile = File(...)):
    if owner_type == OwnershipType.user:
        user = session.scalar(select(User).where(User.id == owner_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    elif owner_type == OwnershipType.organization:
        org = session.scalar(select(Organization).where(Organization.id == owner_id))
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid owner type")

    existing_file = session.scalar(select(Document).where(Document.file_name == file.filename))
    if existing_file:
        raise HTTPException(status_code=400, detail="File already exists")

    new_file = Document(
        file_name=file.filename,
        id=str(uuid.uuid4()),
        user_id=user.id if owner_type == OwnershipType.user else None,
        organization_id=org.id if owner_type == OwnershipType.organization else None
    )
    session.add(new_file)
    with open("user_files/" + file.filename, "wb") as f:
        content = await file.read()
        f.write(content)
        
    session.commit()  # Commit the transaction



    task = proccess_file.delay(file.filename, owner_id, owner_type, new_file.id)
    return {"filename": file.filename, "status": task.status, "task_id": task.id}


@app.get("/tasks/status/{task_id}", tags=["Tasks"])
async def get_status(task_id: str):
    task = celery.AsyncResult(task_id)
    if task.state == "PENDING":
        response = {
            "state": task.state,
            "status": "Pending...",
        }
    elif task.state != "FAILURE":
        response = {
            "state": task.state,
            "result": task.result,
        }
    else:
        response = {
            "state": task.state,
            "status": str(task.info),  # this is the exception raised
        }
    return response

#run vector search to get the most similar chunks on users documents including documents from the organization
@app.get("/search/{user_id}", tags=["Search"])
async def search(user: Annotated[User, Depends(get_user)], session: SessionDep, query: str)-> List[SearchResponse]:
    #get user documents
    user_documents = session.scalars(
        select(Document).where(Document.user_id == user.id)
    ).all()
    #get organization documents
    if user.organization_id:
        org = session.scalar(
            select(Organization).where(Organization.id == user.organization_id)
        )
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
    else:
        org = None
        
    org_documents = session.scalars(
        select(Document).where(Document.organization_id == org.id)
    ).all() if org else []

    # Embed the query
    query_embedding = embedding_model.encode(query).tolist()

    
    results = session.execute(
            select(
                Chunks.id,
                Chunks.document_id,
                Chunks.chunk,
                Chunks.embedding.l2_distance(query_embedding).label("similarity")
            )
            .where(Chunks.document_id.in_([doc.id for doc in user_documents + org_documents]))
            .order_by("similarity")
            .limit(10)
        ).all()

    # Format the results
    formatted_results = [
        SearchResponse(
            id=row.id,
            document_id=row.document_id,
            chunk=row.chunk,
            similarity=row.similarity  # Include similarity score
        )
        for row in results
    ]
    return formatted_results



import uuid
from fastapi import FastAPI, File, HTTPException, UploadFile, status

from sqlalchemy import select

from .tasks import proccess_file

from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .models.sql_models import Organization, User, Document
from .models.api_models import OwnershipType

from .scripts.create_db_schema import create_tables, drop_tables
from .dependencies import SessionDep

from .middleware.error_handler import ErrorHandlingMiddleware
from uuid import UUID

from .routes import organizations, users, search, tasks

app = FastAPI()
app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(tasks.router)



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






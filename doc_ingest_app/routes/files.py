import uuid
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile, status

from sqlalchemy import select
from uuid import UUID

from ..tasks import proccess_file
from ..models.sql_models import Organization, User, Document
from ..models.api_models import OwnershipType
from ..dependencies import SessionDep


router = APIRouter(
    prefix="/files",
    tags=["Files"]
)


@router.post("/{owner_id}/uploadFile", status_code=status.HTTP_201_CREATED)
async def upload_file(owner_id: UUID, owner_type: OwnershipType, session: SessionDep, file: UploadFile = File(...)):
    '''
    uploads file by writing it to the file system and creating a record in the database
    calls the proccess_file task to process the file
    '''
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

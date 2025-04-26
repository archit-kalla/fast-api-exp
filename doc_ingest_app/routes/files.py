import uuid
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile, status
from sqlalchemy import select
from uuid import UUID
from boto3.session import Session as BotoSession
from botocore.exceptions import BotoCoreError, ClientError
from ..tasks import proccess_file
from ..models.sql_models import Organization, User, Document
from ..models.api_models import OwnershipType
from ..dependencies import SessionDep
import os

# S3 Configuration
S3_BUCKET_NAME = "documents"
S3_ENDPOINT_URL = "http://localhost:4566"
AWS_ACCESS_KEY_ID = "test"  # Default LocalStack credentials
AWS_SECRET_ACCESS_KEY = "test"

# Initialize Boto3 S3 client
s3_client = BotoSession(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
).client("s3", endpoint_url=S3_ENDPOINT_URL)

router = APIRouter(
    prefix="/files",
    tags=["Files"]
)


@router.post("/{owner_id}/uploadFile", status_code=status.HTTP_201_CREATED)
async def upload_file(owner_id: UUID, owner_type: OwnershipType, session: SessionDep, file: UploadFile = File(...)):
    '''
    Uploads file to an S3 bucket and creates a record in the database.
    Calls the proccess_file task to process the file.
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

    file_id = uuid.uuid4()
    try:
        # Upload file to S3
        s3_client.upload_fileobj(
            file.file,  # File-like object
            S3_BUCKET_NAME,
            str(file_id)
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")


    new_file = Document(
        file_name=file.filename,
        id=file_id,
        user_id=user.id if owner_type == OwnershipType.user else None,
        organization_id=org.id if owner_type == OwnershipType.organization else None
    )
    session.add(new_file)


    session.commit()  # Commit the transaction

    task = proccess_file.delay(file.filename, owner_id, owner_type, file_id)
    return {"filename": file.filename, "status": task.status, "task_id": task.id}
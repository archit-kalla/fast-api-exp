import uuid
from celery import Celery
import time
from io import BytesIO

from sentence_transformers import SentenceTransformer
from sqlalchemy import URL, select
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session
from botocore.exceptions import BotoCoreError, ClientError
from boto3.session import Session as BotoSession

from uuid import UUID

from doc_ingest_app.models.api_models import OwnershipType

from .models.sql_models import Organization, User, Document, Chunks, Base
import os

celery = Celery(
    "doc_ingest_app.tasks",
    broker="redis://localhost:6379",
    backend="redis://localhost:6379/0"
)

url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="admin",
    host="localhost",
    port=5432,
    database="postgres"
)
engine = create_engine(url, echo=True)

embedding_dim = 384
# Initialize the embedding model
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

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

# We want atomic transactions because we want to ensure that if any part of the process fails, the entire transaction is rolled back
@celery.task
def proccess_file(file_name: str, owner_id: UUID, owner_type: OwnershipType, file_id: UUID):
    """
    Process the file and return the result.
    """
    # Download the file from S3
    try:
        s3_object = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=str(file_id))
        file_content = s3_object["Body"].read()  # Read the file content as bytes
    except (BotoCoreError, ClientError) as e:
        raise FileNotFoundError(f"Failed to download file {file_name} from S3: {str(e)}")

    # Use a context manager for session management
    with Session(engine) as session:
        with session.begin():
            # Ensure the file_id is in the database
            file = session.scalar(
                select(Document).where(Document.id == file_id)
            )
            if not file:
                raise FileNotFoundError(f"File {file_name} with id {file_id} not found in database")
            
            # Ensure the owner_id is in the database
            if owner_type == OwnershipType.user:
                owner = session.scalar(
                    select(User).where(User.id == owner_id)
                )
            elif owner_type == OwnershipType.organization:
                owner = session.scalar(
                    select(Organization).where(Organization.id == owner_id)
                )
            else:
                raise ValueError(f"Invalid owner type {owner_type}")
            if not owner:
                raise FileNotFoundError(f"Owner {owner_id} not found in database")

            # Chunk the file
            chunk_size = 1024
            chunks = []
            file_stream = BytesIO(file_content)  # Create a file-like object from the downloaded content
            while True:
                chunk = file_stream.read(chunk_size).decode("utf-8")  # Decode bytes to string
                if not chunk:
                    break
                # Process the chunk
                chunks.append(chunk)

            # Create embeddings for the chunks and associate them
            for chunk in chunks:
                # Create embedding for the chunk
                embedding = embedding_model.encode(chunk).tolist()  # Convert to list for JSON serialization
                # Create a new chunk object
                new_chunk = Chunks(
                    id=str(uuid.uuid4()),
                    chunk=chunk,
                    embedding=embedding
                )
                # Add the chunk to the document
                file.chunks.append(new_chunk)
                # Add the chunk to the database
                session.add(new_chunk)

            # Associate the file with the owner
            if owner_type == "user":
                owner.documents.append(file)
            elif owner_type == "organization":
                owner.documents.append(file)

@celery.task
def fake_task_remote():
    time.sleep(20)
    return "Fake task completed"
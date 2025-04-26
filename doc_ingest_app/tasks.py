import uuid
from celery import Celery
import time

from sentence_transformers import SentenceTransformer
from sqlalchemy import URL, select
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session

from .models.sql_models import Organization, User, Conversation, Document, Chunks, Base
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

#we want atomic transactions because we want to ensure that if any part of the process fails, the entire transaction is rolled back
@celery.task
def proccess_file(file_name, owner_id, owner_type, file_id):
    """
    Process the file and return the result.
    """
    # Ensure the file exists
    if not os.path.exists("user_files/" + file_name):
        raise FileNotFoundError(f"File {file_name} not found")
    
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
            if owner_type == "user":
                owner = session.scalar(
                    select(User).where(User.id == owner_id)
                )
            elif owner_type == "organization":
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
            with open("user_files/" + file_name, "r", encoding="utf-8") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    # Process the chunk
                    chunks.append(chunk)  # No need for str() conversion

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
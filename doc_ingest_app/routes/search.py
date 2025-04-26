from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from ..models.sql_models import Organization, User, Document, Chunks
from ..models.api_models import SearchResponse
from ..dependencies import get_user, SessionDep

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)
embedding_dim = 384
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


#run vector search to get the most similar chunks on users documents including documents from the organization
@router.get("/{user_id}")
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
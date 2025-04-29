import pytest
from uuid import uuid4
from sentence_transformers import SentenceTransformer

from ..models.sql_models import User, Organization, Document, Chunks

embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


@pytest.fixture(scope="function")
async def setup_test_data(test_db):
    user = User(id=uuid4(), username="testuser", email="testuser@example.com")
    org = Organization(id=uuid4(), name="Test Organization")
    user.organization_id = org.id

    doc1 = Document(id=uuid4(), user_id=user.id, organization_id=None, file_name="doc1.txt")
    doc2 = Document(id=uuid4(), user_id=None, organization_id=org.id, file_name="doc2.txt")

    chunk1 = Chunks(id=uuid4(), document_id=doc1.id, chunk="This is a test chunk", embedding=embedding_model.encode("This is a test chunk"))
    chunk2 = Chunks(id=uuid4(), document_id=doc2.id, chunk="Another test chunk", embedding=embedding_model.encode("Another test chunk"))

    async with test_db.begin():
        test_db.add_all([user, org, doc1, doc2, chunk1, chunk2])

    return user, org, [chunk1, chunk2]


@pytest.mark.asyncio
@pytest.mark.parametrize("query, expected_chunks", [
    ("test chunk", 2)
])
async def test_search(client, setup_test_data, query, expected_chunks):
    user, _, _ = await setup_test_data
    response = client.get(f"/search/{user.id}?query={query}")
    assert response.status_code == 200

    results = response.json()
    assert len(results) == expected_chunks

    if expected_chunks > 0:
        for result in results:
            assert "id" in result
            assert "document_id" in result
            assert "chunk" in result
            assert "similarity" in result
import pytest
from uuid import uuid4

from ..models.sql_models import User, Conversation, Message

@pytest.fixture(scope="function")
async def setup_test_data(test_db):
    user = User(id=uuid4(), username="testuser", email="testuser@example.com")
    conversation_id = uuid4()
    message = Message(id=uuid4(), conversation_id=conversation_id, query="Test message")
    conversation = Conversation(
        id=conversation_id,
        user_id=user.id,
        title="Test Conversation",
        messages=[message],
        document_ids=[],
    )

    async with test_db.begin():
        test_db.add_all([user, conversation])

    return user, conversation

@pytest.mark.asyncio
async def test_start_conversation(client, setup_test_data):
    user, _ = await setup_test_data
    payload = {"query": "New conversation query"}
    response = client.post(f"/conversations/{user.id}/entry", json=payload)
    assert response.status_code == 200

    result = response.json()
    assert "id" in result
    assert "document_ids" in result
    assert "created_at" in result

@pytest.mark.asyncio
async def test_get_conversation(client, setup_test_data):
    _, conversation = await setup_test_data
    response = client.get(f"/conversations/{conversation.id}")
    assert response.status_code == 200

    result = response.json()
    assert result["id"] == str(conversation.id)
    assert result["title"] == conversation.title
    assert "messages" in result
    assert isinstance(result["messages"], list)
    assert "document_ids" in result
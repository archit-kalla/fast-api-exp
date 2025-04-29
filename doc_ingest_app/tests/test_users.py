import pytest
from uuid import uuid4

from ..models.sql_models import User, Organization

@pytest.fixture(scope="function")
async def setup_test_data(test_db):
    org = Organization(id=uuid4(), name="Test Organization")
    user = User(id=uuid4(), username="testuser", email="testuser@example.com", organization_id=org.id)

    async with test_db.begin():
        test_db.add_all([org, user])

    return user, org

@pytest.mark.asyncio
async def test_create_user(client):
    payload = {"username": "newuser", "email": "newuser@example.com", "organization_id": str(uuid4())}
    response = client.post("/users/create", json=payload)
    assert response.status_code == 201

    result = response.json()
    assert "id" in result
    assert "username" in result
    assert result["username"] == payload["username"]

@pytest.mark.asyncio
async def test_get_user(client, setup_test_data):
    user, _ = await setup_test_data
    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200

    result = response.json()
    assert result["id"] == str(user.id)
    assert result["username"] == user.username
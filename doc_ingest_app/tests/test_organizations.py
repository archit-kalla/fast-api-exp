import pytest
from uuid import uuid4
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sql_models import Organization, User

@pytest_asyncio.fixture(scope="function")
async def setup_test_data(test_db: AsyncSession):
    session = test_db
    org = Organization(id=uuid4(), name="Test Organization")
    user = User(id=uuid4(), username="testuser", email="testuser@example.com", organization_id=org.id)
    org.users.append(user)

    session.add(org)
    session.add(user)
    await test_db.commit()
    await test_db.refresh(org)
    await test_db.refresh(user)  # Fixed missing await
    yield org, user
    await test_db.delete(org)
    await test_db.delete(user)
    await test_db.commit()



@pytest.mark.asyncio
async def test_create_organization(client):
    payload = {"name": "New Organizastion"}
    response = await client.post("/organizations/create", json=payload)
    assert response.status_code == 201

    result = response.json()
    assert "id" in result
    assert "name" in result
    assert result["name"] == payload["name"]

@pytest.mark.asyncio
async def test_get_organization(client, setup_test_data):
    org, user = setup_test_data 
    response = await client.get(f"/organizations/{org.id}")
    assert response.status_code == 200

    result = response.json()
    assert result["id"] == str(org.id)
    assert result["name"] == org.name
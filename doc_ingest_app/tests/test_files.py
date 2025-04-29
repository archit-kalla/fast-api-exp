import pytest
from uuid import uuid4
from unittest.mock import patch

from ..models.sql_models import User, Organization, Document
from botocore.response import StreamingBody
import io

@pytest.fixture(scope="function")
async def setup_test_data(test_db):
    user = User(id=uuid4(), username="testuser", email="testuser@example.com")
    org = Organization(id=uuid4(), name="Test Organization")
    document = Document(id=uuid4(), user_id=user.id, file_name="testfile.txt")

    async with test_db.begin():
        test_db.add_all([user, org, document])

    return user, org, document

@pytest.mark.asyncio
async def test_upload_file(client, setup_test_data):
    user, _, _ = await setup_test_data
    payload = {"file": ("newfile.txt", b"File content")}

    with patch("doc_ingest_app.routes.files.s3_client.upload_fileobj") as mock_upload:
        mock_upload.return_value = None
        response = client.post(f"/files/{user.id}/uploadFile?owner_type=user", files=payload)

    assert response.status_code == 201
    result = response.json()
    assert "filename" in result
    assert result["filename"] == "newfile.txt"

@pytest.mark.asyncio
async def test_download_file(client, setup_test_data):
    _, _, document = await setup_test_data
    with patch("doc_ingest_app.routes.files.s3_client.get_object") as mock_get_object:
        mock_get_object.return_value = {
            "Body": StreamingBody(
                raw_stream=io.BytesIO(b"File content"),
                content_length=len(b"File content")
            )
        }

        response = client.get(f"/files/{document.id}/download")

    assert response.status_code == 200
    streamed_content = b"".join(response.iter_bytes())
    assert streamed_content == b"File content"
    assert response.headers["Content-Disposition"] == f'attachment; filename="{document.file_name}"'

@pytest.mark.asyncio
async def test_delete_file(client, setup_test_data):
    _, _, document = await setup_test_data
    with patch("doc_ingest_app.routes.files.s3_client.delete_object") as mock_delete:
        mock_delete.return_value = None
        response = client.delete(f"/files/{document.id}")

    assert response.status_code == 204
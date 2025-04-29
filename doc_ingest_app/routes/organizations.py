from typing import List
import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..models.sql_models import Document, Organization, User
from ..models.api_models import FilesResponse, OrganizationCreate, OrganizationResponse, OrganizationUpdate, OrganizationAddUsers, UserResponse

from ..dependencies import SessionDep, OrganizationDep

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)

@router.get("/")
async def get_all_organizations(session: SessionDep) -> List[OrganizationResponse]:
    organizations = await session.scalars(
        select(Organization)
    )
    return organizations.all()

@router.get("/{org_id}")
async def get_organization_by_id(org: OrganizationDep, session: SessionDep) -> OrganizationResponse:
    return org

@router.get("/{org_id}/getFiles")
async def get_files_by_organization(org: OrganizationDep, session: SessionDep) -> List[FilesResponse]:
    """
    Get all files associated with the organization.
    """
    org = await session.merge(org)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    files = await session.scalars(
        select(Document).where(Document.organization_id == org.id)
    )
    return files.all()

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_organization(org: OrganizationCreate, session: SessionDep) -> OrganizationResponse:
    existing_org = await session.scalar(
        select(Organization).where(Organization.name == org.name)
    )
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization already exists")
    new_org = Organization(
        name=org.name,
        id=uuid.uuid4()
    )
    session.add(new_org)
    await session.commit()
    await session.refresh(new_org)
    # Eagerly load relationships (e.g., users) to avoid lazy-loading issues
    new_org = await session.scalar(
        select(Organization)
        .where(Organization.id == new_org.id)
        .options(joinedload(Organization.users))  # Adjust based on your model relationships
    )
    return new_org

@router.put("/{org_id}", status_code=status.HTTP_200_OK)
async def update_organization(existing_org: OrganizationDep, org_data: OrganizationUpdate, session: SessionDep) -> OrganizationResponse:
    existing_org = await session.merge(existing_org)
    if org_data.name:
        existing_org.name = org_data.name
    await session.commit()
    await session.refresh(existing_org)
    return existing_org

@router.put("/{org_id}/addUsers")
async def add_user_to_organization(org: OrganizationDep, user_data: OrganizationAddUsers, session: SessionDep) -> OrganizationResponse:
    org = await session.merge(org)
    for user_id in user_data.user_ids:
        existing_user = await session.scalar(
            select(User).where(User.id == user_id)
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        existing_user.organization_id = org.id
        org.users.append(existing_user)
    await session.commit()
    await session.refresh(org)
    # Eagerly load relationships (e.g., users) to avoid lazy-loading issues
    org = await session.scalar(
        select(Organization)
        .where(Organization.id == org.id)
        .options(joinedload(Organization.users))  #use this to load users to minimize number of queries
    )
    return org

@router.put("/{org_id}/removeUsers")
async def delete_users_from_organization(org: OrganizationDep, user_data: OrganizationAddUsers, session: SessionDep) -> OrganizationResponse:
    org = await session.merge(org)
    for user_id in user_data.user_ids:
        existing_user = await session.scalar(
            select(User).where(User.id == user_id)
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        existing_user.organization_id = None
        org.users.remove(existing_user)
    await session.commit()
    await session.refresh(org)
    return org

@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(existing_org: OrganizationDep, session: SessionDep) -> None:
    await session.delete(existing_org)
    await session.commit()
    return None



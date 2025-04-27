from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from ..models.sql_models import Document, Organization, User
from ..models.api_models import FilesResponse, OrganizationCreate, OrganizationResponse, OrganizationUpdate, OrganizationAddUsers, UserResponse

from ..dependencies import SessionDep, get_organization

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)

@router.get("/")
async def get_all_organizations(session: SessionDep) -> List[OrganizationResponse]:
    organizations = session.scalars(
        select(Organization)
    ).all()
    return organizations

@router.get("/{org_id}")
async def get_organization_by_id(org: Annotated[Organization, Depends(get_organization)], session: SessionDep) -> OrganizationResponse:
    return org

@router.get("/{org_id}/getFiles")
async def get_files_by_organization(org: Annotated[Organization, Depends(get_organization)], session: SessionDep) -> List[FilesResponse]:
    """
    Get all files associated with the organization.
    """
    # Check if the organization exists in the database
    org = session.merge(org)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Fetch files associated with the organization
    files = session.scalars(
        select(Document).where(Document.organization_id == org.id)
    ).all()
    
    return files

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_organization(org: OrganizationCreate, session: SessionDep) -> OrganizationResponse:
    # Check if organization already exists
    existing_org = session.scalar(
        select(Organization).where(Organization.name == org.name)
    )
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization already exists")
    new_org = Organization(
        name=org.name,
        id=str(uuid.uuid4())
    )
    session.add(new_org)
    session.commit()  # Commit the transaction
    return new_org

@router.put("/{org_id}", status_code=status.HTTP_200_OK)
async def update_organization(existing_org: Annotated[Organization, Depends(get_organization)], org_data: OrganizationUpdate, session: SessionDep) -> OrganizationResponse:
    # Ensure the organization instance is attached to the current session
    existing_org = session.merge(existing_org)
    if org_data.name:
        existing_org.name = org_data.name
    session.refresh(existing_org)
    session.commit()  # Commit the transaction
    return existing_org

@router.put("/{org_id}/addUsers")
async def add_user_to_organization(org: Annotated[Organization, Depends(get_organization)], user_data: OrganizationAddUsers, session: SessionDep) -> OrganizationResponse:
    org = session.merge(org)
    # Check if users exist and associate them with the organization
    for user_id in user_data.user_ids:
        existing_user = session.scalar(
            select(User).where(User.id == user_id)
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        existing_user.organization_id = org.id
        org.users.append(existing_user)
    session.commit()  # Commit the transaction
    return org

#only disassociate users from the organization not delete them
@router.put("/{org_id}/removeUsers")
async def delete_users_from_organization(org: Annotated[Organization, Depends(get_organization)], user_data: OrganizationAddUsers, session: SessionDep) -> OrganizationResponse:
    org = session.merge(org)
    # Check if users exist and disassociate them from the organization
    for user_id in user_data.user_ids:
        existing_user = session.scalar(
            select(User).where(User.id == user_id)
        )
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        existing_user.organization_id = None
        org.users.remove(existing_user)
    
    session.refresh(org)
    session.commit()
    return org

@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(existing_org: Annotated[Organization, Depends(get_organization)], session: SessionDep) -> None:
    session.delete(existing_org)
    session.commit()
    return None



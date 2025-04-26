from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from ..models.sql_models import Organization, User
from ..models.api_models import OrganizationCreate, OrganizationResponse, OrganizationUpdate, OrganizationAddUsers

from ..dependencies import SessionDep, get_organization

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)

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

@router.get("/{org_id}")
async def get_organization_by_id(org: Annotated[Organization, Depends(get_organization)], session: SessionDep) -> OrganizationResponse:
    return org

@router.put("/{org_id}", status_code=status.HTTP_200_OK)
async def update_organization(existing_org: Annotated[Organization, Depends(get_organization)], org_data: OrganizationUpdate, session: SessionDep) -> OrganizationResponse:
    # Ensure the organization instance is attached to the current session
    existing_org = session.merge(existing_org)
    if org_data.name:
        existing_org.name = org_data.name
    session.refresh(existing_org)
    session.commit()  # Commit the transaction
    return existing_org

@router.post("/{org_id}/addUsers", status_code=status.HTTP_200_OK)
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

@router.get("/")
async def get_all_organizations(session: SessionDep) -> List[OrganizationResponse]:
    organizations = session.scalars(
        select(Organization)
    ).all()
    return organizations
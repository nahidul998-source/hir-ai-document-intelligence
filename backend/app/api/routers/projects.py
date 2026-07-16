from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_project_service, get_current_user
from app.application.services.project_service import ProjectService
from app.infrastructure.database.models import User
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_in: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    project = await project_service.create_project(project_in, owner_id=current_user.id)
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user)
):
    projects = await project_service.list_projects(owner_id=current_user.id)
    return projects

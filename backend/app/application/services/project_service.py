import uuid
from typing import List, Optional
from app.infrastructure.database.models import Project
from app.infrastructure.repositories.projects import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def create_project(self, schema: ProjectCreate, owner_id: uuid.UUID) -> Project:
        project = Project(
            name=schema.name,
            description=schema.description,
            owner_id=owner_id
        )
        return await self.project_repo.add(project)

    async def get_project(self, project_id: uuid.UUID) -> Optional[Project]:
        return await self.project_repo.get(project_id)

    async def list_projects(self, owner_id: uuid.UUID) -> List[Project]:
        return await self.project_repo.get_by_owner(owner_id)

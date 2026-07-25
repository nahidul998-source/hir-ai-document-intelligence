import asyncio
import uuid
from sqlalchemy import select
from app.database.session import async_session_maker
from app.infrastructure.database.models import Document
from app.core.context import tenant_context

async def test_tenant_isolation():
    # Example UUIDs
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    
    async with async_session_maker() as session:
        from app.infrastructure.database.models import Tenant, User, Project, Role
        
        # Create Tenant
        tenant = Tenant(id=tenant_a, name=f"Tenant A {uuid.uuid4()}", code=f"TA{str(uuid.uuid4())[:4]}", status="ACTIVE", max_users=10, storage_quota_gb=10.0)
        session.add(tenant)
        await session.flush()
        
        # Create Role
        role = Role(name=f"Admin-{uuid.uuid4()}", permissions={}, tenant_id=tenant_a)
        session.add(role)
        await session.flush()
        
        # Create User
        user = User(email=f"test-{uuid.uuid4()}@example.com", hashed_password="pw", is_active=True, role_id=role.id, tenant_id=tenant_a)
        session.add(user)
        await session.flush()
        
        # Create Project
        project = Project(name="Test Project", tenant_id=tenant_a, owner_id=user.id)
        session.add(project)
        await session.flush()
        
        # Create Document
        doc = Document(filename="Tenant A Doc", file_type="pdf", minio_key="test/test.pdf", status="UPLOADED", document_type="invoice", tenant_id=tenant_a, uploader_id=user.id, project_id=project.id)
        session.add(doc)
        await session.commit()
        
        # 2. Query WITHOUT tenant context (simulate background task)
        tenant_context.set(None)
        result = await session.execute(select(Document))
        all_docs = result.scalars().all()
        print(f"Docs without context: {len(all_docs)}")
        
        # 3. Query WITH tenant context B (should return 0 for tenant A's doc)
        tenant_context.set(tenant_b)
        result = await session.execute(select(Document))
        tenant_b_docs = result.scalars().all()
        print(f"Docs for tenant B: {len(tenant_b_docs)}")
        
        # 4. Query WITH tenant context A (should return 1)
        tenant_context.set(tenant_a)
        result = await session.execute(select(Document))
        tenant_a_docs = result.scalars().all()
        print(f"Docs for tenant A: {len(tenant_a_docs)}")

if __name__ == "__main__":
    asyncio.run(test_tenant_isolation())

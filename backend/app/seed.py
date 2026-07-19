import asyncio
from sqlalchemy import select
from passlib.context import CryptContext

from app.database.session import engine, async_session_maker
from app.infrastructure.database.models import Base, User, Role
import app.infrastructure.database.models_master_data
import app.infrastructure.database.models_phase2
import app.infrastructure.database.models_phase3

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    print("Starting database seeding...")
    
    # 1. Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created/verified.")

    # 2. Seed Admin User
    async with async_session_maker() as session:
        # Check if Admin role exists
        result = await session.execute(select(Role).where(Role.name == "Admin"))
        admin_role = result.scalar_one_or_none()
        
        if not admin_role:
            admin_role = Role(name="Admin", permissions={"all": True})
            session.add(admin_role)
            await session.flush()
            print("Admin role created.")
            
        # Check if Admin user exists
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            hashed_pw = pwd_context.hash("admin")
            admin_user = User(
                email="admin@example.com",
                hashed_password=hashed_pw,
                role_id=admin_role.id,
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print("Default admin user created: admin@example.com / admin")
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(seed())

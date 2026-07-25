import asyncio
from sqlalchemy import select
from passlib.context import CryptContext

from app.database.session import engine, async_session_maker
from app.infrastructure.database.models import Base, User, Role
import app.infrastructure.database.models
import app.infrastructure.database.models
import app.infrastructure.database.models
import app.infrastructure.database.models

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

        # 3. Seed AI Providers & Routing Rules
        from app.infrastructure.database.models import AIProviderConfig, AIProviderRoutingRule
        import yaml
        import os
        
        # Check if configs already seeded
        result = await session.execute(select(AIProviderConfig))
        configs = result.scalars().all()
        
        if not configs:
            test_dir = os.path.dirname(os.path.abspath(__file__))
            yaml_path = os.path.join(test_dir, "../../configs/ai.yaml")
            if os.path.exists(yaml_path):
                with open(yaml_path, "r") as f:
                    ai_data = yaml.safe_load(f)
                
                providers_data = ai_data.get("providers", {})
                priority_list = ai_data.get("priority", [])
                
                for idx, key in enumerate(priority_list):
                    if key in providers_data:
                        p = providers_data[key]
                        config = AIProviderConfig(
                            key=key,
                            name=p.get("name", key),
                            enabled=p.get("enabled", True),
                            api_url=p.get("api_url", ""),
                            api_key=p.get("api_key", ""),
                            model_name=p.get("model_name", ""),
                            connect_timeout=p.get("connect_timeout", 5),
                            read_timeout=p.get("timeout", 60), # Fallback to timeout if read_timeout not specified
                            retry_timeout=p.get("retry_timeout", 10),
                            priority_index=idx,
                            capabilities={
                                "context_length": p.get("context_length", 4096),
                                "json_mode": p.get("json_mode", True),
                                "vision": p.get("vision", False),
                                "streaming": p.get("streaming", False)
                            }
                        )
                        session.add(config)
                
                # Seed default routing rules
                routing_rules = {
                    "invoice": ["local_qwen", "github", "gemini"],
                    "order_sheet": ["local_qwen", "github", "gemini"],
                    "tech_pack": ["gemini", "github"],
                    "generic": ["local_qwen", "github", "gemini"]
                }
                for doc_type, keys in routing_rules.items():
                    rule = AIProviderRoutingRule(
                        document_type=doc_type,
                        provider_keys=keys
                    )
                    session.add(rule)
                
                await session.commit()
                print("AI Providers & Routing Rules seeded from ai.yaml.")
            else:
                print(f"Warning: ai.yaml not found at {yaml_path}")
        else:
            print("AI Providers already seeded in database.")

if __name__ == "__main__":
    asyncio.run(seed())

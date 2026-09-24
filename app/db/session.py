import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Base
from app.db.migrations import run_compatibility_migrations

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./techconnect.db")

engine_kwargs: dict = {"echo": False, "pool_pre_ping": True}
if "postgresql" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"ssl": "require"}
else:
    engine_kwargs["pool_recycle"] = 280

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session_maker() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(run_compatibility_migrations)

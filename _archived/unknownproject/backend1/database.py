import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# High-performance PostgreSQL database URL. 
# Defaults to psycopg2 (since it is installed in the environment)
# Using PigPig3897!! as the default password fallback for local connections
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:PigPig3897!!@localhost/ostraka_db")

# Detect if the environment/URL specifies an asynchronous PostgreSQL connection
# (such as asyncpg for high-throughput async processing loops)
IS_ASYNC = "+async" in DATABASE_URL or "asyncpg" in DATABASE_URL

# Declarative Base for all entity models
Base = declarative_base()

if IS_ASYNC:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    
    # Create highly performant asynchronous engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True
    )
    
    # Task-safe async session maker
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async def init_db() -> None:
        """
        Asynchronously initializes the database schema by creating all tables.
        Uses run_sync to execute DDL statements within the async connection.
        """
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
else:
    # Create standard synchronous engine using psycopg2
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True
    )
    
    # Thread-safe synchronous session maker
    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    def init_db() -> None:
        """
        Synchronously initializes the database schema by creating all tables.
        """
        Base.metadata.create_all(bind=engine)

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_existing_tables()


def _migrate_existing_tables():
    """Apply small additive migrations for existing deployments."""
    inspector = inspect(engine)
    if "task" not in inspector.get_table_names():
        return

    task_columns = {column["name"] for column in inspector.get_columns("task")}
    if "platform_task_id" not in task_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE task ADD COLUMN platform_task_id VARCHAR"))
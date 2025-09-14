"""
Database utilities and connection management
"""
import os
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


class DatabaseManager:
    """Database connection manager for microservices"""
    
    def __init__(self, database_url: str, echo: bool = False):
        self.database_url = database_url
        self.echo = echo
        self._engine = None
        self._session_factory = None
    
    @property
    def engine(self):
        """Get or create database engine"""
        if self._engine is None:
            self._engine = create_engine(
                self.database_url,
                echo=self.echo,
                pool_pre_ping=True,
                pool_recycle=300,
                # For SQLite testing
                poolclass=StaticPool if "sqlite" in self.database_url else None,
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
            )
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        return self._session_factory
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self, base_class):
        """Create all tables for given base class"""
        base_class.metadata.create_all(bind=self.engine)
    
    def drop_tables(self, base_class):
        """Drop all tables for given base class"""
        base_class.metadata.drop_all(bind=self.engine)


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def init_database(database_url: str = None, echo: bool = False) -> DatabaseManager:
    """Initialize database manager"""
    global db_manager
    
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    db_manager = DatabaseManager(database_url, echo)
    return db_manager


def get_database() -> DatabaseManager:
    """Get current database manager"""
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_manager


def get_session() -> Generator[Session, None, None]:
    """Get database session (FastAPI dependency)"""
    db = get_database()
    yield from db.get_session()


# Workspace-aware query utilities
class WorkspaceQueryMixin:
    """Mixin for workspace-scoped queries"""
    
    @classmethod
    def get_by_workspace(cls, session: Session, workspace_id: str, **filters):
        """Get records filtered by workspace"""
        query = session.query(cls).filter(cls.workspace_id == workspace_id)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)
        
        return query
    
    @classmethod
    def get_by_id_and_workspace(cls, session: Session, record_id: str, workspace_id: str):
        """Get single record by ID and workspace"""
        return session.query(cls).filter(
            cls.id == record_id,
            cls.workspace_id == workspace_id,
            cls.is_deleted == False
        ).first()
    
    @classmethod
    def create_in_workspace(cls, session: Session, workspace_id: str, **data):
        """Create new record in workspace"""
        data['workspace_id'] = workspace_id
        instance = cls(**data)
        session.add(instance)
        session.flush()
        return instance
    
    def soft_delete(self, session: Session):
        """Soft delete record"""
        from datetime import datetime
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        session.flush()


# Migration utilities
def run_migrations(alembic_cfg_path: str = "alembic.ini"):
    """Run database migrations"""
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config(alembic_cfg_path)
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully")
    except ImportError:
        print("Alembic not installed. Skipping migrations.")
    except Exception as e:
        print(f"Migration failed: {e}")
        raise

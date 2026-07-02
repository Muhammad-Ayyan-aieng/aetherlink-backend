# ============================================================
# AETHER LINK - BASE REPOSITORY
# ============================================================

from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Tuple
from datetime import datetime
from ..core.database import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.
    All repositories inherit from this class.
    """
    
    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize repository.
        
        Args:
            db: SQLAlchemy session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[T]:
        """
        Get record by ID.
        
        Args:
            id: Record ID
            include_deleted: Include soft-deleted records
            
        Returns:
            Record or None
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first()
    
    def get_by_id_or_fail(self, id: int, include_deleted: bool = False) -> T:
        """
        Get record by ID or raise exception.
        
        Args:
            id: Record ID
            include_deleted: Include soft-deleted records
            
        Returns:
            Record
            
        Raises:
            ValueError: If record not found
        """
        record = self.get_by_id(id, include_deleted)
        if not record:
            raise ValueError(f"{self.model.__name__} with ID {id} not found")
        return record
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_deleted: bool = False,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> Tuple[List[T], int]:
        """
        Get all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Max records to return (1-100)
            include_deleted: Include soft-deleted records
            order_by: Column name to order by
            order_desc: Order descending
            
        Returns:
            Tuple of (records, total_count)
        """
        # Validate pagination
        if skip < 0:
            skip = 0
        if limit < 1:
            limit = 1
        if limit > 100:
            limit = 100
        
        query = self.db.query(self.model)
        
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            query = query.order_by(column.desc() if order_desc else column.asc())
        else:
            query = query.order_by(self.model.id.desc())
        
        total = query.count()
        records = query.offset(skip).limit(limit).all()
        
        return records, total
    
    def create(self, **kwargs) -> T:
        """
        Create a new record.
        
        Args:
            **kwargs: Record attributes
            
        Returns:
            Created record
            
        Raises:
            ValueError: If validation fails
            SQLAlchemyError: If database error occurs
        """
        try:
            # Remove any sensitive fields that shouldn't be set
            kwargs.pop('deleted_at', None)
            kwargs.pop('created_at', None)
            kwargs.pop('updated_at', None)
            
            record = self.model(**kwargs)
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Failed to create {self.model.__name__}: {str(e)}")
    
    def update(self, id: int, **kwargs) -> T:
        """
        Update a record.
        
        Args:
            id: Record ID
            **kwargs: Attributes to update
            
        Returns:
            Updated record
            
        Raises:
            ValueError: If record not found or validation fails
            SQLAlchemyError: If database error occurs
        """
        try:
            record = self.get_by_id_or_fail(id)
            
            # Remove protected fields
            kwargs.pop('id', None)
            kwargs.pop('created_at', None)
            kwargs.pop('deleted_at', None)
            
            for key, value in kwargs.items():
                if value is not None and hasattr(record, key):
                    setattr(record, key, value)
            
            self.db.commit()
            self.db.refresh(record)
            return record
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Failed to update {self.model.__name__}: {str(e)}")
    
    def soft_delete(self, id: int) -> bool:
        """
        Soft delete a record.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If record not found
            SQLAlchemyError: If database error occurs
        """
        try:
            record = self.get_by_id_or_fail(id)
            record.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Failed to delete {self.model.__name__}: {str(e)}")
    
    def hard_delete(self, id: int) -> bool:
        """
        Hard delete a record.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If record not found
            SQLAlchemyError: If database error occurs
        """
        try:
            record = self.get_by_id_or_fail(id, include_deleted=True)
            self.db.delete(record)
            self.db.commit()
            return True
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Failed to delete {self.model.__name__}: {str(e)}")
    
    def restore(self, id: int) -> T:
        """
        Restore a soft-deleted record.
        
        Args:
            id: Record ID
            
        Returns:
            Restored record
            
        Raises:
            ValueError: If record not found
            SQLAlchemyError: If database error occurs
        """
        try:
            record = self.get_by_id_or_fail(id, include_deleted=True)
            if record.deleted_at is None:
                raise ValueError(f"{self.model.__name__} is not deleted")
            
            record.deleted_at = None
            self.db.commit()
            self.db.refresh(record)
            return record
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Failed to restore {self.model.__name__}: {str(e)}")
    
    def exists(self, **filters) -> bool:
        """
        Check if record exists with given filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            True if exists
        """
        query = self.db.query(self.model).filter(self.model.deleted_at.is_(None))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first() is not None
    
    def count(self, **filters) -> int:
        """
        Count records with optional filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            Count of records
        """
        query = self.db.query(self.model).filter(self.model.deleted_at.is_(None))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.count()
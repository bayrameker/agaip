"""
Base repository class for the Agaip framework.

This module provides a base repository class with common CRUD operations
and query patterns for all model repositories.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID

from tortoise.models import Model
from tortoise.queryset import QuerySet
from tortoise.exceptions import DoesNotExist

from agaip.core.exceptions import DatabaseError

T = TypeVar('T', bound=Model)


class BaseRepository:
    """Base repository class with common CRUD operations."""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    async def create(self, **kwargs) -> T:
        """Create a new model instance."""
        try:
            instance = await self.model_class.create(**kwargs)
            return instance
        except Exception as e:
            raise DatabaseError(f"Failed to create {self.model_class.__name__}: {e}")
    
    async def get_by_id(self, id: Union[UUID, str, int]) -> Optional[T]:
        """Get model by ID."""
        try:
            return await self.model_class.get(id=id)
        except DoesNotExist:
            return None
        except Exception as e:
            raise DatabaseError(f"Failed to get {self.model_class.__name__} by ID: {e}")
    
    async def get_by_id_or_raise(self, id: Union[UUID, str, int]) -> T:
        """Get model by ID or raise exception if not found."""
        instance = await self.get_by_id(id)
        if instance is None:
            raise DatabaseError(f"{self.model_class.__name__} with ID {id} not found")
        return instance
    
    async def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """Get model by a specific field value."""
        try:
            return await self.model_class.get(**{field_name: value})
        except DoesNotExist:
            return None
        except Exception as e:
            raise DatabaseError(f"Failed to get {self.model_class.__name__} by {field_name}: {e}")
    
    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get all model instances."""
        try:
            queryset = self.model_class.all()
            if offset > 0:
                queryset = queryset.offset(offset)
            if limit is not None:
                queryset = queryset.limit(limit)
            return await queryset
        except Exception as e:
            raise DatabaseError(f"Failed to get all {self.model_class.__name__}: {e}")
    
    async def filter(self, **kwargs) -> List[T]:
        """Filter model instances by criteria."""
        try:
            return await self.model_class.filter(**kwargs)
        except Exception as e:
            raise DatabaseError(f"Failed to filter {self.model_class.__name__}: {e}")
    
    async def filter_one(self, **kwargs) -> Optional[T]:
        """Filter and return single model instance."""
        try:
            return await self.model_class.filter(**kwargs).first()
        except Exception as e:
            raise DatabaseError(f"Failed to filter {self.model_class.__name__}: {e}")
    
    async def update(self, id: Union[UUID, str, int], **kwargs) -> Optional[T]:
        """Update model instance by ID."""
        try:
            instance = await self.get_by_id(id)
            if instance is None:
                return None
            
            for field, value in kwargs.items():
                setattr(instance, field, value)
            
            await instance.save()
            return instance
        except Exception as e:
            raise DatabaseError(f"Failed to update {self.model_class.__name__}: {e}")
    
    async def delete(self, id: Union[UUID, str, int]) -> bool:
        """Delete model instance by ID."""
        try:
            instance = await self.get_by_id(id)
            if instance is None:
                return False
            
            await instance.delete()
            return True
        except Exception as e:
            raise DatabaseError(f"Failed to delete {self.model_class.__name__}: {e}")
    
    async def soft_delete(self, id: Union[UUID, str, int]) -> bool:
        """Soft delete model instance by ID (if supported)."""
        try:
            instance = await self.get_by_id(id)
            if instance is None:
                return False
            
            if hasattr(instance, 'soft_delete'):
                await instance.soft_delete()
                return True
            else:
                # Fallback to hard delete
                await instance.delete()
                return True
        except Exception as e:
            raise DatabaseError(f"Failed to soft delete {self.model_class.__name__}: {e}")
    
    async def count(self, **kwargs) -> int:
        """Count model instances matching criteria."""
        try:
            if kwargs:
                return await self.model_class.filter(**kwargs).count()
            else:
                return await self.model_class.all().count()
        except Exception as e:
            raise DatabaseError(f"Failed to count {self.model_class.__name__}: {e}")
    
    async def exists(self, **kwargs) -> bool:
        """Check if model instance exists matching criteria."""
        try:
            return await self.model_class.filter(**kwargs).exists()
        except Exception as e:
            raise DatabaseError(f"Failed to check existence of {self.model_class.__name__}: {e}")
    
    async def bulk_create(self, instances_data: List[Dict[str, Any]]) -> List[T]:
        """Bulk create model instances."""
        try:
            instances = [self.model_class(**data) for data in instances_data]
            return await self.model_class.bulk_create(instances)
        except Exception as e:
            raise DatabaseError(f"Failed to bulk create {self.model_class.__name__}: {e}")
    
    async def bulk_update(self, instances: List[T], fields: List[str]) -> None:
        """Bulk update model instances."""
        try:
            await self.model_class.bulk_update(instances, fields)
        except Exception as e:
            raise DatabaseError(f"Failed to bulk update {self.model_class.__name__}: {e}")
    
    def get_queryset(self) -> QuerySet:
        """Get base queryset for the model."""
        return self.model_class.all()
    
    def filter_queryset(self, queryset: QuerySet, **kwargs) -> QuerySet:
        """Apply filters to queryset."""
        return queryset.filter(**kwargs)
    
    async def paginate(
        self, 
        page: int = 1, 
        page_size: int = 20, 
        **filters
    ) -> Dict[str, Any]:
        """Paginate model instances."""
        try:
            offset = (page - 1) * page_size
            
            queryset = self.get_queryset()
            if filters:
                queryset = self.filter_queryset(queryset, **filters)
            
            total_count = await queryset.count()
            items = await queryset.offset(offset).limit(page_size)
            
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "items": items,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }
        except Exception as e:
            raise DatabaseError(f"Failed to paginate {self.model_class.__name__}: {e}")

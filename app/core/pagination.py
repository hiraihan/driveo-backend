from typing import Generic, TypeVar
from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import math

T = TypeVar('T')

class PageParams(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=100)

class PageMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int

class Page(BaseModel, Generic[T]):
    data: list[T]
    pagination: PageMeta

async def paginate(db: AsyncSession, stmt, params: PageParams, item_schema: type[T]) -> Page[T]:
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    total = total or 0
    total_pages = math.ceil(total / params.page_size) if total > 0 else 0
    
    paginated_stmt = stmt.limit(params.page_size).offset((params.page - 1) * params.page_size)
    result = await db.execute(paginated_stmt)
    items = result.scalars().all()
    
    return Page(
        data=[item_schema.model_validate(item) for item in items],
        pagination=PageMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=total_pages
        )
    )

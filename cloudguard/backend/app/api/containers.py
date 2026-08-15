"""Containers API."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.container import Container
from app.schemas import ContainerResponse

router = APIRouter()


@router.get("/containers", response_model=List[ContainerResponse], tags=["Containers"])
async def list_containers(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
):
    """List all tracked containers."""
    stmt = select(Container).order_by(desc(Container.risk_score))
    if status:
        stmt = stmt.where(Container.status == status.lower())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/containers/{container_id}", response_model=ContainerResponse, tags=["Containers"])
async def get_container(container_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific container by its container_id."""
    result = await db.execute(
        select(Container).where(Container.container_id == container_id)
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    return container

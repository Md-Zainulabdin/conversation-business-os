from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.stats import OverviewResponse
from app.services import stats as stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    period: str = Query("30d", pattern=r"^(24h|7d|30d|12m)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await stats_service.get_overview(db, current_user, period)

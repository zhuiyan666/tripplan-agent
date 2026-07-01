from fastapi import APIRouter, HTTPException
from app.models.schemas import TripPlanRequest, TripPlan
from app.services.unsplash_service import UnsplashService
from app.agents.trip_planner import TripPlannerAgent
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# 初始化服务
trip_planner = TripPlannerAgent()
unsplash_service = UnsplashService(settings.unsplash_access_key) if settings.unsplash_access_key else None


@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    """创建旅行计划"""
    try:
        # 生成旅行计划
        trip_plan = await trip_planner.plan_trip(request)

        # 为每个景点获取图片
        if unsplash_service:
            for day in trip_plan.days:
                for attraction in day.attractions:
                    if not attraction.image_url:
                        try:
                            image_url = await unsplash_service.get_photo_url(
                                f"{attraction.name} {trip_plan.city}"
                            )
                            attraction.image_url = image_url
                        except Exception:
                            pass

        return trip_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成旅行计划失败: {str(e)}")

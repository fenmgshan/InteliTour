"""美食推荐 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.schemas.food import FoodItem, FoodRecommendRequest, FoodSearchRequest
from backend.services import food_service

router = APIRouter(prefix="/api/food", tags=["food"])


@router.post("/recommend", response_model=list[FoodItem], summary="附近美食 Top-N 推荐")
def recommend(req: FoodRecommendRequest):
    try:
        return food_service.recommend_food(
            req.origin_lat, req.origin_lng, req.cuisine, req.n
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=list[FoodItem], summary="美食模糊搜索（Trie + 编辑距离）")
def search(req: FoodSearchRequest):
    try:
        return food_service.search_food(
            req.q, req.origin_lat, req.origin_lng, req.max_edit_distance, req.n
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

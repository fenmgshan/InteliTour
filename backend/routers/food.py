"""美食推荐 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.schemas.food import FoodItem, FoodRecommendRequest, FoodSearchRequest
from backend.services import food_service
from backend.utils.coords import to_wgs84, convert_dict_latlng

router = APIRouter(prefix="/api/food", tags=["food"])


@router.post("/recommend", response_model=list[FoodItem], summary="附近美食 Top-N 推荐")
def recommend(req: FoodRecommendRequest):
    try:
        # GCJ-02（高德）→ WGS-84（OSM 路网）
        wgs_lat, wgs_lng = to_wgs84(req.origin_lat, req.origin_lng)
        results = food_service.recommend_food(wgs_lat, wgs_lng, req.cuisine, req.n)
        # WGS-84 → GCJ-02，使 POI 位置与高德地图底图对齐
        for item in results:
            convert_dict_latlng(item, "gcj02")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=list[FoodItem], summary="美食模糊搜索（Trie + 编辑距离）")
def search(req: FoodSearchRequest):
    try:
        # GCJ-02（高德）→ WGS-84（OSM 路网）
        wgs_lat, wgs_lng = to_wgs84(req.origin_lat, req.origin_lng)
        results = food_service.search_food(
            req.q, wgs_lat, wgs_lng, req.max_edit_distance, req.n,
        )
        # WGS-84 → GCJ-02，使 POI 位置与高德地图底图对齐
        for item in results:
            convert_dict_latlng(item, "gcj02")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

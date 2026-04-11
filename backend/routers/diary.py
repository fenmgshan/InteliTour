"""日记 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.schemas.diary import DiaryCreate, DiaryResponse, DiaryBrief, DiarySearchRequest
from backend.services import diary_service

router = APIRouter(prefix="/api/diary", tags=["diary"])


@router.post("", response_model=DiaryBrief, summary="发布日记", status_code=201)
def create_diary(req: DiaryCreate):
    try:
        diary_id = diary_service.create_diary(
            req.title, req.author, req.destination, req.content, req.rating
        )
        result = diary_service._brief_dict_by_id(diary_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend", response_model=list[DiaryBrief], summary="Top-N 日记推荐")
def recommend(n: int = 10):
    if n < 1 or n > 50:
        raise HTTPException(status_code=400, detail="n 范围 1-50")
    return diary_service.recommend_diaries(n)


@router.post("/search", response_model=list[DiaryBrief], summary="日记搜索")
def search(req: DiarySearchRequest):
    try:
        return diary_service.search_diaries(req.mode, req.q)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{diary_id}", response_model=DiaryResponse, summary="获取日记详情（热度+1）")
def get_diary(diary_id: int):
    result = diary_service.get_diary(diary_id)
    if result is None:
        raise HTTPException(status_code=404, detail="日记不存在")
    return result


@router.post("/{diary_id}/view", summary="手动触发热度+1")
def view_diary(diary_id: int):
    from backend.services.redis_service import incr_heat
    heat = incr_heat("diary", diary_id)
    return {"id": diary_id, "heat": heat}


@router.delete("/{diary_id}", summary="删除日记")
def delete_diary(diary_id: int):
    ok = diary_service.delete_diary(diary_id)
    if not ok:
        raise HTTPException(status_code=404, detail="日记不存在")
    return {"deleted": diary_id}

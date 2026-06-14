"""坐标吸附 API"""

from fastapi import APIRouter, HTTPException

from backend.schemas.route import SnapRequest, SnapResponse
from backend.services.snap_service import get_snap_service
from backend.utils.coords import to_wgs84, to_gcj02

router = APIRouter(prefix="/api", tags=["snap"])


@router.post("/snap", response_model=SnapResponse, summary="坐标吸附到最近路网节点")
def snap_point(req: SnapRequest):
    try:
        # GCJ-02（高德）→ WGS-84（OSM 路网）
        wgs_lat, wgs_lng = to_wgs84(req.lat, req.lng)
        service = get_snap_service()
        node_id, node_lat, node_lng, dist = service.snap_point(wgs_lat, wgs_lng)
        # WGS-84 → GCJ-02，使吸附点与高德地图底图对齐
        gcj_lat, gcj_lng = to_gcj02(node_lat, node_lng)
        return SnapResponse(
            node_id=int(node_id),
            lat=gcj_lat,
            lng=gcj_lng,
            distance=round(dist, 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

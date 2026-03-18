"""路线规划 API（最短路径 + TSP）"""

from fastapi import APIRouter, HTTPException

from backend.schemas.route import (
    LatLng,
    ShortestPathRequest,
    ShortestPathResponse,
    TSPRequest,
    TSPResponse,
    TSPSegment,
)
from backend.services.snap_service import get_snap_service
from backend.services.graph_service import get_graph
from backend.services.route_service import (
    dijkstra_shortest_path,
    solve_tsp,
    STRATEGY_WEIGHT,
    STRATEGY_SPEED,
)

router = APIRouter(prefix="/api/route", tags=["route"])


def _snap(lat: float, lng: float):
    """吸附坐标并返回图中使用的节点 ID。"""
    service = get_snap_service()
    node_id, _, _, _ = service.snap_point(lat, lng)
    # GraphML 加载后节点 ID 为字符串，需要匹配图中的实际类型
    G = get_graph()
    if node_id in G:
        return node_id
    str_id = str(node_id)
    if str_id in G:
        return str_id
    raise ValueError(f"吸附节点 {node_id} 不在图中")


@router.post(
    "/shortest",
    response_model=ShortestPathResponse,
    summary="两点最短路径",
)
def shortest_path(req: ShortestPathRequest):
    if req.strategy not in STRATEGY_WEIGHT:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的策略: {req.strategy}，可选: {list(STRATEGY_WEIGHT)}",
        )
    try:
        origin_node = _snap(req.origin.lat, req.origin.lng)
        dest_node = _snap(req.destination.lat, req.destination.lng)

        path_coords, total_distance, total_time = dijkstra_shortest_path(
            origin_node, dest_node, req.strategy
        )

        return ShortestPathResponse(
            path=path_coords,
            total_distance=round(total_distance, 2),
            total_time=round(total_time, 2),
            strategy=req.strategy,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tsp",
    response_model=TSPResponse,
    summary="多点 TSP 路线规划",
)
def tsp_route(req: TSPRequest):
    if req.strategy not in STRATEGY_WEIGHT:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的策略: {req.strategy}，可选: {list(STRATEGY_WEIGHT)}",
        )
    if len(req.waypoints) > 15:
        raise HTTPException(
            status_code=400,
            detail="途经点数量不能超过 15 个",
        )
    if len(req.waypoints) == 0:
        raise HTTPException(
            status_code=400,
            detail="至少需要 1 个途经点",
        )

    try:
        origin_node = _snap(req.origin.lat, req.origin.lng)
        waypoint_nodes = [_snap(wp.lat, wp.lng) for wp in req.waypoints]

        order, segments, _ = solve_tsp(
            origin_node, waypoint_nodes, req.strategy, req.round_trip
        )

        # 构造响应
        G = get_graph()
        all_coords = []
        seg_responses = []
        total_distance = 0.0
        total_time = 0.0

        # 构建 from/to 索引序列
        visit_sequence = [-1] + [idx for idx in order]
        if req.round_trip:
            visit_sequence.append(-1)

        for i, (seg_path, seg_dist, seg_time) in enumerate(segments):
            from_idx = visit_sequence[i]
            to_idx = visit_sequence[i + 1]

            seg_coords = []
            for node in seg_path:
                data = G.nodes[node]
                seg_coords.append(LatLng(lat=data["lat"], lng=data["lng"]))

            seg_responses.append(
                TSPSegment(
                    from_index=from_idx,
                    to_index=to_idx,
                    path=seg_coords,
                    distance=round(seg_dist, 2),
                    time=round(seg_time, 2),
                )
            )

            # 拼接完整路径（跳过重复的衔接点）
            if i == 0:
                all_coords.extend(seg_coords)
            else:
                all_coords.extend(seg_coords[1:] if seg_coords else [])

            total_distance += seg_dist
            total_time += seg_time

        return TSPResponse(
            ordered_waypoints=order,
            path=all_coords,
            segments=seg_responses,
            total_distance=round(total_distance, 2),
            total_time=round(total_time, 2),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

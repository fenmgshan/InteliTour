"""路线规划 API（最短路径 + TSP）"""

import traceback

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
    """吸附坐标并返回图中使用的节点 ID（单候选）。"""
    service = get_snap_service()
    node_id, _, _, _ = service.snap_point(lat, lng)
    G = get_graph()
    if node_id in G:
        return node_id
    str_id = str(node_id)
    if str_id in G:
        return str_id
    raise ValueError(f"吸附节点 {node_id} (type={type(node_id).__name__}) 不在图中")


def _snap_nearest_k(lat: float, lng: float, k: int = 3):
    """多候选吸附，返回图中存在的 K 个最近节点 ID。

    直线最近 ≠ 路网最优入口。多候选可避免吸附到立交桥对面、
    断头路等导致绕路的节点。
    """
    service = get_snap_service()
    candidates = service.snap_nearest_k(lat, lng, k)
    G = get_graph()
    result = []
    for node_id, _, _, _ in candidates:
        if node_id in G:
            result.append(node_id)
        else:
            str_id = str(node_id)
            if str_id in G:
                result.append(str_id)
    if not result:
        raise ValueError(f"坐标 ({lat}, {lng}) 附近无路网节点")
    return result


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
        # 多候选吸附：直线最近 ≠ 路网最优入口
        origin_nodes = _snap_nearest_k(req.origin.lat, req.origin.lng)
        dest_nodes = _snap_nearest_k(req.destination.lat, req.destination.lng)

        best = None
        for o in origin_nodes:
            for d in dest_nodes:
                try:
                    path_coords, dist, time_val = dijkstra_shortest_path(o, d, req.strategy)
                    if best is None or dist < best[1]:
                        best = (path_coords, dist, time_val)
                except Exception:
                    continue

        if best is None:
            raise HTTPException(status_code=500, detail="无法找到连通路径")

        path_coords, total_distance, total_time = best
        return ShortestPathResponse(
            path=path_coords,
            total_distance=round(total_distance, 2),
            total_time=round(total_time, 2),
            strategy=req.strategy,
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
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
        # 途经点精确吸附（用户手动点击），起点多候选择优
        waypoint_nodes = [_snap(wp.lat, wp.lng) for wp in req.waypoints]
        origin_candidates = _snap_nearest_k(req.origin.lat, req.origin.lng)

        best = None  # (order, segments, G_ref for response)

        for o in origin_candidates:
            try:
                order, segments, _ = solve_tsp(
                    o, waypoint_nodes, req.strategy, req.round_trip
                )
                seg_total_dist = sum(s[1] for s in segments)
                if best is None or seg_total_dist < best[0]:
                    best = (seg_total_dist, order, segments)
            except Exception:
                continue

        if best is None:
            raise HTTPException(status_code=500, detail="无法找到连通路径")

        _, order, segments = best

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
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

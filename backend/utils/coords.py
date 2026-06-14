"""WGS-84 ↔ GCJ-02 坐标系转换

高德地图使用 GCJ-02（国测局坐标系），OpenStreetMap 使用 WGS-84。
中国境内两坐标系偏移 100-700m，不转换会导致路线偏移、定位不准。

算法来源：GCJ-02 公开的加密偏移公式，双向转换。
"""

import math

PI = math.pi
X_PI = PI * 3000.0 / 180.0
A = 6378245.0          # 长半轴
EE = 0.00669342162296594323  # 偏心率平方


def _out_of_china(lng: float, lat: float) -> bool:
    """判断经纬度是否在中国境外（境外无需转换）。"""
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def _transform_lat(x: float, y: float) -> float:
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * PI) + 320.0 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(x: float, y: float) -> float:
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(lng: float, lat: float) -> tuple[float, float]:
    """WGS-84 → GCJ-02"""
    if _out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1.0 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1.0 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    return lng + dlng, lat + dlat


def gcj02_to_wgs84(lng: float, lat: float) -> tuple[float, float]:
    """GCJ-02 → WGS-84（迭代法，高精度）"""
    if _out_of_china(lng, lat):
        return lng, lat
    mglng, mglat = wgs84_to_gcj02(lng, lat)
    return lng * 2.0 - mglng, lat * 2.0 - mglat


def to_wgs84(lat: float, lng: float) -> tuple[float, float]:
    """(lat, lng) GCJ-02 → WGS-84。前端 AMap 点击坐标 → 后端处理坐标。"""
    wgs_lng, wgs_lat = gcj02_to_wgs84(lng, lat)
    return wgs_lat, wgs_lng


def to_gcj02(lat: float, lng: float) -> tuple[float, float]:
    """(lat, lng) WGS-84 → GCJ-02。后端 OSM 坐标 → 前端 AMap 展示坐标。"""
    gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
    return gcj_lat, gcj_lng


def convert_latlng(obj, to: str = "gcj02"):
    """转换 LatLng 对象的坐标。"""
    fn = to_gcj02 if to == "gcj02" else to_wgs84
    new_lat, new_lng = fn(obj.lat, obj.lng)
    obj.lat = new_lat
    obj.lng = new_lng
    return obj


def convert_dict_latlng(d: dict, to: str = "gcj02"):
    """原地转换 dict 中的 lat/lng 字段。"""
    fn = to_gcj02 if to == "gcj02" else to_wgs84
    if "lat" in d and "lng" in d:
        d["lat"], d["lng"] = fn(d["lat"], d["lng"])
    return d

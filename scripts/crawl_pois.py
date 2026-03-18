"""爬取建筑物与服务设施 POI

使用 OSMnx 爬取天安门周边 5km 范围内的:
- 景点 (tourism=*)
- 餐饮 (amenity=restaurant/cafe/fast_food)
- 便利服务 (amenity=toilets, shop=convenience/supermarket)
- 建筑物 (building=*)
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import osmnx as ox
import geopandas as gpd
from sqlalchemy import text
from database.config import get_engine, get_session
from database.models import POI, Building

CENTER_LAT = 39.9042
CENTER_LNG = 116.3974
RADIUS = 5000


# 类别映射：OSM tag 值 -> (category, sub_category)
TOURISM_CATEGORIES = {
    "attraction": ("景点", "景点"),
    "museum": ("景点", "博物馆"),
    "viewpoint": ("景点", "观景台"),
    "gallery": ("景点", "画廊"),
    "artwork": ("景点", "艺术品"),
    "theme_park": ("景点", "主题公园"),
    "zoo": ("景点", "动物园"),
    "aquarium": ("景点", "水族馆"),
}

AMENITY_CATEGORIES = {
    "restaurant": ("餐厅", "餐厅"),
    "cafe": ("餐厅", "咖啡厅"),
    "fast_food": ("餐厅", "快餐"),
    "toilets": ("卫生间", "公共卫生间"),
}

SHOP_CATEGORIES = {
    "convenience": ("便利店", "便利店"),
    "supermarket": ("超市", "超市"),
}


def get_centroid(geom):
    """获取几何体质心坐标"""
    centroid = geom.centroid
    return centroid.y, centroid.x


def crawl_pois():
    """爬取 POI 数据"""
    all_pois = []

    # 1. 景点 tourism=*
    print("正在爬取景点数据...")
    try:
        tourism_gdf = ox.geometries_from_point(
            (CENTER_LAT, CENTER_LNG), dist=RADIUS,
            tags={"tourism": True}
        )
        for idx, row in tourism_gdf.iterrows():
            tourism_val = row.get("tourism", "")
            if not tourism_val or tourism_val not in TOURISM_CATEGORIES:
                cat, sub = "景点", str(tourism_val)
            else:
                cat, sub = TOURISM_CATEGORIES[tourism_val]

            lat, lng = get_centroid(row.geometry)
            osm_id = idx[1] if isinstance(idx, tuple) else None

            all_pois.append({
                "osm_id": int(osm_id) if osm_id else None,
                "name": str(row.get("name", row.get("name:en", "")))[:255],
                "category": cat,
                "sub_category": sub[:50],
                "lat": lat,
                "lng": lng,
                "address": str(row.get("addr:street", ""))[:500],
                "phone": str(row.get("phone", ""))[:50],
                "opening_hours": str(row.get("opening_hours", ""))[:255],
                "tags_json": json.dumps(
                    {k: str(v) for k, v in row.items()
                     if k != "geometry" and v is not None and str(v) != "nan"},
                    ensure_ascii=False
                ),
            })
        print(f"  景点: {len(tourism_gdf)} 条")
    except Exception as e:
        print(f"  景点爬取失败: {e}")

    # 2. 餐饮 amenity=restaurant|cafe|fast_food
    print("正在爬取餐饮数据...")
    try:
        food_gdf = ox.geometries_from_point(
            (CENTER_LAT, CENTER_LNG), dist=RADIUS,
            tags={"amenity": ["restaurant", "cafe", "fast_food"]}
        )
        for idx, row in food_gdf.iterrows():
            amenity_val = row.get("amenity", "")
            cat, sub = AMENITY_CATEGORIES.get(amenity_val, ("餐厅", str(amenity_val)))

            lat, lng = get_centroid(row.geometry)
            osm_id = idx[1] if isinstance(idx, tuple) else None

            all_pois.append({
                "osm_id": int(osm_id) if osm_id else None,
                "name": str(row.get("name", row.get("name:en", "")))[:255],
                "category": cat,
                "sub_category": sub[:50],
                "lat": lat,
                "lng": lng,
                "address": str(row.get("addr:street", ""))[:500],
                "phone": str(row.get("phone", ""))[:50],
                "opening_hours": str(row.get("opening_hours", ""))[:255],
                "tags_json": json.dumps(
                    {k: str(v) for k, v in row.items()
                     if k != "geometry" and v is not None and str(v) != "nan"},
                    ensure_ascii=False
                ),
            })
        print(f"  餐饮: {len(food_gdf)} 条")
    except Exception as e:
        print(f"  餐饮爬取失败: {e}")

    # 3. 卫生间 amenity=toilets
    print("正在爬取卫生间数据...")
    try:
        toilet_gdf = ox.geometries_from_point(
            (CENTER_LAT, CENTER_LNG), dist=RADIUS,
            tags={"amenity": "toilets"}
        )
        for idx, row in toilet_gdf.iterrows():
            lat, lng = get_centroid(row.geometry)
            osm_id = idx[1] if isinstance(idx, tuple) else None

            all_pois.append({
                "osm_id": int(osm_id) if osm_id else None,
                "name": str(row.get("name", "公共卫生间"))[:255],
                "category": "卫生间",
                "sub_category": "公共卫生间",
                "lat": lat,
                "lng": lng,
                "address": str(row.get("addr:street", ""))[:500],
                "phone": "",
                "opening_hours": str(row.get("opening_hours", ""))[:255],
                "tags_json": json.dumps(
                    {k: str(v) for k, v in row.items()
                     if k != "geometry" and v is not None and str(v) != "nan"},
                    ensure_ascii=False
                ),
            })
        print(f"  卫生间: {len(toilet_gdf)} 条")
    except Exception as e:
        print(f"  卫生间爬取失败: {e}")

    # 4. 便利店/超市 shop=convenience|supermarket
    print("正在爬取便利店/超市数据...")
    try:
        shop_gdf = ox.geometries_from_point(
            (CENTER_LAT, CENTER_LNG), dist=RADIUS,
            tags={"shop": ["convenience", "supermarket"]}
        )
        for idx, row in shop_gdf.iterrows():
            shop_val = row.get("shop", "")
            cat, sub = SHOP_CATEGORIES.get(shop_val, ("便利店", str(shop_val)))

            lat, lng = get_centroid(row.geometry)
            osm_id = idx[1] if isinstance(idx, tuple) else None

            all_pois.append({
                "osm_id": int(osm_id) if osm_id else None,
                "name": str(row.get("name", row.get("name:en", "")))[:255],
                "category": cat,
                "sub_category": sub[:50],
                "lat": lat,
                "lng": lng,
                "address": str(row.get("addr:street", ""))[:500],
                "phone": str(row.get("phone", ""))[:50],
                "opening_hours": str(row.get("opening_hours", ""))[:255],
                "tags_json": json.dumps(
                    {k: str(v) for k, v in row.items()
                     if k != "geometry" and v is not None and str(v) != "nan"},
                    ensure_ascii=False
                ),
            })
        print(f"  便利店/超市: {len(shop_gdf)} 条")
    except Exception as e:
        print(f"  便利店/超市爬取失败: {e}")

    return all_pois


def crawl_buildings():
    """爬取建筑物数据"""
    print("正在爬取建筑物数据...")
    all_buildings = []
    try:
        building_gdf = ox.geometries_from_point(
            (CENTER_LAT, CENTER_LNG), dist=RADIUS,
            tags={"building": True}
        )
        for idx, row in building_gdf.iterrows():
            lat, lng = get_centroid(row.geometry)
            osm_id = idx[1] if isinstance(idx, tuple) else None

            # 楼层数
            floors = 0
            floors_str = row.get("building:levels", 0)
            if floors_str:
                try:
                    floors = int(float(str(floors_str)))
                except (ValueError, TypeError):
                    floors = 0

            geom_wkt = ""
            if row.geometry is not None:
                geom_wkt = row.geometry.wkt

            all_buildings.append({
                "osm_id": int(osm_id) if osm_id else None,
                "name": str(row.get("name", ""))[:255],
                "building_type": str(row.get("building", ""))[:50],
                "lat": lat,
                "lng": lng,
                "address": str(row.get("addr:street", ""))[:500],
                "floors": floors,
                "geometry_wkt": geom_wkt,
            })
        print(f"  建筑物: {len(building_gdf)} 条")
    except Exception as e:
        print(f"  建筑物爬取失败: {e}")

    return all_buildings


def save_pois_to_mysql(pois_data):
    """写入 POI 到 MySQL"""
    session = get_session()
    try:
        session.execute(text("DELETE FROM pois"))
        session.commit()

        objects = [POI(**p) for p in pois_data]
        session.bulk_save_objects(objects)
        session.commit()
        print(f"[OK] 写入 {len(objects)} 条 POI")
    finally:
        session.close()


def save_buildings_to_mysql(buildings_data):
    """写入建筑物到 MySQL"""
    session = get_session()
    try:
        session.execute(text("DELETE FROM buildings"))
        session.commit()

        objects = [Building(**b) for b in buildings_data]
        session.bulk_save_objects(objects)
        session.commit()
        print(f"[OK] 写入 {len(objects)} 条建筑物")
    finally:
        session.close()


def main():
    pois = crawl_pois()
    buildings = crawl_buildings()

    # 按类别统计
    from collections import Counter
    cat_counts = Counter(p["category"] for p in pois)
    print("\nPOI 类别统计:")
    for cat, cnt in cat_counts.most_common():
        print(f"  {cat}: {cnt}")

    save_pois_to_mysql(pois)
    save_buildings_to_mysql(buildings)
    print("[OK] POI 与建筑物爬取完成")


if __name__ == "__main__":
    main()

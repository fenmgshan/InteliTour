"""API 集成测试脚本

需要先启动服务器和数据库，测试真实 API 端点。
运行: python3 tests/test_api_integration.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_diary_api():
    print_section("测试日记 API")

    # 1. 创建日记
    print("\n[1] 创建日记...")
    diary_data = {
        "title": "北京故宫游记",
        "author": "测试用户",
        "destination": "故宫",
        "content": "今天参观了故宫博物院，感受到了中国古代建筑的宏伟壮丽。" * 50,
        "rating": 4.8,
    }
    resp = requests.post(f"{BASE_URL}/api/diary", json=diary_data)
    assert resp.status_code == 201, f"创建失败: {resp.text}"
    diary = resp.json()
    diary_id = diary["id"]
    print(f"✓ 创建成功，ID={diary_id}, 热度={diary['heat']}")

    # 2. 获取详情（触发热度+1）
    print(f"\n[2] 获取日记详情 (ID={diary_id})...")
    resp = requests.get(f"{BASE_URL}/api/diary/{diary_id}")
    assert resp.status_code == 200
    detail = resp.json()
    print(f"✓ 标题: {detail['title']}")
    print(f"✓ 热度: {detail['heat']} (应为 1)")
    print(f"✓ 正文长度: {len(detail['content'])} 字符")

    # 3. 手动触发热度+1
    print(f"\n[3] 手动增加热度...")
    resp = requests.post(f"{BASE_URL}/api/diary/{diary_id}/view")
    assert resp.status_code == 200
    print(f"✓ 当前热度: {resp.json()['heat']}")

    # 4. 搜索 - 按标题精确查找
    print(f"\n[4] 搜索日记 (mode=title)...")
    resp = requests.post(
        f"{BASE_URL}/api/diary/search",
        json={"mode": "title", "q": "北京故宫游记"}
    )
    assert resp.status_code == 200
    results = resp.json()
    print(f"✓ 找到 {len(results)} 条结果")

    # 5. 搜索 - 按目的地
    print(f"\n[5] 搜索日记 (mode=destination)...")
    resp = requests.post(
        f"{BASE_URL}/api/diary/search",
        json={"mode": "destination", "q": "故宫"}
    )
    assert resp.status_code == 200
    results = resp.json()
    print(f"✓ 找到 {len(results)} 条结果")

    # 6. 搜索 - 全文检索
    print(f"\n[6] 搜索日记 (mode=fulltext)...")
    resp = requests.post(
        f"{BASE_URL}/api/diary/search",
        json={"mode": "fulltext", "q": "建筑"}
    )
    assert resp.status_code == 200
    results = resp.json()
    print(f"✓ 全文检索找到 {len(results)} 条结果")

    # 7. Top-N 推荐
    print(f"\n[7] 获取 Top-5 推荐...")
    resp = requests.get(f"{BASE_URL}/api/diary/recommend?n=5")
    assert resp.status_code == 200
    recommendations = resp.json()
    print(f"✓ 推荐 {len(recommendations)} 条日记")
    for i, d in enumerate(recommendations[:3], 1):
        print(f"  {i}. {d['title']} (热度={d['heat']}, 评分={d['rating']})")

    # 8. 删除日记
    print(f"\n[8] 删除日记 (ID={diary_id})...")
    resp = requests.delete(f"{BASE_URL}/api/diary/{diary_id}")
    assert resp.status_code == 200
    print(f"✓ 删除成功")

    print("\n✅ 日记 API 测试全部通过")


def test_food_api():
    print_section("测试美食推荐 API")

    # 1. 附近美食推荐（天安门附近）
    print("\n[1] 附近美食 Top-10 推荐...")
    req_data = {
        "origin_lat": 39.9042,
        "origin_lng": 116.3974,
        "cuisine": "",  # 不过滤菜系
        "n": 10,
    }
    resp = requests.post(f"{BASE_URL}/api/food/recommend", json=req_data)
    assert resp.status_code == 200
    foods = resp.json()
    print(f"✓ 推荐 {len(foods)} 家餐厅")
    for i, f in enumerate(foods[:3], 1):
        print(f"  {i}. {f['name']} - {f['sub_category']} "
              f"(距离={f['distance']:.0f}m, 评分={f['rating']}, 综合分={f['score']})")

    # 2. 按菜系过滤
    print("\n[2] 过滤川菜...")
    req_data["cuisine"] = "川菜"
    resp = requests.post(f"{BASE_URL}/api/food/recommend", json=req_data)
    assert resp.status_code == 200
    foods = resp.json()
    print(f"✓ 找到 {len(foods)} 家川菜餐厅")

    # 3. 模糊搜索（Trie + Levenshtein）
    print("\n[3] 模糊搜索 '麻辣烫'...")
    search_data = {
        "q": "麻辣烫",
        "origin_lat": 39.9042,
        "origin_lng": 116.3974,
        "max_edit_distance": 2,
        "n": 5,
    }
    resp = requests.post(f"{BASE_URL}/api/food/search", json=search_data)
    assert resp.status_code == 200
    results = resp.json()
    print(f"✓ 找到 {len(results)} 个匹配结果")
    for r in results[:3]:
        print(f"  - {r['name']} (距离={r['distance']:.0f}m)")

    # 4. 容错搜索（错别字）
    print("\n[4] 容错搜索 '麻辣糖' (错别字)...")
    search_data["q"] = "麻辣糖"
    resp = requests.post(f"{BASE_URL}/api/food/search", json=search_data)
    assert resp.status_code == 200
    results = resp.json()
    print(f"✓ 容错找到 {len(results)} 个结果（应包含'麻辣烫'）")

    print("\n✅ 美食推荐 API 测试全部通过")


def test_nearby_api():
    print_section("测试周边设施查询 API")

    # 1. 查找附近卫生间
    print("\n[1] 查找附近 500m 内的卫生间...")
    req_data = {
        "origin_lat": 39.9042,
        "origin_lng": 116.3974,
        "category": "toilet",
        "max_dist": 500,
        "limit": 10,
    }
    resp = requests.post(f"{BASE_URL}/api/nearby", json=req_data)
    assert resp.status_code == 200
    facilities = resp.json()
    print(f"✓ 找到 {len(facilities)} 个卫生间")
    for i, f in enumerate(facilities[:3], 1):
        print(f"  {i}. {f['name']} (距离={f['distance']:.0f}m)")

    # 2. 查找附近超市
    print("\n[2] 查找附近 1000m 内的超市...")
    req_data["category"] = "supermarket"
    req_data["max_dist"] = 1000
    resp = requests.post(f"{BASE_URL}/api/nearby", json=req_data)
    assert resp.status_code == 200
    facilities = resp.json()
    print(f"✓ 找到 {len(facilities)} 个超市")

    # 3. 查找附近便利店
    print("\n[3] 查找附近 800m 内的便利店...")
    req_data["category"] = "convenience"
    req_data["max_dist"] = 800
    resp = requests.post(f"{BASE_URL}/api/nearby", json=req_data)
    assert resp.status_code == 200
    facilities = resp.json()
    print(f"✓ 找到 {len(facilities)} 个便利店")

    # 4. 验证距离排序
    if facilities:
        print("\n[4] 验证结果按距离升序排列...")
        distances = [f["distance"] for f in facilities]
        assert distances == sorted(distances), "距离未正确排序！"
        print(f"✓ 距离排序正确: {distances[:5]}")

    print("\n✅ 周边设施查询 API 测试全部通过")


def main():
    print("\n" + "="*60)
    print("  InteliTour API 集成测试")
    print("="*60)
    print(f"\n服务器地址: {BASE_URL}")
    print("请确保服务器已启动且数据库已初始化\n")

    try:
        # 健康检查
        resp = requests.get(f"{BASE_URL}/docs")
        assert resp.status_code == 200
        print("✓ 服务器连接正常\n")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("\n请先启动服务器:")
        print("  cd InteliTour && python3 -m backend.app")
        return

    try:
        test_diary_api()
        time.sleep(0.5)
        test_food_api()
        time.sleep(0.5)
        test_nearby_api()

        print("\n" + "="*60)
        print("  🎉 所有集成测试通过！")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

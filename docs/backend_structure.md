# InteliTour Backend 目录结构文档

## 项目概述

InteliTour 是一个智慧旅游路线规划系统，覆盖北京地区（天安门周边 5km 半径）。后端基于 FastAPI 框架，提供 RESTful API 服务。

**技术栈：**
- FastAPI - Web 框架
- NetworkX - 图算法
- MySQL + SQLAlchemy - 数据持久化
- Redis - 热度/评分缓存
- Whoosh - 全文检索
- uvicorn - ASGI 服务器

**启动方式：**
```bash
cd InteliTour && python3 -m backend.app
```

**API 文档：** http://localhost:8000/docs

---

## 目录结构总览

```
backend/
├── app.py                    # FastAPI 应用入口
├── __init__.py
├── routers/                  # API 路由层
│   ├── __init__.py
│   ├── snap.py              # 坐标吸附
│   ├── route.py             # 路线规划
│   ├── diary.py             # 旅游日记
│   ├── food.py              # 美食推荐
│   └── nearby.py            # 周边设施
├── services/                 # 业务逻辑层
│   ├── __init__.py
│   ├── graph_service.py     # 路网图加载
│   ├── snap_service.py      # 坐标吸附服务
│   ├── route_service.py     # 路径规划算法
│   ├── diary_service.py     # 日记管理
│   ├── food_service.py      # 美食搜索推荐
│   ├── nearby_service.py    # 周边查询
│   ├── redis_service.py     # Redis 缓存
│   └── heap_service.py      # 堆排序工具
└── schemas/                  # 数据模型层（Pydantic）
    ├── __init__.py
    ├── route.py             # 路线相关模型
    ├── diary.py             # 日记相关模型
    ├── food.py              # 美食相关模型
    └── nearby.py            # 周边查询模型
```

---

## 核心文件详解

### 1. app.py - 应用入口

**文件路径：** `backend/app.py`

**主要功能：**
- FastAPI 应用初始化
- CORS 跨域配置（支持本地前端开发）
- 路由注册
- 启动时预加载路网图和吸附服务

**关键代码逻辑：**
```python
@app.on_event("startup")
def startup():
    init_graph()           # 加载 GraphML 路网图
    init_snap_service()    # 初始化 KD-Tree 吸附索引
```

**CORS 配置：**
- 允许来源：localhost:5173, localhost:3000（前端开发服务器）
- 允许所有方法和请求头
- 支持凭证传递

**注册的路由模块：**
1. snap - 坐标吸附
2. route - 路线规划
3. diary - 旅游日记
4. food - 美食推荐
5. nearby - 周边设施

---

## routers/ - API 路由层

路由层负责处理 HTTP 请求，进行参数验证，调用业务逻辑层，返回响应。

### 2. routers/snap.py - 坐标吸附

**API 前缀：** `/api`

**功能：** 将任意经纬度坐标吸附到最近的路网节点

**接口：**
- `POST /api/snap` - 坐标吸附
  - 请求：`{lat: float, lng: float}`
  - 响应：`{node_id: int, lat: float, lng: float, distance: float}`
  - distance 单位：米

**使用场景：** 用户点击地图时，将点击位置映射到可导航的路网节点

### 3. routers/route.py - 路线规划

**API 前缀：** `/api/route`

**功能：** 提供最短路径和 TSP 多点路线规划

**接口：**

**3.1 POST /api/route/shortest** - 两点最短路径
- 请求参数：
  - `origin`: {lat, lng} - 起点坐标
  - `destination`: {lat, lng} - 终点坐标
  - `strategy`: 策略选择（distance/time/bike/ebike）
- 响应：
  - `path`: 路径坐标数组
  - `total_distance`: 总距离（米）
  - `total_time`: 总时间（秒）
  - `strategy`: 使用的策略

**3.2 POST /api/route/tsp** - 多点 TSP 路线规划
- 请求参数：
  - `origin`: {lat, lng} - 起点
  - `waypoints`: [{lat, lng}, ...] - 途经点列表（最多 15 个）
  - `strategy`: 策略选择
  - `round_trip`: 是否返回起点
- 响应：
  - `ordered_waypoints`: 优化后的访问顺序（索引数组）
  - `path`: 完整路径坐标
  - `segments`: 每段路径详情
  - `total_distance`: 总距离
  - `total_time`: 总时间

**策略说明：**
- `distance` - 最短距离
- `time` - 最短时间（步行，5km/h）
- `bike` - 骑行优化（15km/h）
- `ebike` - 电动车优化（25km/h）

**算法：** Dijkstra 最短路径 + Bitmask DP 求解 TSP

### 4. routers/diary.py - 旅游日记

**API 前缀：** `/api/diary`

**功能：** 旅游日记的发布、查询、搜索、评分

**接口：**

**4.1 POST /api/diary** - 发布日记
- 请求：`{title, author, destination, content, rating}`
- 响应：日记摘要（不含正文）
- 状态码：201

**4.2 GET /api/diary/recommend?n=10** - Top-N 推荐
- 参数：n（1-50，默认 10）
- 响应：日记摘要列表（按热度+评分排序）

**4.3 POST /api/diary/search** - 全文搜索
- 请求：`{mode: "title"|"destination"|"content", q: "关键词"}`
- 响应：匹配的日记列表
- 搜索引擎：Whoosh（倒排索引 + BM25）

**4.4 GET /api/diary/{diary_id}** - 获取详情
- 响应：完整日记内容（自动热度+1）

**4.5 POST /api/diary/{diary_id}/rate?score=4.5** - 评分
- 参数：score（0-5）
- 响应：`{id, rating}` - 返回新的平均分

**4.6 POST /api/diary/{diary_id}/view** - 手动增加热度
- 响应：`{id, heat}` - 返回当前热度值

**4.7 DELETE /api/diary/{diary_id}** - 删除日记

**技术特性：**
- 正文使用 zlib 压缩存储（节省空间）
- Whoosh 全文索引（支持中文分词）
- Redis 缓存热度和评分
- MySQL B+树索引（title 字段）

### 5. routers/food.py - 美食推荐

**API 前缀：** `/api/food`

**功能：** 美食搜索和推荐

**接口：**

**5.1 POST /api/food/recommend** - 附近美食 Top-N 推荐
- 请求：`{origin_lat, origin_lng, cuisine: "川菜"|"粤菜"|null, n: 10}`
- 响应：美食列表（按评分+距离排序）
- cuisine 为 null 时返回所有菜系

**5.2 POST /api/food/search** - 模糊搜索
- 请求：`{q: "关键词", origin_lat, origin_lng, max_edit_distance: 2, n: 10}`
- 响应：匹配的美食列表
- 算法：Trie 前缀树 + Levenshtein 编辑距离

**技术特性：**
- Trie 树快速前缀匹配
- 编辑距离容错搜索
- 路网距离计算（非直线距离）
- Min-Heap Top-N 排序

### 6. routers/nearby.py - 周边设施查询

**API 前缀：** `/api/nearby`

**功能：** 查询指定位置周边的设施（餐饮、景点、酒店等）

**接口：**

**6.1 POST /api/nearby** - 周边设施查询
- 请求：`{origin_lat, origin_lng, category: "餐饮"|"景点"|"酒店", max_dist: 1000, limit: 20}`
- 响应：设施列表（按距离排序）
- max_dist 单位：米
- limit：返回数量上限

**算法：** 有界 Dijkstra（等时圈算法）
- 从起点开始扩展，直到距离超过 max_dist
- 比暴力计算所有 POI 距离更高效

---

## services/ - 业务逻辑层

业务逻辑层封装核心算法和数据处理逻辑，被路由层调用。

### 7. services/graph_service.py - 路网图加载

**功能：** 单例模式加载和管理路网图

**核心方法：**
- `init_graph()` - 启动时调用，加载 GraphML 文件
- `get_graph()` - 获取全局图实例（NetworkX DiGraph）

**预处理逻辑：**
1. 加载 GraphML 文件（节点 ID 为字符串）
2. 转换属性类型（length, congestion, max_speed → float）
3. 预计算权重：
   - `time` = length / (步行速度 × 拥堵系数)
   - `bike` = length / (骑行速度 × 拥堵系数)
   - `ebike` = length / (电动车速度 × 拥堵系数)

**速度常量：**
- 步行：5 km/h
- 骑行：15 km/h
- 电动车：25 km/h

### 8. services/snap_service.py - 坐标吸附服务

**功能：** 将任意经纬度坐标吸附到最近的路网节点

**核心方法：**
- `init_snap_service()` - 启动时调用，初始化 KD-Tree
- `get_snap_service()` - 获取单例实例
- `snap_point(lat, lng)` - 返回 (node_id, node_lat, node_lng, distance)

**算法：** KD-Tree 空间索引
- 时间复杂度：O(log N)
- 比暴力遍历所有节点快得多

**使用场景：** 用户点击地图或输入坐标时，需要映射到可导航的路网节点

### 9. services/route_service.py - 路径规划算法

**功能：** 实现最短路径和 TSP 路线规划

**核心方法：**
- `dijkstra_shortest_path(origin, dest, strategy)` - 两点最短路径
- `solve_tsp(origin, waypoints, strategy, round_trip)` - TSP 多点规划

**算法实现：**

**9.1 Dijkstra 最短路径**
- 使用 heapq 优先队列
- 根据 strategy 选择权重（distance/time/bike/ebike）
- 返回路径坐标、总距离、总时间

**9.2 TSP（旅行商问题）**
- Bitmask DP 动态规划
- 状态：dp[mask][i] = 访问集合 mask，当前在节点 i 的最短距离
- 时间复杂度：O(2^n × n^2)
- 限制：最多 15 个途经点（2^15 = 32768 状态）

**策略常量：**
```python
STRATEGY_WEIGHT = {
    "distance": "length",
    "time": "time",
    "bike": "bike",
    "ebike": "ebike",
}
```

### 10. services/redis_service.py - Redis 缓存服务

**功能：** 管理热度和评分数据

**核心方法：**
- `incr_heat(namespace, item_id)` - 热度+1
- `get_heat(namespace, item_id)` - 获取热度值
- `get_all_heats(namespace)` - 获取所有热度数据
- `add_rating(namespace, item_id, score)` - 添加评分（累加总分+计数）
- `get_avg_rating(namespace, item_id)` - 获取平均评分

**数据结构：**
- 热度：`{namespace}:heat:{item_id}` → 整数
- 评分：`{namespace}:rating:{item_id}` → Hash {total: 总分, count: 评分次数}

**命名空间：**
- `diary` - 日记
- `food` - 美食

**评分计算：** 平均分 = 总分 / 评分次数

### 11. services/heap_service.py - 堆排序工具

**功能：** 高效的 Top-N 排序

**核心方法：**
- `top_n(items, key_func, n, reverse=False)` - 返回前 N 个元素

**算法：** Min-Heap
- 时间复杂度：O(N log K)，其中 K = n
- 空间复杂度：O(K)
- 比完整排序 O(N log N) 更高效

**使用场景：**
- 日记推荐（按热度+评分排序）
- 美食推荐（按评分+距离排序）

### 12. services/diary_service.py - 日记管理服务

**功能：** 日记的 CRUD、搜索、推荐

**核心方法：**
- `create_diary(title, author, destination, content, rating)` - 创建日记
- `get_diary(diary_id)` - 获取详情（热度+1）
- `delete_diary(diary_id)` - 删除日记
- `search_diaries(mode, query)` - 搜索日记
- `recommend_diaries(n)` - Top-N 推荐

**技术实现：**

**12.1 压缩存储**
- 使用 zlib 压缩正文（LZ77 + Huffman 编码）
- 压缩率通常 50-70%
- 存储字段：`content_compressed` (BLOB)

**12.2 全文检索**
- Whoosh 搜索引擎（纯 Python 实现）
- 索引目录：`data/whoosh_diary/`
- Schema：id, title, destination, content
- 支持中文分词和 BM25 排序

**12.3 搜索模式**
- `title` - 标题精确匹配（MySQL B+树索引）
- `destination` - 目的地精确匹配（MySQL B+树索引）
- `content` - 正文全文搜索（Whoosh 倒排索引）

**12.4 推荐算法**
- 综合评分 = 热度 × 0.3 + 平均评分 × 0.7
- 使用 Min-Heap 选出 Top-N

### 13. services/food_service.py - 美食搜索推荐服务

**功能：** 美食的搜索和推荐

**核心方法：**
- `recommend_food(origin_lat, origin_lng, cuisine, n)` - 附近美食推荐
- `search_food(query, origin_lat, origin_lng, max_edit_distance, n)` - 模糊搜索

**技术实现：**

**13.1 Trie 前缀树**
- 用于快速前缀匹配
- 支持中文字符
- 时间复杂度：O(L)，L 为查询长度

**13.2 Levenshtein 编辑距离**
- 容错搜索（拼写错误、同音字）
- 动态规划算法
- 可配置最大编辑距离（默认 2）

**13.3 路网距离计算**
- 使用 Dijkstra 计算实际路网距离
- 非直线距离，更符合实际出行

**13.4 推荐排序**
- 综合评分 = 评分 × 0.6 - 距离归一化 × 0.4
- 使用 Min-Heap 选出 Top-N

### 14. services/nearby_service.py - 周边设施查询服务

**功能：** 查询指定位置周边的设施

**核心方法：**
- `find_nearby(origin_lat, origin_lng, category, max_dist, limit)` - 周边查询

**算法：** 有界 Dijkstra（等时圈算法）

**实现原理：**
1. 从起点开始扩展
2. 记录每个节点的最短距离
3. 当距离超过 max_dist 时停止扩展
4. 查询该范围内的 POI
5. 按距离排序返回

**优势：**
- 比暴力计算所有 POI 距离更高效
- 只计算可达范围内的节点
- 适合大规模路网

**时间复杂度：** O(E log V)，E 为边数，V 为节点数（实际只遍历可达范围）

---

## schemas/ - 数据模型层（Pydantic）

数据模型层定义 API 的请求和响应格式，提供自动验证和文档生成。

### 15. schemas/route.py - 路线相关模型

**定义的模型：**

**15.1 基础模型**
- `LatLng` - 经纬度坐标 {lat: float, lng: float}

**15.2 坐标吸附**
- `SnapRequest` - 吸附请求 {lat, lng}
- `SnapResponse` - 吸附响应 {node_id, lat, lng, distance}

**15.3 最短路径**
- `ShortestPathRequest` - {origin: LatLng, destination: LatLng, strategy: str}
- `ShortestPathResponse` - {path: List[LatLng], total_distance, total_time, strategy}

**15.4 TSP 路线**
- `TSPRequest` - {origin, waypoints: List[LatLng], strategy, round_trip: bool}
- `TSPResponse` - {ordered_waypoints: List[int], path, segments, total_distance, total_time}
- `TSPSegment` - {from_index, to_index, path, distance, time}

### 16. schemas/diary.py - 日记相关模型

**定义的模型：**
- `DiaryCreate` - 创建请求 {title, author, destination, content, rating}
- `DiaryBrief` - 摘要响应 {id, title, author, destination, rating, heat, created_at}
- `DiaryResponse` - 完整响应 {id, title, author, destination, content, rating, heat, created_at}
- `DiarySearchRequest` - 搜索请求 {mode: "title"|"destination"|"content", q: str}

### 17. schemas/food.py - 美食相关模型

**定义的模型：**
- `FoodItem` - 美食信息 {id, name, cuisine, rating, distance, lat, lng}
- `FoodRecommendRequest` - 推荐请求 {origin_lat, origin_lng, cuisine: Optional[str], n: int}
- `FoodSearchRequest` - 搜索请求 {q, origin_lat, origin_lng, max_edit_distance, n}

### 18. schemas/nearby.py - 周边查询模型

**定义的模型：**
- `NearbyRequest` - 查询请求 {origin_lat, origin_lng, category, max_dist, limit}
- `NearbyItem` - 设施信息 {id, name, category, distance, lat, lng}

---

## 数据流程说明

### 典型请求流程（以最短路径为例）

1. **用户请求** → `POST /api/route/shortest`
2. **路由层** (`routers/route.py`) 
   - 接收请求，Pydantic 自动验证参数
   - 调用 `_snap()` 吸附起点和终点坐标
3. **吸附服务** (`services/snap_service.py`)
   - 使用 KD-Tree 查找最近节点
   - 返回节点 ID 和坐标
4. **路径规划** (`services/route_service.py`)
   - 从图服务获取路网图
   - 执行 Dijkstra 算法
   - 返回路径坐标和统计信息
5. **响应** → 返回 JSON 格式的路径数据

### 日记推荐流程

1. **用户请求** → `GET /api/diary/recommend?n=10`
2. **路由层** → 调用 `diary_service.recommend_diaries()`
3. **日记服务** 
   - 从 MySQL 读取所有日记 ID
   - 从 Redis 批量获取热度和评分
   - 计算综合评分
   - 使用 Min-Heap 选出 Top-N
4. **响应** → 返回日记摘要列表（不含正文）

---

## 技术亮点总结

### 1. 图算法优化
- **预计算权重**：启动时一次性计算所有边的权重，避免运行时重复计算
- **多策略支持**：distance/time/bike/ebike 四种策略，满足不同出行需求
- **Bitmask DP**：高效求解 TSP 问题，支持最多 15 个途经点

### 2. 空间索引
- **KD-Tree**：O(log N) 时间复杂度的坐标吸附
- **有界 Dijkstra**：只计算可达范围内的节点，避免全图遍历

### 3. 数据压缩与检索
- **zlib 压缩**：日记正文压缩存储，节省 50-70% 空间
- **Whoosh 全文索引**：支持中文分词和 BM25 排序
- **Trie 树**：快速前缀匹配，支持模糊搜索

### 4. 缓存策略
- **Redis 热数据**：热度和评分数据缓存，减少数据库压力
- **单例模式**：路网图和吸附服务启动时加载，全局共享

### 5. 高效排序
- **Min-Heap Top-N**：O(N log K) 复杂度，比完整排序更快
- **综合评分**：多维度加权计算，平衡热度、评分、距离等因素

---

## 模块依赖关系

```
app.py
  ├─> routers/
  │     ├─> snap.py → services/snap_service.py
  │     ├─> route.py → services/snap_service.py, graph_service.py, route_service.py
  │     ├─> diary.py → services/diary_service.py, redis_service.py
  │     ├─> food.py → services/food_service.py
  │     └─> nearby.py → services/nearby_service.py
  │
  └─> services/
        ├─> graph_service.py → scripts/export_graphml.py
        ├─> snap_service.py → scripts/snap_to_network.py
        ├─> route_service.py → graph_service.py
        ├─> diary_service.py → redis_service.py, heap_service.py, database/
        ├─> food_service.py → graph_service.py, heap_service.py, database/
        ├─> nearby_service.py → graph_service.py, snap_service.py, database/
        ├─> redis_service.py → Redis
        └─> heap_service.py (独立工具)
```

**依赖层次：**
1. **基础层**：database/, scripts/, heap_service.py
2. **服务层**：graph_service.py, snap_service.py, redis_service.py
3. **业务层**：route_service.py, diary_service.py, food_service.py, nearby_service.py
4. **接口层**：routers/
5. **应用层**：app.py

---

## 性能指标

### 时间复杂度
- **坐标吸附**：O(log N) - KD-Tree 查询
- **最短路径**：O(E log V) - Dijkstra 算法
- **TSP 规划**：O(2^n × n^2) - Bitmask DP（n ≤ 15）
- **Top-N 推荐**：O(N log K) - Min-Heap
- **全文搜索**：O(log M + R) - Whoosh 倒排索引，M 为词项数，R 为结果数
- **模糊搜索**：O(L × D) - Trie + 编辑距离，L 为查询长度，D 为候选数

### 空间复杂度
- **路网图**：O(V + E) - 节点和边数据
- **KD-Tree**：O(V) - 节点坐标索引
- **Whoosh 索引**：O(M) - 词项数
- **Redis 缓存**：O(N) - 日记/美食数量

### 响应时间（估算）
- 坐标吸附：< 10ms
- 最短路径：< 100ms
- TSP (10 点)：< 500ms
- 日记推荐：< 50ms
- 全文搜索：< 100ms

---

## 扩展建议

### 1. 性能优化
- **缓存路径结果**：对热门起终点的路径结果进行缓存
- **异步处理**：使用 asyncio 处理 I/O 密集型操作
- **连接池**：MySQL 和 Redis 连接池优化
- **CDN 加速**：静态资源和 API 响应缓存

### 2. 功能扩展
- **实时路况**：接入实时交通数据，动态调整拥堵系数
- **多模式路径**：支持公交、地铁等公共交通
- **路径偏好**：用户可设置避开高速、优先风景路线等
- **社交功能**：日记点赞、评论、关注等

### 3. 数据增强
- **POI 丰富**：增加更多类别的兴趣点
- **室内导航**：支持大型建筑物内部导航
- **3D 可视化**：地形高度数据和 3D 路径展示

### 4. 监控与运维
- **日志系统**：结构化日志和分布式追踪
- **性能监控**：API 响应时间、错误率监控
- **告警机制**：异常情况自动告警
- **负载均衡**：多实例部署和负载均衡

---

## 总结

InteliTour 后端采用分层架构设计，职责清晰：

- **routers/** - 处理 HTTP 请求，参数验证
- **services/** - 封装业务逻辑和算法
- **schemas/** - 定义数据模型，自动验证

核心技术特点：

1. **高效图算法**：Dijkstra、Bitmask DP、有界 Dijkstra
2. **空间索引**：KD-Tree 快速坐标吸附
3. **全文检索**：Whoosh + zlib 压缩
4. **智能推荐**：多维度评分 + Min-Heap 排序
5. **缓存优化**：Redis 热数据缓存

项目结构清晰，易于维护和扩展。各模块低耦合高内聚，符合软件工程最佳实践。

---

**文档生成时间：** 2026-05-09  
**项目版本：** 0.1.0  
**维护者：** InteliTour Team

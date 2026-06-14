# InteliTour Scripts 目录结构文档

## 项目概述

scripts 目录包含数据采集和预处理脚本，负责从 OpenStreetMap 爬取数据、处理数据并导出为可用格式。

**技术栈：**
- OSMnx - OpenStreetMap 数据爬取和处理
- NetworkX - 图数据结构和算法
- SciPy - KD-Tree 空间索引
- GeoPandas - 地理空间数据处理

**数据范围：**
- 中心点：天安门 (39.9042°N, 116.3974°E)
- 半径：5000 米（5 公里）
- 覆盖区域：北京核心景区

**执行顺序：**
```bash
# 1. 爬取路网数据
python3 -m scripts.crawl_road_network

# 2. 爬取 POI 数据
python3 -m scripts.crawl_pois

# 3. 吸附 POI 到路网
python3 -m scripts.snap_to_network

# 4. 导出 GraphML（可选，后端启动时自动加载）
python3 -m scripts.export_graphml
```

---

## 目录结构总览

```
scripts/
├── __init__.py                  # 包初始化文件
├── crawl_road_network.py       # 爬取路网数据
├── crawl_pois.py                # 爬取 POI 数据
├── snap_to_network.py           # 坐标吸附到路网
├── export_graphml.py            # 导出 GraphML 格式
└── cache/                       # 缓存目录（OSMnx 自动创建）
```

---

## 核心脚本详解

### 1. crawl_road_network.py - 爬取路网数据

**文件路径：** `scripts/crawl_road_network.py`

**主要功能：** 从 OpenStreetMap 爬取步行路网数据并存入数据库

**核心参数：**
- 中心点：天安门 (39.9042, 116.3974)
- 半径：5000 米
- 网络类型：walk（步行路网）
- 简化：True（合并直线段）

**核心函数：**

**1.1 crawl_walk_network()**
- 使用 OSMnx 爬取步行路网
- 调用 `ox.graph_from_point()` 获取指定范围的路网
- 返回 NetworkX DiGraph 对象

**1.2 detect_node_type(G, node_id)**
- 判断节点类型
- 度数 >= 3：交叉口
- 度数 < 3：普通节点

**1.3 save_to_mysql(G)**
- 将路网数据写入 MySQL
- 清空 road_nodes 和 road_edges 表
- 批量插入节点和边数据
- 计算边长度（Haversine 距离）

**1.4 main()**
- 主流程：
  1. 爬取路网
  2. 保存到 MySQL
  3. 导出 GraphML 文件到 data/beijing_walk.graphml

**输出数据：**
- road_nodes 表：节点 ID、经纬度、节点类型
- road_edges 表：边 ID、起止节点、长度、道路属性
- data/beijing_walk.graphml：GraphML 格式文件

### 2. crawl_pois.py - 爬取 POI 数据

**文件路径：** `scripts/crawl_pois.py`

**主要功能：** 从 OpenStreetMap 爬取兴趣点和建筑物数据

**爬取范围：** 天安门周边 5km

**爬取类别：**

**2.1 景点（tourism=*）**
- attraction - 景点
- museum - 博物馆
- viewpoint - 观景台
- gallery - 画廊
- artwork - 艺术品
- theme_park - 主题公园
- zoo - 动物园
- aquarium - 水族馆

**2.2 餐饮（amenity=*）**
- restaurant - 餐厅
- cafe - 咖啡厅
- fast_food - 快餐

**2.3 便利服务**
- toilets - 公共卫生间
- convenience - 便利店
- supermarket - 超市

**2.4 建筑物（building=*）**
- 所有建筑物类型

**核心函数：**

**2.5 crawl_pois()**
- 使用 OSMnx 爬取各类 POI
- 调用 `ox.features_from_point()` 获取指定标签的要素
- 提取坐标、名称、类别等信息

**2.6 crawl_buildings()**
- 爬取建筑物数据
- 提取建筑轮廓（WKT Polygon）
- 计算质心坐标

**2.7 main()**
- 主流程：
  1. 爬取 POI 数据
  2. 爬取建筑物数据
  3. 批量写入数据库

**输出数据：**
- pois 表：POI ID、名称、类别、坐标、OSM tags
- buildings 表：建筑 ID、名称、类型、坐标、轮廓

### 3. snap_to_network.py - 坐标吸附到路网

**文件路径：** `scripts/snap_to_network.py`

**主要功能：** 将 POI 和建筑物吸附到最近的路网节点

**核心类：SnapService**

**3.1 类功能**
- 提供坐标吸附服务
- 使用 KD-Tree 空间索引实现快速查找
- 可作为独立服务供后端 API 调用

**3.2 初始化**
- 从数据库加载所有路网节点
- 构建 KD-Tree 空间索引
- 时间复杂度：O(N log N)

**3.3 snap_point(lat, lng)**
- 查找最近的路网节点
- 返回：(node_id, node_lat, node_lng, distance)
- 时间复杂度：O(log N)

**3.4 haversine(lat1, lng1, lat2, lng2)**
- 计算两点间的 Haversine 距离（球面距离）
- 考虑地球曲率，比欧氏距离更准确
- 返回距离单位：米

**脚本功能：**

**3.5 snap_pois()**
- 遍历 pois 表中的所有记录
- 为每个 POI 找到最近的路网节点
- 更新 snapped_node_id 和 snap_distance 字段

**3.6 snap_buildings()**
- 遍历 buildings 表中的所有记录
- 为每个建筑找到最近的路网节点
- 更新 snapped_node_id 字段

**3.7 main()**
- 主流程：
  1. 创建 SnapService 实例
  2. 吸附 POI
  3. 吸附建筑物

**用途：**
- 将 POI 关联到路网，支持路径规划
- 计算从路网节点到 POI 的实际距离
- 后端 API 复用 SnapService 类

### 4. export_graphml.py - 导出 GraphML 格式

**文件路径：** `scripts/export_graphml.py`

**主要功能：** 从数据库重建路网图并导出为 GraphML 格式

**核心函数：**

**4.1 build_graph_from_db()**
- 从 MySQL 读取路网数据
- 重建 NetworkX DiGraph 对象
- 添加节点属性：lat, lng, node_type
- 添加边属性：length, congestion, highway_type, max_speed

**4.2 export_graphml(G=None)**
- 导出 GraphML 文件到 data/beijing_walk.graphml
- 如果未提供图对象，则从数据库重建
- 创建 data/ 目录（如果不存在）

**4.3 load_graph()**
- 加载 GraphML 文件为 NetworkX 图
- 供后端路由规划模块直接调用
- 返回 NetworkX DiGraph 对象

**文件路径：**
- 输出：`data/beijing_walk.graphml`
- 格式：GraphML（XML 格式的图数据）

**用途：**
- 后端启动时加载路网图（避免每次从数据库读取）
- 支持 NetworkX 图算法（Dijkstra、TSP 等）
- 便于图数据的持久化和共享

**与后端集成：**
- `backend/services/graph_service.py` 调用 `load_graph()`
- 启动时一次性加载，全局共享

---

## 数据处理流程

```
1. crawl_road_network.py
   ↓
   爬取 OSM 路网数据
   ↓
   存入 road_nodes 和 road_edges 表
   ↓
   导出 data/beijing_walk.graphml

2. crawl_pois.py
   ↓
   爬取 OSM POI 和建筑物数据
   ↓
   存入 pois 和 buildings 表

3. snap_to_network.py
   ↓
   构建 KD-Tree 空间索引
   ↓
   为每个 POI/建筑找到最近路网节点
   ↓
   更新 snapped_node_id 字段

4. export_graphml.py（可选）
   ↓
   从数据库重建图
   ↓
   导出 GraphML 文件
```

**数据依赖关系：**
- crawl_pois 依赖 crawl_road_network（需要路网节点存在）
- snap_to_network 依赖前两者（需要路网和 POI 数据）
- export_graphml 依赖 crawl_road_network（需要路网数据）

---

## 技术特点总结

### 1. 数据来源
- **OpenStreetMap**：开放的地理数据平台
- **OSMnx**：简化 OSM 数据爬取和处理
- **数据质量**：OSM 数据由社区维护，覆盖全面

### 2. 空间索引
- **KD-Tree**：高效的空间查询数据结构
- **时间复杂度**：O(log N) 查询，O(N log N) 构建
- **应用场景**：坐标吸附、最近邻查询

### 3. 图数据处理
- **NetworkX**：强大的图算法库
- **DiGraph**：有向图，支持单行道
- **GraphML**：标准的图数据交换格式

### 4. 距离计算
- **Haversine 公式**：球面距离计算
- **考虑地球曲率**：比欧氏距离更准确
- **单位**：米

---

## 使用建议

### 1. 首次运行

```bash
# 确保数据库已初始化
python3 -m database.init_db

# 按顺序执行脚本
python3 -m scripts.crawl_road_network  # 约 2-5 分钟
python3 -m scripts.crawl_pois           # 约 1-3 分钟
python3 -m scripts.snap_to_network      # 约 1 分钟
```

### 2. 数据更新

如果需要更新数据（OSM 数据变化）：
```bash
# 重新爬取路网（会清空现有数据）
python3 -m scripts.crawl_road_network

# 重新爬取 POI
python3 -m scripts.crawl_pois

# 重新吸附
python3 -m scripts.snap_to_network
```

### 3. 注意事项

- **网络连接**：需要访问 OpenStreetMap 服务器
- **执行时间**：首次爬取较慢，OSMnx 会缓存数据到 cache/ 目录
- **数据覆盖**：crawl_road_network 会清空现有路网数据
- **依赖顺序**：必须按顺序执行脚本

### 4. 故障排查

**问题：OSMnx 下载超时**
- 解决：检查网络连接，或使用代理
- OSMnx 会自动重试

**问题：数据库连接失败**
- 解决：检查 MySQL 服务是否启动
- 检查 database/config.py 中的连接配置

**问题：KD-Tree 构建失败**
- 解决：确保 road_nodes 表有数据
- 先运行 crawl_road_network.py

---

## 总结

InteliTour scripts 目录包含数据采集和预处理脚本，职责清晰：

**脚本功能：**
1. **crawl_road_network.py** - 爬取路网数据（节点和边）
2. **crawl_pois.py** - 爬取 POI 和建筑物数据
3. **snap_to_network.py** - 将 POI 吸附到路网节点
4. **export_graphml.py** - 导出 GraphML 格式供后端使用

**数据流程：**
路网爬取 → POI 爬取 → 坐标吸附 → GraphML 导出

**技术亮点：**
1. **OSMnx 集成**：简化 OpenStreetMap 数据爬取
2. **KD-Tree 空间索引**：高效的最近邻查询
3. **NetworkX 图处理**：支持复杂图算法
4. **Haversine 距离**：准确的球面距离计算
5. **模块化设计**：SnapService 可复用

**数据范围：**
- 中心：天安门 (39.9042°N, 116.3974°E)
- 半径：5 公里
- 覆盖：北京核心景区

项目结构清晰，脚本独立可执行，易于维护和扩展。数据处理流程完整，符合地理信息系统开发最佳实践。

---

**文档生成时间：** 2026-05-09  
**项目版本：** 0.1.0  
**维护者：** InteliTour Team

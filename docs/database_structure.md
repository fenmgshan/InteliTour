# InteliTour Database 目录结构文档

## 项目概述

database 目录负责数据库的 ORM 模型定义、连接配置和初始化脚本。使用 SQLAlchemy 作为 ORM 框架，MySQL 作为数据库。

**技术栈：**
- SQLAlchemy - Python ORM 框架
- PyMySQL - MySQL 数据库驱动
- MySQL 8.0+ - 关系型数据库

**数据库信息：**
- 数据库名：intelitour
- 字符集：utf8mb4
- 排序规则：utf8mb4_unicode_ci
- 用户：intelitour_user

**初始化方式：**
```bash
cd InteliTour
python3 -m database.init_db
```

---

## 目录结构总览

```
database/
├── __init__.py          # 包初始化文件
├── config.py            # 数据库连接配置
├── models.py            # SQLAlchemy ORM 模型定义
└── init_db.py           # 数据库初始化脚本
```

---

## 核心文件详解

### 1. config.py - 数据库连接配置

**文件路径：** `database/config.py`

**主要功能：** 管理数据库连接字符串和会话创建

**配置常量：**

**1.1 DATABASE_URL**
- 完整的数据库连接字符串
- 格式：`mysql+pymysql://用户:密码@主机:端口/数据库?charset=utf8mb4`
- 值：`mysql+pymysql://intelitour_user:mypassword@localhost:3306/intelitour?charset=utf8mb4`

**1.2 SERVER_URL**
- 不指定数据库的连接字符串
- 用于创建数据库（需要在数据库不存在时连接到 MySQL 服务器）
- 值：`mysql+pymysql://intelitour_user:mypassword@localhost:3306/?charset=utf8mb4`

**核心函数：**

**1.3 get_engine()**
- 获取数据库引擎（单例模式）
- 配置：
  - `echo=False` - 不打印 SQL 语句
  - `pool_recycle=3600` - 连接池回收时间 1 小时（防止 MySQL 超时）
- 返回：SQLAlchemy Engine 实例

**1.4 get_session()**
- 获取数据库会话（Session）
- 每次调用创建新的会话实例
- 用于执行数据库操作（查询、插入、更新、删除）
- 返回：SQLAlchemy Session 实例

### 2. init_db.py - 数据库初始化脚本

**文件路径：** `database/init_db.py`

**主要功能：** 创建数据库和所有表

**核心函数：**

**2.1 create_database()**
- 创建 intelitour 数据库（如果不存在）
- 使用 SERVER_URL 连接到 MySQL 服务器
- 设置字符集：utf8mb4
- 设置排序规则：utf8mb4_unicode_ci
- 隔离级别：AUTOCOMMIT

**2.2 create_tables()**
- 根据 models.py 中定义的 ORM 模型创建所有表
- 使用 `Base.metadata.create_all(engine)` 自动创建
- 如果表已存在则跳过

**2.3 main()**
- 主函数，按顺序执行：
  1. 创建数据库
  2. 创建所有表
  3. 打印完成信息

**使用方式：**
```bash
python3 -m database.init_db
```

**注意事项：**
- 首次运行前需要确保 MySQL 服务已启动
- 需要确保 intelitour_user 用户已创建并有相应权限
- 脚本是幂等的，可以重复运行

### 3. models.py - SQLAlchemy ORM 模型定义

**文件路径：** `database/models.py`

**主要功能：** 定义数据库表结构和关系

**ORM 基类：**
- `Base = declarative_base()` - 所有模型的基类

**包含的表模型：**
1. RoadNode - 路网节点
2. RoadEdge - 路网边
3. POI - 兴趣点
4. Building - 建筑物
5. IndoorMap - 室内地图
6. Diary - 旅游日记

---

#### 3.1 RoadNode - 路网节点

**表名：** `road_nodes`

**用途：** 存储路网的节点（交叉口、路径点）

**字段定义：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BigInteger | 主键 | OSM node ID |
| lat | Float(32) | NOT NULL | 纬度 |
| lng | Float(32) | NOT NULL | 经度 |
| node_type | String(20) | 默认"普通" | 节点类型（交叉口/普通） |

**索引：**
- `idx_road_nodes_latlng` - (lat, lng) 复合索引，用于空间查询

**数据来源：** OpenStreetMap (OSM)

#### 3.2 RoadEdge - 路网边

**表名：** `road_edges`

**用途：** 存储路网的边（道路段），连接两个节点

**字段定义：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键，自增 | 边 ID |
| source_node_id | BigInteger | 外键，NOT NULL | 起始节点 OSM ID |
| target_node_id | BigInteger | 外键，NOT NULL | 终止节点 OSM ID |
| length | Float | NOT NULL | 边长度（米） |
| name | String(255) | 默认"" | 道路名称 |
| highway_type | String(50) | 默认"" | 道路类型（primary/secondary/residential等） |
| max_speed | Float | 默认0 | 最高限速（km/h） |
| congestion | Float | 默认1.0 | 拥挤度系数（1.0=正常） |
| oneway | Boolean | 默认False | 是否单行道 |
| geometry | Text | 默认"" | WKT LineString 几何（路径形状） |

**外键关系：**
- `source_node_id` → `road_nodes.id`
- `target_node_id` → `road_nodes.id`

**索引：**
- `idx_road_edges_source` - source_node_id 索引
- `idx_road_edges_target` - target_node_id 索引

**用途：**
- 路径规划算法的基础数据
- 计算路径长度和时间
- 支持不同出行策略（步行、骑行、电动车）

#### 3.3 POI - 兴趣点

**表名：** `pois`

**用途：** 存储兴趣点（景点、餐厅、超市、便利店等）

**字段定义：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键，自增 | POI ID |
| osm_id | BigInteger | 可空 | OSM ID |
| name | String(255) | 默认"" | 名称 |
| category | String(50) | 默认"" | 主类别（景点/餐厅/超市/卫生间/便利店等） |
| sub_category | String(50) | 默认"" | 子类别 |
| lat | Float(32) | NOT NULL | 纬度 |
| lng | Float(32) | NOT NULL | 经度 |
| snapped_node_id | BigInteger | 外键，可空 | 吸附到的最近路网节点 |
| snap_distance | Float | 默认0 | 吸附距离（米） |
| address | String(500) | 默认"" | 地址 |
| phone | String(50) | 默认"" | 电话 |
| opening_hours | String(255) | 默认"" | 营业时间 |
| rating | Float | 默认0 | 评分 |
| heat | Float | 默认0 | 热度 |
| has_indoor | Boolean | 默认False | 是否有室内地图 |
| tags_json | Text | 默认"{}" | 原始 OSM tags JSON |

**外键关系：**
- `snapped_node_id` → `road_nodes.id`

**索引：**
- `idx_pois_category` - category 索引（按类别查询）
- `idx_pois_latlng` - (lat, lng) 复合索引（空间查询）
- `idx_pois_snapped` - snapped_node_id 索引（路网关联查询）

**用途：**
- 周边设施查询
- 美食推荐
- 路线规划中的途经点

#### 3.4 Building - 建筑物

**表名：** `buildings`

**用途：** 存储建筑物信息

**字段定义：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键，自增 | 建筑 ID |
| osm_id | BigInteger | 可空 | OSM ID |
| name | String(255) | 默认"" | 建筑名称 |
| building_type | String(50) | 默认"" | 建筑类型 |
| lat | Float(32) | NOT NULL | 质心纬度 |
| lng | Float(32) | NOT NULL | 质心经度 |
| snapped_node_id | BigInteger | 外键，可空 | 吸附到的最近路网节点 |
| address | String(500) | 默认"" | 地址 |
| floors | Integer | 默认0 | 楼层数 |
| geometry_wkt | Text | 默认"" | WKT Polygon 几何（建筑轮廓） |

**外键关系：**
- `snapped_node_id` → `road_nodes.id`

**索引：**
- `idx_buildings_latlng` - (lat, lng) 复合索引
- `idx_buildings_snapped` - snapped_node_id 索引

**用途：**
- 建筑物定位
- 室内导航的基础数据
- 地图可视化

#### 3.5 IndoorMap - 室内地图

**表名：** `indoor_maps`

**用途：** 存储室内地图数据（预留功能）

**字段定义：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键，自增 | 室内地图 ID |
| building_id | Integer | 外键，NOT NULL | 所属建筑 ID |
| floor | Integer | NOT NULL | 楼层 |
| map_image_url | String(500) | 默认"" | 地图图片 URL |
| nodes_json | Text | 默认"[]" | 室内节点 JSON |
| edges_json | Text | 默认"[]" | 室内边 JSON |

**外键关系：**
- `building_id` → `buildings.id`

**索引：**
- `idx_indoor_maps_building` - building_id 索引

**用途：**
- 室内导航（预留功能）
- 大型建筑物内部路径规划

#### 3.6 Diary - 旅游日记

**表名：** `diaries`

**用途：** 存储用户发布的旅游日记

**字段定义：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | 主键，自增 | 日记 ID |
| title | String(255) | NOT NULL | 标题（B+树索引，精确查找） |
| author | String(100) | 默认"匿名" | 作者 |
| destination | String(255) | 默认"" | 目的地名称 |
| content_compressed | LargeBinary | NOT NULL | zlib 压缩后的正文 |
| rating | Float | 默认0.0 | 评分（0-5） |
| created_at | DateTime | 默认当前时间 | 发布时间 |

**索引：**
- `idx_diaries_title` - title 索引（标题精确查找）
- `idx_diaries_destination` - destination 索引（目的地查找）

**技术特性：**
- **压缩存储**：content_compressed 字段使用 zlib 压缩，节省 50-70% 空间
- **全文检索**：配合 Whoosh 索引实现全文搜索
- **B+树索引**：title 和 destination 字段支持快速精确查找

**用途：**
- 旅游日记发布和展示
- 日记搜索和推荐
- 用户评分和热度统计

---

## 表关系图

```
RoadNode (路网节点)
    ↑
    │ (外键关系)
    ├─── RoadEdge.source_node_id
    ├─── RoadEdge.target_node_id
    ├─── POI.snapped_node_id
    └─── Building.snapped_node_id

Building (建筑物)
    ↑
    │ (外键关系)
    └─── IndoorMap.building_id

独立表：
- Diary (旅游日记) - 无外键关系
```

**关系说明：**
1. **RoadNode 是核心表**：路网边、POI、建筑物都通过外键关联到路网节点
2. **RoadEdge 连接节点**：source_node_id 和 target_node_id 构成有向图
3. **POI 和 Building 吸附到路网**：通过 snapped_node_id 关联最近的路网节点
4. **IndoorMap 属于 Building**：一个建筑可以有多个楼层的室内地图
5. **Diary 独立存在**：不依赖其他表，热度和评分存储在 Redis

---

## 数据流程说明

### 路网数据流程

1. **数据采集** → 从 OpenStreetMap 爬取路网数据
2. **节点存储** → 存入 RoadNode 表
3. **边存储** → 存入 RoadEdge 表，关联起止节点
4. **图导出** → 导出为 GraphML 格式供后端使用

### POI 数据流程

1. **数据采集** → 从 OpenStreetMap 爬取 POI 数据
2. **坐标吸附** → 计算每个 POI 到最近路网节点的距离
3. **数据存储** → 存入 POI 表，记录吸附节点 ID
4. **分类索引** → 按 category 建立索引，支持快速查询

### 日记数据流程

1. **用户发布** → 前端提交日记内容
2. **内容压缩** → 后端使用 zlib 压缩正文
3. **数据存储** → 存入 Diary 表
4. **全文索引** → Whoosh 建立倒排索引
5. **热度统计** → Redis 记录浏览次数和评分

---

## 使用建议

### 1. 数据库初始化

```bash
# 首次使用前初始化数据库
cd InteliTour
python3 -m database.init_db
```

### 2. 会话管理

```python
from database.config import get_session

# 获取会话
session = get_session()

try:
    # 执行数据库操作
    result = session.query(RoadNode).filter_by(id=123).first()
    session.commit()
finally:
    # 关闭会话
    session.close()
```

### 3. 查询示例

**查询路网节点：**
```python
from database.models import RoadNode
from database.config import get_session

session = get_session()
nodes = session.query(RoadNode).filter(
    RoadNode.lat.between(39.9, 40.0),
    RoadNode.lng.between(116.3, 116.4)
).all()
session.close()
```

**查询 POI：**
```python
from database.models import POI

session = get_session()
restaurants = session.query(POI).filter_by(category="餐厅").limit(10).all()
session.close()
```

### 4. 性能优化建议

- **使用索引**：查询时尽量使用已建立索引的字段
- **批量操作**：使用 `bulk_insert_mappings` 批量插入数据
- **连接池**：config.py 已配置连接池，避免频繁创建连接
- **及时关闭会话**：使用 try-finally 确保会话关闭

---

## 技术特点总结

### 1. ORM 设计
- **SQLAlchemy**：成熟的 Python ORM 框架
- **声明式映射**：使用 declarative_base 定义模型
- **关系映射**：支持外键和 relationship 定义表关系

### 2. 索引优化
- **空间索引**：(lat, lng) 复合索引支持空间查询
- **分类索引**：category 索引支持快速分类查询
- **外键索引**：所有外键字段都建立索引

### 3. 数据压缩
- **zlib 压缩**：日记正文压缩存储，节省空间
- **LargeBinary 类型**：支持二进制数据存储

### 4. 字符集支持
- **utf8mb4**：支持完整的 Unicode 字符（包括 emoji）
- **utf8mb4_unicode_ci**：不区分大小写的排序规则

### 5. 数据完整性
- **外键约束**：确保数据引用完整性
- **NOT NULL 约束**：关键字段不允许为空
- **默认值**：合理的字段默认值

---

## 总结

InteliTour database 目录采用 SQLAlchemy ORM 框架，结构清晰，职责分明：

**文件结构：**
- **config.py** - 数据库连接配置和会话管理
- **models.py** - 6 个表模型定义（RoadNode, RoadEdge, POI, Building, IndoorMap, Diary）
- **init_db.py** - 数据库初始化脚本

**核心表：**
1. **路网表**（RoadNode, RoadEdge）- 支持路径规划
2. **POI 表** - 支持周边查询和美食推荐
3. **建筑表**（Building, IndoorMap）- 支持室内导航（预留）
4. **日记表**（Diary）- 支持旅游日记功能

**技术亮点：**
1. **完善的索引设计**：空间索引、分类索引、外键索引
2. **数据压缩**：zlib 压缩节省存储空间
3. **外键关系**：确保数据完整性
4. **utf8mb4 字符集**：完整的 Unicode 支持
5. **连接池管理**：提高数据库访问性能

项目结构清晰，易于维护和扩展。数据模型设计合理，符合数据库设计最佳实践。

---

**文档生成时间：** 2026-05-09  
**项目版本：** 0.1.0  
**维护者：** InteliTour Team

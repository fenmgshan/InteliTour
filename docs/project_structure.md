# InteliTour 项目目录结构文档

## 项目概述

InteliTour 是一个智慧旅游路线规划系统，覆盖北京核心景区（天安门周边 5km）。

**技术栈：**
- 后端：Python + FastAPI + MySQL + Redis
- 前端：Vue 3 + Vite + Element Plus + 高德地图
- 数据：OpenStreetMap + NetworkX + Whoosh

**核心功能：**
1. 地图导航（路线规划、周边探索）
2. 旅游日记（发布、搜索、推荐、评分）

---

## 完整目录结构

```
InteliTour/
├── backend/              # 后端服务（FastAPI）
│   ├── app.py           # 应用入口
│   ├── routers/         # API 路由
│   ├── services/        # 业务逻辑
│   └── schemas/         # 数据模型
├── frontend/            # 前端应用（Vue 3）
│   ├── src/            # 源代码
│   │   ├── api/        # API 接口
│   │   ├── router/     # 路由配置
│   │   ├── stores/     # 状态管理
│   │   └── views/      # 页面组件
│   ├── package.json    # 依赖配置
│   └── vite.config.js  # 构建配置
├── database/            # 数据库模块
│   ├── config.py       # 连接配置
│   ├── models.py       # ORM 模型
│   └── init_db.py      # 初始化脚本
├── scripts/             # 数据处理脚本
│   ├── crawl_road_network.py  # 爬取路网
│   ├── crawl_pois.py          # 爬取 POI
│   ├── snap_to_network.py     # 坐标吸附
│   └── export_graphml.py      # 导出图数据
├── data/                # 数据文件
│   ├── beijing_walk.graphml   # 路网图
│   └── whoosh_diary/          # 全文索引
├── docs/                # 项目文档
└── tests/               # 测试代码
```

---

## 目录说明

### backend/ - 后端服务

FastAPI 应用，提供 RESTful API。

**核心文件：**
- `app.py` - 应用入口，CORS 配置，路由注册

**子目录：**
- `routers/` - API 路由层
  - `snap.py` - 坐标吸附接口
  - `route.py` - 路线规划接口（最短路径、TSP）
  - `diary.py` - 日记接口（CRUD、搜索、推荐、评分）
  - `food.py` - 美食接口（推荐、搜索）
  - `nearby.py` - 周边设施查询接口

- `services/` - 业务逻辑层
  - `graph_service.py` - 路网图加载（单例）
  - `snap_service.py` - 坐标吸附服务（KD-Tree）
  - `route_service.py` - 路径规划算法（Dijkstra、TSP）
  - `diary_service.py` - 日记管理（压缩、全文索引）
  - `food_service.py` - 美食搜索（Trie、编辑距离）
  - `nearby_service.py` - 周边查询（有界 Dijkstra）
  - `redis_service.py` - Redis 缓存（热度、评分）
  - `heap_service.py` - 堆排序工具（Top-N）

- `schemas/` - 数据模型层（Pydantic）
  - `route.py` - 路线相关模型
  - `diary.py` - 日记相关模型
  - `food.py` - 美食相关模型
  - `nearby.py` - 周边查询模型

### frontend/ - 前端应用

Vue 3 单页应用，提供用户界面。

**核心文件：**
- `src/main.js` - 应用入口
- `src/App.vue` - 根组件（导航栏）
- `package.json` - 依赖配置
- `vite.config.js` - Vite 构建配置

**子目录：**
- `src/api/` - API 接口封装
  - `diary.js` - 日记 API

- `src/router/` - 路由配置
  - `index.js` - 路由定义（4 个路由）

- `src/stores/` - 状态管理（Pinia）
  - `mapStore.js` - 地图状态

- `src/views/` - 页面组件
  - `MapView.vue` - 地图导航页面
  - `diary/Index.vue` - 日记列表
  - `diary/Detail.vue` - 日记详情
  - `diary/Publish.vue` - 发布日记

### database/ - 数据库模块

SQLAlchemy ORM 模型和配置。

**核心文件：**
- `config.py` - 数据库连接配置（MySQL）
- `models.py` - ORM 模型定义（6 个表）
  - RoadNode - 路网节点
  - RoadEdge - 路网边
  - POI - 兴趣点
  - Building - 建筑物
  - IndoorMap - 室内地图（预留）
  - Diary - 旅游日记
- `init_db.py` - 数据库初始化脚本

### scripts/ - 数据处理脚本

数据采集和预处理脚本。

**核心文件：**
- `crawl_road_network.py` - 爬取 OSM 路网数据
- `crawl_pois.py` - 爬取 OSM POI 和建筑物数据
- `snap_to_network.py` - 将 POI 吸附到路网节点（KD-Tree）
- `export_graphml.py` - 导出 GraphML 格式

**执行顺序：** crawl_road_network → crawl_pois → snap_to_network

### data/ - 数据文件

存储生成的数据文件。

**核心文件：**
- `beijing_walk.graphml` - 路网图数据（NetworkX 格式）
- `whoosh_diary/` - 日记全文索引目录（Whoosh）

### docs/ - 项目文档

项目文档和开发指南。

**核心文件：**
- `backend_structure.md` - 后端目录结构文档
- `frontend_structure.md` - 前端目录结构文档
- `database_structure.md` - 数据库目录结构文档
- `scripts_structure.md` - 数据处理脚本文档
- `project_structure.md` - 项目整体结构文档（本文档）
- `commitGuide/` - 开发日志和提交指南

### tests/ - 测试代码

单元测试和集成测试（待完善）。

---

## 快速启动

### 1. 数据库初始化
```bash
python3 -m database.init_db
```

### 2. 数据采集（首次运行）
```bash
python3 -m scripts.crawl_road_network
python3 -m scripts.crawl_pois
python3 -m scripts.snap_to_network
```

### 3. 启动后端
```bash
cd InteliTour
python3 -m backend.app
# 访问 http://localhost:8000/docs
```

### 4. 启动前端
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

---

## 技术架构

**分层架构：**
```
前端（Vue 3）
    ↓ HTTP
后端（FastAPI）
    ↓ ORM
数据库（MySQL + Redis）
```

**数据流：**
```
OSM 数据 → scripts 处理 → MySQL 存储 → 后端 API → 前端展示
```

---

## 总结

InteliTour 采用前后端分离架构，结构清晰，职责分明：

- **backend/** - FastAPI 后端服务
- **frontend/** - Vue 3 前端应用
- **database/** - SQLAlchemy ORM 模型
- **scripts/** - 数据采集和预处理
- **data/** - 生成的数据文件
- **docs/** - 项目文档

项目覆盖北京核心景区，提供路线规划和旅游日记功能，技术栈现代化，易于维护和扩展。

---

**文档生成时间：** 2026-05-09  
**项目版本：** 0.1.0  
**维护者：** InteliTour Team

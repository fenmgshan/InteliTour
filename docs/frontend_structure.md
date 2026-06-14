# InteliTour Frontend 目录结构文档

## 项目概述

InteliTour 前端是一个基于 Vue 3 的单页应用（SPA），提供地图导航和旅游日记功能。

**技术栈：**
- Vue 3 - 渐进式 JavaScript 框架
- Vite - 现代化前端构建工具
- Vue Router - 官方路由管理器
- Pinia - 官方状态管理库
- Element Plus - Vue 3 UI 组件库
- 高德地图 JS API - 地图服务
- wangEditor - 富文本编辑器

**启动方式：**
```bash
cd frontend
npm install        # 安装依赖
npm run dev        # 开发模式（默认 http://localhost:5173）
npm run build      # 生产构建
```

**开发服务器：** http://localhost:5173

---

## 目录结构总览

```
frontend/
├── src/                      # 源代码目录
│   ├── api/                 # API 接口封装
│   │   └── diary.js        # 日记相关 API
│   ├── router/              # 路由配置
│   │   └── index.js        # 路由定义
│   ├── stores/              # 状态管理（Pinia）
│   │   └── mapStore.js     # 地图状态
│   ├── views/               # 页面组件
│   │   ├── diary/          # 日记模块页面
│   │   │   ├── Index.vue   # 日记列表
│   │   │   ├── Detail.vue  # 日记详情
│   │   │   └── Publish.vue # 发布日记
│   │   ├── MapView.vue     # 地图导航页面
│   │   └── DiaryView.vue   # 日记页面（已废弃）
│   ├── App.vue              # 根组件
│   └── main.js              # 应用入口
├── dist/                     # 构建输出目录
├── vite.config.js           # Vite 配置文件
├── package.json             # 项目配置和依赖
├── package-lock.json        # 依赖锁定文件
└── index.html               # HTML 模板

```

---

## 核心文件详解

### 1. package.json - 项目配置

**文件路径：** `frontend/package.json`

**主要内容：**

**1.1 项目信息**
- 项目名：intelitour-frontend
- 版本：0.1.0

**1.2 脚本命令**
- `npm run dev` - 启动 Vite 开发服务器（热重载）
- `npm run build` - 构建生产版本到 dist/ 目录

**1.3 核心依赖**
- `vue@^3.4.0` - Vue 3 框架
- `vue-router@^4.6.4` - 路由管理
- `pinia@^2.1.0` - 状态管理
- `element-plus@^2.13.7` - UI 组件库
- `@amap/amap-jsapi-loader@^1.0.1` - 高德地图加载器
- `@wangeditor/editor@^5.1.23` - 富文本编辑器核心
- `@wangeditor/editor-for-vue@^5.1.12` - Vue 3 适配器

**1.4 开发依赖**
- `vite@^5.0.0` - 构建工具
- `@vitejs/plugin-vue@^5.0.0` - Vue 3 插件

### 2. main.js - 应用入口

**文件路径：** `frontend/src/main.js`

**主要功能：** 创建 Vue 应用实例并挂载到 DOM

**初始化流程：**
1. 创建 Vue 应用实例
2. 注册 Pinia（状态管理）
3. 注册 Vue Router（路由）
4. 注册 Element Plus（UI 组件库）
5. 挂载到 `#app` 元素

**代码结构：**
```javascript
createApp(App)
  .use(createPinia())    // 状态管理
  .use(router)           // 路由
  .use(ElementPlus)      // UI 组件
  .mount('#app')         // 挂载
```

### 3. App.vue - 根组件

**文件路径：** `frontend/src/App.vue`

**主要功能：** 应用的根组件，包含导航栏和路由视图

**组件结构：**

**3.1 模板部分**
- 顶部导航栏（固定定位）
  - 品牌名称：InteliTour
  - 导航链接：地图导航（/）、旅游日记（/diary）
- 路由视图：`<router-view />` - 渲染当前路由对应的组件

**3.2 样式部分**
- 全局样式重置（box-sizing, margin, padding）
- 导航栏样式：
  - 固定在顶部，高度 44px
  - 蓝色背景（#1677ff）
  - 白色文字
  - 活动链接有下划线标识

---

## router/ - 路由配置

### 4. router/index.js - 路由定义

**文件路径：** `frontend/src/router/index.js`

**主要功能：** 配置应用的路由规则

**路由模式：** HTML5 History 模式（createWebHistory）

**路由配置：**

| 路径 | 组件 | 说明 | 加载方式 |
|------|------|------|----------|
| `/` | MapView.vue | 地图导航页面 | 静态导入 |
| `/diary` | diary/Index.vue | 日记列表页面 | 动态导入 |
| `/diary/publish` | diary/Publish.vue | 发布日记页面 | 动态导入 |
| `/diary/:id` | diary/Detail.vue | 日记详情页面 | 动态导入 |

**加载策略：**
- **静态导入**：MapView 作为首页，直接导入，首次加载即可用
- **动态导入**：日记相关页面使用 `import()` 懒加载，按需加载，减小初始包体积

**路由参数：**
- `:id` - 日记 ID（动态路由参数）

---

## stores/ - 状态管理（Pinia）

### 5. stores/mapStore.js - 地图状态管理

**文件路径：** `frontend/src/stores/mapStore.js`

**主要功能：** 管理地图相关的全局状态

**状态定义：**

**5.1 路线规划模式状态**
- `mode` - 当前模式（'route' 路线规划 | 'explore' 周边探索）
- `origin` - 起点坐标 {lat, lng}
- `waypoints` - 途经点数组 [{lat, lng}, ...]
- `routeResult` - 路线规划结果
- `strategy` - 路线策略（'distance' | 'time' | 'bike' | 'ebike'）
- `roundTrip` - 是否往返

**5.2 周边探索模式状态**
- `exploreOrigin` - 探索起点坐标
- `exploreResults` - 探索结果列表

**Actions（操作方法）：**

**5.3 路线规划操作**
- `setOrigin(p)` - 设置起点
- `addWaypoint(p)` - 添加途经点
- `setRouteResult(r)` - 设置路线结果
- `clear()` - 清空路线数据

**5.4 周边探索操作**
- `setExploreOrigin(p)` - 设置探索起点
- `setExploreResults(r)` - 设置探索结果
- `clearExplore()` - 清空探索数据

**使用场景：**
- 在地图组件中存储用户选择的点位
- 在不同组件间共享路线规划状态
- 保持地图交互状态的一致性

---

## api/ - API 接口封装

### 6. api/diary.js - 日记 API 接口

**文件路径：** `frontend/src/api/diary.js`

**主要功能：** 封装日记相关的后端 API 调用

**API 基础路径：** `/api/diary`

**接口方法：**

**6.1 create(data)** - 创建日记
- 方法：POST
- 路径：`/api/diary`
- 参数：`{title, author, destination, content, rating}`
- 返回：日记摘要

**6.2 list(n = 10)** - 获取推荐日记列表
- 方法：GET
- 路径：`/api/diary/recommend?n={n}`
- 参数：n - 返回数量（默认 10）
- 返回：日记摘要数组

**6.3 search(mode, q)** - 搜索日记
- 方法：POST
- 路径：`/api/diary/search`
- 参数：`{mode: "title"|"destination"|"content", q: "关键词"}`
- 返回：匹配的日记数组

**6.4 get(id)** - 获取日记详情
- 方法：GET
- 路径：`/api/diary/{id}`
- 参数：id - 日记 ID
- 返回：完整日记内容

**6.5 delete(id)** - 删除日记
- 方法：DELETE
- 路径：`/api/diary/{id}`
- 参数：id - 日记 ID
- 返回：删除确认

**6.6 rate(id, score)** - 评分
- 方法：POST
- 路径：`/api/diary/{id}/rate?score={score}`
- 参数：id - 日记 ID，score - 评分（0-5）
- 返回：`{id, rating}` - 新的平均分

**工具函数：**
- `post(url, body)` - 封装 POST 请求，自动设置 JSON 请求头

---

## views/ - 页面组件

### 7. views/MapView.vue - 地图导航页面

**文件路径：** `frontend/src/views/MapView.vue`

**主要功能：** 地图导航主页面，支持路线规划和周边探索

**核心功能：**

**7.1 路线规划模式**
- 点击地图设置起点和途经点
- 支持多种策略：最短距离、最短时间、骑行、电动车
- 支持往返路线（返回起点）
- 调用后端 TSP 算法规划最优路线
- 在地图上绘制路线

**7.2 周边探索模式**
- 点击地图选择探索中心
- 选择设施类别（餐饮、景点、酒店等）
- 设置搜索半径
- 在地图上标注周边设施

**7.3 地图集成**
- 使用高德地图 JS API
- 支持点击事件监听
- 绘制标记点（起点、途经点、设施）
- 绘制路线折线

**状态管理：**
- 使用 `mapStore` 管理地图状态
- 起点、途经点、路线结果等数据存储在 store 中

### 8. views/diary/Index.vue - 日记列表页面

**文件路径：** `frontend/src/views/diary/Index.vue`

**主要功能：** 展示日记列表，支持搜索和推荐

**核心功能：**

**8.1 搜索功能**
- 三种搜索模式：
  - 标题搜索（title）
  - 目的地搜索（destination）
  - 全文检索（fulltext）
- 支持回车键快速搜索
- 支持清空搜索（恢复推荐列表）

**8.2 日记展示**
- 卡片式布局，响应式设计
- 显示信息：标题、目的地、热度、评分、作者
- 点击卡片跳转到详情页

**8.3 推荐列表**
- 默认加载 Top-10 推荐日记
- 按热度和评分综合排序

**8.4 发布按钮**
- 右下角悬浮按钮（FAB - Floating Action Button）
- 点击跳转到发布页面

**UI 组件：**
- Element Plus 组件：el-select, el-input, el-button, el-card, el-row, el-col, el-tag

**响应式布局：**
- xs（手机）：1 列
- sm（平板）：2 列
- md（小屏）：3 列
- lg（大屏）：4 列

### 9. views/diary/Detail.vue - 日记详情页面

**文件路径：** `frontend/src/views/diary/Detail.vue`

**主要功能：** 展示日记完整内容，支持评分和删除

**核心功能：**

**9.1 日记展示**
- 标题、作者、目的地标签
- 热度和评分显示
- 富文本内容渲染（HTML）

**9.2 评分功能**
- 使用 Element Plus 的 el-rate 组件（星级评分）
- 评分后立即提交到后端
- 更新页面显示的平均评分
- 评分冷却机制（防止频繁评分）

**9.3 删除功能**
- 删除按钮（危险样式）
- 删除前二次确认（ElMessageBox）
- 删除成功后返回列表页

**9.4 自动热度统计**
- 页面加载时自动调用后端接口
- 后端自动将该日记热度 +1

**路由参数：**
- 从 `route.params.id` 获取日记 ID

**错误处理：**
- 加载失败提示
- 日记不存在提示
- 删除失败提示

### 10. views/diary/Publish.vue - 发布日记页面

**文件路径：** `frontend/src/views/diary/Publish.vue`

**主要功能：** 发布新日记，支持富文本编辑

**核心功能：**

**10.1 表单输入**
- 标题（必填，最多 255 字符，显示字数统计）
- 作者昵称（选填，默认"匿名"，最多 100 字符）
- 目的地（选填，最多 255 字符）

**10.2 富文本编辑器**
- 使用 wangEditor 5.x
- 工具栏：Toolbar 组件
- 编辑区：Editor 组件，高度 400px
- 支持格式：加粗、斜体、列表、链接、图片等

**10.3 表单验证**
- 标题不能为空
- 内容不能为空（排除空段落 `<p><br></p>`）
- 提交前自动去除首尾空格

**10.4 发布流程**
1. 验证表单
2. 获取编辑器 HTML 内容
3. 调用 API 创建日记
4. 成功后跳转到列表页
5. 失败提示用户重试

**10.5 生命周期管理**
- 组件卸载前销毁编辑器实例（防止内存泄漏）

**UI 组件：**
- Element Plus：el-input, el-button
- wangEditor：Editor, Toolbar

---

## 技术特点总结

### 1. 现代化技术栈
- **Vue 3 Composition API**：使用 `<script setup>` 语法，代码更简洁
- **Vite 构建**：快速的开发服务器和构建工具
- **Pinia 状态管理**：轻量级、类型安全的状态管理
- **Vue Router 4**：支持动态导入和懒加载

### 2. UI 组件库
- **Element Plus**：完整的 Vue 3 UI 组件库
- **响应式设计**：使用 el-row/el-col 实现多端适配
- **丰富组件**：输入框、按钮、卡片、评分、标签等

### 3. 地图集成
- **高德地图 JS API**：专业的地图服务
- **动态加载**：使用 @amap/amap-jsapi-loader 按需加载
- **交互功能**：点击事件、标记点、路线绘制

### 4. 富文本编辑
- **wangEditor 5.x**：轻量级富文本编辑器
- **Vue 3 适配**：官方提供的 Vue 组件
- **工具栏可配置**：支持自定义工具栏

### 5. 性能优化
- **路由懒加载**：日记模块按需加载，减小初始包体积
- **组件按需引入**：Element Plus 支持按需导入
- **编辑器生命周期管理**：及时销毁实例，防止内存泄漏

---

## 页面路由关系

```
App.vue (根组件)
├── 导航栏
│   ├── 地图导航 → /
│   └── 旅游日记 → /diary
└── 路由视图
    ├── / → MapView.vue (地图导航)
    │   ├── 路线规划模式
    │   └── 周边探索模式
    └── /diary → diary/Index.vue (日记列表)
        ├── 搜索功能
        ├── 推荐列表
        ├── /diary/publish → diary/Publish.vue (发布日记)
        │   └── 富文本编辑器
        └── /diary/:id → diary/Detail.vue (日记详情)
            ├── 内容展示
            ├── 评分功能
            └── 删除功能
```

---

## 数据流程说明

### 地图导航流程

1. **用户操作** → 点击地图选择点位
2. **状态更新** → mapStore 存储起点/途经点
3. **路线规划** → 调用后端 `/api/route/tsp` 接口
4. **结果展示** → 在地图上绘制路线，显示距离和时间

### 日记发布流程

1. **用户填写** → 标题、作者、目的地、内容
2. **表单验证** → 检查必填项
3. **API 调用** → POST `/api/diary`
4. **成功跳转** → 返回日记列表页

### 日记浏览流程

1. **加载列表** → GET `/api/diary/recommend?n=10`
2. **点击卡片** → 跳转到 `/diary/:id`
3. **加载详情** → GET `/api/diary/:id`（自动热度+1）
4. **用户评分** → POST `/api/diary/:id/rate?score=4.5`
5. **更新显示** → 页面显示新的平均评分

---

## 开发建议

### 1. 本地开发
```bash
# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev

# 构建生产版本
npm run build
```

### 2. 环境配置
- 确保后端服务运行在 `http://localhost:8000`
- 前端开发服务器会自动代理 `/api` 请求到后端
- 如需修改后端地址，编辑 `vite.config.js`

### 3. 代码规范
- 使用 Composition API 和 `<script setup>` 语法
- 组件命名使用 PascalCase（如 MapView.vue）
- 变量命名使用 camelCase
- 保持组件职责单一

### 4. 性能优化建议
- 大型组件使用路由懒加载
- 图片资源使用 CDN 或压缩
- 避免在模板中使用复杂计算，使用 computed
- 合理使用 v-if 和 v-show

### 5. 扩展方向
- 添加用户认证和授权
- 实现日记评论功能
- 支持图片上传和展示
- 添加地图路线收藏功能
- 实现离线缓存（PWA）

---

## 总结

InteliTour 前端采用现代化的 Vue 3 技术栈，结构清晰，职责分明：

**目录结构：**
- **api/** - API 接口封装，统一管理后端调用
- **router/** - 路由配置，支持懒加载
- **stores/** - Pinia 状态管理，全局状态共享
- **views/** - 页面组件，按功能模块组织

**核心功能：**
1. **地图导航**：基于高德地图，支持路线规划和周边探索
2. **旅游日记**：列表展示、搜索、发布、详情、评分

**技术亮点：**
1. **Vue 3 Composition API**：代码简洁，逻辑复用性强
2. **Vite 构建**：开发体验好，构建速度快
3. **Element Plus**：丰富的 UI 组件，响应式设计
4. **路由懒加载**：优化首屏加载性能
5. **富文本编辑**：wangEditor 提供良好的编辑体验

项目结构清晰，易于维护和扩展。各模块低耦合高内聚，符合前端工程化最佳实践。

---

**文档生成时间：** 2026-05-09  
**项目版本：** 0.1.0  
**维护者：** InteliTour Team

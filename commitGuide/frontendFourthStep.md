● 完成。以下是所做的改动：
  新增文件
  - src/router/index.js — 路由配置，/ →地图，/diary → 日记
  - src/views/MapView.vue — 原地图页面（从 App.vue 迁移）
  - src/views/DiaryView.vue — 日记占位页面  
  - src/api/diary.js — 封装日记 API（create/list/search/get/delete）
  修改文件
  - src/App.vue — 改为导航壳，含顶部蓝色导航栏 + <router-view>
  - src/main.js — 注册 vue-router
  - src/views/MapView.vue — 地图容器高度改为 calc(100vh - 44px) 避免被导航栏遮挡

  验证
  cd InteliTour/frontend && npm run dev
  访问 http://localhost:5173/ 看地图，点导航栏「旅游日记」跳转到 /diary 空白页。

● 构建成功。已完成以下工作：

  修改/新增的文件：
  - main.js — 全局注册 Element Plus
  - api/diary.js — search(mode, q) 接口已与后端对齐（支持 mode 与 q 参数）
  - src/views/diary/Index.vue — 新建日记主页
  - src/router/index.js — /diary 路由指向 diary/Index.vue（启用路由懒加载）

  /diary 页面运行逻辑：
  - 初始加载：调用 diaryApi.list(20) 拉取按热度排序的 Top 20 内容
  - 搜索交互：下拉框选择搜索模式（标题/目的地/全文检索）+ 输入框关键词 → 调用 diaryApi.search(mode, q)
  - 清空搜索条件 → 自动恢复至默认推荐列表
  - 列表卡片字段：标题、目的地标签、👀 热度、⭐ 评分、作者
  - 右下角悬浮按钮（FAB）→ 跳转至 /diary/publish 发布页（待后续创建）

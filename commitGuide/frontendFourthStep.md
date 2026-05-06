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


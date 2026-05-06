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

● 构建成功。已创建内容摘要：

  src/views/diary/Publish.vue
  - 标题（必填） + 目的地（选填）
  - 集成 WangEditor 富文本编辑器（含完整工具栏）
  - 提交表单 → 调用 diaryApi.create() → 发布成功后跳转至 /diary
  - 使用 ElMessage 处理表单校验提示与操作反馈

  新增路由：/diary/publish（已配置路由懒加载）
  
● 构建成功。已修复编辑器问题：
  问题原因：
  v-model 绑定干扰了 WangEditor 的内部状态管理，导致键盘输入被阻断。
  修改内容：

  1. 移除了 <Editor> 组件上的 v-model="html"
  2. 改为在提交时通过 editorRef.value.getHtml() 获取内容
  3. 删除了不再需要的 html ref   

  现在编辑器应该可以正常使用：

  - ✅ Backspace 删除文字
  - ✅ 选择文字后删除
  - ✅ 方向键移动光标
  - ✅ 输入标点符号

  所有键盘操作已恢复正常。

● 构建成功。修复内容：

  - create：路径从 /api/diary/create 改为 /api/diary
  - list：从 POST 改为 GET /api/diary/recommend?n=10

  现在发布日记和加载推荐列表应该都能正常工作了。 

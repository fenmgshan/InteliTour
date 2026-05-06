● 实现完成。变更摘要：                                                                                 
                                                                                                     
  mapStore.js — 新增 mode、exploreOrigin、exploreResults 状态及对应 actions。                          
                                                                                                       
  App.vue — 新增：                                                                                     
                                                                                                       
  - 顶部模式切换（居中固定）：[路线规划] / [周边探索]，蓝色高亮当前模式                              
  - 右侧探索面板（260px，可滚动）：
    - 点击地图 → 设置探索中心坐标
    - 快捷按钮：🚻洗手间 / 🏪 超市 / 🍽️  餐厅 → 调用 POST /api/nearby
    - 🍔 美食推荐 → 调用 POST /api/food/recommend（综合评分 Top-10）
    - 搜索框（支持回车）→ 调用 POST /api/food/search（Trie + 编辑距离容错）
    - 结果卡片：名称 / 子类别 + 路网距离 / 地址
  - 地图 emoji 标注：每次查询清除旧标注，新结果用对应 emoji（🚻🏪🍽️ 🍔）标注在地图上


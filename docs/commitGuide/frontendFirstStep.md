 启动步骤：

  1. 申请高德地图 JS API Key（lbs.amap.com），创建 .env 文件：
  cd frontend
  cp .env.example .env

  编辑 .env，填入你的 Key

  .env（在frontend/ 目录下创建）：

  ```
  VITE_AMAP_KEY=你的JS_API_Key  
  VITE_AMAP_SECURITY_KEY=你的安全密钥
  ```

  _AMapSecurityConfig 必须在 AMapLoader.load() 之前设置，已在 App.vue
  中处理好了。.env 文件不要提交到git。  

  2. 安装依赖并启动：
  cd frontend
  npm install
  npm run dev

  3. 确保后端也在运行：
  cd InteliTour && python3 -m backend.app

  数据流闭环：
  点击地图 → e.lnglat(lng, lat)→ POST /api/snap { lat, lng }
    → SnapResponse { node_id, lat, lng, distance }
    → store.setSnappedNode(data)   ← Pinia 全局状态
    → 地图上标记吸附节点位置

  Vite 的 proxy 配置已将/api/* 转发到 localhost:8000，无需处理跨域。


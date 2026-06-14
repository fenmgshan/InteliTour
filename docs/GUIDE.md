# InteliTour 项目快速启动指南

本指南提供从零开始运行 InteliTour 项目的完整步骤。

---

## 环境要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+) 或 macOS
- **Python**: 3.9+
- **MySQL**: 8.0+
- **Redis**: 6.0+

---

## 第一步：系统依赖安装

### 1.1 安装 MySQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# 启动 MySQL 服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 验证安装
mysql --version
```

### 1.2 安装 Redis

```bash
# Ubuntu/Debian
sudo apt install redis-server

# 启动 Redis 服务
sudo systemctl start redis
sudo systemctl enable redis

# 验证安装
redis-cli ping
# 应返回: PONG
```

### 1.3 安装 Python 依赖

```bash
# 安装 pip（如果未安装）
sudo apt install python3-pip

# 安装 GDAL（地理空间库，osmnx 依赖）
sudo apt install gdal-bin libgdal-dev
```

---

## 第二步：克隆项目并安装依赖

```bash
# 克隆项目（如果还没有）
cd ~
git clone <your-repo-url> InteliTour
cd InteliTour

# 安装 Python 依赖
pip3 install -r requirements.txt

# 验证关键包
python3 -c "import osmnx, networkx, fastapi, sqlalchemy, redis, whoosh; print('All packages OK')"
```

---

## 第三步：配置数据库

### 3.1 创建 MySQL 用户和数据库

```bash
# 登录 MySQL
sudo mysql -u root -p

# 在 MySQL 命令行中执行：
CREATE USER 'intelitour_user'@'localhost' IDENTIFIED BY 'mypassword';
CREATE DATABASE intelitour CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON intelitour.* TO 'intelitour_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3.2 初始化数据库表

```bash
cd ~/InteliTour
python3 database/init_db.py
```

**预期输出：**
```
[OK] 数据库 'intelitour' 已存在或创建成功
[OK] 所有表已创建
```

---

## 第四步：数据采集与预处理

### 4.1 爬取路网数据

```bash
python3 scripts/crawl_road_network.py
```

**说明**：从 OpenStreetMap 下载天安门周边 5km 半径内的步行路网。

**预期输出：**
```
[开始] 爬取路网...
[OK] 路网节点: 12345 个
[OK] 路网边: 23456 条
[OK] 数据已保存到数据库
[OK] GraphML 已导出到 data/beijing_walk.graphml
```

**耗时**：约 2-5 分钟（取决于网络速度）

### 4.2 爬取 POI 数据

```bash
python3 scripts/crawl_pois.py
```

**说明**：爬取景点、餐厅、卫生间、超市、建筑物等 POI。

**预期输出：**
```
[开始] 爬取 POI...
[OK] 景点: 123 个
[OK] 餐厅: 456 个
[OK] 卫生间: 78 个
[OK] 超市: 90 个
[OK] 建筑物: 1234 个
```

**耗时**：约 3-8 分钟

### 4.3 吸附 POI 到路网

```bash
python3 scripts/snap_to_network.py
```

**说明**：将所有 POI 和建筑物吸附到最近的路网节点。

**预期输出：**
```
[SnapService] 加载 12345 个路网节点
[OK] 吸附 POI: 747 个
[OK] 吸附建筑物: 1234 个
```

**耗时**：约 1-2 分钟

### 4.4 导出 GraphML（可选，已在 4.1 自动完成）

```bash
python3 scripts/export_graphml.py
```

---

## 第五步：启动后端服务

```bash
cd ~/InteliTour
python3 -m backend.app
```

**预期输出：**
```
[启动] 正在加载路网图...
[OK] 加载图: 12345 节点, 23456 边
[启动] 正在初始化吸附服务...
[SnapService] 加载 12345 个路网节点
[启动] 后端服务就绪
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**服务地址：**
- API 根路径: `http://localhost:8000`
- Swagger 文档: `http://localhost:8000/docs`
- ReDoc 文档: `http://localhost:8000/redoc`

---

## 第六步：验证服务

### 6.1 访问 Swagger 文档

浏览器打开 `http://localhost:8000/docs`，应看到所有 API 端点。

### 6.2 测试坐标吸附接口

```bash
curl -X POST http://localhost:8000/api/snap \
  -H 'Content-Type: application/json' \
  -d '{"lat": 39.9042, "lng": 116.3974}' \
  | python3 -m json.tool
```

**预期响应：**
```json
{
  "node_id": 123456789,
  "lat": 39.904198,
  "lng": 116.397401,
  "distance": 2.34
}
```

### 6.3 测试最短路径接口

```bash
curl -X POST http://localhost:8000/api/route/shortest \
  -H 'Content-Type: application/json' \
  -d '{
    "origin": {"lat": 39.9042, "lng": 116.3974},
    "destination": {"lat": 39.9163, "lng": 116.3972},
    "strategy": "distance"
  }' | python3 -m json.tool
```

**预期响应：**
```json
{
  "path": [
    {"lat": 39.9042, "lng": 116.3974},
    {"lat": 39.9050, "lng": 116.3975},
    ...
    {"lat": 39.9163, "lng": 116.3972}
  ],
  "total_distance": 1345.67,
  "total_time": 965.12,
  "strategy": "distance"
}
```

---

## 第七步：常用操作

### 7.1 停止服务

在运行 `python3 -m backend.app` 的终端按 `Ctrl+C`。

### 7.2 重启服务

```bash
cd ~/InteliTour
python3 -m backend.app
```

### 7.3 查看日志

服务日志直接输出到终端。如需保存到文件：

```bash
python3 -m backend.app > logs/app.log 2>&1 &
```

### 7.4 后台运行

```bash
nohup python3 -m backend.app > logs/app.log 2>&1 &
```

查看进程：
```bash
ps aux | grep "backend.app"
```

停止后台进程：
```bash
pkill -f "backend.app"
```

---

## 第八步：数据更新

### 8.1 重新爬取数据

```bash
# 清空旧数据（可选）
mysql -u intelitour_user -pmypassword intelitour -e "
  TRUNCATE TABLE road_nodes;
  TRUNCATE TABLE road_edges;
  TRUNCATE TABLE pois;
  TRUNCATE TABLE buildings;
"

# 重新执行数据采集
python3 scripts/crawl_road_network.py
python3 scripts/crawl_pois.py
python3 scripts/snap_to_network.py
```

### 8.2 清空 Redis 缓存

```bash
redis-cli FLUSHDB
```

### 8.3 重建 Whoosh 索引

```bash
rm -rf data/whoosh_diary/
# 重新创建日记时会自动重建索引
```

---

## 故障排查

### 问题 1：MySQL 连接失败

**错误信息：**
```
sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")
```

**解决方法：**
```bash
# 检查 MySQL 是否运行
sudo systemctl status mysql

# 启动 MySQL
sudo systemctl start mysql

# 验证用户权限
mysql -u intelitour_user -pmypassword -e "SHOW DATABASES;"
```

### 问题 2：Redis 连接失败

**错误信息：**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**解决方法：**
```bash
# 检查 Redis 是否运行
sudo systemctl status redis

# 启动 Redis
sudo systemctl start redis

# 测试连接
redis-cli ping
```

### 问题 3：GraphML 文件不存在

**错误信息：**
```
FileNotFoundError: data/beijing_walk.graphml
```

**解决方法：**
```bash
# 重新导出 GraphML
python3 scripts/export_graphml.py

# 或重新爬取路网
python3 scripts/crawl_road_network.py
```

### 问题 4：端口 8000 被占用

**错误信息：**
```
OSError: [Errno 98] Address already in use
```

**解决方法：**
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用其他端口
# 修改 backend/app.py 最后一行：
# uvicorn.run("backend.app:app", host="0.0.0.0", port=8001, reload=True)
```

### 问题 5：OSMnx 下载超时

**错误信息：**
```
requests.exceptions.ReadTimeout
```

**解决方法：**
```bash
# 设置更长的超时时间
# 在 scripts/crawl_road_network.py 开头添加：
import osmnx as ox
ox.settings.timeout = 300  # 5 分钟
```

---

## 快速命令参考

```bash
# 完整启动流程（首次运行）
cd ~/InteliTour
python3 database/init_db.py
python3 scripts/crawl_road_network.py
python3 scripts/crawl_pois.py
python3 scripts/snap_to_network.py
python3 -m backend.app

# 日常启动（数据已准备好）
cd ~/InteliTour
python3 -m backend.app

# 测试 API
curl http://localhost:8000/api/snap -X POST \
  -H 'Content-Type: application/json' \
  -d '{"lat":39.9042,"lng":116.3974}' | python3 -m json.tool

# 查看 Swagger 文档
# 浏览器打开: http://localhost:8000/docs
```

---

## 下一步

- 查看 [TESTING.md](./TESTING.md) 了解测试方法
- 查看 [README.md](./README.md) 了解技术原理
- 访问 `http://localhost:8000/docs` 查看完整 API 文档

---

**项目启动完成！** 🎉

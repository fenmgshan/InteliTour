# InteliTour 测试指南

本文档提供完整的测试方法和指令，覆盖单元测试、集成测试和手动测试。

---

## 测试环境准备

### 1. 安装测试依赖

```bash
pip3 install pytest requests
```

### 2. 初始化数据库（新增 diaries 表）

```bash
cd InteliTour
python3 -c "from database.models import Base; from database.config import get_engine; Base.metadata.create_all(get_engine())"
```

### 3. 启动 Redis（如未运行）

```bash
# 检查 Redis 是否运行
python3 -c "import redis; redis.Redis().ping(); print('Redis OK')"

# 如果失败，启动 Redis 服务
sudo systemctl start redis
# 或
redis-server &
```

---

## 一、单元测试（不依赖数据库）

单元测试使用 mock 和内存数据，验证核心算法正确性。

### 运行所有单元测试

```bash
cd InteliTour
python3 -m pytest tests/ -v
```

### 分模块运行

```bash
# 日记模块（压缩、Redis、Min-Heap、Schema）
python3 -m pytest tests/test_diary.py -v

# 美食模块（Trie、Levenshtein、Schema）
python3 -m pytest tests/test_food.py -v

# 周边设施模块（有界 Dijkstra、快速排序、Schema）
python3 -m pytest tests/test_nearby.py -v

# 路线规划模块（Dijkstra、TSP）
python3 -m pytest tests/test_route_service.py -v
```

### 查看测试覆盖率（可选）

```bash
pip3 install pytest-cov
python3 -m pytest tests/ --cov=backend --cov-report=html
# 打开 htmlcov/index.html 查看详细报告
```

---

## 二、API 集成测试（需要运行服务器）

集成测试调用真实 API 端点，验证端到端流程。

### 步骤 1：启动服务器

```bash
cd InteliTour
python3 -m backend.app
```

等待看到以下输出：
```
[启动] 正在加载路网图...
[OK] 加载图: xxx 节点, xxx 边
[启动] 正在初始化吸附服务...
[SnapService] 加载 xxx 个路网节点
[启动] 后端服务就绪
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤 2：运行集成测试脚本

**新开一个终端**，运行：

```bash
cd InteliTour
python3 tests/test_api_integration.py
```

测试内容：
- **日记 API**：创建、获取、搜索（title/destination/fulltext）、推荐、删除
- **美食推荐 API**：附近推荐、菜系过滤、模糊搜索、容错搜索
- **周边设施 API**：卫生间、超市、便利店查询，距离排序验证

---

## 三、手动 API 测试（curl）

### 3.1 日记 API

#### 创建日记
```bash
curl -X POST http://localhost:8000/api/diary \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "颐和园游记",
    "author": "张三",
    "destination": "颐和园",
    "content": "今天游览了颐和园，风景优美，湖光山色令人陶醉。",
    "rating": 4.5
  }' | python3 -m json.tool
```

#### 获取日记详情（热度+1）
```bash
curl http://localhost:8000/api/diary/1 | python3 -m json.tool
```

#### 搜索日记（按标题）
```bash
curl -X POST http://localhost:8000/api/diary/search \
  -H 'Content-Type: application/json' \
  -d '{"mode": "title", "q": "颐和园游记"}' | python3 -m json.tool
```

#### 搜索日记（全文检索）
```bash
curl -X POST http://localhost:8000/api/diary/search \
  -H 'Content-Type: application/json' \
  -d '{"mode": "fulltext", "q": "风景"}' | python3 -m json.tool
```

#### Top-10 推荐
```bash
curl http://localhost:8000/api/diary/recommend?n=10 | python3 -m json.tool
```

#### 删除日记
```bash
curl -X DELETE http://localhost:8000/api/diary/1
```

---

### 3.2 美食推荐 API

#### 附近美食推荐（天安门附近）
```bash
curl -X POST http://localhost:8000/api/food/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "origin_lat": 39.9042,
    "origin_lng": 116.3974,
    "cuisine": "",
    "n": 10
  }' | python3 -m json.tool
```

#### 过滤川菜
```bash
curl -X POST http://localhost:8000/api/food/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "origin_lat": 39.9042,
    "origin_lng": 116.3974,
    "cuisine": "川菜",
    "n": 5
  }' | python3 -m json.tool
```

#### 模糊搜索（Trie + Levenshtein）
```bash
curl -X POST http://localhost:8000/api/food/search \
  -H 'Content-Type: application/json' \
  -d '{
    "q": "麻辣烫",
    "origin_lat": 39.9042,
    "origin_lng": 116.3974,
    "max_edit_distance": 2,
    "n": 5
  }' | python3 -m json.tool
```

#### 容错搜索（错别字 "麻辣糖"）
```bash
curl -X POST http://localhost:8000/api/food/search \
  -H 'Content-Type: application/json' \
  -d '{
    "q": "麻辣糖",
    "origin_lat": 39.9042,
    "origin_lng": 116.3974,
    "max_edit_distance": 2,
    "n": 5
  }' | python3 -m json.tool
```

---

### 3.3 周边设施查询 API

#### 查找附近卫生间
```bash
curl -X POST http://localhost:8000/api/nearby \
  -H 'Content-Type: application/json' \
  -d '{
    "origin_lat": 39.9042,
    "origin_lng": 116.3974,
    "category": "toilet",
    "max_dist": 500,
    "limit": 10
  }' | python3 -m json.tool
```

#### 查找附近超市
```bash
curl -X POST http://localhost:8000/api/nearby \
  -H 'Content-Type: application/json' \
  -d '{
    "origin_lat": 39.9042,
    "origin_lng": 116.3974,
    "category": "supermarket",
    "max_dist": 1000,
    "limit": 20
  }' | python3 -m json.tool
```

#### 查找附近便利店
```bash
curl -X POST http://localhost:8000/api/nearby \
  -H 'Content-Type: application/json' \
  -d '{
    "origin_lat": 39.9042,
    "origin_lng": 116.3974,
    "category": "convenience",
    "max_dist": 800,
    "limit": 15
  }' | python3 -m json.tool
```

---

## 四、Swagger 交互式测试

浏览器打开 `http://localhost:8000/docs`，可以：
- 查看所有 API 端点的请求/响应结构
- 直接在页面上填参数调用接口
- 查看实时响应和错误信息

---

## 五、性能测试（可选）

### 压缩率测试
```bash
python3 -c "
from backend.services.diary_service import _compress, _decompress
text = '这是一篇测试日记，内容重复。' * 1000
compressed = _compress(text)
ratio = len(compressed) / len(text.encode('utf-8'))
print(f'原始大小: {len(text.encode(\"utf-8\"))} 字节')
print(f'压缩后: {len(compressed)} 字节')
print(f'压缩率: {ratio:.2%}')
"
```

### Min-Heap 性能测试
```bash
python3 -c "
import time
from backend.services.heap_service import top_n
items = list(range(100000))
start = time.time()
result = top_n(items, lambda x: float(x), n=10)
elapsed = time.time() - start
print(f'从 100,000 个元素中选 Top-10: {elapsed*1000:.2f} ms')
assert result == list(range(99999, 99989, -1))
"
```

### Levenshtein 性能测试
```bash
python3 -c "
import time
from backend.services.food_service import levenshtein
s1 = 'a' * 1000
s2 = 'a' * 999 + 'b'
start = time.time()
dist = levenshtein(s1, s2)
elapsed = time.time() - start
print(f'计算 1000 字符编辑距离: {elapsed*1000:.2f} ms')
assert dist == 1
"
```

---

## 六、常见问题排查

### 问题 1：服务器启动失败 "图尚未加载"
**原因**：GraphML 文件不存在或路径错误。

**解决**：
```bash
# 检查 GraphML 是否存在
ls -lh data/beijing_walk.graphml

# 如果不存在，重新导出
python3 -c "from scripts.export_graphml import main; main()"
```

### 问题 2：Redis 连接失败
**原因**：Redis 服务未启动。

**解决**：
```bash
sudo systemctl start redis
# 或
redis-server &
```

### 问题 3：Whoosh 索引错误
**原因**：索引目录权限问题或损坏。

**解决**：
```bash
rm -rf data/whoosh_diary/
# 重新创建日记时会自动重建索引
```

### 问题 4：测试数据不足
**原因**：数据库中 POI 数据为空。

**解决**：
```bash
# 重新爬取 POI 数据
python3 scripts/crawl_pois.py
python3 scripts/snap_to_network.py
```

---

## 七、测试检查清单

运行以下命令验证所有功能：

```bash
# 1. 单元测试
python3 -m pytest tests/ -v

# 2. 启动服务器（新终端）
python3 -m backend.app

# 3. 集成测试（另一个终端）
python3 tests/test_api_integration.py

# 4. 访问 Swagger 文档
# 浏览器打开 http://localhost:8000/docs

# 5. 手动测试一个端点
curl http://localhost:8000/api/diary/recommend?n=5 | python3 -m json.tool
```

全部通过即表示系统正常运行。

---

## 八、测试覆盖范围

| 模块 | 单元测试 | 集成测试 | 手动测试 |
|------|---------|---------|---------|
| 日记管理 | ✅ 压缩、Redis、Min-Heap、Schema | ✅ CRUD、搜索、推荐 | ✅ curl 示例 |
| 美食推荐 | ✅ Trie、Levenshtein、Schema | ✅ 推荐、搜索、容错 | ✅ curl 示例 |
| 周边设施 | ✅ 有界 Dijkstra、快速排序 | ✅ 多类别查询、排序 | ✅ curl 示例 |
| 路线规划 | ✅ Dijkstra、TSP | ✅ 最短路径、多点 TSP | ✅ curl 示例 |

---

## 九、持续集成（CI）配置示例

如果使用 GitHub Actions，可创建 `.github/workflows/test.yml`：

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis
        ports:
          - 6379:6379
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: intelitour
        ports:
          - 3306:3306

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov requests
      - run: python3 -m pytest tests/ -v --cov=backend
```

---

**测试愉快！** 🎉

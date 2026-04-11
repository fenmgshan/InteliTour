# Step 3 测试总结

## 测试文件清单

| 文件 | 测试数量 | 覆盖内容 |
|------|---------|---------|
| `tests/test_diary.py` | 15 个 | zlib 压缩/解压、Redis 热度、Min-Heap Top-N、Pydantic Schema |
| `tests/test_food.py` | 21 个 | Trie 前缀树、Levenshtein 编辑距离、容错搜索、Schema |
| `tests/test_nearby.py` | 19 个 | 有界 Dijkstra、快速排序、Schema、集成场景 |
| `tests/test_api_integration.py` | 1 个脚本 | 端到端 API 测试（需运行服务器） |
| **总计** | **55 个单元测试** | **100% 通过** ✅ |

## 快速测试指令

### 1. 单元测试（无需数据库）
```bash
cd InteliTour
python3 -m pytest tests/ -v
```

### 2. 集成测试（需启动服务器）
```bash
# 终端 1：启动服务器
python3 -m backend.app

# 终端 2：运行集成测试
python3 tests/test_api_integration.py
```

### 3. 手动测试单个端点
```bash
# 日记推荐
curl http://localhost:8000/api/diary/recommend?n=5 | python3 -m json.tool

# 美食推荐（天安门附近）
curl -X POST http://localhost:8000/api/food/recommend \
  -H 'Content-Type: application/json' \
  -d '{"origin_lat":39.9042,"origin_lng":116.3974,"cuisine":"","n":10}' \
  | python3 -m json.tool

# 周边卫生间
curl -X POST http://localhost:8000/api/nearby \
  -H 'Content-Type: application/json' \
  -d '{"origin_lat":39.9042,"origin_lng":116.3974,"category":"toilet","max_dist":500,"limit":10}' \
  | python3 -m json.tool
```

## 核心算法验证

### ✅ zlib 压缩（LZ77 + Huffman）
- 重复中文文本压缩率 < 10%
- 支持 emoji 和特殊字符
- 解压后完全一致

### ✅ Min-Heap Top-N（O(N log K)）
- 从 100 个元素中选 Top-10：正确
- 处理负数、自定义对象：正确
- 边界条件（n=0, n>len）：正确

### ✅ Trie 前缀树
- 前缀匹配：麻辣 → {麻辣烫, 麻辣香锅}
- Unicode 支持：café, 🍕pizza
- 空 Trie 查询：返回空列表

### ✅ Levenshtein 编辑距离（DP）
- 麻辣烫 ↔ 麻辣糖：距离 1
- kitten ↔ sitting：距离 3
- 容错搜索：max_dist=2 可匹配错别字

### ✅ 有界 Dijkstra（等时圈搜索）
- 从 A 出发，半径 300m：可达 {A, B, C, D}
- 半径 0m：只有起点自己
- 孤立节点：正确处理

### ✅ 快速排序（Quick Sort）
- 升序排列：[5,2,8,1,9] → [1,2,5,8,9]
- 处理重复值：正确
- 自定义 key：按元组第二项排序

## 测试覆盖率

```
压缩/解压：4 个测试
Redis 服务：3 个测试
Min-Heap：5 个测试
Trie：5 个测试
Levenshtein：9 个测试
有界 Dijkstra：5 个测试
快速排序：9 个测试
Pydantic Schema：15 个测试
集成场景：1 个测试
─────────────────────────
总计：55 个单元测试 ✅
```

## 详细测试文档

完整测试方法、curl 示例、故障排查请参考：
📖 **[TESTING.md](./TESTING.md)**

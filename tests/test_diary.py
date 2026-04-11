"""旅游日记服务单元测试

测试 zlib 压缩、Whoosh 索引、Min-Heap 推荐等核心功能。
不依赖真实数据库，使用 mock 和内存数据。
"""

import zlib
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

from backend.services.diary_service import _compress, _decompress


# ══════════════════════════════════════════════════════════
# 压缩/解压测试
# ══════════════════════════════════════════════════════════

class TestCompression:
    def test_compress_decompress_ascii(self):
        text = "This is a test diary entry." * 50
        compressed = _compress(text)
        assert _decompress(compressed) == text
        ratio = len(compressed) / len(text.encode("utf-8"))
        assert ratio < 0.5, f"压缩率应 < 50%，实际 {ratio:.2%}"

    def test_compress_decompress_chinese(self):
        text = "这是一篇测试日记，包含中文字符。" * 100
        compressed = _compress(text)
        assert _decompress(compressed) == text
        ratio = len(compressed) / len(text.encode("utf-8"))
        assert ratio < 0.1, f"重复中文压缩率应 < 10%，实际 {ratio:.2%}"

    def test_compress_empty(self):
        assert _decompress(_compress("")) == ""

    def test_compress_special_chars(self):
        text = "🎉🎊🎈 emoji test 😀😁😂" * 20
        assert _decompress(_compress(text)) == text


# ══════════════════════════════════════════════════════════
# Redis 服务测试
# ══════════════════════════════════════════════════════════

class TestRedisService:
    @patch("backend.services.redis_service.get_redis")
    def test_incr_heat(self, mock_get_redis):
        mock_client = MagicMock()
        mock_client.hincrby.return_value = 5
        mock_get_redis.return_value = mock_client

        from backend.services.redis_service import incr_heat
        result = incr_heat("diary", 123)
        assert result == 5
        mock_client.hincrby.assert_called_once_with("diary:heat", "123", 1)

    @patch("backend.services.redis_service.get_redis")
    def test_get_heat_exists(self, mock_get_redis):
        mock_client = MagicMock()
        mock_client.hget.return_value = "42"
        mock_get_redis.return_value = mock_client

        from backend.services.redis_service import get_heat
        result = get_heat("diary", 123)
        assert result == 42.0

    @patch("backend.services.redis_service.get_redis")
    def test_get_heat_not_exists(self, mock_get_redis):
        mock_client = MagicMock()
        mock_client.hget.return_value = None
        mock_get_redis.return_value = mock_client

        from backend.services.redis_service import get_heat
        result = get_heat("diary", 999)
        assert result == 0.0


# ══════════════════════════════════════════════════════════
# Min-Heap Top-N 测试
# ══════════════════════════════════════════════════════════

class TestHeapService:
    def test_top_n_basic(self):
        from backend.services.heap_service import top_n
        items = list(range(100))
        result = top_n(items, lambda x: float(x), n=10)
        assert result == list(range(99, 89, -1))

    def test_top_n_less_than_n(self):
        from backend.services.heap_service import top_n
        items = [1, 2, 3]
        result = top_n(items, lambda x: float(x), n=10)
        assert len(result) == 3
        assert result == [3, 2, 1]

    def test_top_n_zero(self):
        from backend.services.heap_service import top_n
        result = top_n([1, 2, 3], lambda x: float(x), n=0)
        assert result == []

    def test_top_n_negative_scores(self):
        from backend.services.heap_service import top_n
        items = [-5, -2, -10, 3, 0, -1]
        result = top_n(items, lambda x: float(x), n=3)
        assert result == [3, 0, -1]

    def test_top_n_custom_objects(self):
        from backend.services.heap_service import top_n

        class Item:
            def __init__(self, name, score):
                self.name = name
                self.score = score

        items = [Item("a", 10), Item("b", 50), Item("c", 30), Item("d", 20)]
        result = top_n(items, lambda x: x.score, n=2)
        assert [x.name for x in result] == ["b", "c"]


# ══════════════════════════════════════════════════════════
# Pydantic Schema 验证测试
# ══════════════════════════════════════════════════════════

class TestDiarySchemas:
    def test_diary_create_valid(self):
        from backend.schemas.diary import DiaryCreate
        data = {
            "title": "北京游记",
            "author": "张三",
            "destination": "故宫",
            "content": "今天去了故宫，非常壮观。",
            "rating": 4.5,
        }
        diary = DiaryCreate(**data)
        assert diary.title == "北京游记"
        assert diary.rating == 4.5

    def test_diary_create_rating_out_of_range(self):
        from backend.schemas.diary import DiaryCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DiaryCreate(
                title="test",
                content="test",
                rating=6.0,  # 超出 0-5 范围
            )

    def test_diary_search_request(self):
        from backend.schemas.diary import DiarySearchRequest
        req = DiarySearchRequest(mode="title", q="北京")
        assert req.mode == "title"
        assert req.q == "北京"


# ══════════════════════════════════════════════════════════
# 运行测试
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

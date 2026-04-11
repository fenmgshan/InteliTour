"""美食推荐服务单元测试

测试 Trie 前缀树、Levenshtein 编辑距离等核心算法。
"""

import pytest

from backend.services.food_service import Trie, levenshtein


# ══════════════════════════════════════════════════════════
# Trie 字典树测试
# ══════════════════════════════════════════════════════════

class TestTrie:
    def test_insert_and_prefix_search(self):
        trie = Trie()
        trie.insert("麻辣烫", 1)
        trie.insert("麻辣香锅", 2)
        trie.insert("麻婆豆腐", 3)
        trie.insert("北京烤鸭", 4)

        assert set(trie.prefix_search("麻辣")) == {1, 2}
        assert set(trie.prefix_search("麻")) == {1, 2, 3}
        assert set(trie.prefix_search("北京")) == {4}
        assert trie.prefix_search("川菜") == []

    def test_empty_trie(self):
        trie = Trie()
        assert trie.prefix_search("test") == []

    def test_single_char_prefix(self):
        trie = Trie()
        trie.insert("a", 1)
        trie.insert("ab", 2)
        trie.insert("abc", 3)
        assert set(trie.prefix_search("a")) == {1, 2, 3}
        assert set(trie.prefix_search("ab")) == {2, 3}
        assert set(trie.prefix_search("abc")) == {3}

    def test_duplicate_words(self):
        trie = Trie()
        trie.insert("test", 1)
        trie.insert("test", 2)
        assert set(trie.prefix_search("test")) == {1, 2}

    def test_unicode_support(self):
        trie = Trie()
        trie.insert("café", 1)
        trie.insert("naïve", 2)
        trie.insert("🍕pizza", 3)
        assert trie.prefix_search("café") == [1]
        assert trie.prefix_search("🍕") == [3]


# ══════════════════════════════════════════════════════════
# Levenshtein 编辑距离测试
# ══════════════════════════════════════════════════════════

class TestLevenshtein:
    def test_identical_strings(self):
        assert levenshtein("hello", "hello") == 0
        assert levenshtein("北京烤鸭", "北京烤鸭") == 0

    def test_one_char_difference(self):
        assert levenshtein("麻辣烫", "麻辣糖") == 1
        assert levenshtein("cat", "bat") == 1

    def test_insertion(self):
        assert levenshtein("cat", "cats") == 1
        assert levenshtein("", "abc") == 3

    def test_deletion(self):
        assert levenshtein("cats", "cat") == 1
        assert levenshtein("abc", "") == 3

    def test_substitution(self):
        assert levenshtein("abc", "xyz") == 3
        assert levenshtein("kitten", "sitting") == 3

    def test_empty_strings(self):
        assert levenshtein("", "") == 0
        assert levenshtein("test", "") == 4
        assert levenshtein("", "test") == 4

    def test_chinese_characters(self):
        assert levenshtein("北京", "南京") == 1
        assert levenshtein("麻辣烫", "麻辣香锅") == 2

    def test_case_sensitive(self):
        assert levenshtein("Hello", "hello") == 1

    def test_long_strings(self):
        s1 = "a" * 100
        s2 = "a" * 99 + "b"
        assert levenshtein(s1, s2) == 1


# ══════════════════════════════════════════════════════════
# Pydantic Schema 验证测试
# ══════════════════════════════════════════════════════════

class TestFoodSchemas:
    def test_food_recommend_request_valid(self):
        from backend.schemas.food import FoodRecommendRequest
        req = FoodRecommendRequest(
            origin_lat=39.9042,
            origin_lng=116.3974,
            cuisine="川菜",
            n=10,
        )
        assert req.origin_lat == 39.9042
        assert req.cuisine == "川菜"
        assert req.n == 10

    def test_food_recommend_request_defaults(self):
        from backend.schemas.food import FoodRecommendRequest
        req = FoodRecommendRequest(origin_lat=39.9, origin_lng=116.4)
        assert req.cuisine == ""
        assert req.n == 10

    def test_food_search_request_valid(self):
        from backend.schemas.food import FoodSearchRequest
        req = FoodSearchRequest(
            q="麻辣烫",
            origin_lat=39.9,
            origin_lng=116.4,
            max_edit_distance=2,
        )
        assert req.q == "麻辣烫"
        assert req.max_edit_distance == 2

    def test_food_search_request_no_origin(self):
        from backend.schemas.food import FoodSearchRequest
        req = FoodSearchRequest(q="pizza")
        assert req.origin_lat is None
        assert req.origin_lng is None

    def test_food_item_response(self):
        from backend.schemas.food import FoodItem
        item = FoodItem(
            id=1,
            name="老北京炸酱面",
            category="restaurant",
            sub_category="中餐",
            lat=39.9,
            lng=116.4,
            address="北京市东城区",
            rating=4.5,
            heat=100.0,
            distance=250.5,
            score=0.85,
        )
        assert item.name == "老北京炸酱面"
        assert item.distance == 250.5


# ══════════════════════════════════════════════════════════
# 边界条件测试
# ══════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_levenshtein_max_distance(self):
        """测试编辑距离阈值过滤逻辑"""
        # 模拟搜索场景：用户输入 "麻辣糖"（错别字），应匹配 "麻辣烫"
        query = "麻辣糖"
        candidates = ["麻辣烫", "麻辣香锅", "北京烤鸭", "宫保鸡丁"]
        max_dist = 2

        matches = [c for c in candidates if levenshtein(query, c) <= max_dist]
        assert "麻辣烫" in matches
        assert "麻辣香锅" in matches
        assert "北京烤鸭" not in matches

    def test_trie_prefix_no_match(self):
        trie = Trie()
        trie.insert("apple", 1)
        trie.insert("application", 2)
        # 搜索不存在的前缀
        assert trie.prefix_search("banana") == []
        assert trie.prefix_search("app") == [1, 2]


# ══════════════════════════════════════════════════════════
# 运行测试
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

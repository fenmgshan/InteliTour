"""Min-Heap Top-N 不完全排序

供日记推荐和美食推荐共用。
时间复杂度 O(N log K)，K 为返回数量，避免全量排序。
"""

import heapq
from typing import Callable, TypeVar

T = TypeVar("T")


def top_n(items: list[T], score_fn: Callable[[T], float], n: int = 10) -> list[T]:
    """从 items 中用最小堆选出得分最高的前 n 个，按得分降序返回。

    Args:
        items: 候选列表
        score_fn: 计算单个元素得分的函数
        n: 返回数量

    Returns:
        得分最高的前 n 个元素，降序排列
    """
    if n <= 0:
        return []

    # 堆元素: (score, index, item)，用 index 避免 item 不可比较时报错
    heap: list[tuple[float, int, T]] = []

    for idx, item in enumerate(items):
        score = score_fn(item)
        if len(heap) < n:
            heapq.heappush(heap, (score, idx, item))
        elif score > heap[0][0]:
            heapq.heapreplace(heap, (score, idx, item))

    # 堆中元素按得分降序返回
    heap.sort(key=lambda x: x[0], reverse=True)
    return [item for _, _, item in heap]

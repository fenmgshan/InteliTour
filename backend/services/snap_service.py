"""吸附服务单例

封装 SnapService，在应用启动时初始化一次。
"""

from scripts.snap_to_network import SnapService

_snap_service: SnapService | None = None


def init_snap_service() -> None:
    """初始化吸附服务（应用启动时调用一次）。"""
    global _snap_service
    _snap_service = SnapService()


def get_snap_service() -> SnapService:
    """获取全局吸附服务实例。"""
    if _snap_service is None:
        raise RuntimeError("SnapService 尚未初始化，请先调用 init_snap_service()")
    return _snap_service

"""FastAPI 应用入口

启动: cd InteliTour && python3 -m backend.app
Swagger 文档: http://localhost:8000/docs
"""

import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.graph_service import init_graph
from backend.services.snap_service import init_snap_service
from backend.routers import snap, route


app = FastAPI(
    title="InteliTour API",
    description="智慧旅游路线规划后端",
    version="0.1.0",
)


@app.on_event("startup")
def startup():
    """应用启动时加载图和吸附服务。"""
    print("[启动] 正在加载路网图...")
    init_graph()
    print("[启动] 正在初始化吸附服务...")
    init_snap_service()
    print("[启动] 后端服务就绪")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(snap.router)
app.include_router(route.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)

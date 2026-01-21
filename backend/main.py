"""FastAPI 主入口"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .routers import compress_router
from .utils import ensure_temp_dir

# 创建应用
app = FastAPI(
    title="文档压缩服务",
    description="在线文档压缩工具，支持 PDF 和 DOCX 文件",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保临时目录存在
ensure_temp_dir()

# 注册路由
app.include_router(compress_router)


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "document-compressor"}


# 挂载前端静态文件 (必须放在所有API路由之后)
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

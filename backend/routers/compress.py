"""文档压缩API路由"""
import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any

from ..utils import (
    generate_task_id,
    get_task_dir,
    validate_file,
    get_file_extension,
    get_file_size,
    format_file_size,
    cleanup_task
)
from ..services import PDFCompressor, DOCXCompressor

router = APIRouter(prefix="/api", tags=["compress"])


@router.post("/compress")
async def compress_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    上传并压缩文档
    
    支持 PDF 和 DOCX 文件，自动生成三种压缩级别的版本
    """
    # 获取文件信息
    filename = file.filename or "unknown"
    
    # 读取文件内容以获取大小
    content = await file.read()
    file_size = len(content)
    
    # 验证文件
    is_valid, error_msg = validate_file(filename, file_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 生成任务ID和目录
    task_id = generate_task_id()
    task_dir = get_task_dir(task_id)
    
    # 保存上传的文件
    input_path = task_dir / f"original_{filename}"
    async with aiofiles.open(input_path, 'wb') as f:
        await f.write(content)
    
    # 获取原始文件大小
    original_size = get_file_size(input_path)
    
    # 根据文件类型选择处理器
    ext = get_file_extension(filename)
    
    try:
        if ext == ".pdf":
            results = PDFCompressor.compress_pdf_all_levels(
                str(input_path),
                str(task_dir),
                filename
            )
        elif ext == ".docx":
            results = DOCXCompressor.compress_docx_all_levels(
                str(input_path),
                str(task_dir),
                filename
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 构建响应
        files = []
        level_names = {
            "extreme": "极致压缩",
            "medium": "适中压缩", 
            "basic": "基础压缩"
        }
        
        for level, info in results.items():
            if info.get("success"):
                compression_ratio = round((1 - info["size"] / original_size) * 100, 1) if original_size > 0 else 0
                files.append({
                    "level": level,
                    "level_name": level_names.get(level, level),
                    "filename": info["filename"],
                    "size": info["size"],
                    "size_formatted": info["size_formatted"],
                    "compression_ratio": f"{compression_ratio}%",
                    "download_url": f"/api/download/{task_id}/{info['filename']}"
                })
            else:
                files.append({
                    "level": level,
                    "level_name": level_names.get(level, level),
                    "success": False,
                    "error": info.get("error", "压缩失败")
                })
        
        return {
            "success": True,
            "task_id": task_id,
            "original_filename": filename,
            "original_size": original_size,
            "original_size_formatted": format_file_size(original_size),
            "files": files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理失败的任务
        cleanup_task(task_id)
        raise HTTPException(status_code=500, detail=f"处理文件时发生错误: {str(e)}")


@router.get("/download/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    """
    下载压缩后的文件
    """
    from ..utils import TEMP_DIR
    
    file_path = TEMP_DIR / task_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    
    # 确保文件路径安全（防止路径遍历攻击）
    try:
        file_path = file_path.resolve()
        temp_dir = TEMP_DIR.resolve()
        if not str(file_path).startswith(str(temp_dir)):
            raise HTTPException(status_code=403, detail="非法访问")
    except Exception:
        raise HTTPException(status_code=403, detail="非法访问")
    
    # 根据文件扩展名设置媒体类型
    ext = get_file_extension(filename)
    media_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务及其文件
    """
    try:
        cleanup_task(task_id)
        return {"success": True, "message": "任务已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

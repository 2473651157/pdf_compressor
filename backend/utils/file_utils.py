"""文件工具函数"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMP_DIR = BASE_DIR / "temp"

# 允许的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB


def ensure_temp_dir():
    """确保临时目录存在"""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def generate_task_id() -> str:
    """生成唯一任务ID"""
    return str(uuid.uuid4())[:8]


def get_task_dir(task_id: str) -> Path:
    """获取任务目录路径"""
    task_dir = TEMP_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    验证文件是否有效
    返回: (是否有效, 错误信息)
    """
    if not filename:
        return False, "文件名为空"
    
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件类型: {ext}，仅支持 PDF 和 DOCX"
    
    if file_size > MAX_FILE_SIZE:
        return False, f"文件过大: {file_size / 1024 / 1024:.1f}MB，最大支持 200MB"
    
    return True, ""


def get_file_extension(filename: str) -> str:
    """获取文件扩展名(小写)"""
    return Path(filename).suffix.lower()


def get_output_filename(original_name: str, level: str) -> str:
    """生成输出文件名"""
    stem = Path(original_name).stem
    ext = Path(original_name).suffix
    level_names = {
        "extreme": "极致压缩",
        "medium": "适中压缩",
        "basic": "基础压缩"
    }
    return f"{stem}_{level_names.get(level, level)}{ext}"


def cleanup_task(task_id: str):
    """清理任务目录"""
    task_dir = TEMP_DIR / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir)


def get_file_size(file_path: Path) -> int:
    """获取文件大小(字节)"""
    return file_path.stat().st_size if file_path.exists() else 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / 1024 / 1024:.2f} MB"

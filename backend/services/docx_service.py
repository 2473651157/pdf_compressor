"""DOCX处理服务"""
import os
import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import re

from .image_service import ImageCompressor, CompressionLevel


class DOCXCompressor:
    """DOCX压缩器"""
    
    # 支持的图片格式
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif'}
    
    @staticmethod
    def compress_docx(
        input_path: str,
        output_path: str,
        level: CompressionLevel
    ) -> bool:
        """
        压缩DOCX文件中的图片
        
        DOCX文件实际上是ZIP格式，图片存储在word/media/目录下
        
        Args:
            input_path: 输入DOCX路径
            output_path: 输出DOCX路径
            level: 压缩级别
            
        Returns:
            是否成功
        """
        temp_dir = None
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            extract_dir = os.path.join(temp_dir, "extracted")
            
            # 解压DOCX文件
            with zipfile.ZipFile(input_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 处理媒体文件夹中的图片
            media_dir = os.path.join(extract_dir, "word", "media")
            if os.path.exists(media_dir):
                DOCXCompressor._compress_media_images(media_dir, level)
            
            # 重新打包为DOCX
            DOCXCompressor._create_docx(extract_dir, output_path)
            
            return True
            
        except Exception as e:
            print(f"DOCX压缩失败: {e}")
            return False
            
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @staticmethod
    def _compress_media_images(media_dir: str, level: CompressionLevel):
        """
        压缩media目录中的所有图片
        """
        for filename in os.listdir(media_dir):
            file_path = os.path.join(media_dir, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in DOCXCompressor.IMAGE_EXTENSIONS:
                continue
            
            try:
                # 读取图片
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                # 跳过太小的图片
                if len(image_data) < 1024:
                    continue
                
                # 压缩图片
                compressed_data, output_format = ImageCompressor.compress_image(
                    image_data,
                    level,
                    ext[1:]  # 去掉点号
                )
                
                # 只有压缩后更小时才替换
                if len(compressed_data) < len(image_data):
                    # 更新为JPEG格式
                    new_filename = os.path.splitext(filename)[0] + ".jpeg"
                    new_path = os.path.join(media_dir, new_filename)
                    
                    # 写入压缩后的图片
                    with open(new_path, 'wb') as f:
                        f.write(compressed_data)
                    
                    # 如果文件名变了，删除原文件
                    if new_path != file_path:
                        os.remove(file_path)
                        
                        # 更新文档中的引用
                        DOCXCompressor._update_image_references(
                            os.path.dirname(media_dir),  # word目录
                            filename,
                            new_filename
                        )
                        
            except Exception as e:
                print(f"处理图片 {filename} 时出错: {e}")
                continue
    
    @staticmethod
    def _update_image_references(word_dir: str, old_name: str, new_name: str):
        """
        更新文档中的图片引用
        
        需要更新的文件:
        - word/_rels/document.xml.rels
        - [Content_Types].xml
        """
        # 更新 document.xml.rels
        rels_path = os.path.join(word_dir, "_rels", "document.xml.rels")
        if os.path.exists(rels_path):
            DOCXCompressor._replace_in_file(rels_path, old_name, new_name)
        
        # 更新 [Content_Types].xml
        content_types_path = os.path.join(os.path.dirname(word_dir), "[Content_Types].xml")
        if os.path.exists(content_types_path):
            # 确保JPEG类型存在
            with open(content_types_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加JPEG类型（如果不存在）
            if 'Extension="jpeg"' not in content and 'Extension="jpg"' not in content:
                # 在</Types>前添加
                jpeg_type = '<Default Extension="jpeg" ContentType="image/jpeg"/>'
                content = content.replace('</Types>', f'{jpeg_type}</Types>')
                
                with open(content_types_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 替换文件引用
            DOCXCompressor._replace_in_file(content_types_path, old_name, new_name)
    
    @staticmethod
    def _replace_in_file(file_path: str, old_text: str, new_text: str):
        """在文件中替换文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = content.replace(old_text, new_text)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"更新文件引用失败 {file_path}: {e}")
    
    @staticmethod
    def _create_docx(source_dir: str, output_path: str):
        """
        将目录重新打包为DOCX文件
        """
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
    
    @staticmethod
    def compress_docx_all_levels(
        input_path: str,
        output_dir: str,
        original_name: str
    ) -> dict:
        """
        使用所有压缩级别处理DOCX
        
        Args:
            input_path: 输入DOCX路径
            output_dir: 输出目录
            original_name: 原始文件名
            
        Returns:
            各级别输出文件信息
        """
        from ..utils import get_output_filename, get_file_size, format_file_size
        
        results = {}
        output_dir = Path(output_dir)
        
        for level in CompressionLevel:
            output_name = get_output_filename(original_name, level.value)
            output_path = output_dir / output_name
            
            success = DOCXCompressor.compress_docx(
                input_path,
                str(output_path),
                level
            )
            
            if success:
                file_size = get_file_size(output_path)
                results[level.value] = {
                    "filename": output_name,
                    "path": str(output_path),
                    "size": file_size,
                    "size_formatted": format_file_size(file_size),
                    "success": True
                }
            else:
                results[level.value] = {
                    "filename": output_name,
                    "success": False,
                    "error": "压缩失败"
                }
        
        return results

"""PDF处理服务"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional
from io import BytesIO

from .image_service import ImageCompressor, CompressionLevel


class PDFCompressor:
    """PDF压缩器"""
    
    @staticmethod
    def compress_pdf(
        input_path: str,
        output_path: str,
        level: CompressionLevel
    ) -> bool:
        """
        压缩PDF文件中的图片
        
        Args:
            input_path: 输入PDF路径
            output_path: 输出PDF路径
            level: 压缩级别
            
        Returns:
            是否成功
        """
        try:
            # 打开PDF文档
            doc = fitz.open(input_path)
            
            # 遍历所有页面
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 获取页面中的所有图片
                image_list = page.get_images(full=True)
                
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]  # 图片的xref引用
                    
                    try:
                        # 提取图片
                        base_image = doc.extract_image(xref)
                        if base_image is None:
                            continue
                        
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # 跳过太小的图片(可能是图标等)
                        if len(image_bytes) < 1024:  # 小于1KB
                            continue
                        
                        # 压缩图片
                        compressed_data, _ = ImageCompressor.compress_image(
                            image_bytes, 
                            level,
                            image_ext
                        )
                        
                        # 只有当压缩后更小时才替换
                        if len(compressed_data) < len(image_bytes):
                            # 替换PDF中的图片
                            doc.update_stream(xref, compressed_data)
                            
                    except Exception as e:
                        # 单个图片处理失败不影响整体
                        print(f"处理图片 {xref} 时出错: {e}")
                        continue
            
            # 保存压缩后的PDF
            doc.save(
                output_path,
                garbage=4,  # 清理未使用的对象
                deflate=True,  # 压缩流
                clean=True,  # 清理内容流
            )
            doc.close()
            
            return True
            
        except Exception as e:
            print(f"PDF压缩失败: {e}")
            return False
    
    @staticmethod
    def compress_pdf_all_levels(
        input_path: str,
        output_dir: str,
        original_name: str
    ) -> dict:
        """
        使用所有压缩级别处理PDF
        
        Args:
            input_path: 输入PDF路径
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
            
            success = PDFCompressor.compress_pdf(
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

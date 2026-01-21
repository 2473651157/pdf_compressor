"""PDF处理服务"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional
from io import BytesIO
from PIL import Image, ImageOps

from .image_service import ImageCompressor, CompressionLevel, COMPRESSION_SETTINGS


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
            settings = COMPRESSION_SETTINGS[level]
            
            # 记录已处理的xref，避免重复处理
            processed_xrefs = set()
            
            # 遍历所有页面
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 获取页面中的所有图片
                image_list = page.get_images(full=True)
                
                for img_info in image_list:
                    xref = img_info[0]  # 图片的xref引用
                    
                    # 跳过已处理的图片
                    if xref in processed_xrefs:
                        continue
                    processed_xrefs.add(xref)
                    
                    try:
                        # 提取图片
                        base_image = doc.extract_image(xref)
                        if base_image is None:
                            continue
                        
                        image_bytes = base_image["image"]
                        image_ext = base_image.get("ext", "jpeg")
                        
                        # 跳过太小的图片(可能是图标等)
                        if len(image_bytes) < 4096:  # 小于4KB
                            continue
                        
                        # 使用PIL打开图片
                        try:
                            pil_image = Image.open(BytesIO(image_bytes))
                        except Exception:
                            continue
                        
                        # 处理EXIF方向
                        try:
                            pil_image = ImageOps.exif_transpose(pil_image)
                        except Exception:
                            pass
                        
                        orig_width, orig_height = pil_image.size
                        
                        # 基础压缩：只压缩质量，不缩小尺寸
                        if level == CompressionLevel.BASIC:
                            max_width = max(orig_width, settings["max_width"])
                            max_height = max(orig_height, settings["max_height"])
                        else:
                            max_width = settings["max_width"]
                            max_height = settings["max_height"]
                        
                        # 转换颜色模式
                        if pil_image.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', pil_image.size, (255, 255, 255))
                            background.paste(pil_image, mask=pil_image.split()[-1])
                            pil_image = background
                        elif pil_image.mode == 'P':
                            pil_image = pil_image.convert('RGBA')
                            background = Image.new('RGB', pil_image.size, (255, 255, 255))
                            background.paste(pil_image, mask=pil_image.split()[-1])
                            pil_image = background
                        elif pil_image.mode == 'CMYK':
                            pil_image = pil_image.convert('RGB')
                        elif pil_image.mode not in ('RGB', 'L'):
                            pil_image = pil_image.convert('RGB')
                        
                        # 灰度图保持灰度
                        if pil_image.mode == 'L':
                            pil_image = pil_image.convert('RGB')
                        
                        # 调整尺寸（仅当超过限制时）
                        if orig_width > max_width or orig_height > max_height:
                            ratio = min(max_width / orig_width, max_height / orig_height)
                            new_width = max(1, int(orig_width * ratio))
                            new_height = max(1, int(orig_height * ratio))
                            pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
                        
                        # 压缩为JPEG
                        output_buffer = BytesIO()
                        pil_image.save(
                            output_buffer, 
                            format="JPEG", 
                            quality=settings["quality"],
                            optimize=True,
                            subsampling=settings.get("subsampling", 2)
                        )
                        compressed_data = output_buffer.getvalue()
                        
                        # 只有当压缩后更小时才替换
                        if len(compressed_data) < len(image_bytes):
                            # 创建新的图片对象插入
                            try:
                                # 获取图片在页面中的位置信息
                                for img_ref in page.get_images(full=True):
                                    if img_ref[0] == xref:
                                        # 使用 _updateStream 更新图片数据
                                        doc._updateStream(xref, compressed_data)
                                        break
                            except Exception as e:
                                print(f"替换图片失败: {e}")
                                continue
                            
                    except Exception as e:
                        # 单个图片处理失败不影响整体
                        print(f"处理图片 {xref} 时出错: {e}")
                        continue
            
            # 保存压缩后的PDF
            doc.save(
                output_path,
                garbage=4,          # 最高级别垃圾回收
                deflate=True,       # 压缩流
                deflate_images=True,# 压缩图片流
                deflate_fonts=True, # 压缩字体流
                clean=True,         # 清理内容流
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
        import shutil
        from ..utils import get_output_filename, get_file_size, format_file_size
        
        results = {}
        output_dir = Path(output_dir)
        original_size = get_file_size(Path(input_path))
        
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
                
                # 如果压缩后文件更大，使用原文件
                if file_size >= original_size:
                    shutil.copy2(input_path, output_path)
                    file_size = original_size
                
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

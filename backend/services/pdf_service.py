"""PDF处理服务"""
import fitz  # PyMuPDF
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageOps
import tempfile
import os
import shutil

from .image_service import CompressionLevel, COMPRESSION_SETTINGS


class PDFCompressor:
    """PDF压缩器"""
    
    @staticmethod
    def compress_pdf(
        input_path: str,
        output_path: str,
        level: CompressionLevel
    ) -> bool:
        """
        压缩PDF文件中的图片 - 通过重建PDF实现真正的压缩
        """
        try:
            settings = COMPRESSION_SETTINGS[level]
            quality = settings["quality"]
            max_width = settings["max_width"]
            max_height = settings["max_height"]
            
            # 打开源PDF
            doc = fitz.open(input_path)
            
            # 已处理的图片xref
            processed = set()
            
            # 遍历所有页面处理图片
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                for img_info in image_list:
                    xref = img_info[0]
                    
                    if xref in processed:
                        continue
                    processed.add(xref)
                    
                    try:
                        # 提取图片
                        pix = fitz.Pixmap(doc, xref)
                        
                        # 跳过太小的图片
                        if pix.width * pix.height < 10000:  # 小于100x100像素
                            continue
                        
                        # 转换为PIL图像
                        if pix.n > 3:  # CMYK或带alpha
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        
                        img_data = pix.tobytes("jpeg")
                        pil_image = Image.open(BytesIO(img_data))
                        
                        orig_width, orig_height = pil_image.size
                        original_size = len(img_data)
                        
                        # 根据压缩级别决定目标尺寸
                        if level == CompressionLevel.BASIC:
                            # 基础压缩：不缩小，只降低质量
                            target_width = orig_width
                            target_height = orig_height
                        else:
                            # 计算目标尺寸
                            if orig_width > max_width or orig_height > max_height:
                                ratio = min(max_width / orig_width, max_height / orig_height)
                                target_width = max(1, int(orig_width * ratio))
                                target_height = max(1, int(orig_height * ratio))
                            else:
                                target_width = orig_width
                                target_height = orig_height
                        
                        # 调整尺寸
                        if target_width != orig_width or target_height != orig_height:
                            pil_image = pil_image.resize(
                                (target_width, target_height), 
                                Image.LANCZOS
                            )
                        
                        # 确保是RGB模式
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        
                        # 压缩图片
                        output_buffer = BytesIO()
                        pil_image.save(
                            output_buffer,
                            format="JPEG",
                            quality=quality,
                            optimize=True
                        )
                        compressed_data = output_buffer.getvalue()
                        
                        # 只有压缩后更小才替换
                        if len(compressed_data) < original_size * 0.95:
                            # 创建新的Pixmap并替换
                            new_pix = fitz.Pixmap(compressed_data)
                            
                            # 更新图片数据
                            doc.update_stream(xref, compressed_data)
                            
                            # 同时更新xref对象的属性
                            try:
                                doc.xref_set_key(xref, "Filter", "/DCTDecode")
                                doc.xref_set_key(xref, "ColorSpace", "/DeviceRGB")
                                doc.xref_set_key(xref, "Width", str(target_width))
                                doc.xref_set_key(xref, "Height", str(target_height))
                                doc.xref_set_key(xref, "BitsPerComponent", "8")
                            except Exception:
                                pass
                        
                    except Exception as e:
                        print(f"处理图片 {xref} 出错: {e}")
                        continue
            
            # 保存压缩后的PDF
            doc.save(
                output_path,
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                clean=True,
                pretty=False,
                linear=False,
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
        """使用所有压缩级别处理PDF"""
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
                
                # 如果压缩后文件更大或相等，使用原文件
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

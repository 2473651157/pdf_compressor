"""图片压缩服务"""
from enum import Enum
from io import BytesIO
from PIL import Image
from typing import Tuple, Optional


class CompressionLevel(str, Enum):
    """压缩级别枚举"""
    EXTREME = "extreme"  # 极致压缩
    MEDIUM = "medium"    # 适中压缩
    BASIC = "basic"      # 基础压缩


# 压缩参数配置
COMPRESSION_SETTINGS = {
    CompressionLevel.EXTREME: {
        "quality": 35,
        "max_width": 600,
        "max_height": 800,
    },
    CompressionLevel.MEDIUM: {
        "quality": 65,
        "max_width": 1000,
        "max_height": 1400,
    },
    CompressionLevel.BASIC: {
        "quality": 85,
        "max_width": 1600,
        "max_height": 2200,
    },
}


class ImageCompressor:
    """图片压缩器"""
    
    @staticmethod
    def get_settings(level: CompressionLevel) -> dict:
        """获取压缩级别对应的设置"""
        return COMPRESSION_SETTINGS.get(level, COMPRESSION_SETTINGS[CompressionLevel.MEDIUM])
    
    @staticmethod
    def compress_image(
        image_data: bytes,
        level: CompressionLevel,
        original_format: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        压缩图片
        
        Args:
            image_data: 原始图片数据
            level: 压缩级别
            original_format: 原始格式 (可选)
            
        Returns:
            (压缩后的图片数据, 输出格式)
        """
        settings = ImageCompressor.get_settings(level)
        
        # 打开图片
        img = Image.open(BytesIO(image_data))
        
        # 转换模式 (处理RGBA等)
        if img.mode in ('RGBA', 'LA', 'P'):
            # 对于有透明通道的图片，转为RGB并填充白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 调整尺寸
        img = ImageCompressor._resize_image(
            img, 
            settings["max_width"], 
            settings["max_height"]
        )
        
        # 压缩并输出
        output = BytesIO()
        img.save(
            output, 
            format="JPEG", 
            quality=settings["quality"],
            optimize=True
        )
        
        return output.getvalue(), "jpeg"
    
    @staticmethod
    def _resize_image(img: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """
        按最大宽高等比例缩放图片
        """
        width, height = img.size
        
        # 如果图片已经小于限制，不进行缩放
        if width <= max_width and height <= max_height:
            return img
        
        # 计算缩放比例
        ratio_w = max_width / width
        ratio_h = max_height / height
        ratio = min(ratio_w, ratio_h)
        
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # 使用高质量缩放
        return img.resize((new_width, new_height), Image.LANCZOS)
    
    @staticmethod
    def compress_image_file(
        input_path: str,
        output_path: str,
        level: CompressionLevel
    ) -> bool:
        """
        压缩图片文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            level: 压缩级别
            
        Returns:
            是否成功
        """
        try:
            with open(input_path, 'rb') as f:
                image_data = f.read()
            
            compressed_data, _ = ImageCompressor.compress_image(image_data, level)
            
            with open(output_path, 'wb') as f:
                f.write(compressed_data)
            
            return True
        except Exception as e:
            print(f"压缩图片失败: {e}")
            return False

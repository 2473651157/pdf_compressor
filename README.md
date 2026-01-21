# DocPress - 智能文档压缩工具

一个在线文档压缩网站，支持 PDF 和 Word (DOCX) 文件压缩，提供三种压缩级别选择。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特性

- **多格式支持**: 支持 PDF 和 DOCX 文件压缩
- **三种压缩级别**:
  - 🔥 **极致压缩**: 最小文件体积，适合网络传输
  - ⚖️ **适中压缩**: 平衡质量与大小
  - 🎨 **基础压缩**: 保持较高质量，轻微压缩
- **智能处理**: 自动检测并压缩文档中的图片
- **拖拽上传**: 支持拖放文件或点击选择
- **实时进度**: 显示上传和处理进度
- **一键下载**: 同时生成三个版本供选择下载

## 🛠️ 技术栈

### 后端
- **FastAPI** - 高性能 Python Web 框架
- **PyMuPDF** - PDF 文档处理
- **Pillow** - 图片压缩处理
- **python-docx** - Word 文档处理

### 前端
- **Vanilla JavaScript** - 原生 JS，无框架依赖
- **Modern CSS** - CSS3 动画与渐变效果

## 📦 安装

### 环境要求
- Python 3.8+
- pip

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/2473651157/pdf_compressor.git
cd pdf_compressor
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动服务
```bash
python run.py
```

4. 访问应用
```
http://localhost:8000
```

## 📁 项目结构

```
doc-compressor/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── routers/
│   │   └── compress.py      # 压缩 API 路由
│   ├── services/
│   │   ├── pdf_service.py   # PDF 处理服务
│   │   ├── docx_service.py  # DOCX 处理服务
│   │   └── image_service.py # 图片压缩服务
│   └── utils/
│       └── file_utils.py    # 文件工具函数
├── frontend/
│   ├── index.html           # 主页面
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       └── app.js           # 前端交互逻辑
├── temp/                    # 临时文件目录
├── requirements.txt         # Python 依赖
└── run.py                   # 启动脚本
```

## 🔧 API 接口

### 上传并压缩文档
```
POST /api/compress
Content-Type: multipart/form-data

参数: file - 上传的文件 (PDF/DOCX)

返回: {
  "success": true,
  "task_id": "xxx",
  "original_filename": "document.pdf",
  "original_size_formatted": "10.5 MB",
  "files": [
    {
      "level": "extreme",
      "level_name": "极致压缩",
      "filename": "document_极致压缩.pdf",
      "size_formatted": "2.1 MB",
      "compression_ratio": "80%",
      "download_url": "/api/download/xxx/document_极致压缩.pdf"
    },
    ...
  ]
}
```

### 下载压缩文件
```
GET /api/download/{task_id}/{filename}
```

### 健康检查
```
GET /api/health
```

## ⚙️ 压缩参数

| 级别 | JPEG 质量 | 最大分辨率 | 色度子采样 |
|------|-----------|------------|------------|
| 极致 | 45% | 1024px | 4:2:2 |
| 适中 | 70% | 1600px | 4:2:0 |
| 基础 | 85% | 2400px | 4:4:4 |

## 📝 更新日志

- **v1.5** - 修复图片失真问题，优化颜色模式处理
- **v1.4** - 调整压缩参数，添加 EXIF 方向处理
- **v1.3** - 修复文件不减反增的 bug
- **v1.2** - 修复 PDF 压缩效果问题
- **v1.1** - 文件大小限制从 50MB 提升至 200MB
- **v1.0** - 初始版本

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

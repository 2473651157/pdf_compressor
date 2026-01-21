/**
 * DocPress - 文档压缩前端应用
 */

// API 基础路径
const API_BASE = '/api';

// DOM 元素引用
const elements = {
    uploadSection: document.getElementById('uploadSection'),
    uploadZone: document.getElementById('uploadZone'),
    fileInput: document.getElementById('fileInput'),
    progressSection: document.getElementById('progressSection'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    fileIcon: document.getElementById('fileIcon'),
    progressBar: document.getElementById('progressBar'),
    progressStatus: document.getElementById('progressStatus'),
    resultsSection: document.getElementById('resultsSection'),
    originalName: document.getElementById('originalName'),
    originalSize: document.getElementById('originalSize'),
    resultsGrid: document.getElementById('resultsGrid'),
    btnNew: document.getElementById('btnNew'),
    errorSection: document.getElementById('errorSection'),
    errorMessage: document.getElementById('errorMessage'),
    btnRetry: document.getElementById('btnRetry')
};

// 状态管理
let currentTaskId = null;

/**
 * 初始化应用
 */
function init() {
    setupEventListeners();
}

/**
 * 设置事件监听
 */
function setupEventListeners() {
    // 点击上传区域
    elements.uploadZone.addEventListener('click', () => {
        elements.fileInput.click();
    });

    // 文件选择变化
    elements.fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });

    // 拖放事件
    elements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.add('drag-over');
    });

    elements.uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('drag-over');
    });

    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('drag-over');
        
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });

    // 新建压缩
    elements.btnNew.addEventListener('click', resetToUpload);

    // 重试
    elements.btnRetry.addEventListener('click', resetToUpload);
}

/**
 * 处理文件上传
 */
async function handleFileUpload(file) {
    // 验证文件类型
    const ext = file.name.toLowerCase().split('.').pop();
    if (!['pdf', 'docx'].includes(ext)) {
        showError('不支持的文件类型，请上传 PDF 或 DOCX 文件');
        return;
    }

    // 验证文件大小 (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showError('文件过大，最大支持 50MB');
        return;
    }

    // 显示进度界面
    showProgress(file);

    // 上传文件
    try {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        
        // 上传进度
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 50);
                updateProgress(percent, '正在上传...');
            }
        });

        // 完成处理
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                updateProgress(100, '压缩完成！');
                
                setTimeout(() => {
                    showResults(response);
                }, 500);
            } else {
                let errorMsg = '上传失败';
                try {
                    const errResponse = JSON.parse(xhr.responseText);
                    errorMsg = errResponse.detail || errorMsg;
                } catch (e) {}
                showError(errorMsg);
            }
        });

        // 错误处理
        xhr.addEventListener('error', () => {
            showError('网络错误，请检查连接后重试');
        });

        // 开始请求
        xhr.open('POST', `${API_BASE}/compress`);
        xhr.send(formData);

        // 模拟压缩进度
        simulateProcessingProgress();

    } catch (error) {
        showError(error.message || '上传失败，请重试');
    }
}

/**
 * 模拟处理进度
 */
function simulateProcessingProgress() {
    let progress = 50;
    const interval = setInterval(() => {
        if (progress < 95) {
            progress += Math.random() * 5;
            updateProgress(Math.min(progress, 95), '正在压缩...');
        } else {
            clearInterval(interval);
        }
    }, 300);

    // 保存 interval ID 以便清理
    window.processingInterval = interval;
}

/**
 * 显示进度界面
 */
function showProgress(file) {
    hideAllSections();
    elements.progressSection.style.display = 'block';

    // 设置文件信息
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);

    // 设置文件图标样式
    const ext = file.name.toLowerCase().split('.').pop();
    elements.fileIcon.className = 'file-icon ' + ext;

    // 重置进度
    updateProgress(0, '准备上传...');
}

/**
 * 更新进度
 */
function updateProgress(percent, status) {
    elements.progressBar.style.width = `${percent}%`;
    elements.progressStatus.textContent = status;
}

/**
 * 显示结果
 */
function showResults(response) {
    // 清理处理进度
    if (window.processingInterval) {
        clearInterval(window.processingInterval);
    }

    hideAllSections();
    elements.resultsSection.style.display = 'block';

    // 设置原始文件信息
    elements.originalName.textContent = response.original_filename;
    elements.originalSize.textContent = response.original_size_formatted;

    // 保存任务ID
    currentTaskId = response.task_id;

    // 生成结果卡片
    const levelConfigs = {
        extreme: {
            name: '极致压缩',
            desc: '最小文件体积',
            class: 'extreme'
        },
        medium: {
            name: '适中压缩',
            desc: '平衡质量与大小',
            class: 'medium'
        },
        basic: {
            name: '基础压缩',
            desc: '保持较高质量',
            class: 'basic'
        }
    };

    elements.resultsGrid.innerHTML = response.files.map(file => {
        const config = levelConfigs[file.level] || {};
        
        if (file.success === false) {
            return `
                <div class="result-card ${config.class}">
                    <div class="level-name">${config.name}</div>
                    <div class="level-desc">${config.desc}</div>
                    <div class="compressed-size">失败</div>
                    <p style="color: var(--text-muted); font-size: 0.85rem;">${file.error}</p>
                </div>
            `;
        }

        return `
            <div class="result-card ${config.class}">
                <div class="level-name">${config.name}</div>
                <div class="level-desc">${config.desc}</div>
                <div class="compressed-size">${file.size_formatted}</div>
                <div class="compression-ratio">↓ ${file.compression_ratio}</div>
                <button class="btn-download" onclick="downloadFile('${file.download_url}', '${file.filename}')">
                    <svg viewBox="0 0 24 24" fill="none">
                        <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M7 10L12 15L17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    下载
                </button>
            </div>
        `;
    }).join('');
}

/**
 * 下载文件
 */
function downloadFile(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

/**
 * 显示错误
 */
function showError(message) {
    // 清理处理进度
    if (window.processingInterval) {
        clearInterval(window.processingInterval);
    }

    hideAllSections();
    elements.errorSection.style.display = 'block';
    elements.errorMessage.textContent = message;
}

/**
 * 重置到上传界面
 */
function resetToUpload() {
    // 清理任务
    if (currentTaskId) {
        fetch(`${API_BASE}/task/${currentTaskId}`, { method: 'DELETE' }).catch(() => {});
        currentTaskId = null;
    }

    hideAllSections();
    elements.uploadSection.style.display = 'block';
    
    // 重置文件输入
    elements.fileInput.value = '';
}

/**
 * 隐藏所有区域
 */
function hideAllSections() {
    elements.uploadSection.style.display = 'none';
    elements.progressSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    elements.errorSection.style.display = 'none';
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes < 1024) {
        return bytes + ' B';
    } else if (bytes < 1024 * 1024) {
        return (bytes / 1024).toFixed(1) + ' KB';
    } else {
        return (bytes / 1024 / 1024).toFixed(2) + ' MB';
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', init);

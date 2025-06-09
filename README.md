# AI视频动作标注工具

> 基于PyQt6的专业面部动作视频标注工具，支持实时视频录制、精确动作标注和数据集导出

## 📋 项目概述

AI视频动作标注工具是一个集成了视频录制、标注编辑和数据集导出功能的专业应用程序。主要用于面部动作数据的采集、标注和机器学习数据集的生成。

### 🌟 核心功能

- **📹 实时视频录制**：支持WebSocket视频流接收和ROI区域选择
- **🎯 精确动作标注**：45种面部动作类型，支持动作强度和时间线编辑
- **📊 数据集导出**：自动生成训练用的图像和标注文件数据集
- **🎮 逐帧控制**：精确的帧级别播放控制和定位
- **💾 项目管理**：完整的项目保存、加载和版本管理

### 🎭 支持的面部动作类型

包含45种标准面部动作，涵盖：
- 脸颊动作（鼓起、收缩）
- 下巴动作（张嘴、前伸、左右移动）
- 鼻部动作（鼻翼上提）
- 嘴部基础动作（漏斗形、撅嘴、左右移动等）
- 嘴唇精细动作（上下唇内卷、耸肩）
- 微笑相关动作（左右嘴角上扬、下垂）
- 舌头动作（12种不同方向和形状）

## 🚀 快速开始

### 系统要求

- **操作系统**：Windows 10/11、macOS 10.14+、Ubuntu 18.04+
- **Python版本**：3.8 - 3.11
- **内存**：建议8GB以上
- **存储空间**：至少2GB可用空间（用于数据集导出）
- **摄像头**：（可选）用于实时视频录制

### 环境部署

#### 方法一：使用requirements.txt（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd video-annotation-tool

# 2. 创建Python虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 运行应用程序
python app.py
```

#### 方法二：手动安装依赖

```bash
# 核心依赖
pip install PyQt6>=6.4.0
pip install opencv-python>=4.7.0
pip install numpy>=1.21.0
pip install websocket-client>=1.4.0

# 可选依赖（用于更好的性能）
pip install Pillow>=9.0.0
```

### 依赖说明

| 库名称 | 版本要求 | 用途 |
|--------|----------|------|
| PyQt6 | >=6.4.0 | GUI框架，视频播放 |
| opencv-python | >=4.7.0 | 视频处理，图像操作 |
| numpy | >=1.21.0 | 数值计算，图像数据处理 |
| websocket-client | >=1.4.0 | WebSocket视频流接收 |
| Pillow | >=9.0.0 | 图像格式支持（可选） |

## 📖 使用指南

### 1. 视频录制模式

1. **连接设置**：
   - 在"WebSocket连接设置"中输入设备IP地址（如：192.168.31.101）
   - 点击"连接"按钮建立WebSocket连接

2. **ROI区域选择**（可选）：
   - 勾选"启用ROI选择"
   - 用鼠标拖拽选择录制的感兴趣区域
   - 只有选中区域会被录制

3. **开始录制**：
   - 设置保存路径或点击"生成文件名"
   - 点击"开始录制"按钮
   - 录制完成后可自动切换到标注页面

### 2. 视频标注模式

1. **加载视频**：
   - 点击"选择视频文件"或直接从录制页面切换过来
   - 支持多种视频格式（MP4、AVI、MOV等）

2. **标注操作**：
   - 使用播放控制观看视频
   - 利用逐帧控制精确定位（A/D键快速前后移动）
   - 标记起点（S键）和终点（E键）
   - 选择面部动作类型和强度
   - 保存标注到项目

3. **快捷键**：
   - `空格`：播放/暂停
   - `A`：后退指定帧数
   - `D`：前进指定帧数
   - `S`：标记起点
   - `E`：标记终点

### 3. 数据集导出

1. **导出准备**：
   - 确保有标注数据
   - 选择输出目录（建议使用英文路径）

2. **导出格式**：
   - `images/`：标注片段的每一帧图像（JPEG格式）
   - `labels/`：对应的45维标注文件（TXT格式）
   - `dataset_info.json`：数据集元信息

3. **标注文件格式**：
   ```
   每个TXT文件包含45行浮点数（0.0-1.0）
   每行对应一个面部动作的强度值
   动作强度随时间线性增长（y=x）
   ```

## 🔧 项目结构

```
video-annotation-tool/
├── app.py                   # 应用程序入口
├── main_window.py          # 主窗口
├── annotation_page.py      # 标注页面
├── recording_page.py       # 录制页面
├── annotation_manager.py   # 标注数据管理
├── video_player.py         # 视频播放器
├── dataset_exporter.py     # 数据集导出器
├── models.py               # 数据模型
├── styles.py               # UI样式和配置
├── utils.py                # 工具函数
├── widgets/                # 自定义控件
│   ├── __init__.py
│   ├── timeline_widget.py  # 时间线控件
│   ├── annotation_dialog.py # 标注对话框
│   └── roi_video_widget.py # ROI视频控件
├── requirements.txt        # 依赖列表
├── check_project.py        # 项目诊断脚本
└── README.md              # 项目文档
```

## 🛠️ 故障排除

### 常见问题解决

#### 1. 导入错误问题
```bash
# 运行项目诊断脚本
python check_project.py
```
该脚本会检查：
- 文件完整性
- Python语法错误
- 模块导入问题
- 依赖安装状态

#### 2. PyQt6安装问题
```bash
# 卸载旧版本并重新安装
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6
```

#### 3. OpenCV视频编解码问题
```bash
# 重新安装带有完整编解码器的版本
pip uninstall opencv-python
pip install opencv-python-headless
```

#### 4. WebSocket连接失败
- 检查网络连接和防火墙设置
- 确认目标设备IP地址和端口正确
- 验证WebSocket服务端是否正常运行

#### 5. 中文路径问题
- 数据集导出时建议使用英文路径
- 已内置中文路径支持，使用cv2.imencode解决编码问题

### 平台特定问题

#### Windows
```bash
# 如果遇到DLL加载问题
pip install pywin32
```

#### macOS
```bash
# 如果遇到权限问题
sudo pip install PyQt6
```

#### Linux
```bash
# 安装系统依赖
sudo apt-get install python3-pyqt6 python3-opencv
```

## 📈 性能优化建议

### 1. 硬件优化
- **CPU**：Intel i5/AMD Ryzen 5及以上
- **GPU**：（可选）支持CUDA的显卡用于加速视频处理
- **SSD**：使用SSD存储提高数据集导出速度

### 2. 软件优化
```python
# 在dataset_exporter.py中调整图像质量
encode_params = [
    cv2.IMWRITE_JPEG_QUALITY, 85,  # 降低到85提高速度
    cv2.IMWRITE_JPEG_OPTIMIZE, 1,
]
```

### 3. 内存优化
- 处理大型视频时，考虑分段标注
- 定期清理标注列表，避免内存占用过多

## 🤝 开发指南

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行代码检查
flake8 .
black .

# 运行测试
pytest tests/
```

### 添加新的面部动作

1. 在`styles.py`的`FacialActionConfig`中添加新动作：
```python
# 添加到ALL_LABELS列表
ALL_LABELS = [
    # ... 现有动作
    "newAction",  # 新动作英文标签
]

# 添加中文映射
LABEL_MAPPING = {
    # ... 现有映射
    "newAction": "新动作中文名",
}

# 添加颜色配置
FACIAL_ACTION_COLORS = {
    # ... 现有颜色
    "newAction": "#FF5733",
}
```

2. 更新数据集导出器以支持新的动作维度

### 自定义控件开发

在`widgets/`目录下创建新控件：
```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

class CustomWidget(QWidget):
    # 自定义信号
    custom_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 实现自定义控件逻辑
```

## 📄 许可证

本项目采用MIT许可证。详情请参阅[LICENSE](LICENSE)文件。

## 🙋 支持与反馈

### 获取帮助
- 提交Issue：[GitHub Issues](https://github.com/your-repo/issues)
- 查看Wiki：[项目Wiki](https://github.com/your-repo/wiki)
- 运行诊断：`python check_project.py`

### 贡献代码
1. Fork本项目
2. 创建功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 创建Pull Request

### 版本历史
- **v2.0.0** - 面部动作标注版本，支持45种动作类型
- **v1.5.0** - 添加ROI选择和逐帧控制
- **v1.0.0** - 基础视频标注功能

---

## 🎯 未来规划

- [ ] 支持批量视频处理
- [ ] 添加自动标注功能（AI辅助）
- [ ] 集成更多视频格式支持
- [ ] 添加标注数据统计分析
- [ ] 支持多人协作标注
- [ ] 移动端应用开发

**让视频标注变得简单高效！** 🚀
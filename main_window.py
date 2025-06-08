"""
主应用程序窗口 - 支持视频录制和标注两个页面
"""
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QToolBar, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence, QIcon

# 导入页面组件
try:
    from recording_page import RecordingPage
    from annotation_page import AnnotationPage
    from styles import StyleSheet, ColorPalette
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有模块文件都在正确位置")
    sys.exit(1)


class VideoAnnotationMainWindow(QMainWindow):
    """主应用程序窗口"""

    def __init__(self):
        super().__init__()

        # 页面组件
        self.recording_page = None
        self.annotation_page = None
        self.tab_widget = None

        # 设置
        self.settings = QSettings("VideoAnnotationTool", "Settings")

        try:
            self.setup_ui()
            self.setup_connections()
            self.load_settings()
            self.apply_theme()
        except Exception as e:
            print(f"初始化失败: {e}")
            raise

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("AI视频动作标注工具")
        self.setGeometry(100, 100, 1600, 900)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        main_layout.addWidget(self.tab_widget)

        # 创建页面
        self.create_pages()

        # 创建菜单栏、工具栏和状态栏
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()

    def create_pages(self):
        """创建页面"""
        # 视频录制页面
        self.recording_page = RecordingPage()
        self.tab_widget.addTab(self.recording_page, "📹 视频录制")

        # 视频标注页面
        self.annotation_page = AnnotationPage()
        self.tab_widget.addTab(self.annotation_page, "🎯 视频标注")

        # 设置标签样式
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: white;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
            QTabBar::tab:selected:hover {
                background-color: #106ebe;
            }
        """)

    def setup_connections(self):
        """设置信号连接"""
        # 录制页面信号
        if self.recording_page:
            self.recording_page.recording_completed.connect(self.on_recording_completed)

        # 选项卡切换信号
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    @pyqtSlot(str)
    def on_recording_completed(self, video_path: str):
        """录制完成后的处理"""
        # 切换到标注页面
        self.tab_widget.setCurrentIndex(1)  # 标注页面索引为1

        # 加载录制的视频到标注页面
        if self.annotation_page:
            if self.annotation_page.load_video(video_path):
                self.statusBar().showMessage(f"已自动加载录制的视频: {os.path.basename(video_path)}")
            else:
                QMessageBox.warning(self, "警告", "无法加载录制的视频文件")

    def on_tab_changed(self, index):
        """选项卡切换处理"""
        if index == 0:
            self.statusBar().showMessage("当前页面: 视频录制")
        elif index == 1:
            self.statusBar().showMessage("当前页面: 视频标注")

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        # 录制相关
        recording_submenu = file_menu.addMenu("录制")

        switch_to_recording_action = QAction("切换到录制页面", self)
        switch_to_recording_action.setShortcut("Ctrl+R")
        switch_to_recording_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        recording_submenu.addAction(switch_to_recording_action)

        # 标注相关
        annotation_submenu = file_menu.addMenu("标注")

        switch_to_annotation_action = QAction("切换到标注页面", self)
        switch_to_annotation_action.setShortcut("Ctrl+A")
        switch_to_annotation_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        annotation_submenu.addAction(switch_to_annotation_action)

        annotation_submenu.addSeparator()

        open_video_action = QAction("打开视频文件", self)
        open_video_action.setShortcut(QKeySequence.StandardKey.Open)
        open_video_action.triggered.connect(self.open_video_for_annotation)
        annotation_submenu.addAction(open_video_action)

        file_menu.addSeparator()

        # 项目操作
        new_project_action = QAction("新建项目", self)
        new_project_action.setShortcut(QKeySequence.StandardKey.New)
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        open_project_action = QAction("打开项目", self)
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        save_project_action = QAction("保存项目", self)
        save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)

        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # 导出
        export_action = QAction("导出标注", self)
        export_action.triggered.connect(self.export_annotations)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")

        fullscreen_action = QAction("全屏", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        user_guide_action = QAction("使用指南", self)
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)

        # 页面切换
        recording_action = QAction("录制", self)
        recording_action.setToolTip("切换到视频录制页面")
        recording_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        toolbar.addAction(recording_action)

        annotation_action = QAction("标注", self)
        annotation_action.setToolTip("切换到视频标注页面")
        annotation_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        toolbar.addAction(annotation_action)

        toolbar.addSeparator()

        # 文件操作
        open_action = QAction("打开", self)
        open_action.setToolTip("打开视频文件进行标注")
        open_action.triggered.connect(self.open_video_for_annotation)
        toolbar.addAction(open_action)

        save_action = QAction("保存", self)
        save_action.setToolTip("保存当前项目")
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # 导出
        export_action = QAction("导出", self)
        export_action.setToolTip("导出标注数据")
        export_action.triggered.connect(self.export_annotations)
        toolbar.addAction(export_action)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请选择录制视频或标注现有视频")

    def apply_theme(self):
        """应用主题"""
        self.setStyleSheet(StyleSheet.DARK_THEME)

    def load_settings(self):
        """加载设置"""
        # 窗口几何
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # 窗口状态
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

        # 当前页面
        current_tab = self.settings.value("currentTab", 0, type=int)
        if 0 <= current_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(current_tab)

    def save_settings(self):
        """保存设置"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("currentTab", self.tab_widget.currentIndex())

    # === 菜单操作方法 ===

    def open_video_for_annotation(self):
        """为标注打开视频文件"""
        # 切换到标注页面
        self.tab_widget.setCurrentIndex(1)

        # 触发标注页面的文件选择
        if self.annotation_page:
            self.annotation_page.select_video_file()

    def new_project(self):
        """新建项目"""
        if self.annotation_page:
            self.annotation_page.new_project()

    def open_project(self):
        """打开项目"""
        # 切换到标注页面
        self.tab_widget.setCurrentIndex(1)

        if self.annotation_page:
            self.annotation_page.open_project()

    def save_project(self):
        """保存项目"""
        if self.annotation_page:
            return self.annotation_page.save_project()
        return False

    def save_project_as(self):
        """另存项目"""
        if self.annotation_page:
            return self.annotation_page.save_project_as()
        return False

    def export_annotations(self):
        """导出标注数据"""
        if self.annotation_page:
            self.annotation_page.export_annotations()
        else:
            QMessageBox.information(self, "提示", "请先切换到标注页面")

    def toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "设置", "设置功能正在开发中...")

    def show_user_guide(self):
        """显示使用指南"""
        guide_text = """
AI视频动作标注工具使用指南

【录制页面】
1. 输入设备IP地址和端口
2. 点击"连接"按钮连接到视频源
3. 设置保存路径和录制参数
4. 点击"开始录制"开始录制视频
5. 录制完成后可选择自动切换到标注页面

【标注页面】
1. 选择视频文件或加载录制的视频
2. 使用播放控制观看视频
3. 标记起点和终点创建标注区间
4. 使用快速标注按钮或自定义标签
5. 管理标注列表，编辑或删除标注
6. 保存项目或导出标注数据

【快捷键】
- Ctrl+R: 切换到录制页面
- Ctrl+A: 切换到标注页面
- Ctrl+O: 打开视频文件
- Ctrl+S: 保存项目
- F11: 全屏模式

【注意事项】
- WebSocket连接需要确保网络连通性
- 录制时请确保有足够的存储空间
- 标注时间区间不能重叠
"""
        QMessageBox.information(self, "使用指南", guide_text)

    def show_about(self):
        """显示关于信息"""
        about_text = """
AI视频动作标注工具 v2.0

【主要功能】
📹 实时视频录制
  • WebSocket视频流接收
  • 自定义录制参数
  • 自动文件管理

🎯 智能视频标注
  • 精确时间线控制
  • 快速标注预设
  • 可视化标注管理
  • 项目保存与导出

【技术特性】
• 基于PyQt6开发
• 支持多种视频格式
• 实时图像处理
• 响应式用户界面

【开发信息】
版本: 2.0
更新: 2024年
技术栈: Python, PyQt6, OpenCV, WebSocket
        """
        QMessageBox.about(self, "关于", about_text)

    def closeEvent(self, event):
        """关闭事件"""
        # 检查标注页面是否有未保存的更改
        if (self.annotation_page and
            self.annotation_page.annotation_manager and
            self.annotation_page.annotation_manager.is_modified):

            reply = QMessageBox.question(
                self,
                "保存更改",
                "标注项目有未保存的更改，是否保存？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_project():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        # 停止录制页面的所有操作
        if self.recording_page:
            self.recording_page.close()

        # 保存设置
        self.save_settings()
        event.accept()
"""
主应用程序窗口 - 修复导出逻辑版本
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
    # 使用修复后的多标签页面
    from annotation_page import MultiLabelAnnotationPage
    from styles import StyleSheet, ColorPalette
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有模块文件都在正确位置")
    sys.exit(1)


class MultiLabelVideoAnnotationMainWindow(QMainWindow):
    """多标签视频标注主应用程序窗口 - 修复导出逻辑版本"""

    def __init__(self):
        super().__init__()

        # 页面组件
        self.recording_page = None
        self.annotation_page = None
        self.tab_widget = None

        # 设置
        self.settings = QSettings("MultiLabelVideoAnnotationTool", "Settings")

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
        self.setWindowTitle("AI视频多标签动作标注工具 v2.0 (修复版)")
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

        # 多标签视频标注页面（使用修复版）
        self.annotation_page = MultiLabelAnnotationPage()
        self.tab_widget.addTab(self.annotation_page, "🎯 多标签标注")

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
            self.statusBar().showMessage("当前页面: 多标签视频标注")

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
        annotation_submenu = file_menu.addMenu("多标签标注")

        switch_to_annotation_action = QAction("切换到多标签标注页面", self)
        switch_to_annotation_action.setShortcut("Ctrl+A")
        switch_to_annotation_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        annotation_submenu.addAction(switch_to_annotation_action)

        annotation_submenu.addSeparator()

        open_video_action = QAction("打开视频文件", self)
        open_video_action.setShortcut(QKeySequence.StandardKey.Open)
        open_video_action.triggered.connect(self.open_video_for_annotation)
        annotation_submenu.addAction(open_video_action)

        # 多标签功能快捷方式
        annotation_submenu.addSeparator()

        multi_label_action = QAction("创建多标签标注 (M键)", self)
        multi_label_action.setShortcut("M")
        multi_label_action.setToolTip("快速创建包含多个标签的标注")
        multi_label_action.triggered.connect(self.create_multi_label_annotation)
        annotation_submenu.addAction(multi_label_action)

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

        # 多标签数据集导出（修复版）
        export_dataset_action = QAction("导出多标签数据集 🔧修复版", self)
        export_dataset_action.setShortcut("Ctrl+Shift+E")
        export_dataset_action.setToolTip("将多标签标注片段导出为图像和标注文件数据集（已修复取消逻辑问题）")
        export_dataset_action.triggered.connect(self.export_multi_label_dataset)
        file_menu.addAction(export_dataset_action)

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

        # 多标签工具菜单
        tools_menu = menubar.addMenu("工具")

        # 标注统计
        stats_action = QAction("查看标注统计", self)
        stats_action.triggered.connect(self.show_annotation_statistics)
        tools_menu.addAction(stats_action)

        # 验证标注
        validate_action = QAction("验证标注数据", self)
        validate_action.triggered.connect(self.validate_annotations)
        tools_menu.addAction(validate_action)

        # 优化标注
        optimize_action = QAction("优化标注数据", self)
        optimize_action.triggered.connect(self.optimize_annotations)
        tools_menu.addAction(optimize_action)

        tools_menu.addSeparator()

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        user_guide_action = QAction("使用指南", self)
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)

        # 修复说明
        fix_info_action = QAction("修复说明", self)
        fix_info_action.triggered.connect(self.show_fix_info)
        help_menu.addAction(fix_info_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_multi_label_annotation(self):
        """创建多标签标注"""
        if self.annotation_page:
            # 确保在标注页面
            self.tab_widget.setCurrentIndex(1)
            # 调用页面的多标签标注方法
            self.annotation_page.create_multi_label_annotation()
        else:
            QMessageBox.information(self, "提示", "请先切换到多标签标注页面")

    def export_multi_label_dataset(self):
        """导出多标签数据集 - 使用修复后的版本"""
        if self.annotation_page:
            print("🔧 主窗口调用修复版导出...")  # 调试信息
            self.annotation_page.export_multi_label_dataset()
        else:
            QMessageBox.information(self, "提示", "请先切换到多标签标注页面")

    def show_annotation_statistics(self):
        """显示标注统计"""
        if self.annotation_page and self.annotation_page.annotation_manager:
            stats = self.annotation_page.annotation_manager.get_statistics()

            stats_msg = f"""多标签标注统计信息

总标注数: {stats['total_count']}
总时长: {stats['total_duration']:.1f} 秒
平均时长: {stats['average_duration']:.1f} 秒

多标签统计:
• 单标签标注: {stats['multi_label_stats']['single_label_count']}
• 多标签标注: {stats['multi_label_stats']['multi_label_count']}
• 最大标签数: {stats['multi_label_stats']['max_labels_per_annotation']}
• 总标签数: {stats['multi_label_stats']['total_labels']}
• 平均每个标注的标签数: {stats['multi_label_stats']['avg_labels_per_annotation']:.1f}

进度类型统计:
• 线性增长: {stats['progression_stats']['linear_count']} ({stats['progression_stats']['linear_percentage']:.1f}%)
• 恒定强度: {stats['progression_stats']['constant_count']} ({stats['progression_stats']['constant_percentage']:.1f}%)

动作使用频率 (前10):"""

            # 添加最常用的动作
            sorted_labels = sorted(stats['labels'].items(), key=lambda x: x[1]['count'], reverse=True)
            for i, (label, data) in enumerate(sorted_labels[:10]):
                from styles import FacialActionConfig
                chinese_label = FacialActionConfig.get_chinese_label(label)
                stats_msg += f"\n{i+1}. {chinese_label}: {data['count']} 次 (平均强度: {data['avg_intensity']:.2f})"

            QMessageBox.information(self, "标注统计", stats_msg)
        else:
            QMessageBox.information(self, "提示", "没有标注数据")

    def validate_annotations(self):
        """验证标注数据"""
        if self.annotation_page and self.annotation_page.annotation_manager:
            issues = self.annotation_page.annotation_manager.validate_annotations()

            if not issues:
                QMessageBox.information(self, "验证结果", "所有标注数据都是有效的！")
            else:
                issues_msg = "发现以下问题:\n\n" + "\n".join(issues)
                QMessageBox.warning(self, "验证结果", issues_msg)
        else:
            QMessageBox.information(self, "提示", "没有标注数据需要验证")

    def optimize_annotations(self):
        """优化标注数据"""
        if self.annotation_page and self.annotation_page.annotation_manager:
            optimized_count = self.annotation_page.annotation_manager.optimize_annotations()

            if optimized_count > 0:
                QMessageBox.information(
                    self,
                    "优化完成",
                    f"已优化 {optimized_count} 个问题\n\n主要优化内容:\n• 移除重复标签\n• 修正强度值范围"
                )
                # 更新显示
                self.annotation_page.update_annotation_list()
            else:
                QMessageBox.information(self, "优化结果", "标注数据已经是最优状态！")
        else:
            QMessageBox.information(self, "提示", "没有标注数据需要优化")

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)

        # 页面切换
        recording_action = QAction("📹 录制", self)
        recording_action.setToolTip("切换到视频录制页面")
        recording_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        toolbar.addAction(recording_action)

        annotation_action = QAction("🎯 多标签标注", self)
        annotation_action.setToolTip("切换到多标签视频标注页面")
        annotation_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        toolbar.addAction(annotation_action)

        toolbar.addSeparator()

        # 文件操作
        open_action = QAction("📂 打开", self)
        open_action.setToolTip("打开视频文件进行多标签标注")
        open_action.triggered.connect(self.open_video_for_annotation)
        toolbar.addAction(open_action)

        save_action = QAction("💾 保存", self)
        save_action.setToolTip("保存当前项目")
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # 多标签功能
        multi_label_action = QAction("🏷️ 多标签", self)
        multi_label_action.setToolTip("创建多标签标注 (M键)")
        multi_label_action.triggered.connect(self.create_multi_label_annotation)
        toolbar.addAction(multi_label_action)

        # 数据集导出（修复版）
        dataset_action = QAction("📊 导出数据集 🔧", self)
        dataset_action.setToolTip("导出多标签数据集（修复版）")
        dataset_action.triggered.connect(self.export_multi_label_dataset)
        toolbar.addAction(dataset_action)

        toolbar.addSeparator()

        # 统计信息
        stats_action = QAction("📈 统计", self)
        stats_action.setToolTip("查看多标签标注统计")
        stats_action.triggered.connect(self.show_annotation_statistics)
        toolbar.addAction(stats_action)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 支持多标签和不同进度类型的视频标注工具（已修复导出逻辑）")

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
        """为多标签标注打开视频文件"""
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

    def save_project(self) -> bool:
        """保存项目"""
        if self.annotation_page:
            return self.annotation_page.save_project()
        return False

    def save_project_as(self) -> bool:
        """另存项目"""
        if self.annotation_page:
            return self.annotation_page.save_project_as()
        return False

    def toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "设置", "设置功能正在开发中...")

    def show_fix_info(self):
        """显示修复说明"""
        fix_info = """
🔧 导出逻辑修复说明

【问题描述】
在之前的版本中，即使数据集成功导出，程序也会错误地显示"导出已被用户取消"的消息，并且不会自动清空标注列表。

【问题原因】
1. 进度对话框关闭时的逻辑错误
2. 成功完成与用户取消的判断顺序有误
3. 对话框closeEvent中误设取消状态

【修复内容】
✅ 修复进度对话框的关闭逻辑
✅ 区分"完成后关闭"和"用户主动取消"
✅ 调整判断顺序：先检查成功，再检查取消
✅ 添加调试信息便于排查问题
✅ 完善状态标记和流程控制

【修复效果】
• 导出成功后正确显示成功消息
• 可以正常询问是否清空标注列表
• 用户主动取消时正确显示取消消息
• 导出过程更加稳定可靠

【使用建议】
如果仍遇到问题，请查看控制台输出的调试信息，这将帮助定位具体问题所在。
        """
        QMessageBox.information(self, "修复说明", fix_info)

    def show_user_guide(self):
        """显示使用指南"""
        guide_text = """
AI视频多标签动作标注工具使用指南 v2.0 (修复版)

【录制页面】
1. 输入设备IP地址和端口
2. 点击"连接"按钮连接到视频源
3. 设置保存路径和录制参数
4. 点击"开始录制"开始录制视频
5. 录制完成后可选择自动切换到标注页面

【多标签标注页面】 ✨新功能
1. 选择视频文件或加载录制的视频
2. 使用播放控制观看视频
3. 标记起点和终点创建标注区间

【多标签标注功能】
• 🎯 多标签标注：同时为一个时间段添加多个动作标签
• 📈 进度类型设置：每个标签可选择"线性增长"或"恒定强度"
• 🎚️ 强度调节：为每个标签独立设置动作强度 (0.0-1.0)
• 🔄 快速操作：快捷按钮快速添加常用单标签，或使用多标签对话框

【进度类型说明】
• 线性增长：动作强度从0线性增长到设定值
• 恒定强度：动作强度在整个时间段内保持恒定

【数据集导出功能】 🔧已修复
• 自动提取标注片段的每一帧
• 生成45维向量标注文件（对应45个面部动作）
• 支持多标签同时激活
• 根据进度类型计算每帧的动作强度
• 自动应用舌头动作相关规则
• ✅ 修复了"导出成功却显示取消"的问题

【快捷键】
- Ctrl+R: 切换到录制页面
- Ctrl+A: 切换到多标签标注页面
- Ctrl+O: 打开视频文件
- Ctrl+S: 保存项目
- Ctrl+Shift+E: 导出多标签数据集
- M键: 创建多标签标注 ✨新功能
- A/D键: 逐帧后退/前进
- 空格键: 播放/暂停
- S/E键: 标记起点/终点

【注意事项】
- 每个标注可以包含多个标签
- 每个标签可以独立设置强度和进度类型
- 时间线显示多标签指示器
- 工具提示显示详细的多标签信息
- 数据集导出支持复杂的多标签组合
- 🔧 已修复导出逻辑问题，确保正确的成功/取消判断
"""
        QMessageBox.information(self, "使用指南", guide_text)

    def show_about(self):
        """显示关于信息"""
        about_text = """
AI视频多标签动作标注工具 v2.0 (修复版)

【核心功能】
📹 实时视频录制
  • WebSocket视频流接收
  • 自定义录制参数
  • 自动文件管理

🎯 多标签智能视频标注 ✨新功能
  • 支持每个标注同时包含多个标签
  • 每个标签独立设置强度和进度类型
  • 精确时间线控制和可视化
  • 智能工具提示和多标签指示器
  • 项目保存与加载
  • 多标签数据集导出

【技术特性】
• 基于PyQt6开发
• 支持45种面部动作标注
• 多标签同时标注支持
• 线性增长和恒定强度两种进度模式
• 实时图像处理
• 响应式用户界面
• 自动舌头动作规则应用

【新增功能 v2.0】
• ✨ 多标签标注：一个时间段可同时标注多个动作
• 📈 进度类型：线性增长 vs 恒定强度
• 🎚️ 独立强度设置：每个标签可设置不同强度
• 🏷️ 智能标签管理：自动去重和优化
• 📊 多标签统计：详细的使用统计和分析
• 🎯 增强的时间线：多标签可视化和工具提示

【修复内容 (修复版)】
• 🔧 修复导出逻辑：解决"成功却显示取消"的问题
• ✅ 改进状态判断：正确区分完成和取消
• 🐛 优化对话框关闭逻辑：避免误判
• 📝 添加调试信息：便于问题排查
• 🎯 增强用户体验：确保正确的反馈信息

【开发信息】
版本: 2.0 (修复版)
更新: 2024年
技术栈: Python, PyQt6, OpenCV, WebSocket
新特性: 多标签标注, 进度类型, 智能导出
修复: 导出逻辑, 状态判断, 用户反馈
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
                "多标签标注项目有未保存的更改，是否保存？",
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
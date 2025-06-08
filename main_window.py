"""
主应用程序窗口
"""
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QFrame, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QGridLayout, QStatusBar, QMenuBar, QToolBar
)
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QPixmap, QColor
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

# 导入自定义模块
try:
    from models import AnnotationMarker, VideoInfo
    from annotation_manager import AnnotationManager
    from video_player import VideoPlayerManager
    from widgets.timeline_widget import TimelineWidget
    from widgets.annotation_dialog import AnnotationDialog
    from styles import StyleSheet, ColorPalette
    from utils import TimeUtils, FileUtils
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有模块文件都在正确位置")
    sys.exit(1)


class VideoAnnotationMainWindow(QMainWindow):
    """主应用程序窗口"""

    def __init__(self):
        super().__init__()

        # 核心组件
        self.annotation_manager = AnnotationManager()
        self.video_player = None  # 将在setup_ui中初始化

        # UI组件
        self.video_widget = None
        self.timeline = None
        self.play_button = None
        self.time_label = None
        self.annotation_list = None
        self.stats_label = None
        self.mark_start_button = None
        self.mark_end_button = None

        # 状态
        self.marking_start = False
        self.temp_start_time = 0.0

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
        self.setGeometry(100, 100, 1400, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧：视频播放区域
        video_section = self.create_video_section()
        splitter.addWidget(video_section)

        # 右侧：控制面板
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)

        # 设置分割比例
        splitter.setSizes([1000, 400])

        # 创建菜单栏、工具栏和状态栏
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()

        # 初始化视频播放器
        self.video_player = VideoPlayerManager(self.video_widget)

    def create_video_section(self) -> QWidget:
        """创建视频播放区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 视频显示区域
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(800, 450)
        layout.addWidget(self.video_widget)

        # 播放控制
        controls = self.create_playback_controls()
        layout.addWidget(controls)

        # 时间线组
        timeline_group = QGroupBox("时间线控制")
        timeline_layout = QVBoxLayout(timeline_group)

        self.timeline = TimelineWidget()
        timeline_layout.addWidget(self.timeline)

        layout.addWidget(timeline_group)

        return widget

    def create_playback_controls(self) -> QWidget:
        """创建播放控制"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)

        # 播放控制按钮
        self.play_button = QPushButton("播放")
        self.play_button.setEnabled(False)
        layout.addWidget(self.play_button)

        stop_button = QPushButton("停止")
        stop_button.setEnabled(False)
        layout.addWidget(stop_button)

        # 时间显示
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setMinimumWidth(120)
        layout.addWidget(self.time_label)

        layout.addStretch()

        # 标注控制按钮
        self.mark_start_button = QPushButton("标记起点")
        self.mark_start_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.SUCCESS}; }}")
        self.mark_start_button.setEnabled(False)
        layout.addWidget(self.mark_start_button)

        self.mark_end_button = QPushButton("标记终点")
        self.mark_end_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.ERROR}; }}")
        self.mark_end_button.setEnabled(False)
        layout.addWidget(self.mark_end_button)

        # 连接事件
        self.play_button.clicked.connect(self.toggle_playback)
        stop_button.clicked.connect(self.stop_playback)
        self.mark_start_button.clicked.connect(self.mark_start)
        self.mark_end_button.clicked.connect(self.mark_end)

        return widget

    def create_control_panel(self) -> QWidget:
        """创建右侧控制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 快速标注组
        quick_group = self.create_quick_annotation_group()
        layout.addWidget(quick_group)

        # 标注列表组
        list_group = self.create_annotation_list_group()
        layout.addWidget(list_group)

        # 统计信息
        self.stats_label = QLabel("总计: 0 个标注")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 12px; color: #999; padding: 10px;")
        layout.addWidget(self.stats_label)

        return widget

    def create_quick_annotation_group(self) -> QGroupBox:
        """创建快速标注组"""
        group = QGroupBox("快速标注")
        layout = QGridLayout(group)
        layout.setSpacing(8)

        # 快速标注按钮
        quick_actions = [
            ("跳跃", ColorPalette.ANNOTATION_COLORS["跳跃"]),
            ("跑步", ColorPalette.ANNOTATION_COLORS["跑步"]),
            ("走路", ColorPalette.ANNOTATION_COLORS["走路"]),
            ("静止", ColorPalette.ANNOTATION_COLORS["静止"])
        ]

        for i, (label, color) in enumerate(quick_actions):
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 8px;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {color}DD;
                }}
                QPushButton:pressed {{
                    background-color: {color}BB;
                }}
            """)
            btn.clicked.connect(lambda checked, l=label, c=color: self.quick_annotation(l, c))
            layout.addWidget(btn, i // 2, i % 2)

        return group

    def create_annotation_list_group(self) -> QGroupBox:
        """创建标注列表组"""
        group = QGroupBox("标注列表")
        layout = QVBoxLayout(group)

        # 标注列表
        self.annotation_list = QListWidget()
        self.annotation_list.itemDoubleClicked.connect(self.edit_annotation)
        layout.addWidget(self.annotation_list)

        # 操作按钮
        button_layout = QHBoxLayout()

        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_selected_annotation)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_selected_annotation)
        button_layout.addWidget(delete_btn)

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_all_annotations)
        button_layout.addWidget(clear_btn)

        layout.addLayout(button_layout)

        return group

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        # 打开视频
        open_action = QAction("打开视频", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_video)
        file_menu.addAction(open_action)

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

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")

        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setEnabled(False)  # TODO: 实现撤销功能
        edit_menu.addAction(undo_action)

        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setEnabled(False)  # TODO: 实现重做功能
        edit_menu.addAction(redo_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")

        fullscreen_action = QAction("全屏", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)

        # 打开视频
        open_action = QAction("打开", self)
        open_action.triggered.connect(self.open_video)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        # 播放控制
        play_action = QAction("播放", self)
        play_action.triggered.connect(self.toggle_playback)
        toolbar.addAction(play_action)

        toolbar.addSeparator()

        # 导出
        export_action = QAction("导出", self)
        export_action.triggered.connect(self.export_annotations)
        toolbar.addAction(export_action)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请打开视频文件开始标注")

    def setup_connections(self):
        """设置信号连接"""
        # 时间线连接将在video_player初始化后设置
        pass

    def setup_video_connections(self):
        """设置视频相关连接"""
        if self.video_player and self.timeline:
            # 视频播放器信号
            self.video_player.duration_changed.connect(self.timeline.set_duration)
            self.video_player.position_changed.connect(self.timeline.set_position)
            self.video_player.position_changed.connect(self.update_time_display)
            self.video_player.playback_state_changed.connect(self.update_play_button)
            self.video_player.video_loaded.connect(self.on_video_loaded)
            self.video_player.error_occurred.connect(self.show_error)

            # 时间线信号
            self.timeline.position_changed.connect(self.video_player.seek)
            self.timeline.annotation_clicked.connect(self.on_annotation_clicked)

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

    def save_settings(self):
        """保存设置"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    # === 事件处理方法 ===

    def open_video(self):
        """打开视频文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择视频文件",
                "",
                "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v *.webm);;所有文件 (*)"
            )

            if file_path:
                if self.video_player.load_video(file_path):
                    self.setup_video_connections()
                    self.status_bar.showMessage(f"已加载: {os.path.basename(file_path)}")
                    self.enable_controls()
                else:
                    QMessageBox.critical(self, "错误", "视频加载失败")
        except Exception as e:
            print(f"打开视频失败: {e}")
            QMessageBox.critical(self, "错误", f"打开视频失败: {str(e)}")

    def enable_controls(self):
        """启用控制按钮"""
        self.play_button.setEnabled(True)
        self.mark_start_button.setEnabled(True)
        self.mark_end_button.setEnabled(True)

    def toggle_playback(self):
        """切换播放/暂停"""
        if self.video_player:
            self.video_player.toggle_playback()

    def stop_playback(self):
        """停止播放"""
        if self.video_player:
            self.video_player.stop()

    def update_play_button(self, state):
        """更新播放按钮"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("暂停")
        else:
            self.play_button.setText("播放")

    def update_time_display(self, position: float):
        """更新时间显示"""
        if self.video_player:
            current = TimeUtils.format_time(position)
            total = TimeUtils.format_time(self.video_player.get_duration())
            self.time_label.setText(f"{current} / {total}")

    def on_video_loaded(self, video_info: VideoInfo):
        """视频加载完成"""
        self.annotation_manager.video_info = video_info
        self.status_bar.showMessage(f"视频已加载 - 时长: {TimeUtils.format_time(video_info.duration)}")

    def show_error(self, error_msg: str):
        """显示错误信息"""
        QMessageBox.critical(self, "错误", error_msg)
        self.status_bar.showMessage(f"错误: {error_msg}")

    def mark_start(self):
        """标记起点"""
        if self.video_player:
            self.temp_start_time = self.video_player.get_position()
            self.marking_start = True
            self.mark_start_button.setText("起点已标记")
            self.mark_start_button.setEnabled(False)
            self.status_bar.showMessage(f"起点已标记: {TimeUtils.format_time(self.temp_start_time)}")

    def mark_end(self):
        """标记终点"""
        if not self.marking_start:
            QMessageBox.warning(self, "警告", "请先标记起点")
            return

        if not self.video_player:
            return

        end_time = self.video_player.get_position()
        if end_time <= self.temp_start_time:
            QMessageBox.warning(self, "警告", "终点时间必须大于起点时间")
            return

        # 显示标注对话框
        dialog = AnnotationDialog(self.temp_start_time, end_time, parent=self)
        if dialog.exec() == AnnotationDialog.DialogCode.Accepted:
            if dialog.validate_input():
                annotation = AnnotationMarker(
                    start_time=self.temp_start_time,
                    end_time=end_time,
                    label=dialog.get_label(),
                    color=dialog.get_color()
                )
                self.add_annotation(annotation)
                self.reset_marking_state()

    def quick_annotation(self, label: str, color: str):
        """快速标注"""
        if not self.marking_start:
            QMessageBox.warning(self, "警告", "请先标记起点")
            return

        if not self.video_player:
            return

        end_time = self.video_player.get_position()
        if end_time <= self.temp_start_time:
            QMessageBox.warning(self, "警告", "终点时间必须大于起点时间")
            return

        annotation = AnnotationMarker(
            start_time=self.temp_start_time,
            end_time=end_time,
            label=label,
            color=color
        )
        self.add_annotation(annotation)
        self.reset_marking_state()
        self.status_bar.showMessage(f"快速标注已添加: {label}")

    def reset_marking_state(self):
        """重置标记状态"""
        self.marking_start = False
        self.mark_start_button.setText("标记起点")
        self.mark_start_button.setEnabled(True)

    def add_annotation(self, annotation: AnnotationMarker):
        """添加标注"""
        if self.annotation_manager.add_annotation(annotation):
            self.timeline.add_annotation(annotation)
            self.update_annotation_list()
            self.status_bar.showMessage(f"标注已添加: {annotation.label}")
        else:
            QMessageBox.warning(self, "警告", "添加标注失败，可能存在时间重叠")

    def update_annotation_list(self):
        """更新标注列表"""
        self.annotation_list.clear()

        for i, annotation in enumerate(self.annotation_manager.annotations):
            item_text = f"{i + 1}. {annotation.label} ({TimeUtils.format_time(annotation.start_time)} - {TimeUtils.format_time(annotation.end_time)})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, annotation)

            # 设置颜色
            item.setBackground(QColor(annotation.color).lighter(150))

            self.annotation_list.addItem(item)

        # 更新统计
        stats = self.annotation_manager.get_statistics()
        self.stats_label.setText(f"总计: {stats['total_count']} 个标注")

    def edit_annotation(self, item: QListWidgetItem):
        """编辑标注（双击）"""
        annotation = item.data(Qt.ItemDataRole.UserRole)
        if annotation and self.video_player:
            self.video_player.seek(annotation.start_time)

    def edit_selected_annotation(self):
        """编辑选中的标注"""
        current_item = self.annotation_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请选择要编辑的标注")
            return

        annotation = current_item.data(Qt.ItemDataRole.UserRole)
        if annotation:
            dialog = AnnotationDialog(
                annotation.start_time,
                annotation.end_time,
                annotation.label,
                self
            )
            dialog.selected_color = annotation.color
            dialog.update_color_button()

            if dialog.exec() == AnnotationDialog.DialogCode.Accepted:
                if dialog.validate_input():
                    # 更新标注
                    new_annotation = AnnotationMarker(
                        start_time=annotation.start_time,
                        end_time=annotation.end_time,
                        label=dialog.get_label(),
                        color=dialog.get_color(),
                        id=annotation.id
                    )

                    if self.annotation_manager.update_annotation(annotation, new_annotation):
                        self.timeline.remove_annotation(annotation)
                        self.timeline.add_annotation(new_annotation)
                        self.update_annotation_list()
                        self.status_bar.showMessage("标注已更新")

    def delete_selected_annotation(self):
        """删除选中的标注"""
        current_item = self.annotation_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请选择要删除的标注")
            return

        annotation = current_item.data(Qt.ItemDataRole.UserRole)
        if annotation:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除标注 '{annotation.label}' 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.annotation_manager.remove_annotation(annotation):
                    self.timeline.remove_annotation(annotation)
                    self.update_annotation_list()
                    self.status_bar.showMessage("标注已删除")

    def clear_all_annotations(self):
        """清空所有标注"""
        if not self.annotation_manager.annotations:
            QMessageBox.information(self, "提示", "没有标注可清空")
            return

        reply = QMessageBox.question(
            self,
            "确认清空",
            f"确定要删除所有 {len(self.annotation_manager.annotations)} 个标注吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.annotation_manager.clear_annotations()
            self.timeline.clear_annotations()
            self.update_annotation_list()
            self.status_bar.showMessage("所有标注已清空")

    def on_annotation_clicked(self, annotation: AnnotationMarker):
        """时间线标注点击"""
        if self.video_player:
            self.video_player.seek(annotation.start_time)

    def new_project(self):
        """新建项目"""
        if self.annotation_manager.is_modified:
            reply = QMessageBox.question(
                self,
                "保存更改",
                "当前项目有未保存的更改，是否保存？",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_project():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        # 清空数据
        self.annotation_manager = AnnotationManager()
        self.timeline.clear_annotations()
        self.update_annotation_list()
        if self.video_player:
            self.video_player.stop()

        self.status_bar.showMessage("新项目已创建")

    def open_project(self):
        """打开项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开项目文件",
            "",
            "项目文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            if self.annotation_manager.load_project(file_path):
                # 重新加载界面
                self.timeline.clear_annotations()
                for annotation in self.annotation_manager.annotations:
                    self.timeline.add_annotation(annotation)
                self.update_annotation_list()

                # 尝试加载视频
                if self.annotation_manager.video_info.file_path:
                    if self.video_player.load_video(self.annotation_manager.video_info.file_path):
                        self.setup_video_connections()
                        self.enable_controls()

                self.status_bar.showMessage(f"项目已加载: {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "错误", "项目加载失败")

    def save_project(self) -> bool:
        """保存项目"""
        if not self.annotation_manager.project_file_path:
            return self.save_project_as()

        if self.annotation_manager.save_project():
            self.status_bar.showMessage("项目已保存")
            return True
        else:
            QMessageBox.critical(self, "错误", "项目保存失败")
            return False

    def save_project_as(self) -> bool:
        """另存项目"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存项目",
            "untitled.json",
            "项目文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            if self.annotation_manager.save_project(file_path):
                self.status_bar.showMessage(f"项目已保存: {os.path.basename(file_path)}")
                return True
            else:
                QMessageBox.critical(self, "错误", "项目保存失败")
                return False
        return False

    def export_annotations(self):
        """导出标注数据"""
        if not self.annotation_manager.annotations:
            QMessageBox.warning(self, "警告", "暂无标注数据可导出")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出标注数据",
            "annotations.json",
            "JSON文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            if self.annotation_manager.export_to_json(file_path):
                QMessageBox.information(
                    self,
                    "导出成功",
                    f"已导出 {len(self.annotation_manager.annotations)} 条标注到:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "错误", "导出失败")

    def toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(
            self,
            "关于",
            "AI视频动作标注工具\n\n"
            "版本: 1.0\n"
            "基于PyQt6开发\n\n"
            "功能特性:\n"
            "• 视频播放控制\n"
            "• 时间线标注\n"
            "• 快速标注\n"
            "• 项目管理\n"
            "• 数据导出"
        )

    def closeEvent(self, event):
        """关闭事件"""
        if self.annotation_manager.is_modified:
            reply = QMessageBox.question(
                self,
                "保存更改",
                "项目有未保存的更改，是否保存？",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_project():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        # 保存设置
        self.save_settings()
        event.accept()
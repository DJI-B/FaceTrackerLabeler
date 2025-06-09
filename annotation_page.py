"""
视频标注页面 - 移除JSON导出功能
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QFrame,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence, QColor
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

# 导入自定义模块
from models import AnnotationMarker, VideoInfo
from annotation_manager import AnnotationManager
from video_player import VideoPlayerManager
from widgets.timeline_widget import TimelineWidget
from widgets.annotation_dialog import AnnotationDialog
from styles import StyleSheet, ColorPalette
from utils import TimeUtils, FileUtils


class AnnotationPage(QWidget):
    """视频标注页面"""

    def __init__(self, parent=None):
        super().__init__(parent)

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

        try:
            self.setup_ui()
            self.setup_connections()
        except Exception as e:
            print(f"标注页面初始化失败: {e}")
            raise

    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QHBoxLayout(self)

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

        # 初始化视频播放器
        self.video_player = VideoPlayerManager(self.video_widget)

    def create_video_section(self) -> QWidget:
        """创建视频播放区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # 文件选择区域
        file_section = self.create_file_selection()
        layout.addWidget(file_section)

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

    def create_file_selection(self) -> QGroupBox:
        """创建文件选择区域"""
        group = QGroupBox("视频文件选择")
        layout = QHBoxLayout(group)

        # 选择文件按钮
        select_file_button = QPushButton("选择视频文件")
        select_file_button.clicked.connect(self.select_video_file)
        layout.addWidget(select_file_button)

        # 当前文件显示
        self.current_file_label = QLabel("未选择文件")
        self.current_file_label.setStyleSheet("color: #999; font-style: italic;")
        layout.addWidget(self.current_file_label)

        layout.addStretch()

        return group

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

        # 项目管理组
        project_group = self.create_project_group()
        layout.addWidget(project_group)

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

    def create_project_group(self) -> QGroupBox:
        """创建项目管理组"""
        group = QGroupBox("项目管理")
        layout = QGridLayout(group)
        layout.setSpacing(8)

        # 项目操作按钮
        new_button = QPushButton("新建项目")
        new_button.clicked.connect(self.new_project)
        layout.addWidget(new_button, 0, 0)

        open_button = QPushButton("打开项目")
        open_button.clicked.connect(self.open_project)
        layout.addWidget(open_button, 0, 1)

        save_button = QPushButton("保存项目")
        save_button.clicked.connect(self.save_project)
        layout.addWidget(save_button, 1, 0)

        save_as_button = QPushButton("另存为...")
        save_as_button.clicked.connect(self.save_project_as)
        layout.addWidget(save_as_button, 1, 1)

        # 数据集导出按钮
        dataset_export_button = QPushButton("导出数据集")
        dataset_export_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ColorPalette.INFO};
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {ColorPalette.INFO}DD;
            }}
            QPushButton:pressed {{
                background-color: {ColorPalette.INFO}BB;
            }}
        """)
        dataset_export_button.setToolTip("将标注片段导出为图像和标注文件数据集")
        dataset_export_button.clicked.connect(self.export_dataset)
        layout.addWidget(dataset_export_button, 2, 0, 1, 2)  # 占两列

        return group

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

    def setup_connections(self):
        """设置信号连接"""
        # 视频连接将在加载视频后设置
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

    def select_video_file(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v *.webm);;所有文件 (*)"
        )

        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path: str):
        """加载视频文件"""
        try:
            if self.video_player.load_video(file_path):
                self.setup_video_connections()
                self.current_file_label.setText(os.path.basename(file_path))
                self.current_file_label.setStyleSheet("color: white;")
                self.enable_controls()
                return True
            else:
                QMessageBox.critical(self, "错误", "视频加载失败")
                return False
        except Exception as e:
            print(f"加载视频失败: {e}")
            QMessageBox.critical(self, "错误", f"加载视频失败: {str(e)}")
            return False

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

    def show_error(self, error_msg: str):
        """显示错误信息"""
        QMessageBox.critical(self, "错误", error_msg)

    def mark_start(self):
        """标记起点"""
        if self.video_player:
            self.temp_start_time = self.video_player.get_position()
            self.marking_start = True
            self.mark_start_button.setText("起点已标记")
            self.mark_start_button.setEnabled(False)

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
                    if self.load_video(self.annotation_manager.video_info.file_path):
                        pass  # 视频加载成功
            else:
                QMessageBox.critical(self, "错误", "项目加载失败")

    def save_project(self) -> bool:
        """保存项目"""
        if not self.annotation_manager.project_file_path:
            return self.save_project_as()

        if self.annotation_manager.save_project():
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
                return True
            else:
                QMessageBox.critical(self, "错误", "项目保存失败")
                return False
        return False

    def export_dataset(self):
        """导出数据集 - 使用稳定的简化版"""
        if not self.annotation_manager.annotations:
            QMessageBox.warning(self, "警告", "暂无标注数据可导出为数据集")
            return

        if not self.annotation_manager.video_info.file_path:
            QMessageBox.warning(self, "警告", "没有关联的视频文件")
            return

        if not os.path.exists(self.annotation_manager.video_info.file_path):
            QMessageBox.warning(self, "警告", "视频文件不存在，无法导出数据集")
            return

        # 使用简化版导出器，避免多线程问题
        try:
            from dataset_exporter import simple_export_dataset
            simple_export_dataset(
                self,
                self.annotation_manager.video_info.file_path,
                self.annotation_manager.annotations,
                self.annotation_manager.video_info
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"数据集导出失败: {str(e)}")
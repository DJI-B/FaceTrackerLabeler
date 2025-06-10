"""
视频标注页面 - 多标签支持版本
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QFrame,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QGridLayout, QSpinBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence, QColor
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

# 导入自定义模块
from models import AnnotationMarker, VideoInfo, LabelConfig, ProgressionType
from annotation_manager import MultiLabelAnnotationManager
from video_player import VideoPlayerManager
from widgets.timeline_widget import MultiLabelTimelineWidget
# 导入新的多标签对话框
from widgets.annotation_dialog import MultiLabelAnnotationDialog
from styles import StyleSheet, ColorPalette, FacialActionConfig
from utils import TimeUtils, FileUtils


class MultiLabelAnnotationPage(QWidget):
    """多标签视频标注页面"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 核心组件
        self.annotation_manager = MultiLabelAnnotationManager()
        self.video_player = None

        # UI组件
        self.video_widget = None
        self.timeline = None
        self.play_button = None
        self.time_label = None
        self.annotation_list = None
        self.stats_label = None
        self.mark_start_button = None
        self.mark_end_button = None

        # 逐帧控制组件
        self.frame_step_spinbox = None
        self.prev_frame_button = None
        self.next_frame_button = None

        # 状态
        self.marking_start = False
        self.temp_start_time = 0.0

        try:
            self.setup_ui()
            self.setup_connections()
        except Exception as e:
            print(f"多标签标注页面初始化失败: {e}")
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

        # 逐帧控制区域
        frame_controls = self.create_frame_controls()
        layout.addWidget(frame_controls)

        # 时间线组
        timeline_group = QGroupBox("时间线控制")
        timeline_layout = QVBoxLayout(timeline_group)

        self.timeline = MultiLabelTimelineWidget()
        timeline_layout.addWidget(self.timeline)

        layout.addWidget(timeline_group)

        return widget

    def create_file_selection(self) -> QGroupBox:
        """创建文件选择区域"""
        group = QGroupBox("视频文件选择")
        layout = QHBoxLayout(group)

        select_file_button = QPushButton("选择视频文件")
        select_file_button.clicked.connect(self.select_video_file)
        layout.addWidget(select_file_button)

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

    def create_frame_controls(self) -> QGroupBox:
        """创建逐帧控制区域"""
        group = QGroupBox("逐帧控制")
        layout = QHBoxLayout(group)

        # 步长设置
        layout.addWidget(QLabel("步长:"))
        self.frame_step_spinbox = QSpinBox()
        self.frame_step_spinbox.setRange(1, 30)
        self.frame_step_spinbox.setValue(1)
        self.frame_step_spinbox.setSuffix(" 帧")
        layout.addWidget(self.frame_step_spinbox)

        layout.addStretch()

        # 上一帧按钮
        self.prev_frame_button = QPushButton("◀◀ 后退")
        self.prev_frame_button.setEnabled(False)
        self.prev_frame_button.clicked.connect(self.prev_frame)
        layout.addWidget(self.prev_frame_button)

        # 下一帧按钮
        self.next_frame_button = QPushButton("前进 ▶▶")
        self.next_frame_button.setEnabled(False)
        self.next_frame_button.clicked.connect(self.next_frame)
        layout.addWidget(self.next_frame_button)

        return group

    def create_control_panel(self) -> QWidget:
        """创建右侧控制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # 项目管理组
        project_group = self.create_project_group()
        layout.addWidget(project_group)

        # 多标签快速标注组（修改）
        quick_group = self.create_multi_label_quick_annotation_group()
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

        # 多标签数据集导出按钮（修改）
        dataset_export_button = QPushButton("导出多标签数据集")
        dataset_export_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ColorPalette.INFO};
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {ColorPalette.PRIMARY_HOVER};
            }}
        """)
        dataset_export_button.setToolTip("将多标签标注片段导出为图像和标注文件数据集")
        dataset_export_button.clicked.connect(self.export_multi_label_dataset)
        layout.addWidget(dataset_export_button, 2, 0, 1, 2)

        return group

    def create_multi_label_quick_annotation_group(self) -> QGroupBox:
        """创建多标签快速标注组"""
        group = QGroupBox("快速面部动作标注")
        layout = QVBoxLayout(group)

        # 说明文字
        info_label = QLabel("💡 点击按钮快速添加单个动作，或点击'多标签标注'同时选择多个动作")
        info_label.setStyleSheet("color: #0078d4; font-size: 10px; margin: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 快速单标签按钮
        button_layout = QGridLayout()
        button_layout.setSpacing(8)

        quick_actions = FacialActionConfig.QUICK_ACTIONS
        for i, english_action in enumerate(quick_actions):
            chinese_action = FacialActionConfig.get_chinese_label(english_action)
            color = FacialActionConfig.get_label_color(english_action)

            btn = QPushButton(chinese_action)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 6px;
                    min-height: 15px;
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    background-color: {QColor(color).lighter(110).name()};
                }}
            """)
            btn.clicked.connect(lambda checked, eng=english_action, color=color: self.quick_single_annotation(eng, color))
            button_layout.addWidget(btn, i // 2, i % 2)

        layout.addLayout(button_layout)

        # 多标签标注按钮
        multi_label_btn = QPushButton("🎯 多标签标注")
        multi_label_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ColorPalette.PRIMARY};
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {ColorPalette.PRIMARY_HOVER};
            }}
        """)
        multi_label_btn.setToolTip("创建包含多个标签的标注，支持不同进度类型")
        multi_label_btn.clicked.connect(self.create_multi_label_annotation)
        layout.addWidget(multi_label_btn)

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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key.Key_A:
            self.prev_frame()
        elif event.key() == Qt.Key.Key_D:
            self.next_frame()
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_playback()
        elif event.key() == Qt.Key.Key_S:
            if self.mark_start_button.isEnabled():
                self.mark_start()
        elif event.key() == Qt.Key.Key_E:
            if self.mark_end_button.isEnabled():
                self.mark_end()
        elif event.key() == Qt.Key.Key_M:  # M键 - 多标签标注
            self.create_multi_label_annotation()
        else:
            super().keyPressEvent(event)

    def setup_video_connections(self):
        """设置视频相关连接"""
        if self.video_player and self.timeline:
            self.video_player.duration_changed.connect(self.timeline.set_duration)
            self.video_player.position_changed.connect(self.timeline.set_position)
            self.video_player.position_changed.connect(self.update_time_display)
            self.video_player.playback_state_changed.connect(self.update_play_button)
            self.video_player.video_loaded.connect(self.on_video_loaded)
            self.video_player.error_occurred.connect(self.show_error)

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
        self.prev_frame_button.setEnabled(True)
        self.next_frame_button.setEnabled(True)

    def toggle_playback(self):
        """切换播放/暂停"""
        if self.video_player:
            self.video_player.toggle_playback()

    def stop_playback(self):
        """停止播放"""
        if self.video_player:
            self.video_player.stop()

    def prev_frame(self):
        """后退指定帧数"""
        if self.video_player:
            step_frames = self.frame_step_spinbox.value()
            fps = self.video_player.video_info.fps or 30.0
            step_time = step_frames / fps
            current_pos = self.video_player.get_position()
            new_pos = max(0, current_pos - step_time)
            self.video_player.seek(new_pos)

    def next_frame(self):
        """前进指定帧数"""
        if self.video_player:
            step_frames = self.frame_step_spinbox.value()
            fps = self.video_player.video_info.fps or 30.0
            step_time = step_frames / fps
            current_pos = self.video_player.get_position()
            duration = self.video_player.get_duration()
            new_pos = min(duration, current_pos + step_time)
            self.video_player.seek(new_pos)

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

            self.mark_start_button.setText(f"起点: {TimeUtils.format_time(self.temp_start_time)}")
            self.mark_start_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.WARNING}; }}")

            QMessageBox.information(self, "起点已标记",
                f"起点时间: {TimeUtils.format_time(self.temp_start_time)}\n\n可以重新点击'标记起点'来修改起点位置")

    def mark_end(self):
        """标记终点 - 使用多标签对话框"""
        if not self.marking_start:
            QMessageBox.warning(self, "警告", "请先标记起点")
            return

        if not self.video_player:
            return

        end_time = self.video_player.get_position()
        if end_time <= self.temp_start_time:
            QMessageBox.warning(self, "警告", "终点时间必须大于起点时间")
            return

        # 使用多标签对话框
        dialog = MultiLabelAnnotationDialog(self.temp_start_time, end_time, parent=self)
        if dialog.exec() == MultiLabelAnnotationDialog.DialogCode.Accepted:
            if dialog.validate_input():
                annotation = AnnotationMarker(
                    start_time=self.temp_start_time,
                    end_time=end_time,
                    labels=dialog.get_label_configs(),
                    color=dialog.get_color()
                )
                self.add_annotation(annotation)
                self.reset_marking_state()

    def quick_single_annotation(self, english_label: str, color: str):
        """快速单标签标注"""
        if not self.marking_start:
            QMessageBox.warning(self, "警告", "请先标记起点")
            return

        if not self.video_player:
            return

        end_time = self.video_player.get_position()
        if end_time <= self.temp_start_time:
            QMessageBox.warning(self, "警告", "终点时间必须大于起点时间")
            return

        # 创建单标签配置
        label_config = LabelConfig(
            label=english_label,
            intensity=1.0,
            progression=ProgressionType.LINEAR
        )

        annotation = AnnotationMarker(
            start_time=self.temp_start_time,
            end_time=end_time,
            labels=[label_config],
            color=color
        )
        self.add_annotation(annotation)
        self.reset_marking_state()

    def create_multi_label_annotation(self):
        """创建多标签标注"""
        if not self.marking_start:
            QMessageBox.warning(self, "警告", "请先标记起点")
            return

        if not self.video_player:
            return

        end_time = self.video_player.get_position()
        if end_time <= self.temp_start_time:
            QMessageBox.warning(self, "警告", "终点时间必须大于起点时间")
            return

        # 使用多标签对话框
        dialog = MultiLabelAnnotationDialog(self.temp_start_time, end_time, parent=self)
        if dialog.exec() == MultiLabelAnnotationDialog.DialogCode.Accepted:
            if dialog.validate_input():
                annotation = AnnotationMarker(
                    start_time=self.temp_start_time,
                    end_time=end_time,
                    labels=dialog.get_label_configs(),
                    color=dialog.get_color()
                )
                self.add_annotation(annotation)
                self.reset_marking_state()

    def reset_marking_state(self):
        """重置标记状态"""
        self.marking_start = False
        self.mark_start_button.setText("标记起点")
        self.mark_start_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.SUCCESS}; }}")

    def add_annotation(self, annotation: AnnotationMarker):
        """添加标注"""
        if self.annotation_manager.add_annotation(annotation):
            self.timeline.add_annotation(annotation)
            self.update_annotation_list()
        else:
            QMessageBox.warning(self, "警告", "添加标注失败，可能存在时间重叠")

    def update_annotation_list(self):
        """更新标注列表 - 支持多标签显示"""
        self.annotation_list.clear()

        for i, annotation in enumerate(self.annotation_manager.annotations):
            # 显示多标签信息
            labels_text = annotation.display_labels
            time_text = f"({TimeUtils.format_time(annotation.start_time)} - {TimeUtils.format_time(annotation.end_time)})"

            if len(annotation.labels) > 1:
                item_text = f"{i + 1}. 🎯 {labels_text} {time_text}"
            else:
                item_text = f"{i + 1}. {labels_text} {time_text}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, annotation)

            # 设置颜色
            item.setBackground(QColor(annotation.color).lighter(150))

            self.annotation_list.addItem(item)

        # 更新统计
        stats = self.annotation_manager.get_statistics()
        total_labels = sum(len(ann.labels) for ann in self.annotation_manager.annotations)
        multi_label_count = sum(1 for ann in self.annotation_manager.annotations if len(ann.labels) > 1)

        self.stats_label.setText(f"总计: {stats['total_count']} 个标注 | {total_labels} 个标签 | {multi_label_count} 个多标签")

    def edit_annotation(self, item: QListWidgetItem):
        """编辑标注（双击）"""
        annotation = item.data(Qt.ItemDataRole.UserRole)
        if annotation and self.video_player:
            self.video_player.seek(annotation.start_time)

    def edit_selected_annotation(self):
        """编辑选中的标注 - 使用多标签对话框"""
        current_item = self.annotation_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请选择要编辑的标注")
            return

        annotation = current_item.data(Qt.ItemDataRole.UserRole)
        if annotation:
            dialog = MultiLabelAnnotationDialog(
                annotation.start_time,
                annotation.end_time,
                annotation,  # 传递现有标注
                self
            )

            if dialog.exec() == MultiLabelAnnotationDialog.DialogCode.Accepted:
                if dialog.validate_input():
                    new_annotation = AnnotationMarker(
                        start_time=annotation.start_time,
                        end_time=annotation.end_time,
                        labels=dialog.get_label_configs(),
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
                f"确定要删除标注 '{annotation.display_labels}' 吗？",
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

        self.annotation_manager = MultiLabelAnnotationManager()
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
                self.timeline.clear_annotations()
                for annotation in self.annotation_manager.annotations:
                    self.timeline.add_annotation(annotation)
                self.update_annotation_list()

                if self.annotation_manager.video_info.file_path:
                    if self.load_video(self.annotation_manager.video_info.file_path):
                        pass
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

    def export_multi_label_dataset(self):
        """导出多标签数据集"""
        if not self.annotation_manager.annotations:
            QMessageBox.warning(self, "警告", "暂无标注数据可导出为数据集")
            return

        if not self.annotation_manager.video_info.file_path:
            QMessageBox.warning(self, "警告", "没有关联的视频文件")
            return

        if not os.path.exists(self.annotation_manager.video_info.file_path):
            QMessageBox.warning(self, "警告", "视频文件不存在，无法导出数据集")
            return

        try:
            # 导入多标签导出器
            from dataset_exporter import export_multi_label_dataset

            export_success = export_multi_label_dataset(
                self,
                self.annotation_manager.video_info.file_path,
                self.annotation_manager.annotations,
                self.annotation_manager.video_info
            )

            if export_success:
                reply = QMessageBox.question(
                    self,
                    "导出成功",
                    "多标签数据集导出成功！\n\n是否清空当前标注列表？\n(避免重复导出同一份数据)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.annotation_manager.clear_annotations()
                    self.timeline.clear_annotations()
                    self.update_annotation_list()

                    QMessageBox.information(
                        self,
                        "标注已清空",
                        "标注列表已清空，可以继续添加新的标注。\n项目设置和视频文件保持不变。"
                    )

        except Exception as e:
            QMessageBox.critical(self, "导出错误", f"多标签数据集导出失败: {str(e)}")
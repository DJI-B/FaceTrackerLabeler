"""
视频录制页面 - 支持ROI选择功能
"""
import cv2
import asyncio
import websocket
import threading
import numpy as np
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTextEdit, QFileDialog, QMessageBox,
    QProgressBar, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from styles import StyleSheet, ColorPalette
from widgets import ROIVideoWidget


class WebSocketImageReceiver(QThread):
    """WebSocket图像接收线程 - 修复版"""

    image_received = pyqtSignal(np.ndarray)
    connection_status_changed = pyqtSignal(bool, str)  # connected, message

    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
        self.ws = None
        self.running = False

    def run(self):
        """运行WebSocket连接"""
        try:
            # 修改URL格式，参考HTML中的成功实现
            url = f"ws://{self.ip_address}/ws"  # 注意这里改为 /ws 路径
            print(f"尝试连接到: {url}")

            # 添加更多的WebSocket选项
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_ping=self.on_ping,
                on_pong=self.on_pong
            )

            self.running = True
            # 添加ping_interval来保持连接活跃3
            self.ws.run_forever(ping_interval=30, ping_timeout=10)

        except Exception as e:
            print(f"WebSocket连接异常: {e}")
            self.connection_status_changed.emit(False, f"连接失败: {str(e)}")

    def on_open(self, ws):
        """连接打开"""
        print("WebSocket连接已建立")
        self.connection_status_changed.emit(True, "已连接")
        self.frame_count = 0
        self.total_bytes_received = 0

    def on_message(self, ws, message):
        """接收消息 - 参考HTML实现"""
        try:
            # 检查消息类型
            if isinstance(message, bytes):
                # 二进制数据，应该是JPEG图像
                self.total_bytes_received += len(message)

                # 使用numpy处理字节数据
                img_array = np.frombuffer(message, dtype=np.uint8)

                # 解码JPEG图像
                image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                if image is not None:
                    self.image_received.emit(image)
                else:
                    print("图像解码失败")
            else:
                # 文本消息
                pass

        except Exception as e:
            print(f"解析图像失败: {e}")
            # 不要因为单帧解析失败就断开连接，继续尝试

    def on_error(self, ws, error):
        """连接错误"""
        print(f"WebSocket错误: {error}")
        self.connection_status_changed.emit(False, f"连接错误: {str(error)}")

    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        print(f"WebSocket连接已关闭: {close_status_code} - {close_msg}")
        self.connection_status_changed.emit(False, "连接已断开")
        self.running = False

    def on_ping(self, ws, message):
        """收到ping"""
        print("收到ping")

    def on_pong(self, ws, message):
        """收到pong"""
        print("收到pong")

    def stop(self):
        """停止连接"""
        print("停止WebSocket连接")
        self.running = False
        if self.ws:
            self.ws.close()


class VideoRecorder:
    """视频录制器"""

    def __init__(self):
        self.writer = None
        self.is_recording = False
        self.frame_count = 0
        self.output_path = ""

    def start_recording(self, output_path: str, frame_size: tuple):
        """开始录制"""
        try:
            self.output_path = output_path
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(output_path, fourcc, 30, frame_size)
            self.is_recording = True
            self.frame_count = 0
            print(f"开始录制到: {output_path}, 尺寸: {frame_size}")
            return True
        except Exception as e:
            print(f"开始录制失败: {e}")
            return False

    def write_frame(self, frame: np.ndarray):
        """写入帧"""
        if self.is_recording and self.writer:
            self.writer.write(frame)
            self.frame_count += 1

    def stop_recording(self):
        """停止录制"""
        if self.writer:
            self.writer.release()
            self.writer = None
        self.is_recording = False
        print(f"录制停止，共录制 {self.frame_count} 帧")
        return self.output_path, self.frame_count


class RecordingPage(QWidget):
    """视频录制页面 - 支持ROI功能"""

    # 信号定义
    recording_completed = pyqtSignal(str)  # 录制完成，传递视频文件路径

    def __init__(self, parent=None):
        super().__init__(parent)

        # 组件
        self.ws_receiver = None
        self.recorder = VideoRecorder()

        # UI组件
        self.ip_input = None
        self.connect_button = None
        self.video_display = None  # 这将是ROIVideoWidget
        self.status_label = None
        self.record_button = None
        self.save_path_input = None
        self.frame_counter = None
        self.recording_time_label = None

        # ROI相关UI组件
        self.roi_enabled_checkbox = None
        self.roi_reset_button = None
        self.roi_info_label = None

        # 状态
        self.is_connected = False
        self.current_frame = None
        self.recording_start_time = None

        # ROI相关状态
        self.roi_rect = None  # 原始图像坐标系中的ROI

        # 定时器
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_time)

        self.setup_ui()
        self.setup_connections()

        # 自动生成初始文件名
        self.generate_filename()

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 连接设置组
        connection_group = self.create_connection_group()
        layout.addWidget(connection_group)

        # 视频显示区域
        display_group = self.create_display_group()
        layout.addWidget(display_group)

        # ROI控制组
        roi_group = self.create_roi_group()
        layout.addWidget(roi_group)

        # 录制控制组
        recording_group = self.create_recording_group()
        layout.addWidget(recording_group)

        # 状态信息
        self.status_label = QLabel("未连接")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #444; border-radius: 5px;")
        layout.addWidget(self.status_label)

    def create_connection_group(self) -> QGroupBox:
        """创建连接设置组"""
        group = QGroupBox("WebSocket连接设置")
        layout = QHBoxLayout(group)

        # IP地址输入
        layout.addWidget(QLabel("IP地址:"))
        self.ip_input = QLineEdit("192.168.31.101")  # 修改默认IP
        self.ip_input.setPlaceholderText("例如: 192.168.31.101")
        layout.addWidget(self.ip_input)

        # 连接按钮
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)

        return group

    def create_display_group(self) -> QGroupBox:
        """创建视频显示组"""
        group = QGroupBox("视频预览")
        layout = QVBoxLayout(group)

        # 使用支持ROI的视频显示控件
        self.video_display = ROIVideoWidget()
        self.video_display.roi_changed.connect(self.on_roi_changed)
        layout.addWidget(self.video_display)

        return group

    def create_roi_group(self) -> QGroupBox:
        """创建ROI控制组"""
        group = QGroupBox("感兴趣区域 (ROI)")
        layout = QHBoxLayout(group)

        # ROI启用复选框
        self.roi_enabled_checkbox = QCheckBox("启用ROI选择")
        self.roi_enabled_checkbox.toggled.connect(self.on_roi_enabled_changed)
        layout.addWidget(self.roi_enabled_checkbox)

        # ROI重置按钮
        self.roi_reset_button = QPushButton("重置ROI")
        self.roi_reset_button.setEnabled(False)
        self.roi_reset_button.clicked.connect(self.reset_roi)
        layout.addWidget(self.roi_reset_button)

        # ROI信息显示
        self.roi_info_label = QLabel("ROI: 未设置")
        self.roi_info_label.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(self.roi_info_label)

        layout.addStretch()

        # 使用说明
        help_label = QLabel("💡 启用后可用鼠标拖拽选择录制区域")
        help_label.setStyleSheet("color: #0078d4; font-size: 10px;")
        layout.addWidget(help_label)

        return group

    def create_recording_group(self) -> QGroupBox:
        """创建录制控制组"""
        group = QGroupBox("录制控制")
        layout = QVBoxLayout(group)

        # 保存路径设置
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("保存路径:"))
        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("选择保存路径...")
        path_layout.addWidget(self.save_path_input)

        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_save_path)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)

        # 录制参数
        params_layout = QHBoxLayout()

        params_layout.addStretch()

        # 自动生成文件名按钮
        auto_name_button = QPushButton("生成文件名")
        auto_name_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ColorPalette.INFO};
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {ColorPalette.PRIMARY_HOVER};
            }}
        """)
        auto_name_button.clicked.connect(self.generate_filename)
        params_layout.addWidget(auto_name_button)

        layout.addLayout(params_layout)

        # 录制控制按钮
        control_layout = QHBoxLayout()

        self.record_button = QPushButton("开始录制")
        self.record_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.SUCCESS}; }}")
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setEnabled(False)
        control_layout.addWidget(self.record_button)

        control_layout.addStretch()

        # 录制信息显示
        info_layout = QVBoxLayout()
        self.frame_counter = QLabel("帧数: 0")
        self.recording_time_label = QLabel("录制时间: 00:00")
        info_layout.addWidget(self.frame_counter)
        info_layout.addWidget(self.recording_time_label)
        control_layout.addLayout(info_layout)

        layout.addLayout(control_layout)

        return group

    def setup_connections(self):
        """设置信号连接"""
        pass

    def toggle_connection(self):
        """切换连接状态"""
        if not self.is_connected:
            self.connect_websocket()
        else:
            self.disconnect_websocket()

    def connect_websocket(self):
        """连接WebSocket"""
        ip = self.ip_input.text().strip()

        if not ip:
            QMessageBox.warning(self, "警告", "请输入IP地址")
            return

        # 创建WebSocket接收器，不使用端口参数（因为使用/ws路径）
        self.ws_receiver = WebSocketImageReceiver(ip)
        self.ws_receiver.image_received.connect(self.on_image_received)
        self.ws_receiver.connection_status_changed.connect(self.on_connection_status_changed)
        self.ws_receiver.start()

        self.connect_button.setText("连接中...")
        self.connect_button.setEnabled(False)

    def disconnect_websocket(self):
        """断开WebSocket连接"""
        if self.ws_receiver:
            self.ws_receiver.stop()
            self.ws_receiver.wait()
            self.ws_receiver = None

        self.is_connected = False
        self.connect_button.setText("连接")
        self.connect_button.setEnabled(True)
        self.record_button.setEnabled(False)
        self.status_label.setText("已断开连接")
        self.video_display.setText("等待连接...")

        # 重新启用ROI控件
        self.roi_enabled_checkbox.setEnabled(True)
        if self.roi_enabled_checkbox.isChecked():
            self.roi_reset_button.setEnabled(True)

    @pyqtSlot(np.ndarray)
    def on_image_received(self, image):
        """接收到图像"""
        self.current_frame = image.copy()

        # 更新显示
        self.video_display.update_image(image)

        # 如果正在录制，处理并写入帧
        if self.recorder.is_recording:
            # 获取要保存的图像（可能经过ROI裁剪）
            frame_to_save = self.get_frame_for_recording(image)
            self.recorder.write_frame(frame_to_save)
            self.frame_counter.setText(f"帧数: {self.recorder.frame_count}")

    def get_frame_for_recording(self, image: np.ndarray) -> np.ndarray:
        """获取用于录制的帧（应用ROI裁剪）"""
        if self.video_display.has_valid_roi():
            return self.video_display.get_cropped_image(image)
        return image

    @pyqtSlot(bool, str)
    def on_connection_status_changed(self, connected, message):
        """连接状态改变"""
        self.is_connected = connected
        self.status_label.setText(message)

        if connected:
            self.connect_button.setText("断开")
            self.record_button.setEnabled(True)
        else:
            self.connect_button.setText("连接")
            self.record_button.setEnabled(False)

            # 如果正在录制，停止录制
            if self.recorder.is_recording:
                self.stop_recording()

        self.connect_button.setEnabled(True)

    def on_roi_enabled_changed(self, enabled: bool):
        """ROI启用状态改变"""
        self.video_display.set_roi_enabled(enabled)
        self.roi_reset_button.setEnabled(enabled)

        if enabled:
            self.video_display.set_cursor_for_roi()
            self.status_label.setText("ROI模式已启用 - 拖拽鼠标选择录制区域")
        else:
            self.video_display.reset_roi()
            self.roi_info_label.setText("ROI: 未设置")
            self.status_label.setText("ROI模式已禁用")

    def on_roi_changed(self, roi_rect):
        """ROI区域改变"""
        from PyQt6.QtCore import QRect

        if roi_rect.isEmpty():
            self.roi_info_label.setText("ROI: 未设置")
            self.roi_rect = None
        else:
            self.roi_rect = roi_rect
            self.roi_info_label.setText(f"ROI: {roi_rect.width()}×{roi_rect.height()} (x:{roi_rect.x()}, y:{roi_rect.y()})")
            self.status_label.setText("ROI已设置 - 录制时将使用此区域")

    def reset_roi(self):
        """重置ROI"""
        self.video_display.reset_roi()
        self.roi_info_label.setText("ROI: 未设置")
        self.roi_rect = None
        self.status_label.setText("ROI已重置")

    def browse_save_path(self):
        """浏览保存路径"""
        # 获取当前文件名作为默认值
        current_filename = self.save_path_input.text() or f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择保存路径",
            current_filename,
            "视频文件 (*.mp4);;所有文件 (*)"
        )

        if file_path:
            self.save_path_input.setText(file_path)

    def generate_filename(self):
        """生成新的文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"recording_{timestamp}.mp4"
        self.save_path_input.setText(filename)

        # 显示提示信息
        self.status_label.setText(f"已生成文件名: {filename}")

    def toggle_recording(self):
        """切换录制状态"""
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录制"""
        if self.current_frame is None:
            QMessageBox.warning(self, "警告", "没有接收到视频帧")
            return

        save_path = self.save_path_input.text().strip()
        if not save_path:
            QMessageBox.warning(self, "警告", "请设置保存路径")
            return

        # 获取用于录制的帧（可能经过ROI裁剪）
        frame_for_recording = self.get_frame_for_recording(self.current_frame)
        h, w = frame_for_recording.shape[:2]
        frame_size = (w, h)

        # 检查ROI裁剪后的尺寸是否合理
        if w < 10 or h < 10:
            QMessageBox.warning(self, "警告", "ROI区域太小，无法录制。请调整ROI区域或禁用ROI。")
            return

        # 开始录制
        if self.recorder.start_recording(save_path, frame_size):
            self.record_button.setText("停止录制")
            self.record_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.ERROR}; }}")

            # 开始计时
            self.recording_start_time = datetime.now()
            self.recording_timer.start(1000)  # 每秒更新一次

            # 显示录制信息
            roi_info = ""
            if self.video_display.has_valid_roi():
                roi_rect = self.video_display.get_original_roi()
                roi_info = f" (ROI: {roi_rect.width()}×{roi_rect.height()})"

            self.status_label.setText(f"正在录制{roi_info}...")

            # 禁用ROI相关控件，防止录制时修改
            self.roi_enabled_checkbox.setEnabled(False)
            self.roi_reset_button.setEnabled(False)
        else:
            QMessageBox.critical(self, "错误", "开始录制失败")

    def stop_recording(self):
        """停止录制"""
        output_path, frame_count = self.recorder.stop_recording()

        self.record_button.setText("开始录制")
        self.record_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.SUCCESS}; }}")

        # 停止计时
        self.recording_timer.stop()

        # 重新启用ROI控件
        self.roi_enabled_checkbox.setEnabled(True)
        if self.roi_enabled_checkbox.isChecked():
            self.roi_reset_button.setEnabled(True)

        if frame_count > 0:
            # 显示录制完成信息
            roi_info = ""
            if self.video_display.has_valid_roi():
                roi_rect = self.video_display.get_original_roi()
                roi_info = f" (ROI区域: {roi_rect.width()}×{roi_rect.height()})"

            self.status_label.setText(f"录制完成 - 共 {frame_count} 帧{roi_info}")

            # 询问是否打开标注页面
            reply = QMessageBox.question(
                self,
                "录制完成",
                f"录制完成！\n文件保存到: {output_path}\n共录制 {frame_count} 帧{roi_info}\n\n是否切换到标注页面？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.recording_completed.emit(output_path)
        else:
            self.status_label.setText("录制失败")

    def update_recording_time(self):
        """更新录制时间显示"""
        if self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            seconds = int(elapsed.total_seconds())
            minutes = seconds // 60
            seconds = seconds % 60
            self.recording_time_label.setText(f"录制时间: {minutes:02d}:{seconds:02d}")

    def closeEvent(self, event):
        """关闭事件"""
        # 停止录制
        if self.recorder.is_recording:
            self.stop_recording()

        # 断开连接
        if self.is_connected:
            self.disconnect_websocket()

        event.accept()
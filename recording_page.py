"""
视频录制页面
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
from PyQt6.QtGui import QPixmap, QImage
from styles import StyleSheet, ColorPalette


class WebSocketImageReceiver(QThread):
    """WebSocket图像接收线程"""

    image_received = pyqtSignal(np.ndarray)
    connection_status_changed = pyqtSignal(bool, str)  # connected, message

    def __init__(self, ip_address, port=8080):
        super().__init__()
        self.ip_address = ip_address
        self.port = port
        self.ws = None
        self.running = False

    def run(self):
        """运行WebSocket连接"""
        try:
            url = f"ws://{self.ip_address}:{self.port}"
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            self.running = True
            self.ws.run_forever()
        except Exception as e:
            self.connection_status_changed.emit(False, f"连接失败: {str(e)}")

    def on_open(self, ws):
        """连接打开"""
        self.connection_status_changed.emit(True, "已连接")

    def on_message(self, ws, message):
        """接收消息"""
        try:
            # 假设接收的是JPEG图像数据
            img_array = np.frombuffer(message, dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if image is not None:
                self.image_received.emit(image)
        except Exception as e:
            print(f"解析图像失败: {e}")

    def on_error(self, ws, error):
        """连接错误"""
        self.connection_status_changed.emit(False, f"连接错误: {str(error)}")

    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        self.connection_status_changed.emit(False, "连接已断开")

    def stop(self):
        """停止连接"""
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

    def start_recording(self, output_path: str, frame_size: tuple, fps: int = 30):
        """开始录制"""
        try:
            self.output_path = output_path
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
            self.is_recording = True
            self.frame_count = 0
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
        return self.output_path, self.frame_count


class RecordingPage(QWidget):
    """视频录制页面"""

    # 信号定义
    recording_completed = pyqtSignal(str)  # 录制完成，传递视频文件路径

    def __init__(self, parent=None):
        super().__init__(parent)

        # 组件
        self.ws_receiver = None
        self.recorder = VideoRecorder()

        # UI组件
        self.ip_input = None
        self.port_input = None
        self.connect_button = None
        self.video_display = None
        self.status_label = None
        self.record_button = None
        self.save_path_input = None
        self.fps_input = None
        self.frame_counter = None
        self.recording_time_label = None

        # 状态
        self.is_connected = False
        self.current_frame = None
        self.recording_start_time = None

        # 定时器
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_time)

        self.setup_ui()
        self.setup_connections()

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
        self.ip_input = QLineEdit("192.168.1.100")
        self.ip_input.setPlaceholderText("例如: 192.168.1.100")
        layout.addWidget(self.ip_input)

        # 端口输入
        layout.addWidget(QLabel("端口:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1000, 65535)
        self.port_input.setValue(8080)
        layout.addWidget(self.port_input)

        # 连接按钮
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)

        return group

    def create_display_group(self) -> QGroupBox:
        """创建视频显示组"""
        group = QGroupBox("视频预览")
        layout = QVBoxLayout(group)

        # 视频显示标签
        self.video_display = QLabel()
        self.video_display.setMinimumSize(640, 480)
        self.video_display.setStyleSheet("border: 2px solid #555; background-color: black;")
        self.video_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_display.setText("等待连接...")
        layout.addWidget(self.video_display)

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

        params_layout.addWidget(QLabel("帧率:"))
        self.fps_input = QSpinBox()
        self.fps_input.setRange(1, 60)
        self.fps_input.setValue(30)
        self.fps_input.setSuffix(" fps")
        params_layout.addWidget(self.fps_input)

        params_layout.addStretch()

        # 自动生成文件名
        auto_name_checkbox = QCheckBox("自动生成文件名")
        auto_name_checkbox.setChecked(True)
        auto_name_checkbox.toggled.connect(self.toggle_auto_filename)
        params_layout.addWidget(auto_name_checkbox)

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
        port = self.port_input.value()

        if not ip:
            QMessageBox.warning(self, "警告", "请输入IP地址")
            return

        # 创建WebSocket接收器
        self.ws_receiver = WebSocketImageReceiver(ip, port)
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

    @pyqtSlot(np.ndarray)
    def on_image_received(self, image):
        """接收到图像"""
        self.current_frame = image.copy()

        # 显示图像
        self.display_image(image)

        # 如果正在录制，写入帧
        if self.recorder.is_recording:
            self.recorder.write_frame(image)
            self.frame_counter.setText(f"帧数: {self.recorder.frame_count}")

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

    def display_image(self, image):
        """显示图像"""
        try:
            # 转换为RGB格式
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape

            # 缩放以适应显示区域
            display_size = self.video_display.size()
            if display_size.width() > 0 and display_size.height() > 0:
                aspect_ratio = w / h
                display_aspect = display_size.width() / display_size.height()

                if aspect_ratio > display_aspect:
                    new_w = display_size.width()
                    new_h = int(new_w / aspect_ratio)
                else:
                    new_h = display_size.height()
                    new_w = int(new_h * aspect_ratio)

                rgb_image = cv2.resize(rgb_image, (new_w, new_h))

            # 转换为QImage
            bytes_per_line = ch * rgb_image.shape[1]
            qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0],
                            bytes_per_line, QImage.Format.Format_RGB888)

            # 显示
            pixmap = QPixmap.fromImage(qt_image)
            self.video_display.setPixmap(pixmap)

        except Exception as e:
            print(f"显示图像失败: {e}")

    def browse_save_path(self):
        """浏览保存路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择保存路径",
            f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
            "视频文件 (*.mp4);;所有文件 (*)"
        )

        if file_path:
            self.save_path_input.setText(file_path)

    def toggle_auto_filename(self, checked):
        """切换自动文件名"""
        if checked:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.save_path_input.setText(f"recording_{timestamp}.mp4")

    def toggle_recording(self):
        """切换录制状态"""
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始录制"""
        if not self.current_frame is not None:
            QMessageBox.warning(self, "警告", "没有接收到视频帧")
            return

        save_path = self.save_path_input.text().strip()
        if not save_path:
            QMessageBox.warning(self, "警告", "请设置保存路径")
            return

        # 获取帧尺寸
        h, w = self.current_frame.shape[:2]
        frame_size = (w, h)
        fps = self.fps_input.value()

        # 开始录制
        if self.recorder.start_recording(save_path, frame_size, fps):
            self.record_button.setText("停止录制")
            self.record_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.ERROR}; }}")

            # 开始计时
            self.recording_start_time = datetime.now()
            self.recording_timer.start(1000)  # 每秒更新一次

            self.status_label.setText("正在录制...")
        else:
            QMessageBox.critical(self, "错误", "开始录制失败")

    def stop_recording(self):
        """停止录制"""
        output_path, frame_count = self.recorder.stop_recording()

        self.record_button.setText("开始录制")
        self.record_button.setStyleSheet(f"QPushButton {{ background-color: {ColorPalette.SUCCESS}; }}")

        # 停止计时
        self.recording_timer.stop()

        if frame_count > 0:
            self.status_label.setText(f"录制完成 - 共 {frame_count} 帧")

            # 询问是否打开标注页面
            reply = QMessageBox.question(
                self,
                "录制完成",
                f"录制完成！\n文件保存到: {output_path}\n共录制 {frame_count} 帧\n\n是否切换到标注页面？",
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
"""
支持ROI选择的视频显示控件
"""
import cv2
import numpy as np
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QImage, QBrush


class ROIVideoWidget(QLabel):
    """支持ROI选择的视频显示控件"""

    roi_changed = pyqtSignal(QRect)  # ROI区域改变信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("border: 2px solid #555; background-color: black;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("等待连接...")

        # ROI相关属性
        self.roi_enabled = False
        self.roi_rect = QRect()  # 显示坐标系中的ROI
        self.original_roi_rect = QRect()  # 原始图像坐标系中的ROI
        self.is_drawing = False
        self.start_point = QPoint()
        self.current_pixmap = None
        self.original_image = None
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0

    def set_roi_enabled(self, enabled: bool):
        """设置ROI功能是否启用"""
        self.roi_enabled = enabled
        if not enabled:
            self.roi_rect = QRect()
            self.original_roi_rect = QRect()
        self.update()

    def reset_roi(self):
        """重置ROI区域"""
        self.roi_rect = QRect()
        self.original_roi_rect = QRect()
        self.roi_changed.emit(QRect())
        self.update()

    def get_original_roi(self) -> QRect:
        """获取原始图像坐标系中的ROI"""
        return self.original_roi_rect

    def has_valid_roi(self) -> bool:
        """检查是否有有效的ROI"""
        return self.roi_enabled and not self.original_roi_rect.isEmpty()

    def update_image(self, image: np.ndarray):
        """更新显示的图像"""
        try:
            self.original_image = image.copy()

            # 转换为RGB格式
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape

            # 计算缩放和偏移参数
            widget_size = self.size()
            if widget_size.width() > 0 and widget_size.height() > 0:
                aspect_ratio = w / h
                widget_aspect = widget_size.width() / widget_size.height()

                if aspect_ratio > widget_aspect:
                    # 图像更宽，按宽度缩放
                    display_width = widget_size.width()
                    display_height = int(display_width / aspect_ratio)
                    self.display_offset_x = 0
                    self.display_offset_y = (widget_size.height() - display_height) // 2
                else:
                    # 图像更高，按高度缩放
                    display_height = widget_size.height()
                    display_width = int(display_height * aspect_ratio)
                    self.display_offset_x = (widget_size.width() - display_width) // 2
                    self.display_offset_y = 0

                # 计算缩放因子
                self.scale_factor_x = w / display_width
                self.scale_factor_y = h / display_height

                # 缩放图像
                rgb_image = cv2.resize(rgb_image, (display_width, display_height))

            # 转换为QImage
            bytes_per_line = ch * rgb_image.shape[1]
            qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0],
                              bytes_per_line, QImage.Format.Format_RGB888)

            # 转换为QPixmap
            self.current_pixmap = QPixmap.fromImage(qt_image)
            self.setPixmap(self.current_pixmap)

        except Exception as e:
            print(f"更新图像失败: {e}")

    def get_cropped_image(self, image: np.ndarray) -> np.ndarray:
        """根据ROI裁剪图像"""
        if not self.has_valid_roi():
            return image

        roi = self.original_roi_rect
        # 确保ROI在图像范围内
        h, w = image.shape[:2]
        x = max(0, min(roi.x(), w - 1))
        y = max(0, min(roi.y(), h - 1))
        x2 = max(x + 1, min(roi.x() + roi.width(), w))
        y2 = max(y + 1, min(roi.y() + roi.height(), h))

        return image[y:y2, x:x2]

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if not self.roi_enabled or event.button() != Qt.MouseButton.LeftButton:
            return

        # 检查点击是否在图像区域内
        if self.current_pixmap and self._is_point_in_image(event.pos()):
            self.is_drawing = True
            self.start_point = event.pos()
            self.roi_rect = QRect(self.start_point, self.start_point)

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not self.roi_enabled or not self.is_drawing:
            return

        if self.current_pixmap and self._is_point_in_image(event.pos()):
            # 更新ROI矩形
            self.roi_rect = QRect(self.start_point, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if not self.roi_enabled or event.button() != Qt.MouseButton.LeftButton:
            return

        if self.is_drawing:
            self.is_drawing = False

            # 将显示坐标转换为原始图像坐标
            if not self.roi_rect.isEmpty():
                self._convert_display_roi_to_original()
                self.roi_changed.emit(self.original_roi_rect)

    def _is_point_in_image(self, point: QPoint) -> bool:
        """检查点是否在图像显示区域内"""
        if not self.current_pixmap:
            return False

        image_rect = QRect(
            self.display_offset_x,
            self.display_offset_y,
            self.current_pixmap.width(),
            self.current_pixmap.height()
        )
        return image_rect.contains(point)

    def _convert_display_roi_to_original(self):
        """将显示坐标系的ROI转换为原始图像坐标系"""
        if self.roi_rect.isEmpty():
            self.original_roi_rect = QRect()
            return

        # 调整ROI坐标（减去偏移量）
        adjusted_rect = QRect(
            self.roi_rect.x() - self.display_offset_x,
            self.roi_rect.y() - self.display_offset_y,
            self.roi_rect.width(),
            self.roi_rect.height()
        )

        # 缩放到原始图像坐标
        original_x = int(adjusted_rect.x() * self.scale_factor_x)
        original_y = int(adjusted_rect.y() * self.scale_factor_y)
        original_width = int(adjusted_rect.width() * self.scale_factor_x)
        original_height = int(adjusted_rect.height() * self.scale_factor_y)

        self.original_roi_rect = QRect(original_x, original_y, original_width, original_height)

    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)

        # 绘制ROI矩形
        if self.roi_enabled and not self.roi_rect.isEmpty():
            painter = QPainter(self)

            # 设置ROI矩形样式
            pen = QPen(QColor(0, 255, 0), 2)  # 绿色边框
            painter.setPen(pen)

            # 设置半透明填充
            brush = QBrush(QColor(0, 255, 0, 50))  # 半透明绿色
            painter.setBrush(brush)

            # 绘制ROI矩形
            painter.drawRect(self.roi_rect)

            # 绘制ROI信息文本
            if not self.roi_rect.isEmpty():
                info_text = f"ROI: {self.roi_rect.width()}x{self.roi_rect.height()}"
                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.drawText(self.roi_rect.bottomRight() + QPoint(5, 0), info_text)

    def set_cursor_for_roi(self):
        """设置ROI模式的鼠标样式"""
        if self.roi_enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
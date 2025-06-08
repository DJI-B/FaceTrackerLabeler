"""
自定义时间线控件
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
from typing import List
from models import AnnotationMarker
from styles import ColorPalette


class TimelineWidget(QWidget):
    """自定义时间线控件"""

    position_changed = pyqtSignal(float)
    annotation_clicked = pyqtSignal(AnnotationMarker)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setMinimumWidth(600)
        self.setMouseTracking(True)

        # 时间轴属性
        self.duration = 100.0
        self.position = 0.0
        self.annotations: List[AnnotationMarker] = []

        # 绘制属性
        self.margin = 30
        self.timeline_height = 8
        self.marker_height = 25
        self.scale_height = 15
        self.is_dragging = False
        self.hover_annotation = None

        # 颜色配置
        self.bg_color = QColor(ColorPalette.BACKGROUND)
        self.timeline_color = QColor(100, 100, 100)
        self.timeline_active_color = QColor(ColorPalette.PRIMARY)
        self.playhead_color = QColor(255, 255, 255)
        self.text_color = QColor(ColorPalette.ON_SURFACE)

    def set_duration(self, duration: float):
        """设置视频时长"""
        self.duration = max(1.0, duration)
        self.update()

    def set_position(self, position: float):
        """设置播放位置"""
        self.position = max(0, min(position, self.duration))
        self.update()

    def add_annotation(self, annotation: AnnotationMarker):
        """添加标注"""
        self.annotations.append(annotation)
        self.update()

    def remove_annotation(self, annotation: AnnotationMarker):
        """移除标注"""
        if annotation in self.annotations:
            self.annotations.remove(annotation)
            self.update()

    def clear_annotations(self):
        """清空所有标注"""
        self.annotations.clear()
        self.update()

    def time_to_x(self, time_pos: float) -> int:
        """将时间转换为x坐标"""
        if self.duration <= 0:
            return self.margin
        width = self.width() - 2 * self.margin
        return self.margin + int((time_pos / self.duration) * width)

    def x_to_time(self, x: int) -> float:
        """将x坐标转换为时间"""
        width = self.width() - 2 * self.margin
        relative_x = max(0, min(x - self.margin, width))
        if width <= 0:
            return 0.0
        return (relative_x / width) * self.duration

    def get_annotation_at_point(self, x: int, y: int) -> AnnotationMarker:
        """获取指定坐标处的标注"""
        time_pos = self.x_to_time(x)

        # 检查是否在标注区域内
        annotation_y = self.height() // 2 - self.marker_height // 2
        if y < annotation_y or y > annotation_y + self.marker_height:
            return None

        # 查找包含该时间点的标注
        for annotation in self.annotations:
            if annotation.start_time <= time_pos <= annotation.end_time:
                return annotation

        return None

    def paintEvent(self, event):
        """绘制时间线"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景
        painter.fillRect(self.rect(), self.bg_color)

        # 绘制时间刻度
        self.draw_time_scale(painter)

        # 绘制时间线轨道
        self.draw_timeline_track(painter)

        # 绘制标注区间
        for annotation in self.annotations:
            self.draw_annotation(painter, annotation)

        # 绘制播放头
        self.draw_playhead(painter)

    def draw_time_scale(self, painter: QPainter):
        """绘制时间刻度"""
        painter.setPen(QPen(self.text_color, 1))
        painter.setFont(QFont("Arial", 8))

        # 计算刻度间隔
        mark_interval = max(1, int(self.duration / 10))
        if mark_interval < 5:
            mark_interval = 1
        elif mark_interval < 30:
            mark_interval = 5
        else:
            mark_interval = 30

        scale_y = self.height() - self.scale_height

        for i in range(0, int(self.duration) + 1, mark_interval):
            x = self.time_to_x(i)

            # 刻度线
            painter.drawLine(x, scale_y, x, self.height() - 5)

            # 时间文字
            time_text = f"{i // 60:02d}:{i % 60:02d}"
            text_rect = painter.fontMetrics().boundingRect(time_text)
            painter.drawText(x - text_rect.width() // 2, self.height() - 2, time_text)

    def draw_timeline_track(self, painter: QPainter):
        """绘制时间线轨道"""
        track_y = (self.height() - self.scale_height - self.timeline_height) // 2
        timeline_rect = QRect(
            self.margin,
            track_y,
            self.width() - 2 * self.margin,
            self.timeline_height
        )

        # 轨道背景
        painter.fillRect(timeline_rect, self.timeline_color)

        # 已播放部分
        if self.position > 0:
            played_width = int((self.position / self.duration) * timeline_rect.width())
            played_rect = QRect(
                timeline_rect.x(),
                timeline_rect.y(),
                played_width,
                timeline_rect.height()
            )
            painter.fillRect(played_rect, self.timeline_active_color)

    def draw_annotation(self, painter: QPainter, annotation: AnnotationMarker):
        """绘制标注区间"""
        start_x = self.time_to_x(annotation.start_time)
        end_x = self.time_to_x(annotation.end_time)
        width = max(end_x - start_x, 2)  # 最小宽度2像素

        annotation_y = (self.height() - self.scale_height - self.marker_height) // 2
        annotation_rect = QRect(start_x, annotation_y, width, self.marker_height)

        # 标注颜色
        color = QColor(annotation.color)

        # 高亮悬停的标注
        if annotation == self.hover_annotation:
            color = color.lighter(120)

        # 绘制标注背景
        color.setAlpha(150)
        painter.fillRect(annotation_rect, color)

        # 绘制边框
        color.setAlpha(255)
        painter.setPen(QPen(color, 2))
        painter.drawRect(annotation_rect)

        # 绘制标签文字
        if width > 40:  # 只在区间足够宽时显示标签
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

            # 文字居中显示
            text_rect = painter.fontMetrics().boundingRect(annotation.label)
            text_x = annotation_rect.x() + (annotation_rect.width() - text_rect.width()) // 2
            text_y = annotation_rect.y() + (annotation_rect.height() + text_rect.height()) // 2

            painter.drawText(text_x, text_y, annotation.label)

    def draw_playhead(self, painter: QPainter):
        """绘制播放头"""
        x = self.time_to_x(self.position)

        # 播放头线条
        painter.setPen(QPen(self.playhead_color, 3))
        painter.drawLine(x, 20, x, self.height() - self.scale_height - 5)

        # 播放头三角形
        triangle_size = 10
        points = [
            QPoint(x, 20),
            QPoint(x - triangle_size // 2, 20 - triangle_size),
            QPoint(x + triangle_size // 2, 20 - triangle_size)
        ]
        painter.setBrush(QBrush(self.playhead_color))
        painter.setPen(QPen(self.playhead_color))
        painter.drawPolygon(points)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击了标注
            annotation = self.get_annotation_at_point(
                int(event.position().x()),
                int(event.position().y())
            )

            if annotation:
                self.annotation_clicked.emit(annotation)
            else:
                # 拖拽时间线
                self.is_dragging = True
                new_time = self.x_to_time(int(event.position().x()))
                self.set_position(new_time)
                self.position_changed.emit(self.position)

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 检查悬停的标注
        annotation = self.get_annotation_at_point(
            int(event.position().x()),
            int(event.position().y())
        )

        if annotation != self.hover_annotation:
            self.hover_annotation = annotation
            self.update()

        # 设置鼠标样式
        if annotation:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        # 拖拽更新位置
        if self.is_dragging:
            new_time = self.x_to_time(int(event.position().x()))
            self.set_position(new_time)
            self.position_changed.emit(self.position)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.is_dragging = False

    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self.hover_annotation:
            self.hover_annotation = None
            self.update()
        self.setCursor(Qt.CursorShape.ArrowCursor)

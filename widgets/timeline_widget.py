"""
多标签支持的时间线控件
"""
from PyQt6.QtWidgets import QWidget, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
from typing import List
from models import AnnotationMarker
from styles import ColorPalette, FacialActionConfig


class MultiLabelTimelineWidget(QWidget):
    """支持多标签的时间线控件"""

    position_changed = pyqtSignal(float)
    annotation_clicked = pyqtSignal(AnnotationMarker)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)  # 增加高度以支持多标签显示
        self.setMinimumWidth(600)
        self.setMouseTracking(True)

        # 时间轴属性
        self.duration = 100.0
        self.position = 0.0
        self.annotations: List[AnnotationMarker] = []

        # 绘制属性
        self.margin = 30
        self.timeline_height = 8
        self.marker_height = 35  # 增加标记高度
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
            self.draw_multi_label_annotation(painter, annotation)

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

    def draw_multi_label_annotation(self, painter: QPainter, annotation: AnnotationMarker):
        """绘制多标签标注区间"""
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

        # 绘制多标签指示器
        if len(annotation.labels) > 1:
            self.draw_multi_label_indicator(painter, annotation_rect, len(annotation.labels))

        # 绘制标签文字
        self.draw_annotation_text(painter, annotation_rect, annotation, width)

    def draw_multi_label_indicator(self, painter: QPainter, rect: QRect, label_count: int):
        """绘制多标签指示器"""
        # 在右上角绘制标签数量标识
        indicator_size = 16
        indicator_x = rect.right() - indicator_size - 2
        indicator_y = rect.top() + 2

        indicator_rect = QRect(indicator_x, indicator_y, indicator_size, indicator_size)

        # 绘制圆形背景
        painter.setBrush(QBrush(QColor(255, 165, 0, 200)))  # 橙色背景
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawEllipse(indicator_rect)

        # 绘制数字
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.drawText(indicator_rect, Qt.AlignmentFlag.AlignCenter, str(label_count))

    def draw_annotation_text(self, painter: QPainter, rect: QRect, annotation: AnnotationMarker, width: int):
        """绘制标注文字"""
        if width > 60:  # 只在区间足够宽时显示标签
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

            # 多标签显示策略
            if len(annotation.labels) == 1:
                # 单标签：显示中文名称
                chinese_label = FacialActionConfig.get_chinese_label(annotation.labels[0].label)
                display_text = chinese_label
            elif len(annotation.labels) <= 3:
                # 少量多标签：显示简化中文名称
                chinese_labels = [FacialActionConfig.get_chinese_label(lc.label) for lc in annotation.labels[:3]]
                display_text = ", ".join(chinese_labels)
            else:
                # 大量多标签：显示前两个+数量
                chinese_labels = [FacialActionConfig.get_chinese_label(lc.label) for lc in annotation.labels[:2]]
                display_text = f"{', '.join(chinese_labels)}... (+{len(annotation.labels)-2})"

            # 文字居中显示
            text_rect = painter.fontMetrics().boundingRect(display_text)

            # 如果文字太长，截断显示
            if text_rect.width() > width - 20:
                # 简化显示
                if len(annotation.labels) == 1:
                    # 单标签：截断中文名称
                    chinese_label = FacialActionConfig.get_chinese_label(annotation.labels[0].label)
                    display_text = chinese_label[:4] + "..." if len(chinese_label) > 4 else chinese_label
                else:
                    # 多标签：显示数量
                    display_text = f"{len(annotation.labels)}个动作"

                text_rect = painter.fontMetrics().boundingRect(display_text)

            text_x = rect.x() + (rect.width() - text_rect.width()) // 2
            text_y = rect.y() + (rect.height() + text_rect.height()) // 2

            painter.drawText(text_x, text_y, display_text)

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

            # 显示工具提示
            if annotation:
                self.show_annotation_tooltip(event, annotation)

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

    def show_annotation_tooltip(self, event, annotation: AnnotationMarker):
        """显示标注工具提示"""
        from utils import TimeUtils

        # 构建工具提示内容
        tooltip_lines = []

        # 时间信息
        time_info = f"时间: {TimeUtils.format_time(annotation.start_time)} - {TimeUtils.format_time(annotation.end_time)}"
        tooltip_lines.append(time_info)

        # 标签信息
        if len(annotation.labels) == 1:
            label_config = annotation.labels[0]
            chinese_label = FacialActionConfig.get_chinese_label(label_config.label)
            intensity_info = f"动作: {chinese_label}"
            tooltip_lines.append(intensity_info)
            tooltip_lines.append(f"强度: {label_config.intensity:.2f}")
            tooltip_lines.append(f"模式: {'线性增长' if label_config.progression.value == 'linear' else '恒定强度'}")
        else:
            tooltip_lines.append(f"多标签标注 ({len(annotation.labels)} 个动作):")
            for i, label_config in enumerate(annotation.labels[:5]):  # 最多显示5个
                chinese_label = FacialActionConfig.get_chinese_label(label_config.label)
                mode_text = "线性" if label_config.progression.value == 'linear' else "恒定"
                tooltip_lines.append(f"  {i+1}. {chinese_label} (强度:{label_config.intensity:.2f}, {mode_text})")

            if len(annotation.labels) > 5:
                tooltip_lines.append(f"  ... 还有 {len(annotation.labels) - 5} 个动作")

        tooltip_text = "\n".join(tooltip_lines)

        # 显示工具提示
        global_pos = self.mapToGlobal(event.position().toPoint())
        QToolTip.showText(global_pos, tooltip_text)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.is_dragging = False

    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self.hover_annotation:
            self.hover_annotation = None
            self.update()
        self.setCursor(Qt.CursorShape.ArrowCursor)
        QToolTip.hideText()  # 隐藏工具提示
"""
标注编辑对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QColorDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from styles import StyleSheet, ColorPalette
from utils import TimeUtils


class AnnotationDialog(QDialog):
    """标注编辑对话框"""

    def __init__(self, start_time: float, end_time: float, label: str = "", parent=None):
        super().__init__(parent)
        self.start_time = start_time
        self.end_time = end_time
        self.selected_color = ColorPalette.ANNOTATION_COLORS["默认"]

        self.setup_ui()
        self.setStyleSheet(StyleSheet.DIALOG_STYLE)

        # 设置默认值
        if label:
            self.label_input.setText(label)

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("编辑动作标注")
        self.setFixedSize(450, 250)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 时间信息
        time_info = QLabel(
            f"时间段: {TimeUtils.format_time(self.start_time)} - {TimeUtils.format_time(self.end_time)}"
        )
        time_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #0078d4;")
        layout.addWidget(time_info)

        # 标签输入
        label_layout = QVBoxLayout()
        label_layout.addWidget(QLabel("动作标签:"))
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("输入动作名称...")
        label_layout.addWidget(self.label_input)
        layout.addLayout(label_layout)

        # 快速选择
        quick_layout = QVBoxLayout()
        quick_layout.addWidget(QLabel("快速选择:"))

        quick_buttons_layout = QHBoxLayout()
        quick_actions = ["跳跃", "跑步", "走路", "静止"]

        for action in quick_actions:
            btn = QPushButton(action)
            color = ColorPalette.ANNOTATION_COLORS.get(action, ColorPalette.ANNOTATION_COLORS["默认"])
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background-color: {QColor(color).lighter(110).name()};
                }}
            """)
            btn.clicked.connect(lambda checked, text=action: self.quick_select(text))
            quick_buttons_layout.addWidget(btn)

        quick_layout.addLayout(quick_buttons_layout)
        layout.addLayout(quick_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("标注颜色:"))

        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 25)
        self.color_button.clicked.connect(self.choose_color)
        self.update_color_button()
        color_layout.addWidget(self.color_button)

        color_layout.addStretch()
        layout.addLayout(color_layout)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # 焦点设置
        self.label_input.setFocus()
        self.label_input.selectAll()

    def quick_select(self, label: str):
        """快速选择标签"""
        self.label_input.setText(label)
        color = ColorPalette.ANNOTATION_COLORS.get(label, ColorPalette.ANNOTATION_COLORS["默认"])
        self.selected_color = color
        self.update_color_button()

    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.selected_color = color.name()
            self.update_color_button()

    def update_color_button(self):
        """更新颜色按钮显示"""
        self.color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.selected_color};
                border: 2px solid #666;
                border-radius: 4px;
            }}
        """)

    def get_label(self) -> str:
        """获取标签文本"""
        return self.label_input.text().strip()

    def get_color(self) -> str:
        """获取选择的颜色"""
        return self.selected_color

    def validate_input(self) -> bool:
        """验证输入"""
        return bool(self.get_label())

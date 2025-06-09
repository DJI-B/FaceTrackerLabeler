"""
标注编辑对话框 - 面部动作标注版本
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QColorDialog, QSpinBox, QSlider
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from styles import StyleSheet, ColorPalette, FacialActionConfig
from utils import TimeUtils


class AnnotationDialog(QDialog):
    """标注编辑对话框 - 面部动作版本"""

    def __init__(self, start_time: float, end_time: float, label: str = "", parent=None):
        super().__init__(parent)
        self.start_time = start_time
        self.end_time = end_time
        self.selected_color = ColorPalette.INFO

        self.setup_ui()
        self.setStyleSheet(StyleSheet.DIALOG_STYLE)

        # 设置默认值
        if label:
            # 根据标签设置默认选择
            if label in FacialActionConfig.ALL_LABELS:
                chinese_label = FacialActionConfig.get_chinese_label(label)
                index = self.label_combo.findText(chinese_label)
                if index >= 0:
                    self.label_combo.setCurrentIndex(index)
                    self.on_label_changed()

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("编辑面部动作标注")
        self.setFixedSize(500, 400)
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

        # 动作选择
        label_layout = QVBoxLayout()
        label_layout.addWidget(QLabel("面部动作:"))

        self.label_combo = QComboBox()
        self.label_combo.setMinimumHeight(35)

        # 添加所有面部动作选项
        for english_label in FacialActionConfig.ALL_LABELS:
            chinese_label = FacialActionConfig.get_chinese_label(english_label)
            display_text = f"{chinese_label} ({english_label})"
            self.label_combo.addItem(display_text, english_label)

        self.label_combo.currentTextChanged.connect(self.on_label_changed)
        label_layout.addWidget(self.label_combo)
        layout.addLayout(label_layout)

        # 动作强度设置
        intensity_layout = QVBoxLayout()
        intensity_layout.addWidget(QLabel("动作强度 (0.0 - 1.0):"))

        intensity_control_layout = QHBoxLayout()

        # 滑动条
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(100)  # 默认最大强度
        self.intensity_slider.valueChanged.connect(self.on_intensity_changed)
        intensity_control_layout.addWidget(self.intensity_slider)

        # 数值显示
        self.intensity_spinbox = QSpinBox()
        self.intensity_spinbox.setRange(0, 100)
        self.intensity_spinbox.setValue(100)
        self.intensity_spinbox.setSuffix("%")
        self.intensity_spinbox.valueChanged.connect(self.on_intensity_spinbox_changed)
        intensity_control_layout.addWidget(self.intensity_spinbox)

        intensity_layout.addLayout(intensity_control_layout)
        layout.addLayout(intensity_layout)

        # 快速选择常用动作
        quick_layout = QVBoxLayout()
        quick_layout.addWidget(QLabel("快速选择常用动作:"))

        quick_buttons_layout1 = QHBoxLayout()
        quick_buttons_layout2 = QHBoxLayout()

        # 分两行显示快速按钮
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
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 70px;
                }}
                QPushButton:hover {{
                    background-color: {QColor(color).lighter(110).name()};
                }}
            """)
            btn.clicked.connect(lambda checked, eng=english_action: self.quick_select(eng))

            if i < 4:
                quick_buttons_layout1.addWidget(btn)
            else:
                quick_buttons_layout2.addWidget(btn)

        quick_layout.addLayout(quick_buttons_layout1)
        quick_layout.addLayout(quick_buttons_layout2)
        layout.addLayout(quick_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("标注颜色:"))

        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 25)
        self.color_button.clicked.connect(self.choose_color)
        self.update_color_button()
        color_layout.addWidget(self.color_button)

        # 自动颜色按钮
        auto_color_btn = QPushButton("自动")
        auto_color_btn.setFixedSize(50, 25)
        auto_color_btn.clicked.connect(self.auto_select_color)
        color_layout.addWidget(auto_color_btn)

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

        # 初始化颜色
        self.on_label_changed()

    def quick_select(self, english_label: str):
        """快速选择动作"""
        chinese_label = FacialActionConfig.get_chinese_label(english_label)
        display_text = f"{chinese_label} ({english_label})"

        index = self.label_combo.findText(display_text)
        if index >= 0:
            self.label_combo.setCurrentIndex(index)

    def on_label_changed(self):
        """标签改变时的处理"""
        self.auto_select_color()

    def on_intensity_changed(self, value):
        """强度滑动条改变"""
        self.intensity_spinbox.setValue(value)

    def on_intensity_spinbox_changed(self, value):
        """强度数值框改变"""
        self.intensity_slider.setValue(value)

    def auto_select_color(self):
        """自动选择颜色"""
        english_label = self.get_english_label()
        if english_label:
            color = FacialActionConfig.get_label_color(english_label)
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
        """获取标签文本（返回中文显示名）"""
        current_text = self.label_combo.currentText()
        if current_text:
            # 提取括号中的英文部分
            if '(' in current_text and ')' in current_text:
                start = current_text.find('(') + 1
                end = current_text.find(')')
                return current_text[start:end]
            else:
                # 如果没有括号，尝试从数据中获取
                return self.label_combo.currentData()
        return ""

    def get_english_label(self) -> str:
        """获取英文标签"""
        return self.label_combo.currentData() or ""

    def get_chinese_label(self) -> str:
        """获取中文标签"""
        english_label = self.get_english_label()
        return FacialActionConfig.get_chinese_label(english_label)

    def get_intensity(self) -> float:
        """获取动作强度 (0.0-1.0)"""
        return self.intensity_spinbox.value() / 100.0

    def get_color(self) -> str:
        """获取选择的颜色"""
        return self.selected_color

    def validate_input(self) -> bool:
        """验证输入"""
        return bool(self.get_english_label())
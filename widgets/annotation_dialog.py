"""
多标签标注编辑对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QColorDialog, QSpinBox, QSlider,
    QListWidget, QListWidgetItem, QGroupBox, QCheckBox,
    QButtonGroup, QRadioButton, QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from styles import StyleSheet, ColorPalette, FacialActionConfig
from utils import TimeUtils
from models import LabelConfig, ProgressionType


class LabelConfigWidget(QFrame):
    """单个标签配置控件"""

    config_changed = pyqtSignal()

    def __init__(self, label_config: LabelConfig, parent=None):
        super().__init__(parent)
        self.label_config = label_config
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border: 1px solid #666;
                border-radius: 8px;
                padding: 5px;
                margin: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 标签名称（中文显示）
        chinese_label = FacialActionConfig.get_chinese_label(self.label_config.label)
        self.label_name = QLabel(f"🎯 {chinese_label}")
        self.label_name.setStyleSheet("font-weight: bold; color: #0078d4; font-size: 12px;")
        layout.addWidget(self.label_name)

        # 强度设置
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("强度:"))

        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(int(self.label_config.intensity * 100))
        self.intensity_slider.valueChanged.connect(self.on_intensity_changed)
        intensity_layout.addWidget(self.intensity_slider)

        self.intensity_label = QLabel(f"{self.label_config.intensity:.2f}")
        self.intensity_label.setMinimumWidth(40)
        self.intensity_label.setStyleSheet("font-weight: bold;")
        intensity_layout.addWidget(self.intensity_label)

        layout.addLayout(intensity_layout)

        # 进度模式选择
        mode_group = QGroupBox("进度模式")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_group = QButtonGroup()

        self.linear_radio = QRadioButton("📈 线性增长 (0 → 强度值)")
        self.linear_radio.setToolTip("动作强度从0线性增长到设定值")
        self.mode_group.addButton(self.linear_radio, 0)
        mode_layout.addWidget(self.linear_radio)

        self.constant_radio = QRadioButton("📊 恒定强度 (一直为强度值)")
        self.constant_radio.setToolTip("动作强度在整个时间段内保持恒定")
        self.mode_group.addButton(self.constant_radio, 1)
        mode_layout.addWidget(self.constant_radio)

        # 设置默认选择
        if self.label_config.progression == ProgressionType.LINEAR:
            self.linear_radio.setChecked(True)
        else:
            self.constant_radio.setChecked(True)

        self.mode_group.buttonClicked.connect(self.on_mode_changed)

        layout.addWidget(mode_group)

    def on_intensity_changed(self, value):
        """强度改变"""
        self.label_config.intensity = value / 100.0
        self.intensity_label.setText(f"{self.label_config.intensity:.2f}")
        self.config_changed.emit()

    def on_mode_changed(self):
        """模式改变"""
        if self.linear_radio.isChecked():
            self.label_config.progression = ProgressionType.LINEAR
        else:
            self.label_config.progression = ProgressionType.CONSTANT
        self.config_changed.emit()


class MultiLabelAnnotationDialog(QDialog):
    """多标签标注编辑对话框"""

    def __init__(self, start_time: float, end_time: float, annotation=None, parent=None):
        super().__init__(parent)
        self.start_time = start_time
        self.end_time = end_time
        self.selected_color = ColorPalette.INFO
        self.label_configs = []  # LabelConfig 列表
        self.label_widgets = {}  # 标签配置控件字典

        self.setup_ui()
        self.setStyleSheet(StyleSheet.DIALOG_STYLE)

        # 如果是编辑现有标注，设置默认值
        if annotation:
            self.load_annotation(annotation)

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("编辑多标签面部动作标注")
        self.setFixedSize(700, 600)
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

        # 主要内容区域
        content_layout = QHBoxLayout()

        # 左侧：标签选择
        left_panel = self.create_label_selection_panel()
        content_layout.addWidget(left_panel, 1)

        # 右侧：已选标签配置
        right_panel = self.create_label_config_panel()
        content_layout.addWidget(right_panel, 2)

        layout.addLayout(content_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("标注颜色:"))

        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 25)
        self.color_button.clicked.connect(self.choose_color)
        self.update_color_button()
        color_layout.addWidget(self.color_button)

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

    def create_label_selection_panel(self) -> QWidget:
        """创建标签选择面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 快速选择常用动作
        quick_group = QGroupBox("快速选择常用动作")
        quick_layout = QVBoxLayout(quick_group)

        quick_buttons_layout1 = QHBoxLayout()
        quick_buttons_layout2 = QHBoxLayout()

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
                    padding: 6px 8px;
                    min-width: 60px;
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    background-color: {QColor(color).lighter(110).name()};
                }}
            """)
            btn.clicked.connect(lambda checked, eng=english_action: self.add_label(eng))

            if i < 4:
                quick_buttons_layout1.addWidget(btn)
            else:
                quick_buttons_layout2.addWidget(btn)

        quick_layout.addLayout(quick_buttons_layout1)
        quick_layout.addLayout(quick_buttons_layout2)
        layout.addWidget(quick_group)

        # 所有动作选择
        all_group = QGroupBox("所有面部动作")
        all_layout = QVBoxLayout(all_group)

        self.label_list = QListWidget()
        self.label_list.setMaximumHeight(200)

        # 添加所有动作到列表
        for english_label in FacialActionConfig.ALL_LABELS:
            chinese_label = FacialActionConfig.get_chinese_label(english_label)
            display_text = f"{chinese_label} ({english_label})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, english_label)
            self.label_list.addItem(item)

        self.label_list.itemDoubleClicked.connect(self.on_label_item_double_clicked)
        all_layout.addWidget(self.label_list)

        add_button = QPushButton("添加选中动作")
        add_button.clicked.connect(self.add_selected_label)
        all_layout.addWidget(add_button)

        layout.addWidget(all_group)

        return widget

    def create_label_config_panel(self) -> QWidget:
        """创建标签配置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label_header = QLabel("已选择的动作配置")
        label_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #0078d4;")
        layout.addWidget(label_header)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.config_container = QWidget()
        self.config_layout = QVBoxLayout(self.config_container)
        self.config_layout.setSpacing(5)

        scroll_area.setWidget(self.config_container)
        layout.addWidget(scroll_area)

        # 清空按钮
        clear_btn = QPushButton("清空所有")
        clear_btn.setStyleSheet("background-color: #F44336;")
        clear_btn.clicked.connect(self.clear_all_labels)
        layout.addWidget(clear_btn)

        return widget

    def add_label(self, english_label: str):
        """添加标签"""
        # 检查是否已存在
        if any(lc.label == english_label for lc in self.label_configs):
            return

        # 创建新的标签配置
        label_config = LabelConfig(
            label=english_label,
            intensity=1.0,
            progression=ProgressionType.LINEAR
        )
        self.label_configs.append(label_config)

        # 创建配置控件
        widget = LabelConfigWidget(label_config)
        widget.config_changed.connect(self.on_config_changed)

        # 添加删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("background-color: #F44336; padding: 4px;")
        delete_btn.clicked.connect(lambda: self.remove_label(english_label))

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(widget)
        container_layout.addWidget(delete_btn)

        self.config_layout.addWidget(container)
        self.label_widgets[english_label] = container

        self.update_color()

    def remove_label(self, english_label: str):
        """移除标签"""
        # 从配置列表中移除
        self.label_configs = [lc for lc in self.label_configs if lc.label != english_label]

        # 移除UI控件
        if english_label in self.label_widgets:
            widget = self.label_widgets[english_label]
            self.config_layout.removeWidget(widget)
            widget.deleteLater()
            del self.label_widgets[english_label]

        self.update_color()

    def add_selected_label(self):
        """添加列表中选中的标签"""
        current_item = self.label_list.currentItem()
        if current_item:
            english_label = current_item.data(Qt.ItemDataRole.UserRole)
            self.add_label(english_label)

    def on_label_item_double_clicked(self, item):
        """标签项双击"""
        english_label = item.data(Qt.ItemDataRole.UserRole)
        self.add_label(english_label)

    def clear_all_labels(self):
        """清空所有标签"""
        self.label_configs.clear()

        for widget in self.label_widgets.values():
            self.config_layout.removeWidget(widget)
            widget.deleteLater()

        self.label_widgets.clear()
        self.update_color()

    def on_config_changed(self):
        """配置改变"""
        pass

    def update_color(self):
        """更新颜色"""
        if self.label_configs:
            # 使用第一个标签的颜色
            color = FacialActionConfig.get_label_color(self.label_configs[0].label)
            self.selected_color = color
            self.update_color_button()

    def auto_select_color(self):
        """自动选择颜色"""
        self.update_color()

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

    def load_annotation(self, annotation):
        """加载现有标注"""
        self.selected_color = annotation.color
        self.update_color_button()

        # 添加所有标签
        for label_config in annotation.labels:
            self.add_label(label_config.label)

            # 设置配置
            if label_config.label in self.label_widgets:
                widget_container = self.label_widgets[label_config.label]
                # 找到LabelConfigWidget
                for child in widget_container.findChildren(LabelConfigWidget):
                    child.intensity_slider.setValue(int(label_config.intensity * 100))
                    if label_config.progression == ProgressionType.LINEAR:
                        child.linear_radio.setChecked(True)
                    else:
                        child.constant_radio.setChecked(True)
                    break

    def get_label_configs(self) -> list:
        """获取标签配置列表"""
        return self.label_configs

    def get_color(self) -> str:
        """获取选择的颜色"""
        return self.selected_color

    def validate_input(self) -> bool:
        """验证输入"""
        return len(self.label_configs) > 0
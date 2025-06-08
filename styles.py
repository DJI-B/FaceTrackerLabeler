"""
UI样式和主题配置
"""


class StyleSheet:
    """应用程序样式表"""

    DARK_THEME = """
        QMainWindow {
            background-color: #2b2b2b;
            color: white;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #555;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
            background-color: #3c3c3c;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: white;
        }

        QPushButton {
            background-color: #0078d4;
            border: none;
            border-radius: 6px;
            padding: 10px 16px;
            color: white;
            font-weight: bold;
            min-width: 80px;
            min-height: 20px;
        }

        QPushButton:hover {
            background-color: #106ebe;
        }

        QPushButton:pressed {
            background-color: #005a9e;
        }

        QPushButton:disabled {
            background-color: #555;
            color: #999;
        }

        QListWidget {
            background-color: #3c3c3c;
            border: 1px solid #555;
            border-radius: 5px;
            color: white;
            padding: 5px;
        }

        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #555;
            border-radius: 3px;
            margin: 2px;
        }

        QListWidget::item:selected {
            background-color: #0078d4;
        }

        QListWidget::item:hover {
            background-color: #4a4a4a;
        }

        QLabel {
            color: white;
        }

        QFrame {
            background-color: #3c3c3c;
            border: 1px solid #555;
            border-radius: 5px;
        }

        QVideoWidget {
            background-color: black;
            border: 2px solid #444;
            border-radius: 8px;
        }

        QMenuBar {
            background-color: #3c3c3c;
            color: white;
            border-bottom: 1px solid #555;
        }

        QMenuBar::item {
            padding: 8px 12px;
            background-color: transparent;
        }

        QMenuBar::item:selected {
            background-color: #0078d4;
        }

        QMenu {
            background-color: #3c3c3c;
            color: white;
            border: 1px solid #555;
        }

        QMenu::item {
            padding: 8px 20px;
        }

        QMenu::item:selected {
            background-color: #0078d4;
        }

        QToolBar {
            background-color: #3c3c3c;
            border: 1px solid #555;
            spacing: 3px;
        }

        QStatusBar {
            background-color: #3c3c3c;
            color: white;
            border-top: 1px solid #555;
        }
    """

    DIALOG_STYLE = """
        QDialog {
            background-color: #2b2b2b;
            color: white;
        }

        QLabel {
            color: white;
            font-size: 12px;
        }

        QLineEdit {
            background-color: #3c3c3c;
            border: 2px solid #555;
            border-radius: 5px;
            padding: 8px;
            color: white;
            font-size: 12px;
        }

        QLineEdit:focus {
            border-color: #0078d4;
        }

        QPushButton {
            background-color: #0078d4;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            color: white;
            font-weight: bold;
            min-width: 80px;
        }

        QPushButton:hover {
            background-color: #106ebe;
        }

        QPushButton:pressed {
            background-color: #005a9e;
        }
    """


class ColorPalette:
    """颜色配置"""

    # 主题色
    PRIMARY = "#0078d4"
    PRIMARY_HOVER = "#106ebe"
    PRIMARY_PRESSED = "#005a9e"

    # 背景色
    BACKGROUND = "#2b2b2b"
    SURFACE = "#3c3c3c"
    SURFACE_VARIANT = "#4a4a4a"

    # 文字色
    ON_SURFACE = "#ffffff"
    ON_SURFACE_VARIANT = "#cccccc"
    OUTLINE = "#999999"

    # 功能色
    SUCCESS = "#4CAF50"
    WARNING = "#FF9800"
    ERROR = "#F44336"
    INFO = "#2196F3"

    # 标注颜色
    ANNOTATION_COLORS = {
        "跳跃": "#2196F3",
        "跑步": "#4CAF50",
        "走路": "#FF9800",
        "静止": "#9C27B0",
        "默认": "#607D8B"
    }

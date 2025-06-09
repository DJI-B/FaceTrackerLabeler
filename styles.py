"""
UI样式和主题配置 - 面部动作标注版本
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

        QComboBox {
            background-color: #3c3c3c;
            border: 2px solid #555;
            border-radius: 5px;
            padding: 8px;
            color: white;
            font-size: 12px;
            min-height: 20px;
        }

        QComboBox:focus {
            border-color: #0078d4;
        }

        QComboBox::drop-down {
            border: none;
            background-color: #555;
            width: 20px;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin: 5px;
        }

        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            border: 1px solid #555;
            color: white;
            selection-background-color: #0078d4;
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

        QComboBox {
            background-color: #3c3c3c;
            border: 2px solid #555;
            border-radius: 5px;
            padding: 8px;
            color: white;
            font-size: 12px;
            min-height: 20px;
        }

        QComboBox:focus {
            border-color: #0078d4;
        }

        QComboBox::drop-down {
            border: none;
            background-color: #555;
            width: 20px;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
            margin: 5px;
        }

        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            border: 1px solid #555;
            color: white;
            selection-background-color: #0078d4;
            max-height: 200px;
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

    # 面部动作标注颜色 - 按类别分组
    FACIAL_ACTION_COLORS = {
        # 脸颊动作
        "cheekPuffLeft": "#FF6B6B",
        "cheekPuffRight": "#FF8E8E",
        "cheekSuckLeft": "#4ECDC4",
        "cheekSuckRight": "#6ED5CD",

        # 下巴动作
        "jawOpen": "#45B7D1",
        "jawForward": "#67C3E8",
        "jawLeft": "#96DEDA",
        "jawRight": "#A8E6CF",

        # 鼻部动作
        "noseSneerLeft": "#FFD93D",
        "noseSneerRight": "#FFE066",

        # 嘴部基础动作
        "mouthFunnel": "#6C5CE7",
        "mouthPucker": "#A29BFE",
        "mouthLeft": "#FD79A8",
        "mouthRight": "#FDCB6E",
        "mouthClose": "#E17055",

        # 嘴唇动作
        "mouthRollUpper": "#74B9FF",
        "mouthRollLower": "#00B894",
        "mouthShrugUpper": "#FFEAA7",
        "mouthShrugLower": "#DDA0DD",

        # 微笑动作
        "mouthSmileLeft": "#55A3FF",
        "mouthSmileRight": "#74B9FF",
        "mouthFrownLeft": "#FF7675",
        "mouthFrownRight": "#FA8072",

        # 嘴角细节
        "mouthDimpleLeft": "#F8BBD9",
        "mouthDimpleRight": "#FFB8B8",
        "mouthUpperUpLeft": "#C7ECEE",
        "mouthUpperUpRight": "#DDA0DD",
        "mouthLowerDownLeft": "#FFEAA7",
        "mouthLowerDownRight": "#FFE5B4",

        # 嘴部压力和拉伸
        "mouthPressLeft": "#98D8C8",
        "mouthPressRight": "#C7CEEA",
        "mouthStretchLeft": "#FFB7B2",
        "mouthStretchRight": "#FFDAC1",

        # 舌头动作
        "tongueOut": "#FF69B4",
        "tongueUp": "#DA70D6",
        "tongueDown": "#BA55D3",
        "tongueLeft": "#9370DB",
        "tongueRight": "#8A2BE2",
        "tongueRoll": "#7B68EE",
        "tongueBendDown": "#6495ED",
        "tongueCurlUp": "#4682B4",
        "tongueSquish": "#5F9EA0",
        "tongueFlat": "#48D1CC",
        "tongueTwistLeft": "#40E0D0",
        "tongueTwistRight": "#00CED1"
    }


class FacialActionConfig:
    """面部动作配置"""

    # 英文标签到中文的映射
    LABEL_MAPPING = {
        "cheekPuffLeft": "左脸颊鼓起",
        "cheekPuffRight": "右脸颊鼓起",
        "cheekSuckLeft": "左脸颊收缩",
        "cheekSuckRight": "右脸颊收缩",
        "jawOpen": "张嘴",
        "jawForward": "下巴前伸",
        "jawLeft": "下巴左移",
        "jawRight": "下巴右移",
        "noseSneerLeft": "左鼻翼上提",
        "noseSneerRight": "右鼻翼上提",
        "mouthFunnel": "嘴巴漏斗形",
        "mouthPucker": "撅嘴",
        "mouthLeft": "嘴巴左移",
        "mouthRight": "嘴巴右移",
        "mouthRollUpper": "上唇内卷",
        "mouthRollLower": "下唇内卷",
        "mouthShrugUpper": "上唇耸肩",
        "mouthShrugLower": "下唇耸肩",
        "mouthClose": "闭嘴",
        "mouthSmileLeft": "左嘴角上扬",
        "mouthSmileRight": "右嘴角上扬",
        "mouthFrownLeft": "左嘴角下垂",
        "mouthFrownRight": "右嘴角下垂",
        "mouthDimpleLeft": "左酒窝",
        "mouthDimpleRight": "右酒窝",
        "mouthUpperUpLeft": "左上唇上提",
        "mouthUpperUpRight": "右上唇上提",
        "mouthLowerDownLeft": "左下唇下拉",
        "mouthLowerDownRight": "右下唇下拉",
        "mouthPressLeft": "左嘴角紧压",
        "mouthPressRight": "右嘴角紧压",
        "mouthStretchLeft": "左嘴角拉伸",
        "mouthStretchRight": "右嘴角拉伸",
        "tongueOut": "伸舌头",
        "tongueUp": "舌头上抬",
        "tongueDown": "舌头下压",
        "tongueLeft": "舌头左移",
        "tongueRight": "舌头右移",
        "tongueRoll": "舌头卷曲",
        "tongueBendDown": "舌头向下弯曲",
        "tongueCurlUp": "舌头向上卷曲",
        "tongueSquish": "舌头挤压",
        "tongueFlat": "舌头平展",
        "tongueTwistLeft": "舌头左扭",
        "tongueTwistRight": "舌头右扭"
    }

    # 所有英文标签列表（保持顺序）
    ALL_LABELS = [
        "cheekPuffLeft", "cheekPuffRight", "cheekSuckLeft", "cheekSuckRight",
        "jawOpen", "jawForward", "jawLeft", "jawRight",
        "noseSneerLeft", "noseSneerRight",
        "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
        "mouthRollUpper", "mouthRollLower", "mouthShrugUpper", "mouthShrugLower",
        "mouthClose", "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
        "mouthDimpleLeft", "mouthDimpleRight", "mouthUpperUpLeft", "mouthUpperUpRight",
        "mouthLowerDownLeft", "mouthLowerDownRight", "mouthPressLeft", "mouthPressRight",
        "mouthStretchLeft", "mouthStretchRight",
        "tongueOut", "tongueUp", "tongueDown", "tongueLeft", "tongueRight",
        "tongueRoll", "tongueBendDown", "tongueCurlUp", "tongueSquish", "tongueFlat",
        "tongueTwistLeft", "tongueTwistRight"
    ]

    # 舌头相关动作列表
    TONGUE_ACTIONS = [
        "tongueOut", "tongueUp", "tongueDown", "tongueLeft", "tongueRight",
        "tongueRoll", "tongueBendDown", "tongueCurlUp", "tongueSquish",
        "tongueFlat", "tongueTwistLeft", "tongueTwistRight"
    ]

    # 常用快速标注动作（显示在快捷按钮中）
    QUICK_ACTIONS = [
        "jawOpen", "mouthSmileLeft", "mouthSmileRight", "tongueOut",
        "mouthPucker", "mouthFunnel", "cheekPuffLeft", "cheekPuffRight"
    ]

    @classmethod
    def get_chinese_label(cls, english_label: str) -> str:
        """获取中文标签"""
        return cls.LABEL_MAPPING.get(english_label, english_label)

    @classmethod
    def get_english_label(cls, chinese_label: str) -> str:
        """根据中文标签获取英文标签"""
        for eng, chn in cls.LABEL_MAPPING.items():
            if chn == chinese_label:
                return eng
        return chinese_label

    @classmethod
    def get_label_color(cls, english_label: str) -> str:
        """获取标签对应的颜色"""
        return ColorPalette.FACIAL_ACTION_COLORS.get(english_label, ColorPalette.INFO)

    @classmethod
    def is_tongue_action(cls, english_label: str) -> bool:
        """判断是否为舌头相关动作

        注意：舌头动作的特殊规则
        1. 任何舌头动作激活时，jawOpen自动设为1.0
        2. 其他舌头动作激活时，tongueOut自动设为1.0
        """
        return english_label in cls.TONGUE_ACTIONS
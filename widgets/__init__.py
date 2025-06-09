try:
    from .timeline_widget import TimelineWidget
    from .annotation_dialog import AnnotationDialog
    from .roi_video_widget import ROIVideoWidget
except ImportError as e:
    print(f"控件导入失败: {e}")
    # 提供备用方案
    TimelineWidget = None
    AnnotationDialog = None

# 定义包的公开接口
__all__ = [
    "TimelineWidget",
    "AnnotationDialog",
    "ROIVideoWidget",
    # 可以添加更多控件
]

# 控件注册表 - 方便动态创建控件
WIDGET_REGISTRY = {
    "timeline": TimelineWidget,
    "annotation_dialog": AnnotationDialog,
}

# 控件类型常量
WIDGET_TYPES = {
    "TIMELINE": "timeline",
    "DIALOG": "annotation_dialog",
}

# 默认控件配置
DEFAULT_WIDGET_CONFIGS = {
    "timeline": {
        "height": 100,
        "min_width": 600,
        "margin": 30,
        "timeline_height": 8,
        "marker_height": 25,
        "scale_height": 15
    },
    "annotation_dialog": {
        "width": 450,
        "height": 250,
        "modal": True,
        "resizable": False
    }
}

# 控件样式主题
WIDGET_THEMES = {
    "dark": {
        "background": "#2b2b2b",
        "surface": "#3c3c3c",
        "primary": "#0078d4",
        "text": "#ffffff"
    },
    "light": {
        "background": "#ffffff",
        "surface": "#f5f5f5",
        "primary": "#0078d4",
        "text": "#000000"
    }
}
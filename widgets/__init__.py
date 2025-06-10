try:
    # 导入多标签支持的控件
    from .timeline_widget import MultiLabelTimelineWidget as TimelineWidget
    from .annotation_dialog import MultiLabelAnnotationDialog as AnnotationDialog
    from .roi_video_widget import ROIVideoWidget

    # 为了向后兼容，也提供原始名称
    from .annotation_dialog import MultiLabelAnnotationDialog
    from .timeline_widget import MultiLabelTimelineWidget

except ImportError as e:
    print(f"多标签控件导入失败: {e}")
    # 提供备用方案
    TimelineWidget = None
    AnnotationDialog = None
    MultiLabelAnnotationDialog = None
    MultiLabelTimelineWidget = None
    ROIVideoWidget = None

# 定义包的公开接口 - 多标签版本
__all__ = [
    "TimelineWidget",
    "AnnotationDialog",
    "ROIVideoWidget",
    # 多标签特定接口
    "MultiLabelAnnotationDialog",
    "MultiLabelTimelineWidget",
]

# 控件注册表 - 方便动态创建控件
WIDGET_REGISTRY = {
    "timeline": TimelineWidget,
    "annotation_dialog": AnnotationDialog,
    "multi_label_timeline": MultiLabelTimelineWidget,
    "multi_label_dialog": MultiLabelAnnotationDialog,
    "roi_video": ROIVideoWidget,
}

# 控件类型常量
WIDGET_TYPES = {
    "TIMELINE": "timeline",
    "DIALOG": "annotation_dialog",
    "MULTI_LABEL_TIMELINE": "multi_label_timeline",
    "MULTI_LABEL_DIALOG": "multi_label_dialog",
    "ROI_VIDEO": "roi_video",
}

# 默认控件配置 - 多标签版本
DEFAULT_WIDGET_CONFIGS = {
    "timeline": {
        "height": 120,  # 增加高度以支持多标签显示
        "min_width": 600,
        "margin": 30,
        "timeline_height": 8,
        "marker_height": 35,  # 增加标记高度
        "scale_height": 15,
        "supports_multi_label": True
    },
    "annotation_dialog": {
        "width": 700,  # 增加宽度以容纳多标签界面
        "height": 600,  # 增加高度
        "modal": True,
        "resizable": False,
        "supports_multi_label": True,
        "supports_progression_types": True
    },
    "multi_label_dialog": {
        "width": 700,
        "height": 600,
        "modal": True,
        "resizable": False,
        "max_labels_display": 5,
        "quick_actions_count": 8
    },
    "roi_video": {
        "min_width": 640,
        "min_height": 480,
        "supports_roi": True,
        "roi_color": "green"
    }
}

# 控件样式主题 - 多标签版本
WIDGET_THEMES = {
    "dark": {
        "background": "#2b2b2b",
        "surface": "#3c3c3c",
        "primary": "#0078d4",
        "text": "#ffffff",
        "multi_label_indicator": "#FF9800",  # 多标签指示器颜色
        "progression_linear": "#4CAF50",  # 线性进度颜色
        "progression_constant": "#2196F3"  # 恒定进度颜色
    },
    "light": {
        "background": "#ffffff",
        "surface": "#f5f5f5",
        "primary": "#0078d4",
        "text": "#000000",
        "multi_label_indicator": "#FF9800",
        "progression_linear": "#4CAF50",
        "progression_constant": "#2196F3"
    }
}

# 多标签功能配置
MULTI_LABEL_CONFIG = {
    "max_labels_per_annotation": 10,  # 每个标注最大标签数
    "default_intensity": 1.0,  # 默认强度
    "default_progression": "linear",  # 默认进度类型
    "show_progression_indicator": True,  # 显示进度类型指示器
    "show_intensity_in_tooltip": True,  # 在工具提示中显示强度
    "auto_color_selection": True,  # 自动颜色选择
    "progression_types": {
        "linear": {
            "name": "线性增长",
            "description": "动作强度从0线性增长到设定值",
            "icon": "📈",
            "color": "#4CAF50"
        },
        "constant": {
            "name": "恒定强度",
            "description": "动作强度在整个时间段内保持恒定",
            "icon": "📊",
            "color": "#2196F3"
        }
    }
}


# 控件功能验证
def validate_multi_label_support():
    """验证多标签支持"""
    try:
        # 检查必需的多标签类是否可用
        required_classes = [
            MultiLabelAnnotationDialog,
            MultiLabelTimelineWidget,
        ]

        for cls in required_classes:
            if cls is None:
                return False, f"缺少必需的多标签控件: {cls}"

        return True, "多标签控件支持验证通过"

    except Exception as e:
        return False, f"多标签控件验证失败: {e}"


# 控件兼容性检查
def check_widget_compatibility():
    """检查控件兼容性"""
    compatibility_report = {
        "multi_label_support": False,
        "roi_support": False,
        "timeline_enhanced": False,
        "issues": []
    }

    try:
        # 检查多标签支持
        if MultiLabelAnnotationDialog is not None:
            compatibility_report["multi_label_support"] = True
        else:
            compatibility_report["issues"].append("多标签对话框不可用")

        # 检查ROI支持
        if ROIVideoWidget is not None:
            compatibility_report["roi_support"] = True
        else:
            compatibility_report["issues"].append("ROI视频控件不可用")

        # 检查增强时间线
        if MultiLabelTimelineWidget is not None:
            compatibility_report["timeline_enhanced"] = True
        else:
            compatibility_report["issues"].append("多标签时间线控件不可用")

    except Exception as e:
        compatibility_report["issues"].append(f"兼容性检查异常: {e}")

    return compatibility_report


# 初始化时进行验证
if __name__ == "__main__":
    print("多标签控件包初始化...")

    # 验证多标签支持
    is_valid, message = validate_multi_label_support()
    print(f"多标签支持验证: {message}")

    # 检查兼容性
    compat_report = check_widget_compatibility()
    print(f"兼容性报告: {compat_report}")

    print(f"可用控件: {list(WIDGET_REGISTRY.keys())}")
    print("多标签控件包初始化完成！")
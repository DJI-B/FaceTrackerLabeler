"""
数据模型定义 - 多标签支持版本
"""
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List
from enum import Enum


class ProgressionType(Enum):
    """动作进度类型"""
    LINEAR = "linear"      # 线性增长 (0.0 到 intensity)
    CONSTANT = "constant"  # 常量 (一直为 intensity)


@dataclass
class LabelConfig:
    """单个标签的配置"""
    label: str                           # 英文标签名
    intensity: float = 1.0              # 动作强度 (0.0 - 1.0)
    progression: ProgressionType = ProgressionType.LINEAR  # 进度类型


@dataclass
class AnnotationMarker:
    """多标签标注标记数据类"""
    start_time: float
    end_time: float
    labels: List[LabelConfig] = field(default_factory=list)  # 多个标签配置
    color: str = "#2196F3"
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"marker_{int(time.time() * 1000)}"

        # 确保所有标签的强度值在合理范围内
        for label_config in self.labels:
            label_config.intensity = max(0.0, min(1.0, label_config.intensity))

    @property
    def duration(self) -> float:
        """获取标注持续时间"""
        return self.end_time - self.start_time

    @property
    def primary_label(self) -> str:
        """获取主要标签（用于显示）"""
        if self.labels:
            return self.labels[0].label
        return ""

    @property
    def display_labels(self) -> str:
        """获取用于显示的标签列表"""
        from styles import FacialActionConfig
        chinese_labels = []
        for label_config in self.labels:
            chinese_label = FacialActionConfig.get_chinese_label(label_config.label)
            chinese_labels.append(chinese_label)
        return ", ".join(chinese_labels)

    def get_label_config(self, label: str) -> LabelConfig:
        """获取指定标签的配置"""
        for label_config in self.labels:
            if label_config.label == label:
                return label_config
        return None

    def has_label(self, label: str) -> bool:
        """检查是否包含指定标签"""
        return any(lc.label == label for lc in self.labels)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "labels": [
                {
                    "label": lc.label,
                    "intensity": lc.intensity,
                    "progression": lc.progression.value
                }
                for lc in self.labels
            ],
            "color": self.color,
            "duration": self.duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnnotationMarker':
        """从字典创建标注对象"""
        labels = []
        for label_data in data.get("labels", []):
            progression = ProgressionType(label_data.get("progression", "linear"))
            label_config = LabelConfig(
                label=label_data["label"],
                intensity=label_data.get("intensity", 1.0),
                progression=progression
            )
            labels.append(label_config)

        return cls(
            start_time=data["start_time"],
            end_time=data["end_time"],
            labels=labels,
            color=data.get("color", "#2196F3"),
            id=data.get("id", "")
        )

    def get_chinese_labels(self) -> List[str]:
        """获取中文标签列表"""
        from styles import FacialActionConfig
        return [FacialActionConfig.get_chinese_label(lc.label) for lc in self.labels]

    def has_tongue_action(self) -> bool:
        """判断是否包含舌头相关动作"""
        from styles import FacialActionConfig
        return any(FacialActionConfig.is_tongue_action(lc.label) for lc in self.labels)

    def get_value_at_progress(self, label: str, progress: float) -> float:
        """获取指定标签在特定进度下的数值

        Args:
            label: 标签名
            progress: 进度 (0.0 到 1.0)

        Returns:
            该标签在指定进度下的数值
        """
        label_config = self.get_label_config(label)
        if not label_config:
            return 0.0

        if label_config.progression == ProgressionType.CONSTANT:
            return label_config.intensity
        else:  # LINEAR
            return label_config.intensity * progress


@dataclass
class VideoInfo:
    """视频信息数据类"""
    file_path: str = ""
    duration: float = 0.0
    fps: float = 30.0
    width: int = 0
    height: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_path": self.file_path,
            "duration": self.duration,
            "fps": self.fps,
            "width": self.width,
            "height": self.height
        }
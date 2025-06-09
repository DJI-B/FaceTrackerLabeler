"""
数据模型定义 - 面部动作标注版本
"""
import time
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AnnotationMarker:
    """标注标记数据类 - 支持面部动作和强度"""
    start_time: float
    end_time: float
    label: str  # 存储英文标签
    color: str = "#2196F3"
    id: str = ""
    intensity: float = 1.0  # 动作强度 (0.0 - 1.0)

    def __post_init__(self):
        if not self.id:
            self.id = f"marker_{int(time.time() * 1000)}"

        # 确保强度值在合理范围内
        self.intensity = max(0.0, min(1.0, self.intensity))

    @property
    def duration(self) -> float:
        """获取标注持续时间"""
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "label": self.label,  # 英文标签
            "color": self.color,
            "intensity": self.intensity,
            "duration": self.duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnnotationMarker':
        """从字典创建标注对象"""
        return cls(
            start_time=data["start_time"],
            end_time=data["end_time"],
            label=data["label"],  # 英文标签
            color=data.get("color", "#2196F3"),
            id=data.get("id", ""),
            intensity=data.get("intensity", 1.0)
        )

    def get_chinese_label(self) -> str:
        """获取中文标签显示"""
        from styles import FacialActionConfig
        return FacialActionConfig.get_chinese_label(self.label)

    def is_tongue_action(self) -> bool:
        """判断是否为舌头相关动作"""
        from styles import FacialActionConfig
        return FacialActionConfig.is_tongue_action(self.label)


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
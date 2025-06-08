"""
数据模型定义
"""
import time
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AnnotationMarker:
    """标注标记数据类"""
    start_time: float
    end_time: float
    label: str
    color: str = "#2196F3"
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"marker_{int(time.time() * 1000)}"

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
            "label": self.label,
            "color": self.color,
            "duration": self.duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnnotationMarker':
        """从字典创建标注对象"""
        return cls(
            start_time=data["start_time"],
            end_time=data["end_time"],
            label=data["label"],
            color=data.get("color", "#2196F3"),
            id=data.get("id", "")
        )


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

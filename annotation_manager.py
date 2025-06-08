"""
标注数据管理器
"""
import json
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import QMessageBox
from models import AnnotationMarker, VideoInfo
from utils import FileUtils


class AnnotationManager:
    """标注数据管理器"""

    def __init__(self):
        self.annotations: List[AnnotationMarker] = []
        self.video_info = VideoInfo()
        self.project_file_path = ""
        self.is_modified = False

    def add_annotation(self, annotation: AnnotationMarker) -> bool:
        """添加标注"""
        try:
            # 检查时间重叠
            if self.check_time_overlap(annotation):
                return False

            self.annotations.append(annotation)
            self.annotations.sort(key=lambda x: x.start_time)  # 按开始时间排序
            self.is_modified = True
            return True
        except Exception as e:
            print(f"添加标注失败: {e}")
            return False

    def remove_annotation(self, annotation: AnnotationMarker) -> bool:
        """移除标注"""
        try:
            if annotation in self.annotations:
                self.annotations.remove(annotation)
                self.is_modified = True
                return True
            return False
        except Exception as e:
            print(f"移除标注失败: {e}")
            return False

    def update_annotation(self, old_annotation: AnnotationMarker, new_annotation: AnnotationMarker) -> bool:
        """更新标注"""
        try:
            index = self.annotations.index(old_annotation)
            self.annotations[index] = new_annotation
            self.annotations.sort(key=lambda x: x.start_time)
            self.is_modified = True
            return True
        except (ValueError, Exception) as e:
            print(f"更新标注失败: {e}")
            return False

    def clear_annotations(self):
        """清空所有标注"""
        self.annotations.clear()
        self.is_modified = True

    def get_annotations_at_time(self, time: float) -> List[AnnotationMarker]:
        """获取指定时间点的所有标注"""
        return [ann for ann in self.annotations
                if ann.start_time <= time <= ann.end_time]

    def get_annotations_in_range(self, start_time: float, end_time: float) -> List[AnnotationMarker]:
        """获取指定时间范围内的所有标注"""
        return [ann for ann in self.annotations
                if not (ann.end_time < start_time or ann.start_time > end_time)]

    def check_time_overlap(self, new_annotation: AnnotationMarker, exclude: AnnotationMarker = None) -> bool:
        """检查时间重叠"""
        for annotation in self.annotations:
            if annotation == exclude:
                continue

            # 检查是否有重叠
            if not (new_annotation.end_time <= annotation.start_time or
                    new_annotation.start_time >= annotation.end_time):
                return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.annotations:
            return {
                "total_count": 0,
                "total_duration": 0.0,
                "labels": {},
                "average_duration": 0.0
            }

        total_duration = sum(ann.duration for ann in self.annotations)
        label_stats = {}

        for annotation in self.annotations:
            label = annotation.label
            if label not in label_stats:
                label_stats[label] = {"count": 0, "duration": 0.0}
            label_stats[label]["count"] += 1
            label_stats[label]["duration"] += annotation.duration

        return {
            "total_count": len(self.annotations),
            "total_duration": total_duration,
            "labels": label_stats,
            "average_duration": total_duration / len(self.annotations)
        }

    def export_to_json(self, file_path: str) -> bool:
        """导出为JSON格式"""
        try:
            export_data = {
                "project_info": {
                    "version": "1.0",
                    "created_by": "Video Annotation Tool"
                },
                "video_info": self.video_info.to_dict(),
                "annotations": [ann.to_dict() for ann in self.annotations],
                "statistics": self.get_statistics()
            }

            return FileUtils.save_json(export_data, file_path)
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False

    def import_from_json(self, file_path: str) -> bool:
        """从JSON格式导入"""
        try:
            data = FileUtils.load_json(file_path)
            if not data:
                return False

            # 清空现有数据
            self.clear_annotations()

            # 导入标注
            if "annotations" in data:
                for ann_data in data["annotations"]:
                    annotation = AnnotationMarker.from_dict(ann_data)
                    self.annotations.append(annotation)

            # 导入视频信息
            if "video_info" in data:
                video_data = data["video_info"]
                self.video_info = VideoInfo(
                    file_path=video_data.get("file_path", ""),
                    duration=video_data.get("duration", 0.0),
                    fps=video_data.get("fps", 30.0),
                    width=video_data.get("width", 0),
                    height=video_data.get("height", 0)
                )

            self.is_modified = False
            return True

        except Exception as e:
            print(f"导入JSON失败: {e}")
            return False

    def save_project(self, file_path: str = None) -> bool:
        """保存项目"""
        if not file_path:
            file_path = self.project_file_path

        if not file_path:
            return False

        success = self.export_to_json(file_path)
        if success:
            self.project_file_path = file_path
            self.is_modified = False

        return success

    def load_project(self, file_path: str) -> bool:
        """加载项目"""
        success = self.import_from_json(file_path)
        if success:
            self.project_file_path = file_path
            self.is_modified = False

        return success

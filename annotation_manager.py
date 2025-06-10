"""
多标签标注数据管理器
"""
import json
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import QMessageBox
from models import AnnotationMarker, VideoInfo, LabelConfig, ProgressionType
from utils import FileUtils


class MultiLabelAnnotationManager:
    """多标签标注数据管理器"""

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
        """获取多标签统计信息"""
        if not self.annotations:
            return {
                "total_count": 0,
                "total_duration": 0.0,
                "labels": {},
                "average_duration": 0.0,
                "multi_label_stats": {
                    "single_label_count": 0,
                    "multi_label_count": 0,
                    "max_labels_per_annotation": 0,
                    "total_labels": 0
                },
                "progression_stats": {
                    "linear_count": 0,
                    "constant_count": 0
                }
            }

        total_duration = sum(ann.duration for ann in self.annotations)
        label_stats = {}

        # 多标签统计
        single_label_count = 0
        multi_label_count = 0
        max_labels = 0
        total_labels = 0

        # 进度类型统计
        linear_count = 0
        constant_count = 0

        for annotation in self.annotations:
            # 标注类型统计
            label_count = len(annotation.labels)
            total_labels += label_count
            max_labels = max(max_labels, label_count)

            if label_count == 1:
                single_label_count += 1
            else:
                multi_label_count += 1

            # 标签分布统计
            for label_config in annotation.labels:
                label = label_config.label
                if label not in label_stats:
                    label_stats[label] = {
                        "count": 0,
                        "duration": 0.0,
                        "avg_intensity": 0.0,
                        "linear_count": 0,
                        "constant_count": 0
                    }

                label_stats[label]["count"] += 1
                label_stats[label]["duration"] += annotation.duration
                label_stats[label]["avg_intensity"] += label_config.intensity

                # 进度类型统计
                if label_config.progression == ProgressionType.LINEAR:
                    linear_count += 1
                    label_stats[label]["linear_count"] += 1
                else:
                    constant_count += 1
                    label_stats[label]["constant_count"] += 1

        # 计算平均强度
        for label_data in label_stats.values():
            if label_data["count"] > 0:
                label_data["avg_intensity"] /= label_data["count"]

        return {
            "total_count": len(self.annotations),
            "total_duration": total_duration,
            "labels": label_stats,
            "average_duration": total_duration / len(self.annotations),
            "multi_label_stats": {
                "single_label_count": single_label_count,
                "multi_label_count": multi_label_count,
                "max_labels_per_annotation": max_labels,
                "total_labels": total_labels,
                "avg_labels_per_annotation": total_labels / len(self.annotations)
            },
            "progression_stats": {
                "linear_count": linear_count,
                "constant_count": constant_count,
                "linear_percentage": (linear_count / total_labels * 100) if total_labels > 0 else 0,
                "constant_percentage": (constant_count / total_labels * 100) if total_labels > 0 else 0
            }
        }

    def get_labels_by_type(self) -> Dict[str, List[str]]:
        """获取按类型分组的标签"""
        from styles import FacialActionConfig

        all_used_labels = set()
        for annotation in self.annotations:
            for label_config in annotation.labels:
                all_used_labels.add(label_config.label)

        # 按类型分组
        tongue_labels = [label for label in all_used_labels if FacialActionConfig.is_tongue_action(label)]
        other_labels = [label for label in all_used_labels if not FacialActionConfig.is_tongue_action(label)]

        return {
            "tongue_actions": sorted(tongue_labels),
            "other_actions": sorted(other_labels),
            "all_actions": sorted(all_used_labels)
        }

    def export_to_json(self, file_path: str) -> bool:
        """导出为JSON格式 - 支持多标签"""
        try:
            export_data = {
                "project_info": {
                    "version": "2.0",
                    "created_by": "Multi-Label Video Annotation Tool",
                    "supports_multi_label": True,
                    "supports_progression_types": True
                },
                "video_info": self.video_info.to_dict(),
                "annotations": [ann.to_dict() for ann in self.annotations],
                "statistics": self.get_statistics(),
                "label_grouping": self.get_labels_by_type(),
                "progression_types": {
                    "linear": "动作强度从0线性增长到设定值",
                    "constant": "动作强度在整个时间段内保持恒定"
                }
            }

            return FileUtils.save_json(export_data, file_path)
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False

    def import_from_json(self, file_path: str) -> bool:
        """从JSON格式导入 - 支持多标签"""
        try:
            data = FileUtils.load_json(file_path)
            if not data:
                return False

            # 清空现有数据
            self.clear_annotations()

            # 导入标注
            if "annotations" in data:
                for ann_data in data["annotations"]:
                    try:
                        # 检查是否为新版本多标签格式
                        if "labels" in ann_data and isinstance(ann_data["labels"], list):
                            # 新版本多标签格式
                            annotation = AnnotationMarker.from_dict(ann_data)
                        else:
                            # 兼容旧版本单标签格式
                            annotation = self._convert_from_old_format(ann_data)

                        self.annotations.append(annotation)
                    except Exception as e:
                        print(f"导入标注时出错: {e}, 数据: {ann_data}")
                        continue

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

    def _convert_from_old_format(self, ann_data: Dict[str, Any]) -> AnnotationMarker:
        """将旧版本单标签格式转换为新版本多标签格式"""
        label_config = LabelConfig(
            label=ann_data["label"],
            intensity=ann_data.get("intensity", 1.0),
            progression=ProgressionType.LINEAR  # 旧版本默认为线性
        )

        return AnnotationMarker(
            start_time=ann_data["start_time"],
            end_time=ann_data["end_time"],
            labels=[label_config],  # 转换为标签列表
            color=ann_data.get("color", "#2196F3"),
            id=ann_data.get("id", "")
        )

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

    def validate_annotations(self) -> List[str]:
        """验证标注数据，返回问题列表"""
        issues = []

        for i, annotation in enumerate(self.annotations):
            # 检查时间有效性
            if annotation.start_time >= annotation.end_time:
                issues.append(f"标注 {i+1}: 起始时间大于等于结束时间")

            # 检查是否有标签
            if not annotation.labels:
                issues.append(f"标注 {i+1}: 没有设置任何标签")

            # 检查标签配置
            for j, label_config in enumerate(annotation.labels):
                if not label_config.label:
                    issues.append(f"标注 {i+1}, 标签 {j+1}: 标签名为空")

                if not (0.0 <= label_config.intensity <= 1.0):
                    issues.append(f"标注 {i+1}, 标签 {j+1}: 强度值超出范围 (0.0-1.0)")

        return issues

    def optimize_annotations(self) -> int:
        """优化标注数据，返回优化的数量"""
        optimized_count = 0

        for annotation in self.annotations:
            # 移除重复标签
            seen_labels = set()
            unique_labels = []

            for label_config in annotation.labels:
                if label_config.label not in seen_labels:
                    seen_labels.add(label_config.label)
                    unique_labels.append(label_config)
                else:
                    optimized_count += 1

            annotation.labels = unique_labels

            # 确保强度值在有效范围内
            for label_config in annotation.labels:
                old_intensity = label_config.intensity
                label_config.intensity = max(0.0, min(1.0, label_config.intensity))
                if old_intensity != label_config.intensity:
                    optimized_count += 1

        if optimized_count > 0:
            self.is_modified = True

        return optimized_count
"""
面部动作数据集导出器 - 支持45个动作标签
"""
import os
import cv2
import hashlib
import time
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QMessageBox, QApplication, QFileDialog, QInputDialog,
    QProgressBar, QLabel, QVBoxLayout, QHBoxLayout, QDialog,
    QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from models import AnnotationMarker, VideoInfo
from utils import FileUtils, TimeUtils
from styles import FacialActionConfig


class FacialActionDatasetExporter:
    """面部动作数据集导出器"""

    def __init__(self, video_path: str, annotations: List[AnnotationMarker],
                 output_dir: str, fps: float = 30.0):
        self.video_path = video_path
        self.annotations = annotations
        self.output_dir = output_dir
        self.fps = fps

        # 所有45个动作标签
        self.all_labels = FacialActionConfig.ALL_LABELS

        # 统计信息
        self.stats = {
            "exported_images": 0,
            "exported_labels": 0,
            "total_annotations": len(annotations),
            "label_distribution": {label: 0 for label in self.all_labels},
            "errors": []
        }

    def export_dataset(self, progress_callback=None) -> bool:
        """导出数据集"""
        try:
            if progress_callback:
                progress_callback(0, "创建输出目录...")

            # 创建输出目录
            images_dir = Path(self.output_dir) / "images"
            labels_dir = Path(self.output_dir) / "labels"
            images_dir.mkdir(parents=True, exist_ok=True)
            labels_dir.mkdir(parents=True, exist_ok=True)

            # 打开视频文件
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise Exception("无法打开视频文件")

            try:
                video_fps = cap.get(cv2.CAP_PROP_FPS) or self.fps
                total_annotations = len(self.annotations)

                if progress_callback:
                    progress_callback(5, f"开始处理 {total_annotations} 个标注...")

                # 处理每个标注
                for i, annotation in enumerate(self.annotations):
                    try:
                        if progress_callback:
                            progress = int(5 + (i / total_annotations) * 90)
                            chinese_label = FacialActionConfig.get_chinese_label(annotation.label)
                            progress_callback(progress, f"处理标注 {i+1}/{total_annotations}: {chinese_label}")

                        # 处理刷新UI事件
                        QApplication.processEvents()

                        success = self._process_annotation(
                            cap, annotation, images_dir, labels_dir, video_fps
                        )

                        if not success:
                            self.stats["errors"].append(f"处理标注失败: {annotation.label}")

                    except Exception as e:
                        error_msg = f"处理标注 {i+1} 时出错: {str(e)}"
                        self.stats["errors"].append(error_msg)
                        print(error_msg)
                        continue

                # 生成数据集信息文件
                if progress_callback:
                    progress_callback(95, "生成数据集信息...")

                self._generate_dataset_info()

                if progress_callback:
                    progress_callback(100, "导出完成!")

                return True

            finally:
                cap.release()

        except Exception as e:
            error_msg = f"导出失败: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"导出异常: {e}")
            return False

    def _process_annotation(self, cap: cv2.VideoCapture, annotation: AnnotationMarker,
                           images_dir: Path, labels_dir: Path, video_fps: float) -> bool:
        """处理单个标注"""
        try:
            # 计算帧范围
            start_frame = int(annotation.start_time * video_fps)
            end_frame = int(annotation.end_time * video_fps)
            total_frames = end_frame - start_frame + 1

            if total_frames <= 0:
                return False

            # 生成文件名前缀
            base_name = self._generate_unique_name(annotation)

            # 获取动作强度
            intensity = getattr(annotation, 'intensity', 1.0)

            # 提取每一帧
            for frame_idx in range(total_frames):
                current_frame = start_frame + frame_idx

                # 设置帧位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                ret, frame = cap.read()

                if not ret or frame is None:
                    continue

                # 计算动作进度 (0.0 到 1.0)
                if total_frames == 1:
                    action_progress = 0.5
                else:
                    action_progress = frame_idx / (total_frames - 1)

                # 生成文件名
                frame_name = f"{base_name}_frame_{frame_idx:04d}"

                # 保存图像
                image_path = images_dir / f"{frame_name}.jpg"
                if cv2.imwrite(str(image_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                    self.stats["exported_images"] += 1

                # 保存标注文件 - 45个浮点数
                label_path = labels_dir / f"{frame_name}.txt"
                if self._save_facial_action_label_file(label_path, annotation.label, intensity, action_progress):
                    self.stats["exported_labels"] += 1

                # 处理UI事件，保持界面响应
                if frame_idx % 10 == 0:
                    QApplication.processEvents()

            # 更新标签分布统计
            if annotation.label in self.stats["label_distribution"]:
                self.stats["label_distribution"][annotation.label] += total_frames

            return True

        except Exception as e:
            print(f"处理标注异常: {e}")
            return False

    def _save_facial_action_label_file(self, file_path: Path, main_action: str,
                                     intensity: float, action_progress: float) -> bool:
        """保存面部动作标注文件 - 45个浮点数格式

        特殊规则:
        1. 任何舌头动作激活时，jawOpen = 1.0
        2. 其他舌头动作激活时，tongueOut = 1.0
        3. 动作强度按时间进度线性变化 (y = x)
        """
        try:
            # 创建45个动作的数值数组
            action_values = [0.0] * 45

            # 计算实际动作强度值 (基于进度和设定强度)
            # 线性变化：y = x，从0线性增长到最大强度
            # action_progress: 0.0 -> 0%, 1.0 -> 100%
            # current_intensity: 0.0 -> intensity * 0.0, 1.0 -> intensity * 1.0
            current_intensity = intensity * action_progress

            # 确保数值在合理范围内
            current_intensity = max(0.0, min(1.0, current_intensity))

            # 设置主要动作的值
            if main_action in self.all_labels:
                main_index = self.all_labels.index(main_action)
                action_values[main_index] = current_intensity

            # 处理舌头动作的特殊逻辑
            if FacialActionConfig.is_tongue_action(main_action) and current_intensity > 0:
                # 规则1：如果有舌头动作，jawOpen应该为1
                jaw_open_index = self.all_labels.index("jawOpen")
                if action_values[jaw_open_index] < 1.0:
                    action_values[jaw_open_index] = 1.0

                # 规则2：如果是其他舌头动作（非tongueOut），tongueOut应该为1
                if main_action != "tongueOut":
                    tongue_out_index = self.all_labels.index("tongueOut")
                    if action_values[tongue_out_index] < 1.0:
                        action_values[tongue_out_index] = 1.0

            # 写入文件 - 每行一个浮点数
            with open(file_path, 'w', encoding='utf-8') as f:
                for value in action_values:
                    f.write(f"{value:.6f}\n")

            return True

        except Exception as e:
            print(f"保存面部动作标注文件失败: {e}")
            return False

    def _generate_unique_name(self, annotation: AnnotationMarker) -> str:
        """生成唯一文件名"""
        try:
            timestamp = str(int(time.time() * 1000))
            content = f"{annotation.label}_{annotation.start_time}_{annotation.end_time}"
            hash_value = hashlib.md5(content.encode()).hexdigest()[:8]
            clean_label = "".join(c for c in annotation.label if c.isalnum() or c in "_-")
            return f"{clean_label}_{timestamp}_{hash_value}"
        except:
            return f"facial_action_{int(time.time() * 1000)}"

    def _generate_dataset_info(self):
        """生成数据集信息文件"""
        try:
            info_path = Path(self.output_dir) / "dataset_info.json"

            # 创建标签映射信息
            label_mapping = {}
            for i, label in enumerate(self.all_labels):
                chinese_label = FacialActionConfig.get_chinese_label(label)
                label_mapping[i] = {
                    "english": label,
                    "chinese": chinese_label,
                    "index": i
                }

            dataset_info = {
                "dataset_name": "Facial Action Dataset",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_video": self.video_path,
                "total_labels": len(self.all_labels),
                "label_mapping": label_mapping,
                "special_rules": [
                    "当舌头相关动作值不为0时，jawOpen自动设为1.0",
                    "当其他舌头动作激活时，tongueOut自动设为1.0",
                    "动作强度随时间进度线性增长（y=x），从0增长到设定强度",
                    "每个标注文件包含45个浮点数，对应45个面部动作"
                ],
                "label_file_format": {
                    "description": "每行一个浮点数，共45行，对应45个面部动作",
                    "range": "0.0 到 1.0",
                    "order": self.all_labels
                },
                "statistics": self.stats,
                "tongue_actions": FacialActionConfig.TONGUE_ACTIONS
            }

            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"生成数据集信息失败: {e}")


class SimpleProgressDialog(QDialog):
    """简单进度对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出面部动作数据集")
        self.setModal(True)
        self.setFixedSize(550, 220)

        layout = QVBoxLayout(self)

        # 状态标签
        self.status_label = QLabel("准备导出...")
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # 说明文字
        info_label = QLabel("正在将面部动作标注导出为45维向量数据集（线性强度变化）...")
        info_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(info_label)

        # 取消按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.cancelled = False

    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        QApplication.processEvents()

    def reject(self):
        """取消对话框"""
        self.cancelled = True
        super().reject()


def simple_export_dataset(parent, video_path: str, annotations: List[AnnotationMarker],
                         video_info: VideoInfo) -> bool:
    """面部动作数据集导出入口函数"""
    try:
        # 基本验证
        if not annotations:
            QMessageBox.warning(parent, "警告", "没有标注数据可导出")
            return False

        if not os.path.exists(video_path):
            QMessageBox.warning(parent, "警告", "视频文件不存在")
            return False

        # 预估处理时间
        total_frames = sum(int((ann.end_time - ann.start_time) * video_info.fps) for ann in annotations)
        estimated_time = total_frames / 100

        # 显示预导出信息
        info_msg = f"""准备导出面部动作数据集

视频文件: {os.path.basename(video_path)}
标注数量: {len(annotations)}
动作类别: {len(FacialActionConfig.ALL_LABELS)} 种面部动作
预计图像数: {total_frames}
标注文件格式: 每个文件45个浮点数 (对应45种面部动作)
预计耗时: {estimated_time:.1f}秒

特殊规则:
• 舌头动作时自动激活张嘴动作(jawOpen=1.0)
• 其他舌头动作时自动激活舌头伸出(tongueOut=1.0)
• 动作强度随时间线性增长（从0到设定强度）
• 数值范围: 0.0 - 1.0

继续导出吗？"""

        reply = QMessageBox.question(
            parent,
            "确认导出面部动作数据集",
            info_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return False

        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            parent,
            "选择面部动作数据集输出目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not output_dir:
            return False

        # 检查磁盘空间
        try:
            import shutil
            free_space = shutil.disk_usage(output_dir).free
            estimated_size = total_frames * 60 * 1024  # 假设每张图片60KB

            if free_space < estimated_size * 2:
                QMessageBox.warning(
                    parent,
                    "磁盘空间不足",
                    f"预计需要 {estimated_size/1024/1024:.1f}MB 空间，请释放磁盘空间后重试"
                )
                return False
        except:
            pass

        # 创建进度对话框
        progress_dialog = SimpleProgressDialog(parent)
        progress_dialog.show()

        # 创建导出器
        exporter = FacialActionDatasetExporter(
            video_path,
            annotations,
            output_dir,
            video_info.fps
        )

        # 执行导出
        def progress_callback(value, message):
            if progress_dialog.cancelled:
                return False
            progress_dialog.update_progress(value, message)
            return True

        success = exporter.export_dataset(progress_callback)

        progress_dialog.close()

        if success and not progress_dialog.cancelled:
            # 显示结果
            stats = exporter.stats
            message = f"""面部动作数据集导出成功！

输出目录: {output_dir}
图像数量: {stats['exported_images']}
标注文件数量: {stats['exported_labels']}
处理的标注: {stats['total_annotations']}
动作类别: {len(FacialActionConfig.ALL_LABELS)} 种

每个标注文件包含45个浮点数，对应45种面部动作的强度值。

自动激活规则:
• 舌头动作 → jawOpen=1.0
• 其他舌头动作 → tongueOut=1.0"""

            if stats['errors']:
                message += f"\n\n⚠️ 警告: 有 {len(stats['errors'])} 个错误"

            QMessageBox.information(parent, "导出成功", message)
            return True
        elif progress_dialog.cancelled:
            QMessageBox.information(parent, "已取消", "导出已被用户取消")
            return False
        else:
            error_msgs = "\n".join(exporter.stats['errors'][-3:])
            QMessageBox.critical(parent, "导出失败", f"导出过程中出现错误:\n{error_msgs}")
            return False

    except Exception as e:
        QMessageBox.critical(parent, "导出错误", f"导出时出现异常:\n{str(e)}")
        return False
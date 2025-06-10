"""
多标签面部动作数据集导出器
"""
import os
import cv2
import hashlib
import time
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QMessageBox, QApplication, QFileDialog, QInputDialog,
    QProgressBar, QLabel, QVBoxLayout, QHBoxLayout, QDialog,
    QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from models import AnnotationMarker, VideoInfo, LabelConfig, ProgressionType
from utils import FileUtils, TimeUtils
from styles import FacialActionConfig


def cv2_imwrite_chinese(file_path: str, image: np.ndarray, params=None) -> bool:
    """
    解决OpenCV对中文路径支持问题的图像保存函数
    """
    try:
        if params is None:
            params = [cv2.IMWRITE_JPEG_QUALITY, 95]

        # 使用cv2.imencode编码图像
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.jpg' or ext == '.jpeg':
            success, encoded_img = cv2.imencode('.jpg', image, params)
        elif ext == '.png':
            success, encoded_img = cv2.imencode('.png', image)
        else:
            success, encoded_img = cv2.imencode('.jpg', image, params)

        if not success:
            return False

        # 使用numpy保存到文件
        with open(file_path, 'wb') as f:
            f.write(encoded_img.tobytes())

        return True

    except Exception as e:
        print(f"保存图像失败: {e}")
        return False


class MultiLabelDatasetExporter:
    """多标签面部动作数据集导出器"""

    def __init__(self, video_path: str, annotations: List[AnnotationMarker],
                 output_dir: str, fps: float = 30.0):
        self.video_path = video_path
        self.annotations = annotations
        self.output_dir = output_dir
        self.fps = fps
        self.cancelled = False

        # 所有45个动作标签
        self.all_labels = FacialActionConfig.ALL_LABELS

        # 统计信息
        self.stats = {
            "exported_images": 0,
            "exported_labels": 0,
            "total_annotations": len(annotations),
            "label_distribution": {label: 0 for label in self.all_labels},
            "progression_stats": {
                "linear_count": 0,
                "constant_count": 0
            },
            "multi_label_stats": {
                "single_label": 0,
                "multi_label": 0,
                "max_labels_per_annotation": 0
            },
            "errors": [],
            "debug_info": []
        }

    def export_dataset(self, progress_callback=None) -> bool:
        """导出多标签数据集"""
        try:
            self.cancelled = False

            if progress_callback:
                if not progress_callback(0, "创建输出目录..."):
                    self.cancelled = True
                    return False

            # 创建输出目录
            images_dir = Path(self.output_dir) / "images"
            labels_dir = Path(self.output_dir) / "labels"

            try:
                images_dir.mkdir(parents=True, exist_ok=True)
                labels_dir.mkdir(parents=True, exist_ok=True)
                self.stats["debug_info"].append(f"成功创建目录: {images_dir}, {labels_dir}")
            except Exception as e:
                raise Exception(f"创建输出目录失败: {str(e)}")

            # 检查目录权限
            if not os.access(str(images_dir), os.W_OK):
                raise Exception(f"没有写入权限: {images_dir}")
            if not os.access(str(labels_dir), os.W_OK):
                raise Exception(f"没有写入权限: {labels_dir}")

            # 测试中文路径支持
            self._test_chinese_path_support(images_dir)

            # 打开视频文件
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise Exception(f"无法打开视频文件: {self.video_path}")

            # 获取视频信息
            video_fps = cap.get(cv2.CAP_PROP_FPS) or self.fps
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.stats["debug_info"].append(f"视频信息: {video_width}x{video_height}, {video_fps}fps, {frame_count}帧")

            try:
                total_annotations = len(self.annotations)

                if progress_callback:
                    if not progress_callback(5, f"开始处理 {total_annotations} 个多标签标注..."):
                        self.cancelled = True
                        return False

                # 处理每个标注
                for i, annotation in enumerate(self.annotations):
                    try:
                        # 检查是否被取消
                        if self.cancelled:
                            return False

                        if progress_callback:
                            progress = int(5 + (i / total_annotations) * 90)
                            label_count = len(annotation.labels)
                            if not progress_callback(progress, f"处理标注 {i+1}/{total_annotations}: {label_count} 个标签"):
                                self.cancelled = True
                                return False

                        # 处理刷新UI事件
                        QApplication.processEvents()

                        success = self._process_multi_label_annotation(
                            cap, annotation, images_dir, labels_dir, video_fps, i
                        )

                        if not success:
                            error_msg = f"处理标注失败: {annotation.display_labels} ({annotation.start_time}-{annotation.end_time})"
                            self.stats["errors"].append(error_msg)

                    except Exception as e:
                        error_msg = f"处理标注 {i+1} 时出错: {str(e)}"
                        self.stats["errors"].append(error_msg)
                        print(error_msg)
                        continue

                # 检查是否被取消
                if self.cancelled:
                    return False

                # 生成数据集信息文件
                if progress_callback:
                    if not progress_callback(95, "生成数据集信息..."):
                        self.cancelled = True
                        return False

                self._generate_multi_label_dataset_info()

                if progress_callback:
                    if not progress_callback(100, "多标签导出完成!"):
                        self.cancelled = True
                        return False

                return True

            finally:
                cap.release()

        except Exception as e:
            error_msg = f"导出失败: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"导出异常: {e}")
            return False

    def _test_chinese_path_support(self, test_dir: Path):
        """测试中文路径支持"""
        try:
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            test_image[:] = (255, 255, 255)

            test_file = test_dir / "test_multi_label_support.jpg"

            success = cv2_imwrite_chinese(str(test_file), test_image)

            if success and os.path.exists(test_file):
                self.stats["debug_info"].append("多标签路径支持测试: 成功")
                os.remove(test_file)
            else:
                self.stats["debug_info"].append("多标签路径支持测试: 失败")

        except Exception as e:
            self.stats["debug_info"].append(f"多标签路径测试异常: {e}")

    def _process_multi_label_annotation(self, cap: cv2.VideoCapture, annotation: AnnotationMarker,
                                       images_dir: Path, labels_dir: Path, video_fps: float,
                                       annotation_index: int) -> bool:
        """处理单个多标签标注"""
        try:
            # 检查是否被取消
            if self.cancelled:
                return False

            # 统计多标签信息
            label_count = len(annotation.labels)
            if label_count == 1:
                self.stats["multi_label_stats"]["single_label"] += 1
            else:
                self.stats["multi_label_stats"]["multi_label"] += 1

            self.stats["multi_label_stats"]["max_labels_per_annotation"] = max(
                self.stats["multi_label_stats"]["max_labels_per_annotation"],
                label_count
            )

            # 统计进度类型
            for label_config in annotation.labels:
                if label_config.progression == ProgressionType.LINEAR:
                    self.stats["progression_stats"]["linear_count"] += 1
                else:
                    self.stats["progression_stats"]["constant_count"] += 1

            # 计算帧范围
            start_frame = int(annotation.start_time * video_fps)
            end_frame = int(annotation.end_time * video_fps)
            total_frames = end_frame - start_frame + 1

            if total_frames <= 0:
                self.stats["errors"].append(f"无效的时间范围: {annotation.start_time}-{annotation.end_time}")
                return False

            # 生成文件名前缀
            base_name = self._generate_multi_label_safe_name(annotation, annotation_index)

            self.stats["debug_info"].append(f"处理多标签标注: {annotation.display_labels}, 帧范围: {start_frame}-{end_frame}, 总帧数: {total_frames}")

            # 提取每一帧
            frame_success_count = 0
            for frame_idx in range(total_frames):
                # 检查是否被取消
                if self.cancelled:
                    return False

                current_frame = start_frame + frame_idx

                # 设置帧位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                ret, frame = cap.read()

                if not ret or frame is None:
                    self.stats["debug_info"].append(f"跳过帧 {current_frame}: 读取失败")
                    continue

                # 验证帧数据
                if frame.size == 0:
                    self.stats["debug_info"].append(f"跳过帧 {current_frame}: 空帧")
                    continue

                # 计算当前帧的进度 (0.0 到 1.0)
                if total_frames == 1:
                    frame_progress = 0.5
                else:
                    frame_progress = frame_idx / (total_frames - 1)

                # 生成文件名
                frame_name = f"{base_name}_frame_{frame_idx:04d}"

                # 保存图像
                image_path = images_dir / f"{frame_name}.jpg"
                if self._save_image_fixed(frame, str(image_path), frame_name):
                    self.stats["exported_images"] += 1
                    frame_success_count += 1
                else:
                    error_msg = f"保存图像失败: {frame_name}"
                    self.stats["errors"].append(error_msg)

                # 保存多标签标注文件
                label_path = labels_dir / f"{frame_name}.txt"
                if self._save_multi_label_file(label_path, annotation, frame_progress):
                    self.stats["exported_labels"] += 1
                else:
                    error_msg = f"保存多标签标注文件失败: {frame_name}"
                    self.stats["errors"].append(error_msg)

                # 处理UI事件
                if frame_idx % 10 == 0:
                    QApplication.processEvents()
                    if self.cancelled:
                        return False

            # 更新标签分布统计
            for label_config in annotation.labels:
                if label_config.label in self.stats["label_distribution"]:
                    self.stats["label_distribution"][label_config.label] += frame_success_count

            self.stats["debug_info"].append(f"多标签标注 {annotation.display_labels} 完成: 成功保存 {frame_success_count}/{total_frames} 帧")
            return frame_success_count > 0

        except Exception as e:
            error_msg = f"处理多标签标注异常: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(error_msg)
            return False

    def _save_multi_label_file(self, file_path: Path, annotation: AnnotationMarker, frame_progress: float) -> bool:
        """保存多标签面部动作标注文件"""
        try:
            # 检查是否被取消
            if self.cancelled:
                return False

            # 创建45个动作的数值数组
            action_values = [0.0] * 45

            # 处理每个激活的标签
            for label_config in annotation.labels:
                label = label_config.label

                if label in self.all_labels:
                    label_index = self.all_labels.index(label)

                    # 根据进度类型计算当前强度
                    if label_config.progression == ProgressionType.CONSTANT:
                        current_intensity = label_config.intensity
                    else:  # LINEAR
                        current_intensity = label_config.intensity * frame_progress

                    # 确保值在有效范围内
                    current_intensity = max(0.0, min(1.0, current_intensity))
                    action_values[label_index] = current_intensity

            # 处理舌头动作的特殊逻辑
            self._apply_tongue_action_rules(action_values, annotation, frame_progress)

            # 写入文件 - 每行一个浮点数
            with open(file_path, 'w', encoding='utf-8') as f:
                for value in action_values:
                    f.write(f"{value:.6f}\n")

            # 验证文件是否创建成功
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return True
            else:
                self.stats["debug_info"].append(f"多标签标注文件创建失败或为空: {file_path}")
                return False

        except Exception as e:
            error_msg = f"保存多标签面部动作标注文件失败: {str(e)}"
            self.stats["errors"].append(error_msg)
            return False

    def _apply_tongue_action_rules(self, action_values: List[float], annotation: AnnotationMarker, frame_progress: float):
        """应用舌头动作的特殊规则"""
        try:
            # 检查是否有舌头动作
            has_tongue_action = False
            has_non_tongue_out_action = False

            for label_config in annotation.labels:
                if FacialActionConfig.is_tongue_action(label_config.label):
                    has_tongue_action = True
                    if label_config.label != "tongueOut":
                        has_non_tongue_out_action = True

            if has_tongue_action:
                # 规则1：如果有舌头动作，jawOpen应该为1
                jaw_open_index = self.all_labels.index("jawOpen")
                if action_values[jaw_open_index] < 1.0:
                    action_values[jaw_open_index] = 1.0

                # 规则2：如果有其他舌头动作（非tongueOut），tongueOut应该为1
                if has_non_tongue_out_action:
                    tongue_out_index = self.all_labels.index("tongueOut")
                    if action_values[tongue_out_index] < 1.0:
                        action_values[tongue_out_index] = 1.0

        except Exception as e:
            self.stats["debug_info"].append(f"应用舌头动作规则时出错: {e}")

    def _save_image_fixed(self, frame, image_path: str, frame_name: str) -> bool:
        """保存图像 - 支持中文路径"""
        try:
            if self.cancelled:
                return False

            if frame is None or frame.size == 0:
                self.stats["debug_info"].append(f"无效帧数据: {frame_name}")
                return False

            h, w = frame.shape[:2]
            if h <= 0 or w <= 0:
                self.stats["debug_info"].append(f"无效图像尺寸: {w}x{h}, {frame_name}")
                return False

            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)

            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, 95,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                cv2.IMWRITE_JPEG_PROGRESSIVE, 1
            ]

            success = cv2_imwrite_chinese(image_path, frame, encode_params)

            if success and os.path.exists(image_path):
                file_size = os.path.getsize(image_path)
                if file_size > 0:
                    return True
                else:
                    try:
                        os.remove(image_path)
                    except:
                        pass
                    return False
            else:
                return False

        except Exception as e:
            error_msg = f"保存图像异常 {frame_name}: {str(e)}"
            self.stats["errors"].append(error_msg)
            return False

    def _generate_multi_label_safe_name(self, annotation: AnnotationMarker, annotation_index: int) -> str:
        """生成多标签安全的文件名"""
        try:
            # 使用主要标签或组合标签名
            if len(annotation.labels) == 1:
                clean_label = annotation.labels[0].label
            else:
                # 多标签：使用前几个标签的组合
                label_names = [lc.label for lc in annotation.labels[:3]]  # 最多使用前3个
                clean_label = "_".join(label_names)

            # 确保只包含字母、数字、下划线
            clean_label = "".join(c for c in clean_label if c.isalnum() or c == '_')

            # 添加时间戳和索引
            timestamp = str(int(time.time() * 1000))
            unique_name = f"multi_{clean_label}_{annotation_index:03d}_{timestamp}"

            # 限制文件名长度
            if len(unique_name) > 60:
                unique_name = unique_name[:60]

            return unique_name
        except Exception as e:
            # 如果生成失败，使用最简单的方案
            return f"multi_facial_{annotation_index:03d}_{int(time.time() * 1000)}"

    def _generate_multi_label_dataset_info(self):
        """生成多标签数据集信息文件"""
        try:
            if self.cancelled:
                return

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
                "dataset_name": "Multi-Label Facial Action Dataset",
                "dataset_type": "multi_label",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_video": self.video_path,
                "total_labels": len(self.all_labels),
                "label_mapping": label_mapping,
                "multi_label_features": {
                    "supports_multiple_labels_per_annotation": True,
                    "supports_different_progression_types": True,
                    "progression_types": ["linear", "constant"],
                    "automatic_tongue_rules": True
                },
                "special_rules": [
                    "支持每个标注同时包含多个面部动作标签",
                    "每个标签可以独立设置强度和进度类型",
                    "线性进度：动作强度从0线性增长到设定值",
                    "恒定进度：动作强度在整个时间段内保持恒定",
                    "当舌头相关动作值不为0时，jawOpen自动设为1.0",
                    "当其他舌头动作激活时，tongueOut自动设为1.0",
                    "每个标注文件包含45个浮点数，对应45个面部动作"
                ],
                "label_file_format": {
                    "description": "每行一个浮点数，共45行，对应45个面部动作",
                    "range": "0.0 到 1.0",
                    "order": self.all_labels,
                    "multi_label_support": "同一帧可以有多个动作同时激活"
                },
                "statistics": self.stats,
                "progression_types": {
                    "linear": {
                        "description": "动作强度随时间线性增长",
                        "formula": "value = intensity * progress",
                        "count": self.stats["progression_stats"]["linear_count"]
                    },
                    "constant": {
                        "description": "动作强度保持恒定",
                        "formula": "value = intensity",
                        "count": self.stats["progression_stats"]["constant_count"]
                    }
                },
                "tongue_actions": FacialActionConfig.TONGUE_ACTIONS,
                "export_status": "cancelled" if self.cancelled else "completed",
                "debug_information": {
                    "opencv_version": cv2.__version__,
                    "debug_messages": self.stats["debug_info"],
                    "chinese_path_fix": "使用cv2.imencode解决中文路径问题",
                    "multi_label_implementation": "支持多标签同时标注和不同进度类型"
                }
            }

            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, ensure_ascii=False, indent=2)

        except Exception as e:
            error_msg = f"生成多标签数据集信息失败: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(error_msg)

    def cancel_export(self):
        """取消导出"""
        self.cancelled = True


# 简单进度对话框保持不变，只需要修改标题和提示信息
class MultiLabelProgressDialog(QDialog):
    """多标签进度对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出多标签面部动作数据集")
        self.setModal(True)
        self.setFixedSize(600, 280)

        layout = QVBoxLayout(self)

        # 状态标签
        self.status_label = QLabel("准备导出多标签数据集...")
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # 说明文字
        info_label = QLabel("正在导出支持多标签和不同进度类型的面部动作数据集...")
        info_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(info_label)

        # 调试信息显示
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(80)
        self.debug_text.setStyleSheet("font-size: 9px; background-color: #1e1e1e; color: #ccc;")
        layout.addWidget(self.debug_text)

        # 取消按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.cancel_export)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.cancelled = False
        self.exporter = None

    def set_exporter(self, exporter):
        """设置导出器引用"""
        self.exporter = exporter

    def update_progress(self, value: int, message: str) -> bool:
        """更新进度"""
        if self.cancelled:
            return False

        self.progress_bar.setValue(value)
        self.status_label.setText(message)

        self.debug_text.append(f"[{value}%] {message}")
        self.debug_text.ensureCursorVisible()

        QApplication.processEvents()
        return not self.cancelled

    def cancel_export(self):
        """取消导出"""
        self.cancelled = True
        if self.exporter:
            self.exporter.cancel_export()
        self.cancel_button.setText("取消中...")
        self.cancel_button.setEnabled(False)
        self.status_label.setText("正在取消多标签导出...")

    def closeEvent(self, event):
        """关闭事件"""
        if not self.cancelled:
            self.cancel_export()
        event.accept()


def export_multi_label_dataset(parent, video_path: str, annotations: List[AnnotationMarker],
                               video_info: VideoInfo) -> bool:
    """多标签数据集导出入口函数"""
    try:
        # 基本验证
        if not annotations:
            QMessageBox.warning(parent, "警告", "没有标注数据可导出")
            return False

        if not os.path.exists(video_path):
            QMessageBox.warning(parent, "警告", "视频文件不存在")
            return False

        # 统计多标签信息
        total_labels = sum(len(ann.labels) for ann in annotations)
        multi_label_count = sum(1 for ann in annotations if len(ann.labels) > 1)

        # 预估处理时间
        total_frames = sum(int((ann.end_time - ann.start_time) * video_info.fps) for ann in annotations)
        estimated_time = total_frames / 100

        # 显示预导出信息
        info_msg = f"""准备导出多标签面部动作数据集

视频文件: {os.path.basename(video_path)}
标注数量: {len(annotations)}
总标签数: {total_labels}
多标签标注: {multi_label_count}
动作类别: {len(FacialActionConfig.ALL_LABELS)} 种面部动作
预计图像数: {total_frames}
标注文件格式: 每个文件45个浮点数 (对应45种面部动作)
预计耗时: {estimated_time:.1f}秒

新功能特性:
• ✨ 支持每个标注同时包含多个标签
• 📈 支持线性增长和恒定强度两种进度模式
• 🎯 每个标签可独立配置强度和进度类型
• 🔧 自动应用舌头动作相关规则
• 🛠️ 修复中文路径兼容性问题

继续导出吗？"""

        reply = QMessageBox.question(
            parent,
            "确认导出多标签数据集",
            info_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return False

        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            parent,
            "选择多标签数据集输出目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not output_dir:
            return False

        # 创建进度对话框
        progress_dialog = MultiLabelProgressDialog(parent)

        # 创建导出器
        exporter = MultiLabelDatasetExporter(
            video_path,
            annotations,
            output_dir,
            video_info.fps
        )

        progress_dialog.set_exporter(exporter)
        progress_dialog.show()

        # 执行导出
        def progress_callback(value, message):
            return progress_dialog.update_progress(value, message)

        success = exporter.export_dataset(progress_callback)

        # 关闭进度对话框
        progress_dialog.close()

        # 根据结果显示不同消息
        if progress_dialog.cancelled or exporter.cancelled:
            QMessageBox.information(parent, "已取消", "多标签导出已被用户取消")
            return False
        elif success:
            # 导出成功
            stats = exporter.stats

            result_msg = f"""多标签面部动作数据集导出完成！

输出目录: {output_dir}
图像数量: {stats['exported_images']}
标注文件数量: {stats['exported_labels']}
处理的标注: {stats['total_annotations']}
单标签标注: {stats['multi_label_stats']['single_label']}
多标签标注: {stats['multi_label_stats']['multi_label']}
最大标签数: {stats['multi_label_stats']['max_labels_per_annotation']}

进度类型统计:
线性增长: {stats['progression_stats']['linear_count']}
恒定强度: {stats['progression_stats']['constant_count']}

✅ 已支持多标签和不同进度类型"""

            if stats['errors']:
                result_msg += f"\n\n⚠️ 遇到 {len(stats['errors'])} 个问题，详情请查看 dataset_info.json"

            QMessageBox.information(parent, "导出成功", result_msg)
            return True
        else:
            # 导出失败
            error_details = "\n".join(exporter.stats['errors'][-5:]) if exporter.stats['errors'] else "未知错误"
            detailed_msg = f"""多标签导出过程中出现错误:

{error_details}

完整日志请查看输出目录中的 dataset_info.json 文件。"""

            QMessageBox.critical(parent, "导出失败", detailed_msg)
            return False

    except Exception as e:
        QMessageBox.critical(parent, "导出错误", f"多标签导出时出现异常:\n{str(e)}")
        return False
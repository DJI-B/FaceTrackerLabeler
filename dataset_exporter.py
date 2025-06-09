"""
面部动作数据集导出器 - 完整修复版本
解决中文路径问题和导入问题
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
from models import AnnotationMarker, VideoInfo
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


class FacialActionDatasetExporter:
    """面部动作数据集导出器 - 修复中文路径版本"""

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
            "errors": [],
            "debug_info": []
        }

    def export_dataset(self, progress_callback=None) -> bool:
        """导出数据集 - 修复中文路径问题"""
        try:
            if progress_callback:
                progress_callback(0, "创建输出目录...")

            # 创建输出目录
            images_dir = Path(self.output_dir) / "images"
            labels_dir = Path(self.output_dir) / "labels"
            
            # 确保目录创建成功
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

                        success = self._process_annotation_fixed(
                            cap, annotation, images_dir, labels_dir, video_fps, i
                        )

                        if not success:
                            error_msg = f"处理标注失败: {annotation.label} ({annotation.start_time}-{annotation.end_time})"
                            self.stats["errors"].append(error_msg)

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

    def _test_chinese_path_support(self, test_dir: Path):
        """测试中文路径支持"""
        try:
            # 创建测试图像
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            test_image[:] = (255, 255, 255)  # 白色图像
            
            test_file = test_dir / "test_path_support.jpg"
            
            # 测试保存
            success = cv2_imwrite_chinese(str(test_file), test_image)
            
            if success and os.path.exists(test_file):
                self.stats["debug_info"].append("路径支持测试: 成功")
                os.remove(test_file)  # 删除测试文件
            else:
                self.stats["debug_info"].append("路径支持测试: 失败")
                
        except Exception as e:
            self.stats["debug_info"].append(f"路径测试异常: {e}")

    def _process_annotation_fixed(self, cap: cv2.VideoCapture, annotation: AnnotationMarker,
                                 images_dir: Path, labels_dir: Path, video_fps: float, 
                                 annotation_index: int) -> bool:
        """处理单个标注 - 修复版本"""
        try:
            # 计算帧范围
            start_frame = int(annotation.start_time * video_fps)
            end_frame = int(annotation.end_time * video_fps)
            total_frames = end_frame - start_frame + 1

            if total_frames <= 0:
                self.stats["errors"].append(f"无效的时间范围: {annotation.start_time}-{annotation.end_time}")
                return False

            # 生成文件名前缀（避免特殊字符）
            base_name = self._generate_safe_name(annotation, annotation_index)

            # 获取动作强度
            intensity = getattr(annotation, 'intensity', 1.0)

            self.stats["debug_info"].append(f"处理标注: {annotation.label}, 帧范围: {start_frame}-{end_frame}, 总帧数: {total_frames}")

            # 提取每一帧
            frame_success_count = 0
            for frame_idx in range(total_frames):
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

                # 计算动作进度 (0.0 到 1.0)
                if total_frames == 1:
                    action_progress = 0.5
                else:
                    action_progress = frame_idx / (total_frames - 1)

                # 生成文件名
                frame_name = f"{base_name}_frame_{frame_idx:04d}"

                # 保存图像 - 使用修复的保存函数
                image_path = images_dir / f"{frame_name}.jpg"
                if self._save_image_fixed(frame, str(image_path), frame_name):
                    self.stats["exported_images"] += 1
                    frame_success_count += 1
                else:
                    error_msg = f"保存图像失败: {frame_name}"
                    self.stats["errors"].append(error_msg)

                # 保存标注文件 - 45个浮点数
                label_path = labels_dir / f"{frame_name}.txt"
                if self._save_facial_action_label_file(label_path, annotation.label, intensity, action_progress):
                    self.stats["exported_labels"] += 1
                else:
                    error_msg = f"保存标注文件失败: {frame_name}"
                    self.stats["errors"].append(error_msg)

                # 处理UI事件，保持界面响应
                if frame_idx % 10 == 0:
                    QApplication.processEvents()

            # 更新标签分布统计
            if annotation.label in self.stats["label_distribution"]:
                self.stats["label_distribution"][annotation.label] += frame_success_count

            self.stats["debug_info"].append(f"标注 {annotation.label} 完成: 成功保存 {frame_success_count}/{total_frames} 帧")
            return frame_success_count > 0

        except Exception as e:
            error_msg = f"处理标注异常: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(error_msg)
            return False

    def _save_image_fixed(self, frame, image_path: str, frame_name: str) -> bool:
        """保存图像 - 修复版本"""
        try:
            # 验证输入帧
            if frame is None or frame.size == 0:
                self.stats["debug_info"].append(f"无效帧数据: {frame_name}")
                return False

            # 检查图像尺寸
            h, w = frame.shape[:2]
            if h <= 0 or w <= 0:
                self.stats["debug_info"].append(f"无效图像尺寸: {w}x{h}, {frame_name}")
                return False

            # 确保图像是连续的
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)

            # 使用修复的保存函数
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, 95,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                cv2.IMWRITE_JPEG_PROGRESSIVE, 1
            ]

            # 尝试保存图像
            success = cv2_imwrite_chinese(image_path, frame, encode_params)
            
            if success:
                # 验证文件是否真的被创建
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    if file_size > 0:
                        if frame_name.endswith("_frame_0000") or frame_name.endswith("_frame_0010"):  # 只记录部分成功信息
                            self.stats["debug_info"].append(f"成功保存图像: {frame_name}, 大小: {file_size} bytes")
                        return True
                    else:
                        self.stats["debug_info"].append(f"图像文件为空: {frame_name}")
                        try:
                            os.remove(image_path)
                        except:
                            pass
                        return False
                else:
                    self.stats["debug_info"].append(f"图像文件未创建: {frame_name}")
                    return False
            else:
                self.stats["debug_info"].append(f"图像编码失败: {frame_name}")
                return False

        except Exception as e:
            error_msg = f"保存图像异常 {frame_name}: {str(e)}"
            self.stats["errors"].append(error_msg)
            return False

    def _generate_safe_name(self, annotation: AnnotationMarker, annotation_index: int) -> str:
        """生成安全的文件名（避免特殊字符）"""
        try:
            # 使用英文标签，避免中文
            clean_label = annotation.label  # 英文标签
            
            # 确保只包含字母、数字、下划线
            clean_label = "".join(c for c in clean_label if c.isalnum() or c == '_')
            
            # 添加时间戳和索引
            timestamp = str(int(time.time() * 1000))
            unique_name = f"{clean_label}_{annotation_index:03d}_{timestamp}"
            
            # 限制文件名长度
            if len(unique_name) > 50:
                unique_name = unique_name[:50]
                
            return unique_name
        except Exception as e:
            # 如果生成失败，使用最简单的方案
            return f"facial_action_{annotation_index:03d}_{int(time.time() * 1000)}"

    def _save_facial_action_label_file(self, file_path: Path, main_action: str,
                                     intensity: float, action_progress: float) -> bool:
        """保存面部动作标注文件 - 45个浮点数格式"""
        try:
            # 创建45个动作的数值数组
            action_values = [0.0] * 45

            # 计算实际动作强度值 (基于进度和设定强度)
            current_intensity = intensity * action_progress
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

            # 验证文件是否创建成功
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return True
            else:
                self.stats["debug_info"].append(f"标注文件创建失败或为空: {file_path}")
                return False

        except Exception as e:
            error_msg = f"保存面部动作标注文件失败: {str(e)}"
            self.stats["errors"].append(error_msg)
            return False

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
                "tongue_actions": FacialActionConfig.TONGUE_ACTIONS,
                "debug_information": {
                    "opencv_version": cv2.__version__,
                    "debug_messages": self.stats["debug_info"],
                    "chinese_path_fix": "使用cv2.imencode解决中文路径问题"
                }
            }

            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, ensure_ascii=False, indent=2)

        except Exception as e:
            error_msg = f"生成数据集信息失败: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(error_msg)


class SimpleProgressDialog(QDialog):
    """简单进度对话框 - 增加调试信息显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出面部动作数据集")
        self.setModal(True)
        self.setFixedSize(600, 280)

        layout = QVBoxLayout(self)

        # 状态标签
        self.status_label = QLabel("准备导出...")
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # 说明文字
        info_label = QLabel("正在将面部动作标注导出为45维向量数据集（修复中文路径）...")
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
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.cancelled = False

    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
        # 添加调试信息
        self.debug_text.append(f"[{value}%] {message}")
        self.debug_text.ensureCursorVisible()
        
        QApplication.processEvents()

    def reject(self):
        """取消对话框"""
        self.cancelled = True
        super().reject()


def simple_export_dataset(parent, video_path: str, annotations: List[AnnotationMarker],
                         video_info: VideoInfo) -> bool:
    """面部动作数据集导出入口函数 - 修复版本"""
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
        info_msg = f"""准备导出面部动作数据集 (修复版本)

视频文件: {os.path.basename(video_path)}
标注数量: {len(annotations)}
动作类别: {len(FacialActionConfig.ALL_LABELS)} 种面部动作
预计图像数: {total_frames}
标注文件格式: 每个文件45个浮点数 (对应45种面部动作)
预计耗时: {estimated_time:.1f}秒

修复功能:
• 解决OpenCV对中文路径的支持问题
• 使用cv2.imencode避免路径编码问题  
• 优化文件名生成，避免特殊字符
• 增强错误处理和调试信息

建议：选择英文路径作为输出目录以获得最佳兼容性

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
            "选择面部动作数据集输出目录（建议选择英文路径）",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not output_dir:
            return False

        # 检查磁盘空间
        try:
            import shutil
            free_space = shutil.disk_usage(output_dir).free
            estimated_size = total_frames * 60 * 1024

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
            # 显示详细结果
            stats = exporter.stats
            
            result_msg = f"""面部动作数据集导出完成！

输出目录: {output_dir}
图像数量: {stats['exported_images']}
标注文件数量: {stats['exported_labels']}
处理的标注: {stats['total_annotations']}
动作类别: {len(FacialActionConfig.ALL_LABELS)} 种

每个标注文件包含45个浮点数，对应45种面部动作的强度值。

自动激活规则:
• 舌头动作 → jawOpen=1.0
• 其他舌头动作 → tongueOut=1.0

✅ 已修复中文路径和导入问题"""

            if stats['errors']:
                result_msg += f"\n\n⚠️ 遇到 {len(stats['errors'])} 个问题，详情请查看 dataset_info.json"

            QMessageBox.information(parent, "导出成功", result_msg)
            return True
        elif progress_dialog.cancelled:
            QMessageBox.information(parent, "已取消", "导出已被用户取消")
            return False
        else:
            # 显示详细错误信息
            error_details = "\n".join(exporter.stats['errors'][-5:])
            detailed_msg = f"""导出过程中出现错误:

{error_details}

完整日志请查看输出目录中的 dataset_info.json 文件。"""
            
            QMessageBox.critical(parent, "导出失败", detailed_msg)
            return False

    except Exception as e:
        QMessageBox.critical(parent, "导出错误", f"导出时出现异常:\n{str(e)}")
        return False
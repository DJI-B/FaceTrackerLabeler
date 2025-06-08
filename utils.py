"""
通用工具函数
"""
import os
import json
from typing import List, Optional


class TimeUtils:
    """时间相关工具函数"""

    @staticmethod
    def format_time(seconds: float) -> str:
        """格式化时间显示 (MM:SS)"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    def format_time_ms(milliseconds: int) -> str:
        """格式化毫秒时间显示"""
        return TimeUtils.format_time(milliseconds / 1000.0)

    @staticmethod
    def parse_time(time_str: str) -> float:
        """解析时间字符串为秒数"""
        try:
            parts = time_str.split(":")
            if len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + int(seconds)
        except ValueError:
            pass
        return 0.0


class FileUtils:
    """文件操作工具函数"""

    @staticmethod
    def get_video_extensions() -> tuple:
        """获取支持的视频文件扩展名"""
        return ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v', '.webm')

    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """检查是否为视频文件"""
        return file_path.lower().endswith(FileUtils.get_video_extensions())

    @staticmethod
    def save_json(data: dict, file_path: str) -> bool:
        """保存JSON数据到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存JSON文件失败: {e}")
            return False

    @staticmethod
    def load_json(file_path: str) -> Optional[dict]:
        """从文件加载JSON数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载JSON文件失败: {e}")
            return None

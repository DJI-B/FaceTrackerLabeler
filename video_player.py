"""
视频播放器管理器
"""
from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from models import VideoInfo
from utils import FileUtils
import os


class VideoPlayerManager(QObject):
    """视频播放器管理器"""

    # 信号定义
    duration_changed = pyqtSignal(float)  # 时长改变
    position_changed = pyqtSignal(float)  # 位置改变
    playback_state_changed = pyqtSignal(int)  # 播放状态改变
    video_loaded = pyqtSignal(VideoInfo)  # 视频加载完成
    error_occurred = pyqtSignal(str)  # 错误发生

    def __init__(self, video_widget: QVideoWidget):
        super().__init__()

        # 创建播放器
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(video_widget)

        # 视频信息
        self.video_info = VideoInfo()

        # 连接信号
        self.setup_connections()

        # 位置更新定时器
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start(100)  # 100ms更新一次

    def setup_connections(self):
        """设置信号连接"""
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.media_player.errorChanged.connect(self.on_error)

    def load_video(self, file_path: str) -> bool:
        """加载视频文件"""
        try:
            if not os.path.exists(file_path):
                self.error_occurred.emit(f"视频文件不存在: {file_path}")
                return False

            if not FileUtils.is_video_file(file_path):
                self.error_occurred.emit("不支持的视频格式")
                return False

            # 设置媒体源
            url = QUrl.fromLocalFile(file_path)
            self.media_player.setSource(url)

            # 更新视频信息
            self.video_info.file_path = file_path

            return True

        except Exception as e:
            self.error_occurred.emit(f"加载视频失败: {str(e)}")
            return False

    def play(self):
        """播放"""
        self.media_player.play()

    def pause(self):
        """暂停"""
        self.media_player.pause()

    def stop(self):
        """停止"""
        self.media_player.stop()

    def toggle_playback(self):
        """切换播放/暂停"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def seek(self, position: float):
        """跳转到指定位置（秒）"""
        if self.video_info.duration > 0:
            position = max(0, min(position, self.video_info.duration))
            ms_position = int(position * 1000)
            self.media_player.setPosition(ms_position)

    def seek_relative(self, offset: float):
        """相对跳转（秒）"""
        current_pos = self.get_position()
        new_pos = current_pos + offset
        self.seek(new_pos)

    def get_position(self) -> float:
        """获取当前播放位置（秒）"""
        return self.media_player.position() / 1000.0

    def get_duration(self) -> float:
        """获取视频时长（秒）"""
        return self.video_info.duration

    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def set_volume(self, volume: float):
        """设置音量 (0.0 - 1.0)"""
        self.audio_output.setVolume(max(0.0, min(1.0, volume)))

    def get_volume(self) -> float:
        """获取音量"""
        return self.audio_output.volume()

    def set_muted(self, muted: bool):
        """设置静音"""
        self.audio_output.setMuted(muted)

    def is_muted(self) -> bool:
        """是否静音"""
        return self.audio_output.isMuted()

    def on_duration_changed(self, duration: int):
        """时长改变处理"""
        self.video_info.duration = duration / 1000.0
        self.duration_changed.emit(self.video_info.duration)

        # 发送视频加载完成信号
        self.video_loaded.emit(self.video_info)

    def on_position_changed(self, position: int):
        """位置改变处理"""
        position_sec = position / 1000.0
        self.position_changed.emit(position_sec)

    def on_playback_state_changed(self, state):
        """播放状态改变处理"""
        self.playback_state_changed.emit(state)

    def on_error(self, error):
        """错误处理"""
        if error != QMediaPlayer.Error.NoError:
            error_msg = f"播放器错误: {error}"
            self.error_occurred.emit(error_msg)

    def update_position(self):
        """更新位置（定时器调用）"""
        # 这个方法确保位置信号的及时更新
        pass

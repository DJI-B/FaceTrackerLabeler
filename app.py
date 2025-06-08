"""
应用程序主入口
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from main_window import VideoAnnotationMainWindow


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("Video Annotation Tool")
    app.setOrganizationName("AI Tools")
    app.setApplicationVersion("1.0")

    # 创建主窗口
    window = VideoAnnotationMainWindow()
    window.show()

    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
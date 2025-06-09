"""
修复后的 app.py - 解决导入问题
"""
import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加项目根目录到路径
project_root = os.path.dirname(current_dir) if os.path.basename(current_dir) != 'FaceTrackerLabeler' else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

def check_dependencies():
    """检查依赖和文件完整性"""
    missing_files = []
    required_files = [
        'annotation_manager.py',
        'annotation_page.py', 
        'main_window.py',
        'models.py',
        'styles.py',
        'utils.py',
        'video_player.py',
        'recording_page.py',
        'dataset_exporter.py'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    # 检查widgets目录
    widgets_dir = 'widgets'
    if not os.path.exists(widgets_dir):
        missing_files.append('widgets/ 目录')
    else:
        widget_files = [
            'widgets/__init__.py',
            'widgets/timeline_widget.py',
            'widgets/annotation_dialog.py',
            'widgets/roi_video_widget.py'
        ]
        for file in widget_files:
            if not os.path.exists(file):
                missing_files.append(file)
    
    return missing_files

def main():
    """主函数 - 增强错误处理"""
    try:
        # 检查文件完整性
        missing_files = check_dependencies()
        if missing_files:
            print("❌ 缺少以下文件:")
            for file in missing_files:
                print(f"   - {file}")
            print("\n请确保所有必需的文件都在项目目录中")
            input("按回车键退出...")
            return
        
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setApplicationName("Video Annotation Tool")
        app.setOrganizationName("AI Tools")
        app.setApplicationVersion("1.0")
        
        print("🔄 正在导入模块...")
        
        # 尝试导入主窗口
        try:
            from main_window import VideoAnnotationMainWindow
            print("✅ 主窗口模块导入成功")
        except ImportError as e:
            print(f"❌ 导入主窗口失败: {e}")
            
            # 尝试更详细的错误诊断
            try:
                import annotation_manager
                print("✅ annotation_manager 模块可以导入")
            except Exception as e2:
                print(f"❌ annotation_manager 导入失败: {e2}")
            
            try:
                import annotation_page
                print("✅ annotation_page 模块可以导入")
            except Exception as e3:
                print(f"❌ annotation_page 导入失败: {e3}")
            
            QMessageBox.critical(None, "导入错误", f"无法导入必需的模块:\n{str(e)}")
            return
        
        # 创建主窗口
        print("🔄 创建主窗口...")
        window = VideoAnnotationMainWindow()
        window.show()
        print("✅ 应用程序启动成功")

        # 运行应用程序
        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ 应用程序启动失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"Python路径: {sys.path[:3]}...")  # 只显示前3个路径
        
        try:
            QMessageBox.critical(None, "启动错误", f"应用程序启动失败:\n{str(e)}")
        except:
            pass
        
        input("按回车键退出...")


if __name__ == "__main__":
    main()
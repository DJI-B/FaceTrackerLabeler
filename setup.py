#!/usr/bin/env python3
"""
AI视频动作标注工具 - 自动化部署脚本
"""
import os
import sys
import subprocess
import platform

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """安装依赖"""
    print("🔄 正在安装依赖...")
    
    # 升级pip
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # 安装核心依赖
    dependencies = [
        "PyQt6>=6.4.0",
        "opencv-python>=4.7.0", 
        "numpy>=1.21.0",
        "websocket-client>=1.4.0",
        "Pillow>=9.0.0"
    ]
    
    for dep in dependencies:
        print(f"安装 {dep}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"✅ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {dep} 安装失败: {e}")
            return False
    
    return True

def check_file_integrity():
    """检查文件完整性"""
    print("🔍 检查项目文件...")
    
    required_files = [
        'app.py', 'main_window.py', 'annotation_page.py',
        'recording_page.py', 'annotation_manager.py', 'models.py',
        'styles.py', 'utils.py', 'video_player.py', 'dataset_exporter.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少以下文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ 所有核心文件检查通过")
    return True

def test_import():
    """测试导入"""
    print("🧪 测试模块导入...")
    
    test_modules = ['PyQt6.QtWidgets', 'cv2', 'numpy', 'websocket']
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"✅ {module} 导入成功")
        except ImportError as e:
            print(f"❌ {module} 导入失败: {e}")
            return False
    
    return True

def create_desktop_shortcut():
    """创建桌面快捷方式（Windows）"""
    if platform.system() != "Windows":
        return
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "AI视频标注工具.lnk")
        target = os.path.join(os.getcwd(), "app.py")
        wDir = os.getcwd()
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = wDir
        shortcut.save()
        
        print("✅ 桌面快捷方式创建成功")
    except ImportError:
        print("ℹ️ 跳过桌面快捷方式创建（需要pywin32）")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI视频动作标注工具 - 自动化部署")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查文件完整性
    if not check_file_integrity():
        print("\n请确保所有项目文件都在当前目录中")
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        print("\n依赖安装失败，请手动安装")
        sys.exit(1)
    
    # 测试导入
    if not test_import():
        print("\n模块导入测试失败")
        sys.exit(1)
    
    # 创建快捷方式（Windows）
    create_desktop_shortcut()
    
    print("\n" + "=" * 60)
    print("🎉 部署完成！")
    print("=" * 60)
    print("启动命令: python app.py")
    print("诊断命令: python check_project.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
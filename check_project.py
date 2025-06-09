"""
项目诊断脚本 - check_project.py
用于检查项目文件完整性和导入问题
"""
import os
import sys
import importlib.util

def check_file_exists(filepath):
    """检查文件是否存在"""
    exists = os.path.exists(filepath)
    size = os.path.getsize(filepath) if exists else 0
    return exists, size

def check_python_file(filepath):
    """检查Python文件语法"""
    if not os.path.exists(filepath):
        return False, "文件不存在"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试编译
        compile(content, filepath, 'exec')
        return True, "语法正确"
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"其他错误: {e}"

def try_import_module(module_name, filepath=None):
    """尝试导入模块"""
    try:
        if filepath:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            __import__(module_name)
        return True, "导入成功"
    except Exception as e:
        return False, f"导入失败: {e}"

def main():
    """主诊断函数"""
    print("=" * 60)
    print("🔍 视频标注工具项目诊断")
    print("=" * 60)
    
    # 基本环境信息
    print(f"📍 当前工作目录: {os.getcwd()}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"📂 项目根目录: {os.path.abspath('.')}")
    print()
    
    # 检查必需文件
    print("📋 检查必需文件:")
    print("-" * 40)
    
    required_files = {
        "核心模块": [
            'annotation_manager.py',
            'annotation_page.py', 
            'main_window.py',
            'models.py',
            'styles.py',
            'utils.py',
            'video_player.py',
            'recording_page.py',
            'dataset_exporter.py',
            'app.py'
        ],
        "控件模块": [
            'widgets/__init__.py',
            'widgets/timeline_widget.py',
            'widgets/annotation_dialog.py',
            'widgets/roi_video_widget.py'
        ]
    }
    
    all_files_ok = True
    
    for category, files in required_files.items():
        print(f"\n{category}:")
        for file in files:
            exists, size = check_file_exists(file)
            status = "✅" if exists else "❌"
            size_info = f"({size} bytes)" if exists else "(缺失)"
            print(f"  {status} {file} {size_info}")
            
            if not exists:
                all_files_ok = False
    
    print()
    
    # 检查Python文件语法
    print("🔍 检查Python文件语法:")
    print("-" * 40)
    
    python_files = [f for category in required_files.values() for f in category if f.endswith('.py')]
    syntax_ok = True
    
    for file in python_files:
        if os.path.exists(file):
            is_ok, message = check_python_file(file)
            status = "✅" if is_ok else "❌"
            print(f"  {status} {file}: {message}")
            if not is_ok:
                syntax_ok = False
    
    print()
    
    # 检查模块导入
    print("📦 检查模块导入:")
    print("-" * 40)
    
    # 添加当前目录到Python路径
    current_dir = os.path.abspath('.')
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    core_modules = [
        ('annotation_manager', 'annotation_manager.py'),
        ('models', 'models.py'), 
        ('styles', 'styles.py'),
        ('utils', 'utils.py'),
        ('video_player', 'video_player.py')
    ]
    
    import_ok = True
    
    for module_name, filepath in core_modules:
        if os.path.exists(filepath):
            is_ok, message = try_import_module(module_name, filepath)
            status = "✅" if is_ok else "❌"
            print(f"  {status} {module_name}: {message}")
            if not is_ok:
                import_ok = False
        else:
            print(f"  ❌ {module_name}: 文件不存在")
            import_ok = False
    
    print()
    
    # 检查PyQt6
    print("🖥️ 检查PyQt6依赖:")
    print("-" * 40)
    
    pyqt_modules = [
        'PyQt6.QtWidgets',
        'PyQt6.QtCore', 
        'PyQt6.QtGui',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets'
    ]
    
    pyqt_ok = True
    for module in pyqt_modules:
        is_ok, message = try_import_module(module)
        status = "✅" if is_ok else "❌"
        print(f"  {status} {module}: {message}")
        if not is_ok:
            pyqt_ok = False
    
    print()
    
    # 检查其他依赖
    print("📚 检查其他依赖:")
    print("-" * 40)
    
    other_deps = ['cv2', 'numpy', 'websocket']
    deps_ok = True
    
    for dep in other_deps:
        is_ok, message = try_import_module(dep)
        status = "✅" if is_ok else "❌"
        print(f"  {status} {dep}: {message}")
        if not is_ok:
            deps_ok = False
    
    print()
    
    # 总结
    print("📊 诊断总结:")
    print("=" * 40)
    
    issues = []
    if not all_files_ok:
        issues.append("❌ 缺少必需文件")
    if not syntax_ok:
        issues.append("❌ Python语法错误")
    if not import_ok:
        issues.append("❌ 模块导入失败")
    if not pyqt_ok:
        issues.append("❌ PyQt6依赖问题")
    if not deps_ok:
        issues.append("❌ 其他依赖缺失")
    
    if not issues:
        print("🎉 所有检查通过！项目应该可以正常运行。")
        print("\n建议运行命令:")
        print("python app.py")
    else:
        print("⚠️ 发现以下问题:")
        for issue in issues:
            print(f"  {issue}")
        
        print("\n🔧 建议解决方案:")
        if not all_files_ok:
            print("  1. 确保所有必需文件都在项目目录中")
        if not pyqt_ok:
            print("  2. 安装PyQt6: pip install PyQt6")
        if not deps_ok:
            print("  3. 安装依赖: pip install opencv-python numpy websocket-client")
        if not import_ok or not syntax_ok:
            print("  4. 检查Python文件语法错误")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")
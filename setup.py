#!/usr/bin/env python3
"""
Polymarket数据收集项目设置脚本
用于初始化项目环境和验证系统功能
"""

import os
import sys
from pathlib import Path
import subprocess

def create_directory_structure():
    """创建项目目录结构"""
    print("🏗️  创建项目目录结构...")
    
    directories = [
        "Poly_info/data",
        "Poly_price_data/data", 
        "Poly_order/data",
        "Poly_user_data/data",
        "Poly_market_fluctuation/data",
        "data_relationships/data",
        "logs",
        "output"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ 创建目录: {directory}")

def check_dependencies():
    """检查项目依赖"""
    print("\n📦 检查项目依赖...")
    
    required_packages = [
        "requests",
        "pandas", 
        "pathlib",
        "typing-extensions",
        "python-dateutil"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} (缺失)")
    
    if missing_packages:
        print(f"\n⚠️  缺失依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("\n✅ 所有依赖包已安装")
    return True

def test_api_connectivity():
    """测试API连接性"""
    print("\n🌐 测试API连接性...")
    
    try:
        import requests
        
        # 测试Gamma API
        gamma_response = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 1},
            timeout=10
        )
        
        if gamma_response.status_code == 200:
            print("  ✅ Gamma Markets API 连接正常")
        else:
            print(f"  ❌ Gamma Markets API 连接失败: {gamma_response.status_code}")
            return False
        
        # 测试CLOB API
        clob_response = requests.get(
            "https://clob.polymarket.com/prices",
            timeout=10
        )
        
        if clob_response.status_code == 200:
            print("  ✅ CLOB API 连接正常")
        else:
            print(f"  ❌ CLOB API 连接失败: {clob_response.status_code}")
            return False
        
        print("\n✅ API连接测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ API连接测试失败: {e}")
        return False

def run_quick_test():
    """运行快速功能测试"""
    print("\n🧪 运行快速功能测试...")
    
    try:
        # 检查测试文件是否存在
        test_file = Path("tests/quick_test.py")
        if not test_file.exists():
            print("  ❌ 测试文件不存在: tests/quick_test.py")
            return False
        
        # 运行测试
        result = subprocess.run([
            sys.executable, "tests/quick_test.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("  ✅ 快速功能测试通过")
            return True
        else:
            print(f"  ❌ 快速功能测试失败")
            print(f"  错误输出: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ⏰ 测试超时")
        return False
    except Exception as e:
        print(f"  ❌ 测试运行失败: {e}")
        return False

def create_env_template():
    """创建环境变量模板文件"""
    print("\n📝 创建环境变量模板...")
    
    env_template = """# Polymarket数据收集项目环境变量配置
# 复制此文件为 .env 并根据需要修改配置

# API配置
POLYMARKET_API_KEY=
POLYMARKET_API_SECRET=
POLYMARKET_API_PASSPHRASE=
POLYMARKET_PRIVATE_KEY=

# 数据收集配置
DEFAULT_LIMIT=100
MAX_RETRIES=3
TIMEOUT=10
RATE_LIMIT_DELAY=1

# 监控配置
PRICE_CHANGE_THRESHOLD=0.05
FLUCTUATION_CHECK_INTERVAL=10
PRICE_UPDATE_INTERVAL=60

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/polymarket.log
"""
    
    env_file = Path(".env.template")
    env_file.write_text(env_template, encoding='utf-8')
    print(f"  ✅ 创建环境变量模板: {env_file}")

def display_next_steps():
    """显示后续步骤"""
    print("\n🎉 项目设置完成！")
    print("\n📋 后续步骤:")
    print("1. 运行快速测试: python tests/quick_test.py")
    print("2. 查看项目文档: docs/README.md")
    print("3. 时间序列API指南: docs/TIMESERIES_GUIDE.md")
    print("4. 使用示例: python examples/timeseries_example.py")
    print("5. 主程序使用: python main.py --help")
    
    print("\n🔧 常用命令:")
    print("# 获取市场信息")
    print("python main.py market-info --type active --limit 10")
    print("\n# 收集价格数据")
    print("python main.py price-data --mode batch")
    print("\n# 监控市场波动")
    print("python main.py fluctuation --interval 60")

def main():
    """主函数"""
    print("🚀 Polymarket数据收集项目设置")
    print("=" * 50)
    
    # 检查当前目录
    if not Path("config.py").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 执行设置步骤
    success = True
    
    # 1. 创建目录结构
    create_directory_structure()
    
    # 2. 检查依赖
    if not check_dependencies():
        success = False
    
    # 3. 测试API连接
    if success and not test_api_connectivity():
        success = False
    
    # 4. 创建环境变量模板
    create_env_template()
    
    # 5. 运行快速测试（可选）
    if success:
        print("\n❓ 是否运行快速功能测试？(y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes', '是']:
                run_quick_test()
        except KeyboardInterrupt:
            print("\n⏹️  跳过测试")
    
    # 6. 显示后续步骤
    display_next_steps()
    
    if success:
        print("\n✅ 项目设置成功完成！")
    else:
        print("\n⚠️  项目设置完成，但存在一些问题，请检查上述错误信息")

if __name__ == "__main__":
    main() 
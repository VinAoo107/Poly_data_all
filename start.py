#!/usr/bin/env python3
"""
Polymarket数据收集项目快速启动脚本
提供简化的命令行界面访问常用功能
"""

import sys
import subprocess
from pathlib import Path

def show_menu():
    """显示主菜单"""
    print("\n🚀 Polymarket数据收集项目")
    print("=" * 40)
    print("1. 🧪 运行快速测试")
    print("2. 📊 获取市场信息")
    print("3. 💰 收集价格数据")
    print("4. 📈 时间序列示例")
    print("5. 🔍 监控市场波动")
    print("6. 📚 查看文档")
    print("7. ⚙️  项目设置")
    print("8. 🆘 帮助信息")
    print("0. 🚪 退出")
    print("=" * 40)

def run_quick_test():
    """运行快速测试"""
    print("\n🧪 运行快速功能测试...")
    try:
        subprocess.run([sys.executable, "tests/quick_test.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ 测试失败")
    except FileNotFoundError:
        print("❌ 测试文件不存在")

def get_market_info():
    """获取市场信息"""
    print("\n📊 获取市场信息...")
    print("选择市场类型:")
    print("1. 活跃市场")
    print("2. 所有市场")
    print("3. 已关闭市场")
    
    choice = input("请选择 (1-3): ").strip()
    
    market_type_map = {
        "1": "active",
        "2": "all", 
        "3": "closed"
    }
    
    market_type = market_type_map.get(choice, "active")
    limit = input("获取数量 (默认10): ").strip() or "10"
    
    try:
        subprocess.run([
            sys.executable, "main.py", "market-info",
            "--type", market_type,
            "--limit", limit
        ], check=True)
    except subprocess.CalledProcessError:
        print("❌ 获取市场信息失败")

def collect_price_data():
    """收集价格数据"""
    print("\n💰 收集价格数据...")
    print("选择收集模式:")
    print("1. 批量收集")
    print("2. 实时监控")
    print("3. 生成报告")
    
    choice = input("请选择 (1-3): ").strip()
    
    mode_map = {
        "1": "batch",
        "2": "monitor",
        "3": "report"
    }
    
    mode = mode_map.get(choice, "batch")
    
    try:
        subprocess.run([
            sys.executable, "main.py", "price-data",
            "--mode", mode
        ], check=True)
    except subprocess.CalledProcessError:
        print("❌ 收集价格数据失败")

def run_timeseries_example():
    """运行时间序列示例"""
    print("\n📈 运行时间序列数据示例...")
    try:
        subprocess.run([sys.executable, "examples/timeseries_example.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ 示例运行失败")
    except FileNotFoundError:
        print("❌ 示例文件不存在")

def monitor_fluctuation():
    """监控市场波动"""
    print("\n🔍 监控市场波动...")
    
    interval = input("监控间隔(秒，默认60): ").strip() or "60"
    threshold = input("价格变化阈值(默认0.05): ").strip() or "0.05"
    
    try:
        subprocess.run([
            sys.executable, "main.py", "fluctuation",
            "--interval", interval,
            "--threshold", threshold
        ], check=True)
    except subprocess.CalledProcessError:
        print("❌ 监控启动失败")
    except KeyboardInterrupt:
        print("\n⏹️  监控已停止")

def view_docs():
    """查看文档"""
    print("\n📚 项目文档:")
    print("1. 项目README - docs/README.md")
    print("2. 时间序列指南 - docs/TIMESERIES_GUIDE.md")
    print("3. 在线文档 - https://docs.polymarket.com/")
    
    choice = input("选择要查看的文档 (1-3): ").strip()
    
    if choice == "1":
        try:
            with open("docs/README.md", "r", encoding="utf-8") as f:
                content = f.read()
                print("\n" + "="*50)
                print(content[:1000] + "..." if len(content) > 1000 else content)
                print("="*50)
        except FileNotFoundError:
            print("❌ 文档文件不存在")
    elif choice == "2":
        try:
            with open("docs/TIMESERIES_GUIDE.md", "r", encoding="utf-8") as f:
                content = f.read()
                print("\n" + "="*50)
                print(content[:1000] + "..." if len(content) > 1000 else content)
                print("="*50)
        except FileNotFoundError:
            print("❌ 文档文件不存在")
    elif choice == "3":
        print("请访问: https://docs.polymarket.com/")

def run_setup():
    """运行项目设置"""
    print("\n⚙️  运行项目设置...")
    try:
        subprocess.run([sys.executable, "setup.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ 设置失败")
    except FileNotFoundError:
        print("❌ 设置文件不存在")

def show_help():
    """显示帮助信息"""
    print("\n🆘 帮助信息")
    print("=" * 40)
    print("项目结构:")
    print("├── 核心模块/")
    print("│   ├── Poly_info/ - 市场信息收集")
    print("│   ├── Poly_price_data/ - 价格数据收集")
    print("│   ├── Poly_order/ - 订单数据收集")
    print("│   ├── Poly_user_data/ - 用户数据收集")
    print("│   └── Poly_market_fluctuation/ - 市场波动监控")
    print("├── tests/ - 测试文件")
    print("├── examples/ - 使用示例")
    print("├── scripts/ - 实用脚本")
    print("└── docs/ - 项目文档")
    
    print("\n常用命令:")
    print("python main.py --help - 查看主程序帮助")
    print("python tests/quick_test.py - 运行快速测试")
    print("python examples/timeseries_example.py - 时间序列示例")
    print("python setup.py - 项目设置")

def main():
    """主函数"""
    # 检查是否在项目根目录
    if not Path("config.py").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    while True:
        try:
            show_menu()
            choice = input("\n请选择操作 (0-8): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                run_quick_test()
            elif choice == "2":
                get_market_info()
            elif choice == "3":
                collect_price_data()
            elif choice == "4":
                run_timeseries_example()
            elif choice == "5":
                monitor_fluctuation()
            elif choice == "6":
                view_docs()
            elif choice == "7":
                run_setup()
            elif choice == "8":
                show_help()
            else:
                print("❌ 无效选择，请重新输入")
            
            input("\n按回车键继续...")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            input("按回车键继续...")

if __name__ == "__main__":
    main() 
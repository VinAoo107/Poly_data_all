"""
Polymarket 数据收集项目 - 快速测试
简单的API连接和基本功能测试
"""

import sys
import os
from pathlib import Path
import requests
import json
from datetime import datetime

# 设置编码以避免Windows下的Unicode问题
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config import APIEndpoints
except ImportError as e:
    print(f"[错误] 导入配置失败: {e}")
    print("请确保config.py文件存在且格式正确")
    sys.exit(1)

def test_api_connectivity():
    """测试API连接性"""
    print("=== API连接测试 ===")
    
    tests = [
        {
            "name": "Gamma Markets API - 事件",
            "url": f"{APIEndpoints.GAMMA_BASE_URL}/events",
            "params": {"limit": 5}
        },
        {
            "name": "Gamma Markets API - 市场",
            "url": f"{APIEndpoints.GAMMA_BASE_URL}/markets",
            "params": {"limit": 5}
        },
        {
            "name": "CLOB API - 简化市场",
            "url": f"{APIEndpoints.CLOB_BASE_URL}/simplified-markets",
            "params": {"limit": 5}
        }
    ]
    
    results = []
    
    for test in tests:
        try:
            print(f"\n测试: {test['name']}")
            response = requests.get(test['url'], params=test.get('params', {}), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 1
                print(f"[成功] 获取到 {count} 条数据")
                results.append({"test": test['name'], "status": "成功", "count": count})
            else:
                print(f"[失败] 状态码: {response.status_code}")
                results.append({"test": test['name'], "status": "失败", "error": f"状态码 {response.status_code}"})
                
        except Exception as e:
            print(f"[异常] {str(e)}")
            results.append({"test": test['name'], "status": "异常", "error": str(e)})
    
    return results

def test_timeseries_data():
    """测试时间序列数据获取"""
    print("\n=== 时间序列数据测试 ===")
    
    # 使用已知的Token ID
    token_id = "42539672745835417166310556793707418417075205359699744726511175708846683253904"
    
    try:
        print(f"测试Token: {token_id[:30]}...")
        
        params = {
            "market": token_id,
            "interval": "max"
        }
        
        response = requests.get(APIEndpoints.TIMESERIES, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            history = data.get("history", [])
            
            if history:
                print(f"[成功] 获取 {len(history)} 个历史数据点")
                
                # 显示数据范围
                if len(history) > 0:
                    first_point = history[0]
                    last_point = history[-1]
                    
                    if isinstance(first_point, dict) and 't' in first_point:
                        first_time = datetime.fromtimestamp(first_point['t'])
                        last_time = datetime.fromtimestamp(last_point['t'])
                        print(f"时间范围: {first_time.strftime('%Y-%m-%d')} 到 {last_time.strftime('%Y-%m-%d')}")
                
                return {"status": "成功", "count": len(history)}
            else:
                print("[警告] API响应正常，但没有历史数据")
                return {"status": "无数据", "count": 0}
        else:
            print(f"[失败] 请求失败 - 状态码: {response.status_code}")
            return {"status": "失败", "error": f"状态码 {response.status_code}"}
            
    except Exception as e:
        print(f"[异常] 请求异常: {str(e)}")
        return {"status": "异常", "error": str(e)}

def test_project_structure():
    """测试项目结构"""
    print("\n=== 项目结构测试 ===")
    
    required_dirs = [
        "Poly_info",
        "Poly_price_data", 
        "Poly_order",
        "Poly_user_data",
        "Poly_market_fluctuation"
    ]
    
    required_files = [
        "config.py",
        "utils.py",
        "main.py",
        "requirements.txt"
    ]
    
    missing_items = []
    
    # 检查目录
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"[OK] 目录存在: {dir_name}")
        else:
            print(f"[缺失] 目录缺失: {dir_name}")
            missing_items.append(f"目录: {dir_name}")
    
    # 检查文件
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"[OK] 文件存在: {file_name}")
        else:
            print(f"[缺失] 文件缺失: {file_name}")
            missing_items.append(f"文件: {file_name}")
    
    return {"missing_items": missing_items}

def generate_test_report(api_results, timeseries_result, structure_result):
    """生成测试报告"""
    print("\n" + "="*60)
    print("测试报告总结")
    print("="*60)
    
    # API测试总结
    api_success = sum(1 for r in api_results if r['status'] == '成功')
    api_total = len(api_results)
    print(f"\nAPI连接测试: {api_success}/{api_total} 成功")
    
    # 时间序列测试总结
    ts_status = timeseries_result['status']
    print(f"时间序列测试: {ts_status}")
    
    # 项目结构总结
    missing_count = len(structure_result['missing_items'])
    if missing_count == 0:
        print("项目结构: [完整]")
    else:
        print(f"项目结构: [警告] 缺失 {missing_count} 项")
    
    # 整体状态
    print(f"\n整体状态:")
    if api_success >= api_total * 0.8 and ts_status == "成功" and missing_count == 0:
        print("[优秀] 项目状态良好，可以正常使用！")
    elif api_success >= api_total * 0.5:
        print("[警告] 项目基本可用，但可能存在一些问题")
    else:
        print("[错误] 项目存在较多问题，需要检查配置")
    
    # 使用建议
    print(f"\n使用建议:")
    print("1. 运行 'python start.py' 进行交互式操作")
    print("2. 运行 'python main.py --help' 查看所有功能")
    print("3. 查看 README.md 了解详细使用方法")

def main():
    """主测试函数"""
    print("Polymarket 数据收集项目 - 快速测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. API连接测试
        api_results = test_api_connectivity()
        
        # 2. 时间序列数据测试
        timeseries_result = test_timeseries_data()
        
        # 3. 项目结构测试
        structure_result = test_project_structure()
        
        # 4. 生成测试报告
        generate_test_report(api_results, timeseries_result, structure_result)
        
    except Exception as e:
        print(f"\n[错误] 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n测试完成！")

if __name__ == "__main__":
    main() 
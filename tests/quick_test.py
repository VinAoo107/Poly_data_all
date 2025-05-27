"""
Polymarket Data Collection Project - Quick Test
Simple API connectivity and basic functionality test
"""

import sys
import os
from pathlib import Path
import requests
import json
from datetime import datetime

# Set encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config import APIEndpoints
except ImportError as e:
    print(f"[ERROR] Failed to import config: {e}")
    print("Please ensure config.py exists and is properly formatted")
    sys.exit(1)

def test_api_connectivity():
    """Test API connectivity"""
    print("=== API Connectivity Test ===")
    
    tests = [
        {
            "name": "Gamma Markets API - Events",
            "url": f"{APIEndpoints.GAMMA_BASE_URL}/events",
            "params": {"limit": 5}
        },
        {
            "name": "Gamma Markets API - Markets",
            "url": f"{APIEndpoints.GAMMA_BASE_URL}/markets",
            "params": {"limit": 5}
        },
        {
            "name": "CLOB API - Simplified Markets",
            "url": f"{APIEndpoints.CLOB_BASE_URL}/simplified-markets",
            "params": {"limit": 5}
        }
    ]
    
    results = []
    
    for test in tests:
        try:
            print(f"\nTesting: {test['name']}")
            response = requests.get(test['url'], params=test.get('params', {}), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 1
                print(f"[SUCCESS] Retrieved {count} data items")
                results.append({"test": test['name'], "status": "SUCCESS", "count": count})
            else:
                print(f"[FAILED] Status code: {response.status_code}")
                results.append({"test": test['name'], "status": "FAILED", "error": f"Status {response.status_code}"})
                
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            results.append({"test": test['name'], "status": "ERROR", "error": str(e)})
    
    return results

def test_timeseries_data():
    """Test timeseries data retrieval"""
    print("\n=== Timeseries Data Test ===")
    
    # Use known Token ID
    token_id = "42539672745835417166310556793707418417075205359699744726511175708846683253904"
    
    try:
        print(f"Testing Token: {token_id[:30]}...")
        
        params = {
            "market": token_id,
            "interval": "max"
        }
        
        response = requests.get(APIEndpoints.TIMESERIES, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            history = data.get("history", [])
            
            if history:
                print(f"[SUCCESS] Retrieved {len(history)} historical data points")
                
                # Show data range
                if len(history) > 0:
                    first_point = history[0]
                    last_point = history[-1]
                    
                    if isinstance(first_point, dict) and 't' in first_point:
                        first_time = datetime.fromtimestamp(first_point['t'])
                        last_time = datetime.fromtimestamp(last_point['t'])
                        print(f"Time range: {first_time.strftime('%Y-%m-%d')} to {last_time.strftime('%Y-%m-%d')}")
                
                return {"status": "SUCCESS", "count": len(history)}
            else:
                print("[WARNING] API response OK, but no historical data")
                return {"status": "NO_DATA", "count": 0}
        else:
            print(f"[FAILED] Request failed - Status code: {response.status_code}")
            return {"status": "FAILED", "error": f"Status {response.status_code}"}
            
    except Exception as e:
        print(f"[ERROR] Request error: {str(e)}")
        return {"status": "ERROR", "error": str(e)}

def test_project_structure():
    """Test project structure"""
    print("\n=== Project Structure Test ===")
    
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
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"[OK] Directory exists: {dir_name}")
        else:
            print(f"[MISSING] Directory missing: {dir_name}")
            missing_items.append(f"Directory: {dir_name}")
    
    # Check files
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"[OK] File exists: {file_name}")
        else:
            print(f"[MISSING] File missing: {file_name}")
            missing_items.append(f"File: {file_name}")
    
    return {"missing_items": missing_items}

def generate_test_report(api_results, timeseries_result, structure_result):
    """Generate test report"""
    print("\n" + "="*60)
    print("Test Report Summary")
    print("="*60)
    
    # API test summary
    api_success = sum(1 for r in api_results if r['status'] == 'SUCCESS')
    api_total = len(api_results)
    print(f"\nAPI Connectivity Test: {api_success}/{api_total} successful")
    
    # Timeseries test summary
    ts_status = timeseries_result['status']
    print(f"Timeseries Test: {ts_status}")
    
    # Project structure summary
    missing_count = len(structure_result['missing_items'])
    if missing_count == 0:
        print("Project Structure: [COMPLETE]")
    else:
        print(f"Project Structure: [WARNING] Missing {missing_count} items")
    
    # Overall status
    print(f"\nOverall Status:")
    if api_success >= api_total * 0.8 and ts_status == "SUCCESS" and missing_count == 0:
        print("[EXCELLENT] Project is in good condition and ready to use!")
    elif api_success >= api_total * 0.5:
        print("[WARNING] Project is basically usable but may have some issues")
    else:
        print("[ERROR] Project has multiple issues, please check configuration")
    
    # Usage suggestions
    print(f"\nUsage Suggestions:")
    print("1. Run 'python start.py' for interactive operation")
    print("2. Run 'python main.py --help' to see all features")
    print("3. Check README.md for detailed usage instructions")

def main():
    """Main test function"""
    print("Polymarket Data Collection Project - Quick Test")
    print("="*60)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. API connectivity test
        api_results = test_api_connectivity()
        
        # 2. Timeseries data test
        timeseries_result = test_timeseries_data()
        
        # 3. Project structure test
        structure_result = test_project_structure()
        
        # 4. Generate test report
        generate_test_report(api_results, timeseries_result, structure_result)
        
    except Exception as e:
        print(f"\n[ERROR] Exception occurred during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\nTest completed!")

if __name__ == "__main__":
    main() 
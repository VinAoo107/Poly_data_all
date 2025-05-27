"""
Polymarket时间序列数据获取示例
基于官方文档: https://docs.polymarket.com/developers/CLOB/timeseries

这个示例展示了如何正确使用Polymarket的时间序列API端点
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, List, Union

class PolymarketTimeseriesClient:
    """Polymarket时间序列数据客户端"""
    
    def __init__(self):
        self.clob_endpoint = "https://clob.polymarket.com"
        self.gamma_endpoint = "https://gamma-api.polymarket.com"
    
    def get_price_history(self, 
                         market_id: str, 
                         interval: Optional[str] = None,
                         start_ts: Optional[int] = None,
                         end_ts: Optional[int] = None,
                         fidelity: int = 60) -> Optional[Dict]:
        """
        获取价格历史数据
        
        参数:
            market_id: 市场/代币ID (CLOB token ID)
            interval: 时间间隔 ("1m", "1w", "1d", "6h", "1h", "max")
            start_ts: 开始时间戳 (UNIX timestamp)
            end_ts: 结束时间戳 (UNIX timestamp)
            fidelity: 数据精度，以分钟为单位 (1=每分钟, 60=每小时, 1440=每天)
            
        注意: interval 和 start_ts/end_ts 参数互斥
        
        返回:
            包含历史数据的字典，格式: {"history": [{"t": timestamp, "p": price}, ...]}
        """
        
        # 构建请求参数
        params = {
            "market": market_id,
            "fidelity": fidelity
        }
        
        # 添加时间参数 (interval 和 startTs/endTs 互斥)
        if interval:
            params["interval"] = interval
        elif start_ts and end_ts:
            params["startTs"] = start_ts
            params["endTs"] = end_ts
        else:
            # 默认使用max interval获取所有历史数据
            params["interval"] = "max"
        
        try:
            response = requests.get(
                f"{self.clob_endpoint}/prices-history",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"请求失败: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"请求异常: {e}")
            return None
    
    def get_price_history_dataframe(self, 
                                   market_id: str, 
                                   **kwargs) -> Optional[pd.DataFrame]:
        """
        获取价格历史数据并转换为pandas DataFrame
        
        参数:
            market_id: 市场/代币ID
            **kwargs: 传递给get_price_history的其他参数
            
        返回:
            pandas DataFrame，包含时间戳、价格等信息
        """
        
        data = self.get_price_history(market_id, **kwargs)
        
        if not data or "history" not in data:
            return None
        
        history = data["history"]
        
        if not history:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(history)
        
        # 重命名列（根据文档规范）
        df.rename(columns={"t": "timestamp", "p": "price"}, inplace=True)
        
        # 转换时间戳为datetime
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
        df.set_index("datetime", inplace=True)
        
        # 排序并去重
        df.sort_index(inplace=True)
        if df.index.duplicated().any():
            df = df[~df.index.duplicated(keep='last')]
        
        # 添加市场ID信息
        df["market_id"] = market_id
        
        return df
    
    def get_market_token_ids(self, limit: int = 10) -> List[Dict]:
        """
        获取市场数据和对应的token IDs
        
        参数:
            limit: 获取的市场数量
            
        返回:
            包含市场信息和token IDs的列表
        """
        
        try:
            response = requests.get(
                f"{self.gamma_endpoint}/markets",
                params={"limit": limit, "active": "true"},
                timeout=10
            )
            
            if response.status_code == 200:
                markets = response.json()
                
                market_info = []
                for market in markets:
                    clob_token_ids = market.get('clobTokenIds')
                    
                    if clob_token_ids:
                        # 处理不同格式的clobTokenIds
                        if isinstance(clob_token_ids, str):
                            try:
                                clob_token_ids = json.loads(clob_token_ids)
                            except:
                                pass
                        
                        # 提取token IDs
                        if isinstance(clob_token_ids, list):
                            token_ids = clob_token_ids
                        elif isinstance(clob_token_ids, str):
                            token_ids = [clob_token_ids]
                        else:
                            continue
                        
                        market_info.append({
                            "market_id": market.get("id"),
                            "question": market.get("question"),
                            "token_ids": token_ids,
                            "active": market.get("active"),
                            "outcomes": market.get("outcomes", [])
                        })
                
                return market_info
            else:
                print(f"获取市场数据失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"获取市场数据异常: {e}")
            return []

def example_usage():
    """使用示例"""
    print("Polymarket时间序列数据获取示例")
    print("=" * 50)
    
    client = PolymarketTimeseriesClient()
    
    # 示例1: 使用已知的token ID获取历史数据
    print("\n1. 使用已知token ID获取历史数据")
    sample_token_id = "42539672745835417166310556793707418417075205359699744726511175708846683253904"
    
    # 获取最近1周的小时级数据
    df = client.get_price_history_dataframe(
        market_id=sample_token_id,
        interval="1w",
        fidelity=60  # 1小时精度
    )
    
    if df is not None and not df.empty:
        print(f"✅ 成功获取 {len(df)} 个数据点")
        print(f"时间范围: {df.index.min()} 至 {df.index.max()}")
        print(f"价格范围: {df['price'].min():.4f} - {df['price'].max():.4f}")
        print("\n数据预览:")
        print(df.head())
    else:
        print("❌ 未获取到数据")
    
    # 示例2: 使用时间戳范围获取数据
    print("\n2. 使用时间戳范围获取数据")
    
    # 设置时间范围（最近3天）
    end_time = datetime.now()
    start_time = end_time - timedelta(days=3)
    
    df_range = client.get_price_history_dataframe(
        market_id=sample_token_id,
        start_ts=int(start_time.timestamp()),
        end_ts=int(end_time.timestamp()),
        fidelity=1440  # 日级别数据
    )
    
    if df_range is not None and not df_range.empty:
        print(f"✅ 成功获取 {len(df_range)} 个数据点")
        print(f"查询时间范围: {start_time} 至 {end_time}")
        print(f"实际数据范围: {df_range.index.min()} 至 {df_range.index.max()}")
    else:
        print("❌ 指定时间范围内未获取到数据")
    
    # 示例3: 获取真实市场数据并测试时间序列
    print("\n3. 获取真实市场数据并测试时间序列")
    
    markets = client.get_market_token_ids(limit=3)
    
    if markets:
        print(f"获取到 {len(markets)} 个市场")
        
        for i, market in enumerate(markets):
            print(f"\n--- 市场 {i+1}: {market['question'][:50]}... ---")
            
            # 测试第一个token ID
            if market['token_ids']:
                token_id = market['token_ids'][0]
                print(f"Token ID: {token_id[:20]}...")
                
                # 获取最大历史数据
                df_market = client.get_price_history_dataframe(
                    market_id=token_id,
                    interval="max",
                    fidelity=1440  # 日级别
                )
                
                if df_market is not None and not df_market.empty:
                    print(f"✅ 获取到 {len(df_market)} 个价格数据点")
                    print(f"价格范围: {df_market['price'].min():.4f} - {df_market['price'].max():.4f}")
                    
                    # 计算价格变化
                    if len(df_market) > 1:
                        price_change = ((df_market['price'].iloc[-1] - df_market['price'].iloc[0]) / 
                                      df_market['price'].iloc[0]) * 100
                        print(f"总价格变化: {price_change:.2f}%")
                else:
                    print("⚠️ 没有历史价格数据")
    else:
        print("❌ 未获取到市场数据")

def save_timeseries_data_example():
    """保存时间序列数据的示例"""
    print("\n4. 保存时间序列数据示例")
    
    client = PolymarketTimeseriesClient()
    sample_token_id = "42539672745835417166310556793707418417075205359699744726511175708846683253904"
    
    # 获取不同精度的数据
    fidelity_configs = [
        (60, "hourly"),      # 小时级
        (1440, "daily"),     # 日级
    ]
    
    for fidelity, name in fidelity_configs:
        print(f"\n获取{name}数据 (fidelity={fidelity})...")
        
        df = client.get_price_history_dataframe(
            market_id=sample_token_id,
            interval="max",
            fidelity=fidelity
        )
        
        if df is not None and not df.empty:
            # 保存为CSV
            filename = f"price_history_{name}_{sample_token_id[:10]}.csv"
            df.to_csv(filename)
            print(f"✅ 数据已保存到: {filename}")
            print(f"   数据点数: {len(df)}")
            print(f"   时间范围: {df.index.min()} 至 {df.index.max()}")
        else:
            print(f"❌ 未获取到{name}数据")

if __name__ == "__main__":
    # 运行示例
    example_usage()
    save_timeseries_data_example()
    
    print("\n" + "=" * 50)
    print("时间序列API使用要点总结:")
    print("1. 端点: https://clob.polymarket.com/prices-history")
    print("2. 必需参数: market (token_id)")
    print("3. 时间参数: interval 或 startTs/endTs (二选一)")
    print("4. 精度参数: fidelity (分钟为单位)")
    print("5. 响应格式: {\"history\": [{\"t\": timestamp, \"p\": price}, ...]}")
    print("6. interval选项: 1m, 1w, 1d, 6h, 1h, max")
    print("7. 常用fidelity: 1(分钟), 60(小时), 1440(天)") 
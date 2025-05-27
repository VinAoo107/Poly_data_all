# Polymarket时间序列数据获取指南

## 概述

本指南详细说明如何使用Polymarket的时间序列API端点获取历史价格数据。基于官方文档：[https://docs.polymarket.com/developers/CLOB/timeseries](https://docs.polymarket.com/developers/CLOB/timeseries)

## API端点信息

### 基础信息
- **端点URL**: `https://clob.polymarket.com/prices-history`
- **请求方法**: GET
- **认证**: 无需认证（公开端点）

### 请求参数

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| `market` | string | ✅ | CLOB代币ID（市场标识符） |
| `interval` | string | ❌ | 时间间隔（与startTs/endTs互斥） |
| `startTs` | number | ❌ | 开始时间戳（UNIX时间戳，UTC） |
| `endTs` | number | ❌ | 结束时间戳（UNIX时间戳，UTC） |
| `fidelity` | number | ❌ | 数据精度（分钟为单位，默认值根据interval确定） |

### 参数详细说明

#### interval选项
- `1m`: 1个月
- `1w`: 1周
- `1d`: 1天
- `6h`: 6小时
- `1h`: 1小时
- `max`: 最大范围（所有历史数据）

#### fidelity常用值
- `1`: 1分钟精度
- `5`: 5分钟精度
- `15`: 15分钟精度
- `60`: 1小时精度
- `240`: 4小时精度
- `1440`: 1天精度

#### 重要约束
- `interval` 和 `startTs`/`endTs` 参数**互斥**，只能使用其中一种
- 如果使用时间戳范围，必须同时提供 `startTs` 和 `endTs`

## 响应格式

### 成功响应
```json
{
  "history": [
    {
      "t": 1746212406,    // UNIX时间戳
      "p": 0.185          // 价格
    },
    {
      "t": 1746216005,
      "p": 0.205
    }
    // ... 更多数据点
  ]
}
```

### TimeseriesPoint结构
根据官方文档，每个数据点包含：
- `t` (number): UTC时间戳
- `p` (number): 价格

## 使用示例

### 1. 基础用法 - 获取最大历史数据
```python
import requests

def get_max_history(token_id):
    """获取所有历史数据"""
    params = {
        "market": token_id,
        "interval": "max",
        "fidelity": 1440  # 日级别数据
    }
    
    response = requests.get(
        "https://clob.polymarket.com/prices-history",
        params=params
    )
    
    if response.status_code == 200:
        return response.json()
    return None
```

### 2. 使用时间范围
```python
from datetime import datetime, timedelta

def get_recent_data(token_id, days=7):
    """获取最近N天的数据"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    params = {
        "market": token_id,
        "startTs": int(start_time.timestamp()),
        "endTs": int(end_time.timestamp()),
        "fidelity": 60  # 小时级别
    }
    
    response = requests.get(
        "https://clob.polymarket.com/prices-history",
        params=params
    )
    
    return response.json() if response.status_code == 200 else None
```

### 3. 转换为pandas DataFrame
```python
import pandas as pd

def to_dataframe(history_data):
    """将API响应转换为pandas DataFrame"""
    if not history_data or "history" not in history_data:
        return None
    
    history = history_data["history"]
    if not history:
        return None
    
    # 创建DataFrame
    df = pd.DataFrame(history)
    
    # 重命名列
    df.rename(columns={"t": "timestamp", "p": "price"}, inplace=True)
    
    # 转换时间戳
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    df.set_index("datetime", inplace=True)
    
    # 排序并去重
    df.sort_index(inplace=True)
    if df.index.duplicated().any():
        df = df[~df.index.duplicated(keep='last')]
    
    return df
```

## 实际数据示例

基于测试结果，以下是实际获取的数据示例：

### 小时级数据（fidelity=60）
```csv
datetime,timestamp,price,market_id
2025-05-02 19:00:06,1746212406,0.185,42539672745835417166310556793707418417075205359699744726511175708846683253904
2025-05-02 20:00:05,1746216005,0.205,42539672745835417166310556793707418417075205359699744726511175708846683253904
2025-05-02 21:00:06,1746219606,0.205,42539672745835417166310556793707418417075205359699744726511175708846683253904
```

### 日级数据（fidelity=1440）
```csv
datetime,timestamp,price,market_id
2025-05-03 00:00:06,1746230406,0.21,42539672745835417166310556793707418417075205359699744726511175708846683253904
2025-05-04 00:00:05,1746316805,0.26,42539672745835417166310556793707418417075205359699744726511175708846683253904
2025-05-05 00:00:05,1746403205,0.385,42539672745835417166310556793707418417075205359699744726511175708846683253904
```

## 获取市场Token ID

要使用时间序列API，首先需要获取有效的CLOB token ID：

```python
def get_market_token_ids():
    """从Gamma API获取市场和对应的token IDs"""
    response = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={"limit": 10, "active": "true"}
    )
    
    if response.status_code == 200:
        markets = response.json()
        
        for market in markets:
            clob_token_ids = market.get('clobTokenIds')
            
            if clob_token_ids:
                # 处理不同格式的clobTokenIds
                if isinstance(clob_token_ids, str):
                    try:
                        import json
                        clob_token_ids = json.loads(clob_token_ids)
                    except:
                        pass
                
                print(f"市场: {market.get('question')[:50]}...")
                print(f"Token IDs: {clob_token_ids}")
```

## 集成到现有项目

### 更新PriceCollector类

在 `Poly_price_data/price_collector.py` 中添加时间序列功能：

```python
def fetch_timeseries_data(self, 
                         market_id: str, 
                         interval: str = "max",
                         fidelity: int = 1440) -> Optional[pd.DataFrame]:
    """
    获取时间序列数据
    
    参数:
        market_id: CLOB token ID
        interval: 时间间隔 ("1m", "1w", "1d", "6h", "1h", "max")
        fidelity: 数据精度（分钟为单位）
    
    返回:
        pandas.DataFrame: 时间序列数据
    """
    params = {
        "market": market_id,
        "interval": interval,
        "fidelity": fidelity
    }
    
    try:
        self.rate_limiter.wait()
        response = self.clob_client.get("/prices-history", params=params)
        
        if not response or "history" not in response:
            return None
        
        history = response["history"]
        if not history:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(history)
        df.rename(columns={"t": "timestamp", "p": "price"}, inplace=True)
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
        df.set_index("datetime", inplace=True)
        df.sort_index(inplace=True)
        
        # 去重
        if df.index.duplicated().any():
            df = df[~df.index.duplicated(keep='last')]
        
        df["market_id"] = market_id
        df["fidelity"] = fidelity
        
        return df
        
    except Exception as e:
        self.logger.error(f"获取时间序列数据失败: {e}")
        return None
```

## 最佳实践

### 1. 数据精度选择
- **实时监控**: fidelity=1 (1分钟)
- **短期分析**: fidelity=60 (1小时)
- **长期趋势**: fidelity=1440 (1天)

### 2. 时间范围选择
- **最新数据**: interval="1d" 或 "1h"
- **历史分析**: interval="max"
- **特定时期**: 使用startTs/endTs

### 3. 错误处理
```python
def safe_get_timeseries(token_id, **kwargs):
    """安全获取时间序列数据"""
    try:
        response = requests.get(
            "https://clob.polymarket.com/prices-history",
            params={"market": token_id, **kwargs},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "history" in data and data["history"]:
                return data
        
        print(f"无数据或请求失败: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"请求异常: {e}")
        return None
```

### 4. 数据验证
```python
def validate_timeseries_data(df):
    """验证时间序列数据质量"""
    if df is None or df.empty:
        return False, "数据为空"
    
    # 检查时间序列连续性
    time_diffs = df.index.to_series().diff().dropna()
    expected_interval = time_diffs.mode().iloc[0] if not time_diffs.empty else None
    
    # 检查价格范围
    if df['price'].min() < 0 or df['price'].max() > 1:
        return False, "价格超出预期范围 [0, 1]"
    
    return True, "数据验证通过"
```

## 常见问题

### Q: 为什么某些市场没有历史数据？
A: 新创建的市场或交易量很低的市场可能没有足够的历史价格数据。

### Q: 如何处理数据中的时间戳重复？
A: 使用pandas的`duplicated()`方法检测并移除重复时间戳，保留最后一个值。

### Q: interval和startTs/endTs可以同时使用吗？
A: 不可以，这两种参数是互斥的。根据文档，只能使用其中一种方式指定时间范围。

### Q: fidelity参数的最小值是多少？
A: 根据测试，fidelity=1（1分钟）是最小精度。

## 相关文件

- `timeseries_example.py`: 完整的使用示例
- `test_timeseries_data.py`: 全面的API测试
- `Poly_price_data/price_collector.py`: 价格数据收集器
- `price_history_*.csv`: 生成的示例数据文件

## 总结

Polymarket的时间序列API提供了灵活且强大的历史价格数据获取功能。通过合理使用interval、fidelity等参数，可以获取不同精度和时间范围的数据，满足各种分析需求。

关键要点：
1. 使用正确的CLOB token ID作为market参数
2. 根据需求选择合适的时间范围和精度
3. 注意interval和时间戳参数的互斥性
4. 实施适当的错误处理和数据验证
5. 利用pandas进行数据处理和分析 
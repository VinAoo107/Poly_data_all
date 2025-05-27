# Polymarket 数据收集项目

## 📋 项目概述

**项目名称**: Polymarket 综合数据收集系统
**版本**: v2.0
**最后更新**: 2025-05-27
**开发者**: 姚文豪
**联系方式**: 通过GitHub Issues联系

本项目是一个全面的Polymarket数据收集和分析系统，支持多维度的预测市场数据获取、实时监控和历史数据分析。

## 🎯 项目目标

- **全面数据收集**: 支持市场信息、价格数据、订单数据、用户数据等多维度收集
- **实时监控**: 提供市场波动监控和价格变化预警
- **历史数据分析**: 支持已结束事件的历史数据获取和回测分析
- **数据关联分析**: 建立不同数据类型之间的关联关系
- **易于使用**: 提供命令行界面和交互式启动方式

## 🔧 命令行参数详解

### 通用参数

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `--verbose`, `-v` | 开关 | False | 启用详细输出，显示调试信息 | `--verbose` |
| `--quiet`, `-q` | 开关 | False | 静默模式，只显示错误信息 | `--quiet` |

### 📊 市场信息收集 (market-info)

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | standard, comprehensive, sampling, simplified, timeseries, single | standard | 数据收集模式 | `--mode comprehensive` |
| `--type` | 选择 | all, active, closed, archived | all | 市场类型筛选 | `--type active` |
| `--market-id` | 字符串 | - | - | 指定单个市场ID（single模式） | `--market-id 12345` |
| `--include-timeseries` | 开关 | - | False | 包含时间序列数据 | `--include-timeseries` |
| `--timeseries-interval` | 选择 | 1m, 5m, 15m, 1h, 4h, 1d | 1h | 时间序列数据间隔 | `--timeseries-interval 1h` |
| `--no-analysis` | 开关 | - | False | 跳过数据分析步骤 | `--no-analysis` |
| `--reset` | 开关 | - | False | 重置收集进度 | `--reset` |

**使用示例:**
```bash
# 获取50个活跃市场的基本信息
python main.py market-info --type active --limit 50

# 获取100个已关闭市场的详细信息（包含时间序列）
python main.py market-info --type closed --limit 100 --mode comprehensive --include-timeseries

# 获取单个市场的完整信息
python main.py market-info --mode single --market-id 12345
```

### 💰 价格数据收集 (price-data)

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | batch, monitor, report, history | batch | 运行模式 | `--mode monitor` |
| `--markets` | 列表 | - | - | 要处理的市场ID列表 | `--markets 123 456 789` |
| `--detailed` | 开关 | - | False | 包含详细的价格数据 | `--detailed` |
| `--interval` | 整数 | - | 60 | 监控模式的检查间隔（秒） | `--interval 30` |
| `--days` | 整数 | - | 30 | 报告模式的分析天数 | `--days 7` |
| `--fidelity` | 选择 | 1, 60, 1440 | 1 | 历史数据精度（1=分钟，60=小时，1440=天） | `--fidelity 60` |
| `--max-markets` | 整数 | - | 10 | 最大处理市场数量 | `--max-markets 5` |

**使用示例:**
```bash
# 批量收集指定市场的价格数据
python main.py price-data --mode batch --markets 123 456 --detailed

# 每30秒监控市场价格变化
python main.py price-data --mode monitor --markets 123 456 --interval 30

# 生成过去7天的价格报告
python main.py price-data --mode report --days 7
```

### 📋 订单数据收集 (order-data)

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | orders, trades, active, comprehensive | comprehensive | 收集模式 | `--mode trades` |
| `--market` | 字符串 | - | - | 指定市场ID | `--market 12345` |
| `--status` | 选择 | live, filled, cancelled, partially_filled | - | 订单状态筛选 | `--status live` |
| `--limit` | 整数 | - | 1000 | **限制返回的记录数量** | `--limit 500` |
| `--no-analysis` | 开关 | - | False | 跳过数据分析 | `--no-analysis` |
| `--reset` | 开关 | - | False | 重置收集进度 | `--reset` |

**使用示例:**
```bash
# 获取指定市场的最新1000条交易记录
python main.py order-data --mode trades --market 12345 --limit 1000

# 获取所有活跃订单
python main.py order-data --mode orders --status live --limit 500

# 综合收集订单和交易数据
python main.py order-data --mode comprehensive --market 12345
```

### 👤 用户数据收集 (user-data)

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | single, batch | single | 收集模式 | `--mode batch` |
| `--user` | 字符串 | - | - | 用户地址（single模式） | `--user 0x123...` |
| `--users-file` | 字符串 | - | - | 用户地址文件路径（batch模式） | `--users-file users.txt` |
| `--users` | 列表 | - | - | 用户地址列表（batch模式） | `--users 0x123... 0x456...` |
| `--limit` | 整数 | - | 50 | **每批次获取的用户数量** | `--limit 100` |

**使用示例:**
```bash
# 获取单个用户的数据
python main.py user-data --mode single --user 0x123...

# 批量获取多个用户的数据
python main.py user-data --mode batch --users 0x123... 0x456... --limit 100

# 从文件读取用户列表并批量处理
python main.py user-data --mode batch --users-file big_traders.txt --limit 50
```

### 📈 市场波动监控 (fluctuation)

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--markets` | 列表 | - | **必需** | 要监控的市场ID列表 | `--markets 123 456` |
| `--duration` | 整数 | - | - | 监控持续时间（分钟） | `--duration 60` |
| `--threshold` | 浮点数 | - | 0.05 | 价格变化阈值（5%=0.05） | `--threshold 0.1` |
| `--interval` | 整数 | - | 10 | 检查间隔（秒） | `--interval 30` |
| `--background` | 开关 | - | False | 后台运行模式 | `--background` |

**使用示例:**
```bash
# 监控指定市场60分钟，价格变化超过10%时报警
python main.py fluctuation --markets 123 456 --duration 60 --threshold 0.1

# 每30秒检查一次价格变化
python main.py fluctuation --markets 123 --interval 30 --background
```

### 🔄 综合数据收集 (comprehensive)

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | ecosystem, test, market-view, user-view, correlations, report | ecosystem | 运行模式 | `--mode test` |
| `--markets` | 列表 | - | - | 指定的市场ID列表 | `--markets 123 456` |
| `--user` | 字符串 | - | - | 用户地址（user-view模式） | `--user 0x123...` |
| `--include-users` | 开关 | - | True | 包含用户数据收集 | `--include-users` |
| `--include-monitoring` | 开关 | - | False | 包含价格监控 | `--include-monitoring` |
| `--monitoring-duration` | 整数 | - | 30 | 价格监控持续时间（分钟） | `--monitoring-duration 60` |
| `--max-markets` | 整数 | - | 3 | 测试模式：最大市场数量 | `--max-markets 5` |
| `--max-users` | 整数 | - | 10 | 测试模式：最大用户数量 | `--max-users 20` |

**使用示例:**
```bash
# 收集完整的市场生态系统数据
python main.py comprehensive --mode ecosystem --include-monitoring

# 测试模式：收集少量数据验证功能
python main.py comprehensive --mode test --max-markets 3 --max-users 5

# 获取特定市场的综合视图
python main.py comprehensive --mode market-view --markets 12345
```

## 💡 关于 `--limit` 参数的详细说明

### 什么是 `--limit`？
`--limit` 是一个**数量限制参数**，用来控制API返回的数据条数。

### 为什么需要限制数量？

1. **API保护**: 防止单次请求过多数据导致服务器过载
2. **性能优化**: 大量数据会消耗更多内存和处理时间
3. **网络效率**: 减少网络传输时间和带宽使用
4. **测试友好**: 开发和测试时只需要少量数据

### 常用的 `--limit` 值

| 值 | 适用场景 | 说明 |
|---|----------|------|
| `--limit 10` | 快速测试 | 获取少量数据验证功能 |
| `--limit 50` | 一般使用 | 平衡数据量和处理速度 |
| `--limit 100` | 详细分析 | 获取较多数据进行分析 |
| `--limit 500` | 深度分析 | 大量数据，适合统计分析 |
| `--limit 1000` | 批量处理 | 最大数据量，用于全面分析 |

### 使用建议

```bash
# 🔍 测试阶段：使用小数量
python main.py market-info --type active --limit 10

# 📊 日常分析：使用中等数量  
python main.py market-info --type active --limit 50

# 📈 深度研究：使用大数量
python main.py order-data --type trades --limit 1000
```

## 📊 可获取的数据类型

### 1. 市场信息数据 (Market Information)

**数据来源**: Gamma Markets API
**获取方法**: `Poly_info/market_info_collector.py`

#### 可获取的数据:

- **事件数据 (Events)**
  - 事件ID、标题、描述
  - 开始时间、结束时间
  - 事件状态 (活跃/已关闭/已归档)
  - 事件标签和分类
  - 关联的市场列表

- **市场数据 (Markets)**
  - 市场ID、问题描述
  - 市场状态 (活跃/已关闭)
  - 创建时间、结束时间
  - 市场类型和分类
  - Token信息

- **简化市场数据 (Simplified Markets)**
  - 轻量级市场信息
  - 基本价格信息
  - 市场状态概览

#### 获取方法:

```bash
# 获取50个活跃事件（limit=50表示最多返回50条记录）
python main.py market-info --type active --limit 50

# 获取100个已关闭事件
python main.py market-info --type closed --limit 100

# 获取所有市场信息（不限制数量）
python main.py market-info --type all --include-analysis
```

#### 代码示例:

```python
from Poly_info.market_info_collector import MarketInfoCollector

collector = MarketInfoCollector()

# 获取活跃事件（limit=50表示最多获取50个事件）
events = collector.fetch_events(market_type="active", limit=50)

# 获取市场数据
markets = collector.fetch_markets(active=True, limit=100)

# 获取简化市场数据
simplified = collector.fetch_simplified_markets(active=True)
```

### 2. 价格数据 (Price Data)

**数据来源**: CLOB API
**获取方法**: `Poly_price_data/price_collector.py`

#### 可获取的数据:

- **实时价格 (Current Prices)**
  - 当前买入/卖出价格
  - 价格变化幅度
  - 最后更新时间

- **历史价格 (Historical Prices)**
  - 时间序列价格数据
  - 支持不同时间精度 (分钟/小时/天)
  - 价格变化趋势

- **订单簿数据 (Order Book)**
  - 买单/卖单深度
  - 价格层级分布
  - 流动性信息

- **价格统计 (Price Statistics)**
  - 中位价格 (Midpoint)
  - 买卖价差 (Spread)
  - 价格波动率

#### 获取方法:

```bash
# 批量收集价格数据
python main.py price-data --mode batch --markets token1 token2

# 连续监控价格变化（每60秒检查一次）
python main.py price-data --mode monitor --interval 60

# 生成价格报告
python main.py price-data --mode report --output-format json
```

#### 代码示例:

```python
from Poly_price_data.price_collector import PriceCollector

collector = PriceCollector()

# 获取历史价格数据
token_id = "42539672745835417166310556793707418417075205359699744726511175708846683253904"
history = collector.fetch_timeseries_data(token_id, interval="max")

# 获取当前价格
current_prices = collector.fetch_current_prices([token_id])

# 获取订单簿
order_book = collector.fetch_order_book(token_id)
```

### 3. 订单数据 (Order Data)

**数据来源**: CLOB API
**获取方法**: `Poly_order/order_collector.py`

#### 可获取的数据:

- **订单信息 (Orders)**
  - 订单ID、类型 (买入/卖出)
  - 价格、数量、状态
  - 创建时间、更新时间
  - 制造商/接受者信息

- **交易数据 (Trades)**
  - 交易ID、价格、数量
  - 交易时间、交易状态
  - 买方/卖方信息
  - 手续费信息

- **订单统计 (Order Statistics)**
  - 订单分布分析
  - 交易频率统计
  - 价格影响分析

#### 获取方法:

```bash
# 获取订单数据
python main.py order-data --type orders --market-id 12345

# 获取最新1000条交易记录（limit=1000表示最多返回1000条交易）
python main.py order-data --type trades --limit 1000

# 获取订单统计
python main.py order-data --type statistics --analysis
```

#### 代码示例:

```python
from Poly_order.order_collector import OrderCollector

collector = OrderCollector()

# 获取市场订单（limit=100表示最多获取100个订单）
orders = collector.fetch_orders(market_id="12345", limit=100)

# 获取交易历史
trades = collector.fetch_trades(market_id="12345")

# 获取订单统计
stats = collector.analyze_orders(orders)
```

### 4. 用户数据 (User Data)

**数据来源**: CLOB API
**获取方法**: `Poly_user_data/user_collector.py`

#### 可获取的数据:

- **用户持仓 (User Positions)**
  - 持仓Token和数量
  - 持仓价值
  - 盈亏情况

- **用户交易历史 (Trading History)**
  - 历史交易记录
  - 交易频率分析
  - 偏好市场分析

- **用户统计 (User Statistics)**
  - 交易活跃度
  - 风险偏好分析
  - 收益率统计

#### 获取方法:

```bash
# 获取用户数据
python main.py user-data --user-id 0x123... --include-positions

# 批量用户分析（limit=100表示每批次处理100个用户）
python main.py user-data --batch-file users.txt --limit 100

# 用户统计报告
python main.py user-data --statistics --output report.json
```

#### 代码示例:

```python
from Poly_user_data.user_collector import UserCollector

collector = UserCollector()

# 获取用户持仓
positions = collector.fetch_user_positions("0x123...")

# 获取交易历史
history = collector.fetch_user_trades("0x123...")

# 用户统计分析
stats = collector.analyze_user_activity("0x123...")
```

### 5. 市场波动监控 (Market Fluctuation)

**数据来源**: 实时价格监控
**获取方法**: `Poly_market_fluctuation/fluctuation_monitor.py`

#### 可获取的数据:

- **价格波动监控**
  - 实时价格变化检测
  - 波动幅度分析
  - 异常价格预警

- **趋势分析**
  - 价格趋势识别
  - 成交量变化分析
  - 市场情绪指标

- **预警系统**
  - 价格突变预警
  - 成交量异常预警
  - 自定义阈值监控

#### 获取方法:

```bash
# 启动实时监控（每30秒检查一次）
python main.py fluctuation --mode monitor --interval 30

# 趋势分析
python main.py fluctuation --mode analysis --timeframe 24h

# 生成监控报告
python main.py fluctuation --mode report --output dashboard.html
```

#### 代码示例:

```python
from Poly_market_fluctuation.fluctuation_monitor import FluctuationMonitor

monitor = FluctuationMonitor()

# 启动实时监控
monitor.start_monitoring(
    tokens=["token1", "token2"],
    interval=60,  # 每60秒检查一次
    price_threshold=0.05  # 5%价格变化阈值
)

# 分析价格趋势
trends = monitor.analyze_trends(token_id, timeframe="24h")

# 生成监控报告
report = monitor.generate_report()
```

## 🚀 快速开始

### 1. 环境设置

```bash
# 克隆项目
git clone <repository-url>
cd Poly_data_all

# 安装依赖
pip install -r requirements.txt

# 项目初始化
python setup.py
```

### 2. 快速参考表

| 需求 | 命令 | 说明 |
|------|------|------|
| 🔍 **快速测试** | `python main.py market-info --type active --limit 5` | 获取5个活跃市场验证功能 |
| 📊 **获取市场信息** | `python main.py market-info --type active --limit 50` | 获取50个活跃市场的基本信息 |
| 💰 **监控价格** | `python main.py price-data --mode monitor --interval 60` | 每60秒监控价格变化 |
| 📋 **获取交易数据** | `python main.py order-data --mode trades --limit 1000` | 获取最新1000条交易记录 |
| 👤 **用户数据** | `python main.py user-data --mode single --user 0x123...` | 获取单个用户的完整数据 |
| 📈 **市场监控** | `python main.py fluctuation --markets 123 --threshold 0.05` | 监控市场价格变化超过5% |
| 🔄 **综合测试** | `python main.py comprehensive --mode test --max-markets 3` | 测试模式收集少量数据 |
| 🆘 **获取帮助** | `python main.py --help` | 查看所有可用命令和参数 |

### 3. 基本使用

```bash
# 交互式启动（推荐新手使用）
python start.py

# 快速测试
python tests/quick_test.py

# 查看所有可用参数
python main.py --help

# 查看特定模块的参数
python main.py market-info --help
```

### 4. 配置文件

编辑 `config.py` 文件来自定义配置：

```python
# API配置
class APIConfig:
    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
    CLOB_BASE_URL = "https://clob.polymarket.com"
  
# 数据配置
class DataConfig:
    OUTPUT_DIR = "output"
    LOG_LEVEL = "INFO"
```

## 📁 项目结构

```
Poly_data_all/
├── 📁 核心模块/
│   ├── Poly_info/              # 市场信息收集
│   │   └── market_info_collector.py
│   ├── Poly_price_data/        # 价格数据收集
│   │   └── price_collector.py
│   ├── Poly_order/             # 订单数据收集
│   │   └── order_collector.py
│   ├── Poly_user_data/         # 用户数据收集
│   │   └── user_collector.py
│   └── Poly_market_fluctuation/ # 市场波动监控
│       └── fluctuation_monitor.py
├── 📁 配置和工具/
│   ├── config.py               # 项目配置
│   ├── utils.py                # 通用工具
│   ├── main.py                 # 主程序入口
│   └── data_relationship_manager.py # 数据关联管理
├── 📁 测试/
│   └── tests/
│       └── quick_test.py       # 快速测试
├── 📁 示例/
│   └── examples/               # 使用示例
├── 📁 脚本/
│   └── scripts/                # 实用脚本
├── 📁 文档/
│   └── docs/                   # 项目文档
├── 📁 输出/
│   ├── output/                 # 数据输出目录
│   └── logs/                   # 日志文件
└── 📁 辅助工具/
    ├── setup.py                # 项目设置
    ├── start.py                # 快速启动
    ├── requirements.txt        # 依赖管理
    └── README.md               # 项目文档
```

## 🔧 高级功能

### 1. 数据关联分析

```python
from data_relationship_manager import DataRelationshipManager

manager = DataRelationshipManager()

# 建立数据关联
relationships = manager.build_relationships()

# 分析数据依赖
dependencies = manager.analyze_dependencies()
```

### 2. 批量数据收集

```bash
# 综合数据收集（生态系统模式）
python main.py comprehensive --mode ecosystem --include-monitoring

# 测试模式收集（限制数据量）
python main.py comprehensive --mode test --max-markets 5 --max-users 10
```

### 3. 数据导出和分析

```bash
# 生成综合报告
python main.py comprehensive --mode report

# 分析数据关联性
python main.py comprehensive --mode correlations
```

## 📈 数据质量和验证

### 数据完整性检查

- 自动验证API响应格式
- 检查数据字段完整性
- 识别和处理缺失数据

### 数据准确性验证

- 交叉验证不同数据源
- 时间戳一致性检查
- 价格数据合理性验证

### 错误处理

- 网络请求重试机制
- API限制处理
- 数据保存失败恢复

## 🔍 已知限制

### API限制

- 某些端点需要认证
- 请求频率限制
- 数据历史深度限制

### 数据可用性

- 新市场可能缺少历史数据
- 低活跃市场数据稀少
- 已结束市场的实时数据不可用

## 📚 使用示例

### 示例1: 获取活跃市场价格数据

```python
from Poly_price_data.price_collector import PriceCollector

collector = PriceCollector()

# 获取活跃市场
markets = collector.get_active_markets()

# 收集价格数据（限制前10个市场）
for market in markets[:10]:  # limit=10，只处理前10个市场
    prices = collector.fetch_current_prices(market['tokens'])
    print(f"市场: {market['question']}")
    print(f"价格: {prices}")
```

### 示例2: 监控价格变化

```python
from Poly_market_fluctuation.fluctuation_monitor import FluctuationMonitor

monitor = FluctuationMonitor()

# 设置监控参数
tokens = ["token1", "token2"]
threshold = 0.05  # 5%价格变化阈值

# 启动监控
monitor.start_monitoring(
    tokens=tokens,
    price_threshold=threshold,
    interval=60  # 每60秒检查一次
)
```

### 示例3: 批量获取用户数据

```python
from Poly_user_data.user_collector import UserCollector

collector = UserCollector()

# 用户地址列表
user_addresses = ["0x123...", "0x456...", "0x789..."]

# 批量获取用户数据（limit=50表示每批次最多处理50个用户）
for i in range(0, len(user_addresses), 50):  # 每批50个用户
    batch = user_addresses[i:i+50]
    for user_addr in batch:
        positions = collector.fetch_user_positions(user_addr)
        print(f"用户 {user_addr}: {len(positions)} 个持仓")
```

### 示例4: 历史数据分析

```python
from Poly_info.market_info_collector import MarketInfoCollector
from Poly_price_data.price_collector import PriceCollector

# 获取已结束的事件（limit=20表示最多获取20个事件）
info_collector = MarketInfoCollector()
closed_events = info_collector.fetch_events(market_type="closed", limit=20)

# 分析历史价格数据
price_collector = PriceCollector()
for event in closed_events:
    if event.get('tokens'):
        for token in event['tokens']:
            history = price_collector.fetch_timeseries_data(
                token, 
                interval="max"
            )
            if history:
                print(f"事件: {event['title']}")
                print(f"历史数据点: {len(history)}")
```

### 示例5: 命令行快速操作

```bash
# 🔍 快速测试：获取少量数据验证功能
python main.py market-info --type active --limit 5 --verbose

# 📊 日常分析：获取适量数据进行分析
python main.py order-data --mode trades --limit 100 --market 12345

# 📈 深度研究：获取大量数据进行统计分析
python main.py comprehensive --mode test --max-markets 10 --max-users 50

# 🔄 实时监控：监控市场价格变化
python main.py fluctuation --markets 123 456 --threshold 0.05 --interval 30
```

## 🛠️ 故障排除

### 常见问题

1. **API请求失败**

   - 检查网络连接
   - 验证API端点URL
   - 检查请求参数格式
2. **数据为空**

   - 确认Token ID有效
   - 检查市场是否有交易活动
   - 尝试不同的时间参数
3. **权限错误**

   - 检查API密钥配置
   - 确认访问权限
   - 使用公开端点作为替代

### 调试方法

```bash
# 启用详细日志（使用--verbose参数）
python main.py market-info --type active --limit 5 --verbose

# 运行诊断测试
python tests/quick_test.py --verbose

# 检查配置
python -c "from config import *; print('配置加载成功')"

# 测试单个市场数据获取
python main.py market-info --mode single --market-id 12345 --verbose
```

## 📞 技术支持

### 获取帮助

- 查看 `docs/` 目录中的详细文档
- 运行 `python tests/quick_test.py` 进行系统诊断
- 检查 `logs/` 目录中的错误日志
- 使用 `python start.py` 的交互式界面

### 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 🔄 版本历史

- **v2.0** (2025-05-27): 项目重构，完善文档，清理测试文件
- **v1.5** (2025-05-26): 添加历史数据支持，修复API端点
- **v1.0** (2025-04-26): 初始版本，基础功能实现

## 📖 总结

这个Polymarket数据收集项目为你提供了完整的预测市场数据获取解决方案。通过理解`--limit`等参数的含义，你可以：

### 🎯 核心功能
- **灵活控制数据量**: 使用`--limit`参数控制获取的数据条数
- **多模式操作**: 支持测试、监控、批量处理等多种模式
- **实时监控**: 监控市场价格变化和异常波动
- **历史分析**: 获取和分析历史市场数据

### 💡 使用建议
1. **新手**: 从`--limit 5`开始，使用`--verbose`查看详细输出
2. **日常使用**: 使用`--limit 50-100`获取适量数据
3. **深度分析**: 使用`--limit 1000`获取大量数据进行统计分析
4. **实时监控**: 使用`fluctuation`模块监控市场变化

### 🔧 参数组合示例
```bash
# 新手友好：详细输出 + 少量数据
python main.py market-info --type active --limit 5 --verbose

# 生产环境：适量数据 + 静默模式
python main.py market-info --type active --limit 50 --quiet

# 研究分析：大量数据 + 综合模式
python main.py order-data --mode comprehensive --limit 1000
```

### 📞 获取更多帮助
- 使用`python main.py --help`查看所有命令
- 使用`python main.py [模块] --help`查看特定模块参数
- 查看`examples/`目录中的示例代码
- 运行`python start.py`使用交互式界面

---

**项目状态**: ✅ 生产就绪
**维护状态**: 🔄 积极维护
**文档状态**: 📚 完整文档

*最后更新: 2025-05-27*

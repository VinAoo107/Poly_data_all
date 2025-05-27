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

## 💡 关于 `--limit` 参数的重要说明

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
| `--limit 5-10` | 快速测试 | 获取少量数据验证功能 |
| `--limit 50` | 一般使用 | 平衡数据量和处理速度 |
| `--limit 100` | 详细分析 | 获取较多数据进行分析 |
| `--limit 500` | 深度分析 | 大量数据，适合统计分析 |
| `--limit 1000` | 批量处理 | 最大数据量，用于全面分析 |

## 📊 数据收集模块详解

### 1. 📊 市场信息收集 (market-info)

**数据来源**: Gamma Markets API  
**获取方法**: `Poly_info/market_info_collector.py`

#### 🔧 命令行参数

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | standard, comprehensive, sampling, simplified, timeseries, single | standard | 数据收集模式 | `--mode comprehensive` |
| `--type` | 选择 | all, active, closed, archived | all | 市场类型筛选 | `--type active` |
| `--market-id` | 字符串 | - | - | 指定单个市场ID（single模式） | `--market-id 12345` |
| `--include-timeseries` | 开关 | - | False | 包含时间序列数据 | `--include-timeseries` |
| `--timeseries-interval` | 选择 | 1m, 5m, 15m, 1h, 4h, 1d | 1h | 时间序列数据间隔 | `--timeseries-interval 1h` |
| `--no-analysis` | 开关 | - | False | 跳过数据分析步骤 | `--no-analysis` |
| `--reset` | 开关 | - | False | 重置收集进度 | `--reset` |

#### 📋 可获取的数据

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

#### 💻 使用示例

```bash
# 获取5个活跃市场（测试用）
python main.py market-info --type active --limit 5 --verbose

# 获取50个活跃市场的基本信息
python main.py market-info --type active --limit 50

# 获取100个已关闭市场的详细信息（包含时间序列）
python main.py market-info --type closed --limit 100 --mode comprehensive --include-timeseries

# 获取单个市场的完整信息
python main.py market-info --mode single --market-id 12345
```

#### 🐍 代码示例

```python
from Poly_info.market_info_collector import MarketInfoCollector

collector = MarketInfoCollector()

# 获取活跃事件（limit=50表示最多获取50个事件）
events = collector.fetch_events(market_type="active", limit=50)
print(f"获取到 {len(events)} 个活跃事件")

# 获取市场数据
markets = collector.fetch_markets(active=True, limit=100)
print(f"获取到 {len(markets)} 个市场")

# 获取简化市场数据
simplified = collector.fetch_simplified_markets(active=True)
print(f"获取到 {len(simplified)} 个简化市场")
```

---

### 2. 💰 价格数据收集 (price-data)

**数据来源**: CLOB API  
**获取方法**: `Poly_price_data/price_collector.py`

#### 🔧 命令行参数

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | batch, monitor, report, history | batch | 运行模式 | `--mode monitor` |
| `--markets` | 列表 | - | - | 要处理的市场ID列表 | `--markets 123 456 789` |
| `--detailed` | 开关 | - | False | 包含详细的价格数据 | `--detailed` |
| `--interval` | 整数 | - | 60 | 监控模式的检查间隔（秒） | `--interval 30` |
| `--days` | 整数 | - | 30 | 报告模式的分析天数 | `--days 7` |
| `--fidelity` | 选择 | 1, 60, 1440 | 1 | 历史数据精度（1=分钟，60=小时，1440=天） | `--fidelity 60` |
| `--max-markets` | 整数 | - | 10 | 最大处理市场数量 | `--max-markets 5` |

#### 📋 可获取的数据

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

#### 💻 使用示例

```bash
# 批量收集指定市场的价格数据
python main.py price-data --mode batch --markets 123 456 --detailed

# 每30秒监控市场价格变化
python main.py price-data --mode monitor --markets 123 456 --interval 30

# 生成过去7天的价格报告
python main.py price-data --mode report --days 7

# 获取历史价格数据（小时精度）
python main.py price-data --mode history --markets 123 --fidelity 60
```

#### 🐍 代码示例

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

# 获取历史价格数据
token_id = "42539672745835417166310556793707418417075205359699744726511175708846683253904"
history = collector.fetch_timeseries_data(token_id, interval="max")
print(f"历史数据点: {len(history)}")
```

---

### 3. 📋 订单数据收集 (order-data)

**数据来源**: CLOB API  
**获取方法**: `Poly_order/order_collector.py`

#### 🔧 命令行参数

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | orders, trades, active, comprehensive | comprehensive | 收集模式 | `--mode trades` |
| `--market` | 字符串 | - | - | 指定市场ID | `--market 12345` |
| `--status` | 选择 | live, filled, cancelled, partially_filled | - | 订单状态筛选 | `--status live` |
| `--limit` | 整数 | - | 1000 | **限制返回的记录数量** | `--limit 500` |
| `--no-analysis` | 开关 | - | False | 跳过数据分析 | `--no-analysis` |
| `--reset` | 开关 | - | False | 重置收集进度 | `--reset` |

#### 📋 可获取的数据

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

#### 💻 使用示例

```bash
# 获取指定市场的最新1000条交易记录
python main.py order-data --mode trades --market 12345 --limit 1000

# 获取500个活跃订单
python main.py order-data --mode orders --status live --limit 500

# 综合收集订单和交易数据
python main.py order-data --mode comprehensive --market 12345

# 获取100条交易记录进行快速分析
python main.py order-data --mode trades --limit 100 --market 12345
```

#### 🐍 代码示例

```python
from Poly_order.order_collector import OrderCollector

collector = OrderCollector()

# 获取市场订单（limit=100表示最多获取100个订单）
orders = collector.fetch_orders(market_id="12345", limit=100)
print(f"获取到 {len(orders)} 个订单")

# 获取交易历史
trades = collector.fetch_trades(market_id="12345")
print(f"获取到 {len(trades)} 条交易记录")

# 获取订单统计
stats = collector.analyze_orders(orders)
print(f"订单统计: {stats}")
```

---

### 4. 👤 用户数据收集 (user-data)

**数据来源**: CLOB API  
**获取方法**: `Poly_user_data/user_collector.py`

#### 🔧 命令行参数

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--mode` | 选择 | single, batch | single | 收集模式 | `--mode batch` |
| `--user` | 字符串 | - | - | 用户地址（single模式） | `--user 0x123...` |
| `--users-file` | 字符串 | - | - | 用户地址文件路径（batch模式） | `--users-file users.txt` |
| `--users` | 列表 | - | - | 用户地址列表（batch模式） | `--users 0x123... 0x456...` |
| `--limit` | 整数 | - | 50 | **每批次获取的用户数量** | `--limit 100` |

#### 📋 可获取的数据

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

#### 💻 使用示例

```bash
# 获取单个用户的数据
python main.py user-data --mode single --user 0x123...

# 批量获取多个用户的数据
python main.py user-data --mode batch --users 0x123... 0x456... --limit 100

# 从文件读取用户列表并批量处理
python main.py user-data --mode batch --users-file big_traders.txt --limit 50

# 快速测试：获取5个用户的数据
python main.py user-data --mode batch --users-file users.txt --limit 5
```

#### 🐍 代码示例

```python
from Poly_user_data.user_collector import UserCollector

collector = UserCollector()

# 获取用户持仓
positions = collector.fetch_user_positions("0x123...")
print(f"用户持仓: {len(positions)} 个")

# 批量获取用户数据（limit=50表示每批次最多处理50个用户）
user_addresses = ["0x123...", "0x456...", "0x789..."]
for i in range(0, len(user_addresses), 50):  # 每批50个用户
    batch = user_addresses[i:i+50]
    for user_addr in batch:
        positions = collector.fetch_user_positions(user_addr)
        print(f"用户 {user_addr}: {len(positions)} 个持仓")
```

---

### 5. 📈 市场波动监控 (fluctuation)

**数据来源**: 实时价格监控  
**获取方法**: `Poly_market_fluctuation/fluctuation_monitor.py`

#### 🔧 命令行参数

| 参数 | 类型 | 可选值 | 默认值 | 说明 | 示例 |
|------|------|--------|--------|------|------|
| `--markets` | 列表 | - | **必需** | 要监控的市场ID列表 | `--markets 123 456` |
| `--duration` | 整数 | - | - | 监控持续时间（分钟） | `--duration 60` |
| `--threshold` | 浮点数 | - | 0.05 | 价格变化阈值（5%=0.05） | `--threshold 0.1` |
| `--interval` | 整数 | - | 10 | 检查间隔（秒） | `--interval 30` |
| `--background` | 开关 | - | False | 后台运行模式 | `--background` |

#### 📋 可获取的数据

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

#### 💻 使用示例

```bash
# 监控指定市场60分钟，价格变化超过10%时报警
python main.py fluctuation --markets 123 456 --duration 60 --threshold 0.1

# 每30秒检查一次价格变化
python main.py fluctuation --markets 123 --interval 30 --background

# 快速测试：监控5分钟，5%阈值
python main.py fluctuation --markets 123 --duration 5 --threshold 0.05 --interval 10
```

#### 🐍 代码示例

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
print(f"价格趋势: {trends}")
```

---

### 6. 🔄 综合数据收集 (comprehensive)

**数据来源**: 多个API综合  
**获取方法**: `comprehensive_collector.py`

#### 🔧 命令行参数

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

#### 📋 可获取的数据

- **生态系统数据**: 市场、价格、订单、用户的综合数据
- **关联分析**: 不同数据类型之间的关系分析
- **综合报告**: 多维度数据的统计报告
- **测试数据**: 用于验证系统功能的样本数据

#### 💻 使用示例

```bash
# 收集完整的市场生态系统数据
python main.py comprehensive --mode ecosystem --include-monitoring

# 测试模式：收集少量数据验证功能
python main.py comprehensive --mode test --max-markets 3 --max-users 5

# 获取特定市场的综合视图
python main.py comprehensive --mode market-view --markets 12345

# 生成综合报告
python main.py comprehensive --mode report
```

## 🔧 通用参数

所有模块都支持以下通用参数：

| 参数 | 类型 | 默认值 | 说明 | 示例 |
|------|------|--------|------|------|
| `--verbose`, `-v` | 开关 | False | 启用详细输出，显示调试信息 | `--verbose` |
| `--quiet`, `-q` | 开关 | False | 静默模式，只显示错误信息 | `--quiet` |

### 参数组合示例

```bash
# 新手友好：详细输出 + 少量数据
python main.py market-info --type active --limit 5 --verbose

# 生产环境：适量数据 + 静默模式
python main.py market-info --type active --limit 50 --quiet

# 研究分析：大量数据 + 综合模式
python main.py order-data --mode comprehensive --limit 1000
```

## 📁 项目结构

```
Poly_data_all/
├── 📁 核心模块/
│   ├── Poly_info/              # 市场信息收集
│   ├── Poly_price_data/        # 价格数据收集
│   ├── Poly_order/             # 订单数据收集
│   ├── Poly_user_data/         # 用户数据收集
│   └── Poly_market_fluctuation/ # 市场波动监控
├── 📁 配置和工具/
│   ├── config.py               # 项目配置
│   ├── utils.py                # 通用工具
│   ├── main.py                 # 主程序入口
│   └── data_relationship_manager.py # 数据关联管理
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

### 数据关联分析

```python
from data_relationship_manager import DataRelationshipManager

manager = DataRelationshipManager()
relationships = manager.build_relationships()
```

### 批量数据收集

```bash
# 综合数据收集（生态系统模式）
python main.py comprehensive --mode ecosystem --include-monitoring

# 测试模式收集（限制数据量）
python main.py comprehensive --mode test --max-markets 5 --max-users 10
```

## 🛠️ 故障排除

### 常见问题

1. **API请求失败**: 检查网络连接和API端点URL
2. **数据为空**: 确认Token ID有效，检查市场是否有交易活动
3. **权限错误**: 检查API密钥配置，使用公开端点作为替代

### 调试方法

```bash
# 启用详细日志
python main.py market-info --type active --limit 5 --verbose

# 运行诊断测试
python tests/quick_test.py --verbose

# 测试单个市场数据获取
python main.py market-info --mode single --market-id 12345 --verbose
```

## 📞 技术支持

### 获取帮助

- 使用 `python main.py --help` 查看所有命令
- 使用 `python main.py [模块] --help` 查看特定模块参数
- 查看 `examples/` 目录中的示例代码
- 运行 `python start.py` 使用交互式界面

### 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📖 总结

这个Polymarket数据收集项目为你提供了完整的预测市场数据获取解决方案：

### 🎯 核心功能
- **灵活控制数据量**: 使用 `--limit` 参数控制获取的数据条数
- **多模式操作**: 支持测试、监控、批量处理等多种模式
- **实时监控**: 监控市场价格变化和异常波动
- **历史分析**: 获取和分析历史市场数据

### 💡 使用建议
1. **新手**: 从 `--limit 5` 开始，使用 `--verbose` 查看详细输出
2. **日常使用**: 使用 `--limit 50-100` 获取适量数据
3. **深度分析**: 使用 `--limit 1000` 获取大量数据进行统计分析
4. **实时监控**: 使用 `fluctuation` 模块监控市场变化

---

**项目状态**: ✅ 生产就绪  
**维护状态**: 🔄 积极维护  
**文档状态**: 📚 完整文档

*最后更新: 2025-05-27*

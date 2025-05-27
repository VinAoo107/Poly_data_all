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
# 获取活跃事件
python main.py market-info --type active --limit 50

# 获取已关闭事件
python main.py market-info --type closed --limit 100

# 获取所有市场信息
python main.py market-info --type all --include-analysis
```

#### 代码示例:

```python
from Poly_info.market_info_collector import MarketInfoCollector

collector = MarketInfoCollector()

# 获取活跃事件
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
python main.py price-data --mode batch --tokens token1,token2

# 连续监控价格变化
python main.py price-data --mode continuous --interval 60

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

# 获取交易数据
python main.py order-data --type trades --limit 1000

# 获取订单统计
python main.py order-data --type statistics --analysis
```

#### 代码示例:

```python
from Poly_order.order_collector import OrderCollector

collector = OrderCollector()

# 获取市场订单
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

# 批量用户分析
python main.py user-data --batch-file users.txt --analysis

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
# 启动实时监控
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
    interval=60,
    price_threshold=0.05
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

### 2. 基本使用

```bash
# 交互式启动
python start.py

# 快速测试
python tests/quick_test.py

# 查看帮助
python main.py --help
```

### 3. 配置文件

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
# 综合数据收集
python main.py comprehensive --mode full --output-format json

# 自定义收集策略
python main.py comprehensive --config custom_config.json
```

### 3. 数据导出

```bash
# 导出为CSV
python main.py export --format csv --data-type all

# 导出为JSON
python main.py export --format json --compress
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

# 收集价格数据
for market in markets[:10]:  # 前10个市场
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
    interval=60  # 每分钟检查一次
)
```

### 示例3: 历史数据分析

```python
from Poly_info.market_info_collector import MarketInfoCollector
from Poly_price_data.price_collector import PriceCollector

# 获取已结束的事件
info_collector = MarketInfoCollector()
closed_events = info_collector.fetch_events(market_type="closed")

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
# 启用详细日志
python main.py --log-level DEBUG

# 运行诊断测试
python tests/quick_test.py --verbose

# 检查配置
python -c "from config import *; print('配置加载成功')"
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

---

**项目状态**: ✅ 生产就绪
**维护状态**: 🔄 积极维护
**文档状态**: 📚 完整文档

*最后更新: 2025-05-27*

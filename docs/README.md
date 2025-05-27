# Polymarket 数据收集项目

这是一个全面的Polymarket数据收集和分析项目，提供了多个模块来获取和分析预测市场的各类数据。

## 项目结构

```
Poly_data_all/
├── config.py                    # 项目配置文件
├── utils.py                     # 通用工具模块
├── main.py                      # 主启动文件
├── comprehensive_collector.py   # 综合数据收集器
├── data_relationship_manager.py # 数据关联管理器
├── requirements.txt             # 依赖文件
├── README.md                    # 项目说明
├── logs/                        # 日志文件目录
├── data_relationships/          # 数据关联存储目录
├── Poly_info/                   # 市场信息收集模块
│   ├── market_info_collector.py
│   └── data/                    # 市场信息数据存储
├── Poly_price_data/             # 价格数据收集模块
│   ├── price_collector.py
│   └── data/                    # 价格数据存储
├── Poly_order/                  # 订单数据收集模块
│   ├── order_collector.py
│   └── data/                    # 订单数据存储
├── Poly_user_data/              # 用户数据收集模块
│   ├── user_collector.py
│   └── data/                    # 用户数据存储
└── Poly_market_fluctuation/     # 市场波动监控模块
    ├── fluctuation_monitor.py
    └── data/                    # 波动监控数据存储
```

## 功能模块

### 1. 综合数据收集器 (comprehensive_collector.py)

- **数据关联管理**: 建立市场、价格、订单、用户之间的关联关系
- **生态系统数据收集**: 一键收集完整的市场生态系统数据
- **综合视图**: 提供市场和用户的360度综合视图
- **关联分析**: 分析市场之间的关联性和用户行为模式
- **SQLite数据库**: 使用关系数据库存储和查询关联数据
- **实时监控**: 集成价格监控和异常检测

### 2. 市场信息收集 (Poly_info)

- 获取市场基本信息和事件数据
- 支持按市场类型筛选（活跃、已关闭、已归档等）
- 提供数据分析和统计功能
- 支持断点续传

### 3. 价格数据收集 (Poly_price_data)

- 批量获取市场价格数据
- 实时价格监控
- 获取订单簿、中间价、价差等详细数据
- 价格变化分析和报告生成
- 价格异常检测和告警

### 4. 订单数据收集 (Poly_order)

- 获取订单信息和交易记录
- 支持按市场、状态等条件筛选
- 活跃订单监控
- 订单和交易数据分析

### 5. 用户数据收集 (Poly_user_data)

- 获取用户持仓信息
- 用户订单和交易历史
- 用户行为分析
- 支持单个用户和批量用户数据收集

### 6. 市场波动监控 (Poly_market_fluctuation)

- 实时监控价格变化
- 价格趋势检测
- 交易量异常检测
- 自动告警系统
- 监控报告生成

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境变量配置（可选）

如果需要使用API认证，可以设置以下环境变量：

```bash
export POLYMARKET_API_KEY="your_api_key"
export POLYMARKET_API_SECRET="your_api_secret"
export POLYMARKET_API_PASSPHRASE="your_passphrase"
export POLYMARKET_PRIVATE_KEY="your_private_key"
```

### 3. 初始化配置

首次运行时，程序会自动创建必要的数据目录。

## 使用方法

### 快速开始 - 推荐使用方式

**🧪 首次使用：先运行测试模式（推荐）**

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行测试模式（验证系统可行性）
python main.py comprehensive --mode test --max-markets 3 --max-users 10 --verbose

# 3. 查看测试结果，确认系统正常后再运行完整收集
```

**📊 完整数据收集**

```bash
# 运行完整数据收集（在测试成功后使用）
python main.py comprehensive --mode ecosystem --include-users --include-monitoring --monitoring-duration 30 --verbose

# 查看收集结果
python main.py comprehensive --mode report
```

### 综合数据收集器 - 详细参数说明

#### 1. 测试模式（推荐首次使用）

```bash
# 基础测试命令
python main.py comprehensive --mode test

# 自定义测试参数
python main.py comprehensive --mode test --max-markets 5 --max-users 15 --include-monitoring --monitoring-duration 5 --verbose
```

**测试模式参数：**
- `--mode test`：启用测试模式，收集少量数据验证系统
- `--max-markets 3`：最大市场数量（默认3个，范围：1-10）
- `--max-users 10`：最大用户数量（默认10个，范围：5-50）
- `--include-monitoring`：是否包含价格监控测试（可选）
- `--monitoring-duration 5`：测试监控时长（分钟，默认5分钟）

**测试模式的优势：**
- ⚡ **快速验证**：通常在1-3分钟内完成
- 🔍 **系统检查**：验证所有模块是否正常工作
- 📊 **数据预览**：了解可以收集到什么类型的数据
- 🛡️ **风险控制**：避免长时间运行后发现问题
- 📋 **智能建议**：提供系统状态评估和改进建议

#### 2. 生态系统数据收集模式

```bash
# 基础命令：收集所有市场的完整数据
python main.py comprehensive --mode ecosystem

# 完整参数示例
python main.py comprehensive --mode ecosystem --markets market1 market2 --include-users --include-monitoring --monitoring-duration 60
```

**参数详解：**

- `--mode ecosystem`：收集完整的市场生态系统数据
- `--markets market1 market2`：指定特定市场ID列表，不指定则自动收集所有活跃市场
- `--include-users`：从订单数据中提取用户并收集用户数据（推荐开启）
- `--include-monitoring`：启用实时价格监控功能
- `--monitoring-duration 30`：监控持续时间（分钟）
  - 最小值：10分钟
  - 最大值：1440分钟（24小时）
  - 默认值：30分钟
- `--verbose`：显示详细输出信息
- `--quiet`：静默模式，只显示错误信息

**其他模块的常用参数：**
- `--type active`：市场类型（active/closed/archived/all）
- `--mode batch`：运行模式（batch/monitor/report等）
- `--detailed`：包含详细数据（订单簿、价差等）
- `--interval 60`：监控间隔（秒）
- `--duration 60`：监控时长（分钟）
- `--threshold 0.05`：价格变化阈值（5%）
- `--status LIVE`：订单状态（LIVE/FILLED/CANCELLED）
- `--user 0x1234...`：用户地址
- `--users user1 user2`：用户地址列表
- `--no-analysis`：跳过数据分析
- `--reset`：重置收集进度

#### 3. 数据查看和分析模式

```bash
# 查看特定市场的综合信息
python main.py comprehensive --mode market-view --markets 0x1234567890abcdef

# 查看特定用户的综合信息
python main.py comprehensive --mode user-view --user 0xabcdef1234567890

# 分析市场关联性
python main.py comprehensive --mode correlations

# 导出完整生态系统报告
python main.py comprehensive --mode report
```

#### 4. 常用命令示例

```bash
# 静默运行数据收集
python main.py comprehensive --mode ecosystem --quiet

# 查看帮助信息
python main.py --help
python main.py comprehensive --help
```

### 单独模块使用（高级用户）

如果您需要单独运行某个特定模块：

#### 市场信息收集

**新增功能：支持所有Polymarket Markets API端点**

```bash
# 标准模式：收集活跃市场信息
python main.py market-info --mode standard --type active

# 综合模式：收集所有类型的市场数据（包含时间序列）
python main.py market-info --mode comprehensive --include-timeseries --timeseries-interval 1h

# 采样模式：收集采样市场数据
python main.py market-info --mode sampling

# 简化模式：收集简化市场数据
python main.py market-info --mode simplified

# 时间序列模式：收集小时级时间序列数据
python main.py market-info --mode timeseries --timeseries-interval 1h

# 单个市场模式：获取特定市场详细信息
python main.py market-info --mode single --market-id [MARKET_ID]

# 传统用法（兼容性）
python main.py market-info --type active --no-analysis --reset
```

**支持的Markets API端点：**
- ✅ **Get Markets** - 获取市场列表
- ✅ **Get Single Market** - 获取单个市场详细信息
- ✅ **Get Sampling Markets** - 获取采样市场
- ✅ **Get Simplified Markets** - 获取简化市场
- ✅ **Get Sampling Simplified Markets** - 获取采样简化市场
- ✅ **Timeseries Data** - 获取时间序列数据

**参数说明：**
- `--mode`: 收集模式（standard/comprehensive/sampling/simplified/timeseries/single）
- `--type`: 市场类型，仅在标准模式下使用（all/active/closed/archived）
- `--market-id`: 市场ID，仅在单个市场模式下使用
- `--include-timeseries`: 在综合模式下包含时间序列数据
- `--timeseries-interval`: 时间序列间隔（1m/5m/15m/1h/4h/1d）

#### 价格数据收集

```bash
# 批量收集价格
python main.py price-data --mode batch --markets market1 market2 --detailed

# 实时价格监控
python main.py price-data --mode monitor --markets market1 market2 --interval 60
```

#### 订单数据收集

```bash
python main.py order-data --mode comprehensive --market market_id --status LIVE
```

#### 用户数据收集

```bash
# 单个用户
python main.py user-data --mode single --user 0x1234567890abcdef

# 批量用户
python main.py user-data --mode batch --users user1 user2 user3
```

#### 市场波动监控

```bash
python main.py fluctuation --markets market1 market2 --duration 60 --threshold 0.05 --interval 10
```

### 常用使用场景

#### 场景1：首次使用，系统测试
```bash
# 快速测试系统是否正常工作
python main.py comprehensive --mode test --verbose
```

#### 场景2：首次使用，获取完整数据

```bash
# 推荐新用户使用的完整命令
python main.py comprehensive --mode ecosystem --include-users --include-monitoring --monitoring-duration 30 --verbose
```

#### 场景3：只关注特定市场

```bash
# 收集特定市场的完整数据
python main.py comprehensive --mode ecosystem --markets 0x1234567890abcdef 0xabcdef1234567890 --include-users
```

#### 场景4：定期数据更新

```bash
# 适合定期运行的轻量级收集
python main.py comprehensive --mode ecosystem --quiet
```

#### 场景5：深度分析现有数据

```bash
# 分析已收集的数据
python main.py comprehensive --mode correlations
python main.py comprehensive --mode report
```

## 配置说明

### API配置

- `CLOB_BASE_URL`: Polymarket CLOB API基础URL
- `GAMMA_BASE_URL`: Gamma API基础URL
- `WSS_URL`: WebSocket端点URL

### 数据获取配置

- `MARKETS_BATCH_SIZE`: 批量获取的市场数量（默认100）
- `PRICE_UPDATE_INTERVAL`: 价格更新间隔（默认60秒）
- `ORDER_UPDATE_INTERVAL`: 订单更新间隔（默认30秒）
- `FLUCTUATION_CHECK_INTERVAL`: 波动检查间隔（默认10秒）
- `PRICE_CHANGE_THRESHOLD`: 价格变动阈值（默认5%）

### 频率限制

项目内置了请求频率限制机制，避免对API造成过大压力：

- 默认请求间隔：1秒
- 最大重试次数：3次
- 请求超时时间：10秒

## 数据存储

### 数据格式

所有数据都以JSON格式存储，包含时间戳和元数据信息。

### 数据目录

- `Poly_info/data/`: 市场信息和事件数据
- `Poly_price_data/data/`: 价格数据和监控记录
- `Poly_order/data/`: 订单和交易数据
- `Poly_user_data/data/`: 用户数据
- `Poly_market_fluctuation/data/`: 波动监控数据和告警记录
- `logs/`: 日志文件

### 进度保存

支持断点续传功能，程序会自动保存进度，中断后可以从上次停止的地方继续。

## 日志记录

项目提供了完整的日志记录功能：

- 控制台输出：实时显示运行状态
- 文件日志：详细记录到日志文件
- 不同级别：DEBUG、INFO、WARNING、ERROR

## 错误处理

- 网络请求重试机制
- 数据格式验证
- 异常情况记录
- 优雅的错误恢复

## 性能优化

- 请求频率限制
- 内存使用优化
- 批量数据处理
- 异步操作支持

## 扩展性

项目采用模块化设计，易于扩展：

- 新增数据源
- 自定义分析算法
- 集成其他API
- 添加新的监控指标

## 注意事项

1. **API限制**: 请遵守Polymarket API的使用限制和条款
2. **数据量**: 大量数据收集可能需要较长时间，建议分批进行
3. **存储空间**: 确保有足够的磁盘空间存储数据
4. **网络稳定**: 长时间运行需要稳定的网络连接
5. **资源使用**: 监控程序会持续运行，注意系统资源使用

## 故障排除

### API端点问题

根据测试结果，部分API端点可能不可用：

#### ✅ 可用的端点：
- **事件数据** (`/events`) - 完全可用
- **市场信息** (`/markets`) - 完全可用

#### ⚠️ 有问题的端点：
- **价格数据** - gamma-api可能没有prices端点
- **订单簿数据** - 需要活跃的市场ID
- **订单/交易数据** - 需要API认证

#### 🔧 解决方案：

1. **对于价格数据问题：**
   ```bash
   # 使用测试模式验证系统可行性
   python main.py comprehensive --mode test --max-markets 1
   ```

2. **对于认证问题：**
   - 设置环境变量（可选）：
   ```bash
   set POLYMARKET_API_KEY=your_api_key
   set POLYMARKET_API_SECRET=your_api_secret
   ```

3. **使用可用功能：**
   ```bash
   # 只收集市场信息（完全可用）
   python main.py market-info --type active
   ```

### 系统状态

- ✅ **核心系统正常** - 所有模块正确运行
- ✅ **数据存储正常** - 文件保存和读取正常
- ✅ **错误处理正常** - 系统正确处理API失败
- ✅ **关联系统正常** - 数据关联功能正常

### 建议的使用方式

1. **首先运行测试模式**（推荐）：
   ```bash
   python main.py comprehensive --mode test
   ```

2. **收集可用的数据**：
   ```bash
   # 收集市场信息（完全可用）
   python main.py market-info --type active
   ```

3. **查看收集的数据**：
   ```bash
   # 查看市场综合视图
   python main.py comprehensive --mode market-view --markets [market_id]
   ```

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和API使用条款。

## 贡献

欢迎提交问题报告和改进建议。

## 联系方式

如有问题或建议，请通过GitHub Issues联系。

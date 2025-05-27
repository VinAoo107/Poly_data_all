"""
Polymarket数据获取项目配置文件
包含API端点、认证信息和通用设置
"""

import os
from pathlib import Path

# API 基础配置
class APIConfig:
    # Polymarket CLOB API
    CLOB_BASE_URL = "https://clob.polymarket.com"
    
    # Gamma API (用于获取events和markets)
    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
    
    # WebSocket端点
    WSS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws"
    
    # 请求配置
    DEFAULT_LIMIT = 100
    MAX_RETRIES = 3
    TIMEOUT = 10
    RATE_LIMIT_DELAY = 1  # 请求间隔(秒)

# 认证配置
class AuthConfig:
    # API密钥配置 (从环境变量读取)
    API_KEY = os.getenv("POLYMARKET_API_KEY", "")
    API_SECRET = os.getenv("POLYMARKET_API_SECRET", "")
    API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE", "")
    
    # 私钥配置 (用于签名)
    PRIVATE_KEY = os.getenv("POLYMARKET_PRIVATE_KEY", "")

# 数据存储配置
class DataConfig:
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent
    
    # 各模块数据目录
    INFO_DATA_DIR = PROJECT_ROOT / "Poly_info" / "data"
    PRICE_DATA_DIR = PROJECT_ROOT / "Poly_price_data" / "data"
    ORDER_DATA_DIR = PROJECT_ROOT / "Poly_order" / "data"
    USER_DATA_DIR = PROJECT_ROOT / "Poly_user_data" / "data"
    FLUCTUATION_DATA_DIR = PROJECT_ROOT / "Poly_market_fluctuation" / "data"
    
    # 数据关联目录
    RELATIONSHIP_DATA_DIR = PROJECT_ROOT / "data_relationships"
    
    # 日志目录
    LOG_DIR = PROJECT_ROOT / "logs"
    
    @classmethod
    def ensure_directories(cls):
        """确保所有数据目录存在"""
        directories = [
            cls.INFO_DATA_DIR,
            cls.PRICE_DATA_DIR,
            cls.ORDER_DATA_DIR,
            cls.USER_DATA_DIR,
            cls.FLUCTUATION_DATA_DIR,
            cls.RELATIONSHIP_DATA_DIR,
            cls.LOG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# 市场类型配置
class MarketTypes:
    ALL = "all"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"
    RESOLVED = "resolved"

# 订单类型配置
class OrderTypes:
    BUY = "BUY"
    SELL = "SELL"

# 订单状态配置
class OrderStatus:
    LIVE = "LIVE"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"

# 交易状态配置
class TradeStatus:
    MATCHED = "MATCHED"
    MINED = "MINED"
    CONFIRMED = "CONFIRMED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"

# 数据获取配置
class DataFetchConfig:
    # 市场信息获取配置
    MARKETS_BATCH_SIZE = 100
    
    # 价格数据获取配置
    PRICE_UPDATE_INTERVAL = 60  # 价格更新间隔(秒)
    PRICE_HISTORY_DAYS = 30     # 获取历史价格天数
    
    # 订单数据获取配置
    ORDER_UPDATE_INTERVAL = 30  # 订单更新间隔(秒)
    
    # 用户数据获取配置
    USER_DATA_UPDATE_INTERVAL = 300  # 用户数据更新间隔(秒)
    
    # 市场波动监控配置
    FLUCTUATION_CHECK_INTERVAL = 10  # 波动检查间隔(秒)
    PRICE_CHANGE_THRESHOLD = 0.05    # 价格变动阈值(5%)

# 初始化配置
def init_config():
    """初始化配置，创建必要的目录"""
    DataConfig.ensure_directories()
    print("配置初始化完成，所有数据目录已创建")

# API端点配置
class APIEndpoints:
    """API端点配置 - 统一管理所有API端点"""
    # 基础URL
    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
    CLOB_BASE_URL = "https://clob.polymarket.com"
    
    # 市场信息相关 - 完整的Markets API端点
    EVENTS = f"{GAMMA_BASE_URL}/events"
    MARKETS = f"{GAMMA_BASE_URL}/markets"  # Get Markets
    MARKET_SINGLE = f"{GAMMA_BASE_URL}/markets"  # Get Single Market (需要添加market_id)
    
    # 修复：这些端点应该使用CLOB API而不是Gamma API
    MARKETS_SAMPLING = f"{CLOB_BASE_URL}/sampling-markets"  # 修复：使用CLOB端点
    MARKETS_SIMPLIFIED = f"{CLOB_BASE_URL}/simplified-markets"  # 修复：使用CLOB端点
    MARKETS_SAMPLING_SIMPLIFIED = f"{CLOB_BASE_URL}/sampling-simplified-markets"  # 修复：使用CLOB端点
    
    # 时间序列数据相关 - 修复：使用CLOB的prices-history端点
    TIMESERIES = f"{CLOB_BASE_URL}/prices-history"  # 修复：时间序列数据使用prices-history端点
    
    # 价格数据相关 - 使用正确的端点
    PRICES_HISTORY = f"{CLOB_BASE_URL}/prices-history"  # 历史价格数据（可用）
    PRICES = f"{CLOB_BASE_URL}/prices"  # 当前价格
    BOOK = f"{CLOB_BASE_URL}/book"
    MIDPOINT = f"{CLOB_BASE_URL}/midpoint"
    SPREAD = f"{CLOB_BASE_URL}/spread"
    
    # 订单和交易相关 - 使用CLOB API
    ORDERS = f"{CLOB_BASE_URL}/orders"
    TRADES = f"{CLOB_BASE_URL}/trades"
    
    # 用户数据相关
    USER_POSITIONS = f"{CLOB_BASE_URL}/positions"
    USER_ORDERS = f"{CLOB_BASE_URL}/orders"
    USER_TRADES = f"{CLOB_BASE_URL}/trades"

if __name__ == "__main__":
    init_config() 
"""
通用工具模块
包含HTTP请求、数据处理、日志记录等功能
"""

import requests
import json
import time
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from config import APIConfig, DataConfig

class Logger:
    """日志管理器"""
    
    @staticmethod
    def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
        """
        设置日志记录器
        
        参数:
            name: 日志记录器名称
            log_file: 日志文件名（可选）
            level: 日志级别
            
        返回:
            配置好的日志记录器
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（如果指定了日志文件）
        if log_file:
            DataConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                DataConfig.LOG_DIR / log_file, 
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger

class HTTPClient:
    """HTTP客户端，处理API请求"""
    
    def __init__(self, base_url: str, logger: logging.Logger = None):
        """
        初始化HTTP客户端
        
        参数:
            base_url: API基础URL
            logger: 日志记录器
        """
        self.base_url = base_url.rstrip('/')
        self.logger = logger or Logger.setup_logger(self.__class__.__name__)
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Polymarket-Data-Collector/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def get(self, endpoint: str, params: Dict = None, **kwargs) -> Optional[Dict]:
        """
        发送GET请求
        
        参数:
            endpoint: API端点
            params: 查询参数
            **kwargs: 其他请求参数
            
        返回:
            响应数据或None
        """
        return self._request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Dict = None, **kwargs) -> Optional[Dict]:
        """
        发送POST请求
        
        参数:
            endpoint: API端点
            data: 请求数据
            **kwargs: 其他请求参数
            
        返回:
            响应数据或None
        """
        return self._request('POST', endpoint, json=data, **kwargs)
    
    def _request(self, method: str, endpoint: str, max_retries: int = None, **kwargs) -> Optional[Dict]:
        """
        发送HTTP请求（带重试机制）
        
        参数:
            method: HTTP方法
            endpoint: API端点
            max_retries: 最大重试次数
            **kwargs: 其他请求参数
            
        返回:
            响应数据或None
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        max_retries = max_retries or APIConfig.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"请求 {method} {url}，参数: {kwargs.get('params', {})}")
                
                response = self.session.request(
                    method, 
                    url, 
                    timeout=APIConfig.TIMEOUT,
                    **kwargs
                )
                response.raise_for_status()
                
                # 尝试解析JSON响应
                try:
                    return response.json()
                except json.JSONDecodeError:
                    self.logger.warning(f"响应不是有效的JSON格式: {response.text[:100]}")
                    return {"raw_response": response.text}
                    
            except requests.RequestException as e:
                self.logger.warning(f"请求失败 (尝试 {attempt+1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** (attempt + 1)
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"达到最大重试次数，请求失败: {url}")
        
        return None

class DataManager:
    """数据管理器，处理数据的保存和加载"""
    
    def __init__(self, data_dir: Path, logger: logging.Logger = None):
        """
        初始化数据管理器
        
        参数:
            data_dir: 数据存储目录
            logger: 日志记录器
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or Logger.setup_logger(self.__class__.__name__)
    
    def save_json(self, data: Any, filename: str, ensure_ascii: bool = False) -> bool:
        """
        保存数据为JSON文件
        
        参数:
            data: 要保存的数据
            filename: 文件名
            ensure_ascii: 是否确保ASCII编码
            
        返回:
            是否保存成功
        """
        try:
            filepath = self.data_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=2, default=str)
            
            self.logger.info(f"数据已保存到: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")
            return False
    
    def load_json(self, filename: str) -> Optional[Any]:
        """
        从JSON文件加载数据
        
        参数:
            filename: 文件名
            
        返回:
            加载的数据或None
        """
        try:
            filepath = self.data_dir / filename
            if not filepath.exists():
                self.logger.warning(f"文件不存在: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"数据已从 {filepath} 加载")
            return data
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            return None
    
    def save_progress(self, data: Dict, progress_file: str = "progress.json") -> bool:
        """
        保存进度信息
        
        参数:
            data: 进度数据
            progress_file: 进度文件名
            
        返回:
            是否保存成功
        """
        progress_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        return self.save_json(progress_data, progress_file)
    
    def load_progress(self, progress_file: str = "progress.json") -> Optional[Dict]:
        """
        加载进度信息
        
        参数:
            progress_file: 进度文件名
            
        返回:
            进度数据或None
        """
        progress_data = self.load_json(progress_file)
        if progress_data and "data" in progress_data:
            return progress_data["data"]
        return None

class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self, delay: float = APIConfig.RATE_LIMIT_DELAY):
        """
        初始化频率限制器
        
        参数:
            delay: 请求间隔时间（秒）
        """
        self.delay = delay
        self.last_request_time = 0
    
    def wait(self):
        """等待适当的时间间隔"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

def format_timestamp(timestamp: Union[int, float, str]) -> str:
    """
    格式化时间戳
    
    参数:
        timestamp: 时间戳（秒或毫秒）
        
    返回:
        格式化的时间字符串
    """
    try:
        # 处理字符串类型的时间戳
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        
        # 如果是毫秒时间戳，转换为秒
        if timestamp > 1e10:
            timestamp = timestamp / 1000
        
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        
    except (ValueError, OSError) as e:
        return f"Invalid timestamp: {timestamp}"

def calculate_price_change(old_price: float, new_price: float) -> Dict[str, float]:
    """
    计算价格变化
    
    参数:
        old_price: 旧价格
        new_price: 新价格
        
    返回:
        包含绝对变化和百分比变化的字典
    """
    if old_price == 0:
        return {"absolute_change": new_price, "percentage_change": float('inf')}
    
    absolute_change = new_price - old_price
    percentage_change = (absolute_change / old_price) * 100
    
    return {
        "absolute_change": absolute_change,
        "percentage_change": percentage_change
    }

def validate_market_id(market_id: str) -> bool:
    """
    验证市场ID格式
    
    参数:
        market_id: 市场ID
        
    返回:
        是否为有效的市场ID
    """
    if not market_id or not isinstance(market_id, str):
        return False
    
    # 基本长度检查（Polymarket的市场ID通常很长）
    if len(market_id) < 10:
        return False
    
    return True

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    将列表分块
    
    参数:
        lst: 要分块的列表
        chunk_size: 每块的大小
        
    返回:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)] 
"""
市场波动监控器
用于实时监控Polymarket的价格变化和市场异常
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
import argparse
import time
import threading
import json
from collections import deque

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config import APIConfig, DataConfig, DataFetchConfig
from utils import HTTPClient, DataManager, Logger, RateLimiter, format_timestamp, calculate_price_change

class FluctuationMonitor:
    """市场波动监控器"""
    
    def __init__(self):
        """初始化市场波动监控器"""
        self.logger = Logger.setup_logger(
            "FluctuationMonitor", 
            "fluctuation_monitor.log"
        )
        
        # 初始化HTTP客户端
        self.clob_client = HTTPClient(APIConfig.CLOB_BASE_URL, self.logger)
        
        # 初始化数据管理器
        self.data_manager = DataManager(DataConfig.FLUCTUATION_DATA_DIR, self.logger)
        
        # 初始化频率限制器
        self.rate_limiter = RateLimiter(DataFetchConfig.FLUCTUATION_CHECK_INTERVAL)
        
        # 监控状态
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # 价格历史缓存（使用deque限制内存使用）
        self.price_history = {}
        self.max_history_length = 1000
        
        # 波动检测配置
        self.price_change_threshold = DataFetchConfig.PRICE_CHANGE_THRESHOLD
        self.volume_spike_threshold = 2.0  # 交易量激增阈值（倍数）
        self.alert_cooldown = 300  # 告警冷却时间（秒）
        
        # 告警历史（避免重复告警）
        self.alert_history = {}
        
        self.logger.info("市场波动监控器初始化完成")
    
    def fetch_current_prices(self, market_ids: List[str] = None) -> Dict[str, Any]:
        """
        获取当前市场价格
        
        参数:
            market_ids: 市场ID列表
            
        返回:
            价格数据
        """
        params = {}
        if market_ids:
            params["market_ids"] = ",".join(market_ids)
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get("/prices", params=params)
        
        if response:
            return response
        
        self.logger.error("获取当前价格失败")
        return {}
    
    def fetch_market_volume(self, market_id: str) -> Optional[Dict]:
        """
        获取市场交易量数据
        
        参数:
            market_id: 市场ID
            
        返回:
            交易量数据
        """
        # 频率限制
        self.rate_limiter.wait()
        
        # 获取最近的交易记录来计算交易量
        response = self.clob_client.get("/trades", params={
            "market": market_id,
            "limit": 100
        })
        
        if response:
            # 处理响应格式
            if isinstance(response, dict) and "data" in response:
                trades = response["data"]
            elif isinstance(response, list):
                trades = response
            else:
                trades = []
            
            # 计算最近1小时的交易量
            current_time = datetime.now(timezone.utc)
            one_hour_ago = current_time - timedelta(hours=1)
            
            recent_volume = 0
            for trade in trades:
                try:
                    trade_time = datetime.fromisoformat(trade.get("timestamp", "").replace('Z', '+00:00'))
                    if trade_time >= one_hour_ago:
                        volume = float(trade.get("volume", 0))
                        recent_volume += volume
                except (ValueError, TypeError):
                    continue
            
            return {
                "market_id": market_id,
                "recent_volume_1h": recent_volume,
                "trade_count": len(trades),
                "timestamp": current_time.isoformat()
            }
        
        return None
    
    def update_price_history(self, market_id: str, price_data: Dict, timestamp: datetime):
        """
        更新价格历史记录
        
        参数:
            market_id: 市场ID
            price_data: 价格数据
            timestamp: 时间戳
        """
        if market_id not in self.price_history:
            self.price_history[market_id] = deque(maxlen=self.max_history_length)
        
        # 添加新的价格记录
        self.price_history[market_id].append({
            "timestamp": timestamp.isoformat(),
            "price_data": price_data
        })
    
    def detect_price_fluctuations(self, market_id: str, current_price_data: Dict) -> List[Dict]:
        """
        检测价格波动
        
        参数:
            market_id: 市场ID
            current_price_data: 当前价格数据
            
        返回:
            检测到的波动列表
        """
        fluctuations = []
        
        if market_id not in self.price_history or len(self.price_history[market_id]) < 2:
            return fluctuations
        
        # 获取历史价格
        history = list(self.price_history[market_id])
        
        # 与最近的价格比较
        if len(history) >= 2:
            last_record = history[-2]  # 倒数第二个记录
            last_price_data = last_record["price_data"]
            
            # 比较价格变化
            if "price" in current_price_data and "price" in last_price_data:
                try:
                    current_price = float(current_price_data["price"])
                    last_price = float(last_price_data["price"])
                    
                    change_info = calculate_price_change(last_price, current_price)
                    
                    # 检查是否超过阈值
                    if abs(change_info["percentage_change"]) >= (self.price_change_threshold * 100):
                        fluctuations.append({
                            "type": "price_change",
                            "market_id": market_id,
                            "current_price": current_price,
                            "last_price": last_price,
                            "absolute_change": change_info["absolute_change"],
                            "percentage_change": change_info["percentage_change"],
                            "severity": self.classify_severity(abs(change_info["percentage_change"])),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"价格比较失败: {e}")
        
        # 检查短期趋势（最近5个数据点）
        if len(history) >= 5:
            recent_prices = []
            for record in history[-5:]:
                if "price" in record["price_data"]:
                    try:
                        recent_prices.append(float(record["price_data"]["price"]))
                    except (ValueError, TypeError):
                        continue
            
            if len(recent_prices) >= 5:
                # 检查是否有持续上涨或下跌趋势
                trend = self.detect_trend(recent_prices)
                if trend["is_significant"]:
                    fluctuations.append({
                        "type": "trend",
                        "market_id": market_id,
                        "trend_direction": trend["direction"],
                        "trend_strength": trend["strength"],
                        "price_range": {
                            "start": recent_prices[0],
                            "end": recent_prices[-1],
                            "min": min(recent_prices),
                            "max": max(recent_prices)
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        
        return fluctuations
    
    def detect_trend(self, prices: List[float]) -> Dict[str, Any]:
        """
        检测价格趋势
        
        参数:
            prices: 价格列表
            
        返回:
            趋势信息
        """
        if len(prices) < 3:
            return {"is_significant": False}
        
        # 计算价格变化方向
        increases = 0
        decreases = 0
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                increases += 1
            elif prices[i] < prices[i-1]:
                decreases += 1
        
        total_changes = increases + decreases
        if total_changes == 0:
            return {"is_significant": False}
        
        # 计算趋势强度
        if increases > decreases:
            direction = "upward"
            strength = increases / total_changes
        else:
            direction = "downward"
            strength = decreases / total_changes
        
        # 判断是否显著（至少80%的变化朝同一方向）
        is_significant = strength >= 0.8 and total_changes >= 3
        
        return {
            "is_significant": is_significant,
            "direction": direction,
            "strength": strength,
            "increases": increases,
            "decreases": decreases
        }
    
    def classify_severity(self, percentage_change: float) -> str:
        """
        分类波动严重程度
        
        参数:
            percentage_change: 百分比变化
            
        返回:
            严重程度等级
        """
        if percentage_change >= 20:
            return "critical"
        elif percentage_change >= 10:
            return "high"
        elif percentage_change >= 5:
            return "medium"
        else:
            return "low"
    
    def detect_volume_spikes(self, market_id: str, current_volume_data: Dict) -> List[Dict]:
        """
        检测交易量激增
        
        参数:
            market_id: 市场ID
            current_volume_data: 当前交易量数据
            
        返回:
            检测到的交易量异常列表
        """
        spikes = []
        
        # 这里可以实现交易量激增检测逻辑
        # 由于需要历史交易量数据，这里提供一个基础框架
        
        current_volume = current_volume_data.get("recent_volume_1h", 0)
        
        # 简单的交易量异常检测（可以根据需要扩展）
        if current_volume > 10000:  # 假设的高交易量阈值
            spikes.append({
                "type": "volume_spike",
                "market_id": market_id,
                "current_volume": current_volume,
                "severity": "high" if current_volume > 50000 else "medium",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return spikes
    
    def should_send_alert(self, market_id: str, alert_type: str) -> bool:
        """
        判断是否应该发送告警（避免重复告警）
        
        参数:
            market_id: 市场ID
            alert_type: 告警类型
            
        返回:
            是否应该发送告警
        """
        alert_key = f"{market_id}_{alert_type}"
        current_time = datetime.now(timezone.utc)
        
        if alert_key in self.alert_history:
            last_alert_time = self.alert_history[alert_key]
            time_diff = (current_time - last_alert_time).total_seconds()
            
            if time_diff < self.alert_cooldown:
                return False
        
        # 更新告警历史
        self.alert_history[alert_key] = current_time
        return True
    
    def process_alerts(self, fluctuations: List[Dict], volume_spikes: List[Dict]):
        """
        处理告警
        
        参数:
            fluctuations: 价格波动列表
            volume_spikes: 交易量异常列表
        """
        all_alerts = fluctuations + volume_spikes
        
        if not all_alerts:
            return
        
        # 过滤重复告警
        filtered_alerts = []
        for alert in all_alerts:
            market_id = alert.get("market_id")
            alert_type = alert.get("type")
            
            if self.should_send_alert(market_id, alert_type):
                filtered_alerts.append(alert)
        
        if filtered_alerts:
            # 保存告警记录
            alert_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "alerts": filtered_alerts,
                "alert_count": len(filtered_alerts)
            }
            
            filename = f"alerts_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            self.data_manager.save_json(alert_data, filename)
            
            # 记录日志
            for alert in filtered_alerts:
                severity = alert.get("severity", "unknown")
                alert_type = alert.get("type", "unknown")
                market_id = alert.get("market_id", "unknown")
                
                self.logger.warning(f"[{severity.upper()}] {alert_type} detected for market {market_id}")
                
                if alert_type == "price_change":
                    self.logger.warning(f"Price change: {alert.get('percentage_change', 0):.2f}%")
                elif alert_type == "volume_spike":
                    self.logger.warning(f"Volume spike: {alert.get('current_volume', 0)}")
    
    def monitor_markets(self, market_ids: List[str], duration_minutes: int = None):
        """
        监控指定市场
        
        参数:
            market_ids: 要监控的市场ID列表
            duration_minutes: 监控持续时间（分钟），None表示无限期监控
        """
        self.logger.info(f"开始监控 {len(market_ids)} 个市场")
        
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None
        
        self.is_monitoring = True
        
        try:
            while self.is_monitoring:
                current_time = datetime.now(timezone.utc)
                
                # 检查是否到达结束时间
                if end_time and current_time >= end_time:
                    self.logger.info("监控时间到达，停止监控")
                    break
                
                self.logger.info(f"执行市场监控检查 - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 获取当前价格
                current_prices = self.fetch_current_prices(market_ids)
                
                all_fluctuations = []
                all_volume_spikes = []
                
                for market_id in market_ids:
                    if market_id in current_prices:
                        price_data = current_prices[market_id]
                        
                        # 更新价格历史
                        self.update_price_history(market_id, price_data, current_time)
                        
                        # 检测价格波动
                        fluctuations = self.detect_price_fluctuations(market_id, price_data)
                        all_fluctuations.extend(fluctuations)
                        
                        # 获取交易量数据并检测异常
                        volume_data = self.fetch_market_volume(market_id)
                        if volume_data:
                            volume_spikes = self.detect_volume_spikes(market_id, volume_data)
                            all_volume_spikes.extend(volume_spikes)
                
                # 处理告警
                self.process_alerts(all_fluctuations, all_volume_spikes)
                
                # 保存监控数据
                monitoring_data = {
                    "timestamp": current_time.isoformat(),
                    "monitored_markets": market_ids,
                    "price_data": current_prices,
                    "fluctuations_detected": len(all_fluctuations),
                    "volume_spikes_detected": len(all_volume_spikes),
                    "fluctuations": all_fluctuations,
                    "volume_spikes": all_volume_spikes
                }
                
                filename = f"monitoring_{current_time.strftime('%Y%m%d_%H%M%S')}.json"
                self.data_manager.save_json(monitoring_data, filename)
                
                # 等待下一次检查
                time.sleep(DataFetchConfig.FLUCTUATION_CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，停止监控")
        except Exception as e:
            self.logger.error(f"监控过程中发生错误: {e}")
        finally:
            self.is_monitoring = False
            
            # 生成监控报告
            self.generate_monitoring_report(start_time, current_time, market_ids)
    
    def start_background_monitoring(self, market_ids: List[str], duration_minutes: int = None):
        """
        在后台线程中开始监控
        
        参数:
            market_ids: 要监控的市场ID列表
            duration_minutes: 监控持续时间（分钟）
        """
        if self.is_monitoring:
            self.logger.warning("监控已在运行中")
            return
        
        self.monitoring_thread = threading.Thread(
            target=self.monitor_markets,
            args=(market_ids, duration_minutes),
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info("后台监控已启动")
        return self.monitoring_thread
    
    def stop_monitoring(self):
        """停止监控"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.logger.info("正在停止监控...")
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=10)
            
            self.logger.info("监控已停止")
        else:
            self.logger.info("监控未在运行")
    
    def generate_monitoring_report(self, start_time: datetime, end_time: datetime, market_ids: List[str]):
        """
        生成监控报告
        
        参数:
            start_time: 监控开始时间
            end_time: 监控结束时间
            market_ids: 监控的市场ID列表
        """
        duration = (end_time - start_time).total_seconds()
        
        report = {
            "monitoring_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "duration_hours": duration / 3600
            },
            "monitored_markets": market_ids,
            "market_count": len(market_ids),
            "statistics": {
                "total_price_records": sum(len(history) for history in self.price_history.values()),
                "markets_with_data": len(self.price_history),
                "alert_types_triggered": len(set(key.split('_')[1] for key in self.alert_history.keys()))
            },
            "alert_summary": {},
            "market_analysis": {}
        }
        
        # 分析每个市场的数据
        for market_id in market_ids:
            if market_id in self.price_history:
                history = list(self.price_history[market_id])
                
                if history:
                    prices = []
                    for record in history:
                        if "price" in record["price_data"]:
                            try:
                                prices.append(float(record["price_data"]["price"]))
                            except (ValueError, TypeError):
                                continue
                    
                    if prices:
                        report["market_analysis"][market_id] = {
                            "data_points": len(prices),
                            "price_range": {
                                "min": min(prices),
                                "max": max(prices),
                                "start": prices[0],
                                "end": prices[-1]
                            },
                            "volatility": self.calculate_volatility(prices),
                            "total_change_percent": ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] != 0 else 0
                        }
        
        # 统计告警信息
        alert_types = {}
        for alert_key in self.alert_history.keys():
            alert_type = alert_key.split('_')[1]
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        
        report["alert_summary"] = alert_types
        
        # 保存报告
        report_filename = f"monitoring_report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.data_manager.save_json(report, report_filename)
        
        self.logger.info(f"监控报告已生成: {report_filename}")
        return report
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """
        计算价格波动率
        
        参数:
            prices: 价格列表
            
        返回:
            波动率
        """
        if len(prices) < 2:
            return 0.0
        
        # 计算价格变化率
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if not returns:
            return 0.0
        
        # 计算标准差作为波动率
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5
        
        return volatility

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="Polymarket市场波动监控器")
    
    parser.add_argument(
        "--markets",
        nargs="+",
        required=True,
        help="要监控的市场ID列表"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        help="监控持续时间（分钟），不指定则无限期监控"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=DataFetchConfig.PRICE_CHANGE_THRESHOLD,
        help="价格变化阈值（小数形式，如0.05表示5%）"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=DataFetchConfig.FLUCTUATION_CHECK_INTERVAL,
        help="检查间隔（秒）"
    )
    
    parser.add_argument(
        "--background",
        action="store_true",
        help="在后台运行监控"
    )
    
    args = parser.parse_args()
    
    # 初始化配置
    DataConfig.ensure_directories()
    
    # 创建监控器
    monitor = FluctuationMonitor()
    
    # 设置自定义参数
    monitor.price_change_threshold = args.threshold
    monitor.rate_limiter.delay = args.interval
    
    print(f"开始监控 {len(args.markets)} 个市场")
    print(f"价格变化阈值: {args.threshold * 100:.1f}%")
    print(f"检查间隔: {args.interval} 秒")
    if args.duration:
        print(f"监控时长: {args.duration} 分钟")
    else:
        print("监控时长: 无限期")
    
    try:
        if args.background:
            # 后台监控
            thread = monitor.start_background_monitoring(args.markets, args.duration)
            print("后台监控已启动，按 Ctrl+C 停止")
            
            try:
                while monitor.is_monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n正在停止监控...")
                monitor.stop_monitoring()
        else:
            # 前台监控
            print("开始监控，按 Ctrl+C 停止")
            monitor.monitor_markets(args.markets, args.duration)
            
    except KeyboardInterrupt:
        print("\n监控已停止")
    
    print("监控完成")

if __name__ == "__main__":
    main() 
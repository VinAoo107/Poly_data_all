"""
价格数据收集器
用于获取Polymarket的市场价格、订单簿、价差等数据
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
import argparse
import time
import threading
import pandas as pd

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config import APIConfig, DataConfig, DataFetchConfig, APIEndpoints
from utils import HTTPClient, DataManager, Logger, RateLimiter, format_timestamp, calculate_price_change

class PriceCollector:
    """价格数据收集器"""
    
    def __init__(self):
        """初始化价格数据收集器"""
        self.logger = Logger.setup_logger(
            "PriceCollector", 
            "price_data.log"
        )
        
        # 初始化HTTP客户端
        self.clob_client = HTTPClient(APIConfig.CLOB_BASE_URL, self.logger)
        
        # 初始化数据管理器
        self.data_manager = DataManager(DataConfig.PRICE_DATA_DIR, self.logger)
        
        # 初始化频率限制器
        self.rate_limiter = RateLimiter()
        
        # 价格历史缓存
        self.price_history = {}
        
        # 运行状态
        self.is_running = False
        
        self.logger.info("价格数据收集器初始化完成")
    
    def fetch_price_history(self, market_id: str, fidelity: int = 1, 
                           interval: str = "max") -> Optional[pd.DataFrame]:
        """
        获取市场历史价格数据（使用可用的API端点）
        
        参数:
            market_id: 市场/代币ID
            fidelity: 数据精度(1=每分钟，60=每小时，1440=每天)
            interval: 时间间隔("max"=全部历史数据)
            
        返回:
            pandas.DataFrame: 处理后的价格数据
        """
        self.logger.info(f"获取市场 {market_id} 的历史价格数据 (fidelity={fidelity})")
        
        # 设置请求参数
        params = {
            "market": market_id,
            "interval": interval,
            "fidelity": fidelity
        }
        
        try:
            # 频率限制
            self.rate_limiter.wait()
            
            # 发送请求到prices-history端点
            response = self.clob_client.get("/prices-history", params=params)
            
            if not response:
                self.logger.error(f"获取市场 {market_id} 历史价格失败")
                return None
            
            # 提取历史数据
            history = response.get("history", [])
            
            if not history:
                self.logger.warning(f"市场 {market_id} 没有历史价格数据")
                return None
            
            self.logger.info(f"成功获取 {len(history)} 个价格数据点")
            
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
                self.logger.warning(f"发现 {df.index.duplicated().sum()} 个重复时间戳，已去重")
                df = df[~df.index.duplicated(keep='last')]
            
            # 添加市场ID信息
            df["market_id"] = market_id
            df["fidelity"] = fidelity
            
            if not df.empty:
                start_time = df.index.min()
                end_time = df.index.max()
                self.logger.info(f"数据时间范围: {start_time} 至 {end_time}")
                self.logger.info(f"总共 {(end_time - start_time).days + 1} 天的数据")
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取历史价格数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def fetch_market_prices(self, market_ids: List[str] = None) -> Dict[str, Any]:
        """
        获取市场价格数据
        
        参数:
            market_ids: 市场ID列表，如果为None则获取所有市场
            
        返回:
            价格数据字典
        """
        params = {}
        if market_ids:
            # 如果指定了市场ID，构建查询参数
            params["market_ids"] = ",".join(market_ids)
        
        self.logger.info(f"获取市场价格数据，市场数量: {len(market_ids) if market_ids else '全部'}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get("/prices", params=params)
        
        if response:
            self.logger.info(f"成功获取价格数据")
            return response
        
        self.logger.error("获取价格数据失败")
        return {}
    
    def fetch_market_book(self, market_id: str) -> Optional[Dict]:
        """
        获取市场订单簿数据
        
        参数:
            market_id: 市场ID
            
        返回:
            订单簿数据
        """
        self.logger.debug(f"获取市场 {market_id} 的订单簿")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get(f"/book", params={"token_id": market_id})
        
        if response:
            self.logger.debug(f"成功获取市场 {market_id} 的订单簿")
            return response
        
        self.logger.warning(f"获取市场 {market_id} 订单簿失败")
        return None
    
    def fetch_market_midpoint(self, market_id: str) -> Optional[Dict]:
        """
        获取市场中间价
        
        参数:
            market_id: 市场ID
            
        返回:
            中间价数据
        """
        self.logger.debug(f"获取市场 {market_id} 的中间价")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get(f"/midpoint", params={"token_id": market_id})
        
        if response:
            self.logger.debug(f"成功获取市场 {market_id} 的中间价")
            return response
        
        self.logger.warning(f"获取市场 {market_id} 中间价失败")
        return None
    
    def fetch_market_spread(self, market_id: str) -> Optional[Dict]:
        """
        获取市场价差
        
        参数:
            market_id: 市场ID
            
        返回:
            价差数据
        """
        self.logger.debug(f"获取市场 {market_id} 的价差")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get(f"/spread", params={"token_id": market_id})
        
        if response:
            self.logger.debug(f"成功获取市场 {market_id} 的价差")
            return response
        
        self.logger.warning(f"获取市场 {market_id} 价差失败")
        return None
    
    def fetch_comprehensive_market_data(self, market_id: str) -> Dict[str, Any]:
        """
        获取市场的综合数据（价格、订单簿、中间价、价差）
        
        参数:
            market_id: 市场ID
            
        返回:
            综合市场数据
        """
        self.logger.info(f"获取市场 {market_id} 的综合数据")
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        comprehensive_data = {
            "market_id": market_id,
            "timestamp": timestamp,
            "data": {}
        }
        
        # 获取价格数据
        prices = self.fetch_market_prices([market_id])
        if prices:
            comprehensive_data["data"]["prices"] = prices
        
        # 获取订单簿
        book = self.fetch_market_book(market_id)
        if book:
            comprehensive_data["data"]["book"] = book
        
        # 获取中间价
        midpoint = self.fetch_market_midpoint(market_id)
        if midpoint:
            comprehensive_data["data"]["midpoint"] = midpoint
        
        # 获取价差
        spread = self.fetch_market_spread(market_id)
        if spread:
            comprehensive_data["data"]["spread"] = spread
        
        self.logger.info(f"市场 {market_id} 综合数据获取完成")
        return comprehensive_data
    
    def collect_batch_prices(self, market_ids: List[str], 
                           include_detailed: bool = False) -> Dict[str, Any]:
        """
        批量收集市场价格数据
        
        参数:
            market_ids: 市场ID列表
            include_detailed: 是否包含详细数据（订单簿、价差等）
            
        返回:
            批量价格数据
        """
        self.logger.info(f"开始批量收集 {len(market_ids)} 个市场的价格数据")
        
        start_time = datetime.now(timezone.utc)
        
        batch_data = {
            "collection_timestamp": start_time.isoformat(),
            "market_count": len(market_ids),
            "include_detailed": include_detailed,
            "markets": {}
        }
        
        # 获取所有市场的基础价格数据
        all_prices = self.fetch_market_prices(market_ids)
        if all_prices:
            batch_data["bulk_prices"] = all_prices
        
        # 如果需要详细数据，逐个获取
        if include_detailed:
            self.logger.info("获取详细市场数据...")
            
            for i, market_id in enumerate(market_ids):
                self.logger.info(f"处理市场 {i+1}/{len(market_ids)}: {market_id}")
                
                try:
                    market_data = self.fetch_comprehensive_market_data(market_id)
                    batch_data["markets"][market_id] = market_data
                    
                    # 每处理10个市场保存一次进度
                    if (i + 1) % 10 == 0:
                        progress_file = f"batch_collection_progress_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
                        self.data_manager.save_progress({
                            "completed_markets": i + 1,
                            "total_markets": len(market_ids),
                            "batch_data": batch_data
                        }, progress_file)
                        
                except Exception as e:
                    self.logger.error(f"获取市场 {market_id} 数据失败: {e}")
                    batch_data["markets"][market_id] = {
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
        
        end_time = datetime.now(timezone.utc)
        batch_data["completion_timestamp"] = end_time.isoformat()
        batch_data["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # 保存批量数据
        filename = f"batch_prices_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.data_manager.save_json(batch_data, filename)
        
        self.logger.info(f"批量价格收集完成，耗时 {batch_data['duration_seconds']:.2f} 秒")
        return batch_data
    
    def collect_batch_price_history(self, market_ids: List[str], 
                                   fidelity: int = 1) -> Dict[str, Any]:
        """
        批量收集市场历史价格数据（使用可用的API端点）
        
        参数:
            market_ids: 市场ID列表
            fidelity: 数据精度(1=每分钟，60=每小时，1440=每天)
            
        返回:
            批量历史价格数据
        """
        self.logger.info(f"开始批量收集 {len(market_ids)} 个市场的历史价格数据 (fidelity={fidelity})")
        
        start_time = datetime.now(timezone.utc)
        
        batch_data = {
            "collection_timestamp": start_time.isoformat(),
            "market_count": len(market_ids),
            "fidelity": fidelity,
            "markets": {},
            "successful_markets": [],
            "failed_markets": []
        }
        
        for i, market_id in enumerate(market_ids):
            self.logger.info(f"处理市场 {i+1}/{len(market_ids)}: {market_id}")
            
            try:
                # 获取历史价格数据
                df = self.fetch_price_history(market_id, fidelity)
                
                if df is not None and not df.empty:
                    # 转换DataFrame为可序列化的格式
                    market_data = {
                        "market_id": market_id,
                        "data_points": len(df),
                        "start_time": df.index.min().isoformat(),
                        "end_time": df.index.max().isoformat(),
                        "price_range": {
                            "min": float(df['price'].min()),
                            "max": float(df['price'].max()),
                            "mean": float(df['price'].mean()),
                            "std": float(df['price'].std())
                        },
                        "data": df.reset_index().to_dict('records')
                    }
                    
                    batch_data["markets"][market_id] = market_data
                    batch_data["successful_markets"].append(market_id)
                    
                    # 保存单个市场的数据到CSV和pickle
                    self.save_market_price_history(df, market_id, fidelity)
                    
                    self.logger.info(f"✅ 市场 {market_id}: {len(df)} 个数据点")
                else:
                    batch_data["failed_markets"].append({
                        "market_id": market_id,
                        "reason": "No data returned"
                    })
                    self.logger.warning(f"❌ 市场 {market_id}: 无数据")
                
            except Exception as e:
                error_msg = str(e)
                batch_data["failed_markets"].append({
                    "market_id": market_id,
                    "reason": error_msg
                })
                self.logger.error(f"❌ 市场 {market_id} 失败: {error_msg}")
            
            # 每处理5个市场保存一次进度
            if (i + 1) % 5 == 0:
                progress_file = f"batch_history_progress_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
                progress_data = {
                    "completed_markets": i + 1,
                    "total_markets": len(market_ids),
                    "successful_count": len(batch_data["successful_markets"]),
                    "failed_count": len(batch_data["failed_markets"]),
                    "fidelity": fidelity
                }
                self.data_manager.save_json(progress_data, progress_file)
        
        end_time = datetime.now(timezone.utc)
        batch_data["completion_timestamp"] = end_time.isoformat()
        batch_data["duration_seconds"] = (end_time - start_time).total_seconds()
        batch_data["success_rate"] = len(batch_data["successful_markets"]) / len(market_ids) * 100
        
        # 保存批量历史数据
        fidelity_name = {1: "minute", 60: "hour", 1440: "day"}.get(fidelity, f"fidelity_{fidelity}")
        filename = f"batch_price_history_{fidelity_name}_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.data_manager.save_json(batch_data, filename)
        
        self.logger.info(f"批量历史价格收集完成，耗时 {batch_data['duration_seconds']:.2f} 秒")
        self.logger.info(f"成功: {len(batch_data['successful_markets'])}, 失败: {len(batch_data['failed_markets'])}")
        self.logger.info(f"成功率: {batch_data['success_rate']:.1f}%")
        
        return batch_data
    
    def save_market_price_history(self, df: pd.DataFrame, market_id: str, fidelity: int):
        """
        保存单个市场的历史价格数据
        
        参数:
            df: 价格数据DataFrame
            market_id: 市场ID
            fidelity: 数据精度
        """
        if df is None or df.empty:
            return
        
        # 确定文件名前缀
        fidelity_name = {1: "minute", 60: "hour", 1440: "day"}.get(fidelity, f"fidelity_{fidelity}")
        
        # 保存为CSV
        csv_filename = f"market_{market_id}_{fidelity_name}_history.csv"
        csv_path = self.data_manager.data_dir / csv_filename
        df.to_csv(csv_path)
        
        # 保存为pickle（更适合大数据）
        pickle_filename = f"market_{market_id}_{fidelity_name}_history.pkl"
        pickle_path = self.data_manager.data_dir / pickle_filename
        df.to_pickle(pickle_path)
        
        self.logger.debug(f"市场 {market_id} 历史数据已保存: {csv_filename}, {pickle_filename}")
    
    def start_continuous_monitoring(self, market_ids: List[str], 
                                  interval: int = None) -> None:
        """
        开始连续监控市场价格
        
        参数:
            market_ids: 要监控的市场ID列表
            interval: 监控间隔（秒）
        """
        interval = interval or DataFetchConfig.PRICE_UPDATE_INTERVAL
        
        self.logger.info(f"开始连续监控 {len(market_ids)} 个市场，间隔 {interval} 秒")
        
        self.is_running = True
        
        def monitoring_loop():
            while self.is_running:
                try:
                    timestamp = datetime.now(timezone.utc)
                    self.logger.info(f"执行价格监控 - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # 获取当前价格
                    current_prices = self.fetch_market_prices(market_ids)
                    
                    if current_prices:
                        # 分析价格变化
                        price_analysis = self.analyze_price_changes(current_prices)
                        
                        # 保存监控数据
                        monitoring_data = {
                            "timestamp": timestamp.isoformat(),
                            "prices": current_prices,
                            "analysis": price_analysis
                        }
                        
                        filename = f"monitoring_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                        self.data_manager.save_json(monitoring_data, filename)
                        
                        # 更新价格历史
                        self.update_price_history(current_prices, timestamp)
                        
                        # 检查显著价格变化
                        significant_changes = self.detect_significant_changes(price_analysis)
                        if significant_changes:
                            self.logger.warning(f"检测到显著价格变化: {len(significant_changes)} 个市场")
                            
                            # 保存显著变化记录
                            alert_data = {
                                "timestamp": timestamp.isoformat(),
                                "significant_changes": significant_changes
                            }
                            alert_filename = f"price_alerts_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                            self.data_manager.save_json(alert_data, alert_filename)
                    
                    # 等待下一次监控
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("收到中断信号，停止监控")
                    self.is_running = False
                    break
                except Exception as e:
                    self.logger.error(f"监控过程中发生错误: {e}")
                    time.sleep(interval)  # 发生错误时也要等待，避免过于频繁的重试
        
        # 在单独的线程中运行监控
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        
        return monitoring_thread
    
    def stop_monitoring(self):
        """停止连续监控"""
        self.is_running = False
        self.logger.info("价格监控已停止")
    
    def update_price_history(self, prices: Dict, timestamp: datetime):
        """
        更新价格历史记录
        
        参数:
            prices: 价格数据
            timestamp: 时间戳
        """
        for market_id, price_info in prices.items():
            if market_id not in self.price_history:
                self.price_history[market_id] = []
            
            # 添加新的价格记录
            self.price_history[market_id].append({
                "timestamp": timestamp.isoformat(),
                "price_data": price_info
            })
            
            # 保持历史记录在合理范围内（最多保留1000条记录）
            if len(self.price_history[market_id]) > 1000:
                self.price_history[market_id] = self.price_history[market_id][-1000:]
    
    def analyze_price_changes(self, current_prices: Dict) -> Dict[str, Any]:
        """
        分析价格变化
        
        参数:
            current_prices: 当前价格数据
            
        返回:
            价格变化分析结果
        """
        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_changes": {},
            "summary": {
                "total_markets": len(current_prices),
                "markets_with_changes": 0,
                "significant_changes": 0
            }
        }
        
        for market_id, current_price_info in current_prices.items():
            if market_id in self.price_history and self.price_history[market_id]:
                # 获取上一次的价格
                last_record = self.price_history[market_id][-1]
                last_price_info = last_record["price_data"]
                
                # 比较价格变化（这里需要根据实际API响应格式调整）
                if "price" in current_price_info and "price" in last_price_info:
                    current_price = float(current_price_info["price"])
                    last_price = float(last_price_info["price"])
                    
                    change_info = calculate_price_change(last_price, current_price)
                    
                    analysis["market_changes"][market_id] = {
                        "current_price": current_price,
                        "last_price": last_price,
                        "absolute_change": change_info["absolute_change"],
                        "percentage_change": change_info["percentage_change"],
                        "is_significant": abs(change_info["percentage_change"]) >= (DataFetchConfig.PRICE_CHANGE_THRESHOLD * 100)
                    }
                    
                    if change_info["absolute_change"] != 0:
                        analysis["summary"]["markets_with_changes"] += 1
                    
                    if abs(change_info["percentage_change"]) >= (DataFetchConfig.PRICE_CHANGE_THRESHOLD * 100):
                        analysis["summary"]["significant_changes"] += 1
        
        return analysis
    
    def detect_significant_changes(self, price_analysis: Dict) -> List[Dict]:
        """
        检测显著的价格变化
        
        参数:
            price_analysis: 价格分析结果
            
        返回:
            显著变化列表
        """
        significant_changes = []
        
        for market_id, change_info in price_analysis.get("market_changes", {}).items():
            if change_info.get("is_significant", False):
                significant_changes.append({
                    "market_id": market_id,
                    "current_price": change_info["current_price"],
                    "last_price": change_info["last_price"],
                    "percentage_change": change_info["percentage_change"],
                    "timestamp": price_analysis["timestamp"]
                })
        
        return significant_changes
    
    def generate_price_report(self, market_ids: List[str] = None, 
                            days: int = None) -> Dict[str, Any]:
        """
        生成价格报告
        
        参数:
            market_ids: 要分析的市场ID列表
            days: 分析的天数
            
        返回:
            价格报告
        """
        days = days or DataFetchConfig.PRICE_HISTORY_DAYS
        
        self.logger.info(f"生成价格报告，分析 {days} 天的数据")
        
        report = {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_period_days": days,
            "markets_analyzed": [],
            "summary": {},
            "detailed_analysis": {}
        }
        
        # 如果没有指定市场ID，使用所有有历史数据的市场
        if not market_ids:
            market_ids = list(self.price_history.keys())
        
        report["markets_analyzed"] = market_ids
        
        # 分析每个市场
        for market_id in market_ids:
            if market_id in self.price_history:
                market_analysis = self.analyze_market_history(market_id, days)
                report["detailed_analysis"][market_id] = market_analysis
        
        # 生成总体摘要
        report["summary"] = self.generate_summary_statistics(report["detailed_analysis"])
        
        # 保存报告
        report_filename = f"price_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        self.data_manager.save_json(report, report_filename)
        
        self.logger.info(f"价格报告生成完成: {report_filename}")
        return report
    
    def analyze_market_history(self, market_id: str, days: int) -> Dict[str, Any]:
        """
        分析单个市场的历史数据
        
        参数:
            market_id: 市场ID
            days: 分析天数
            
        返回:
            市场分析结果
        """
        if market_id not in self.price_history:
            return {"error": "没有历史数据"}
        
        # 获取指定天数内的数据
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        recent_history = [
            record for record in self.price_history[market_id]
            if datetime.fromisoformat(record["timestamp"].replace('Z', '+00:00')) >= cutoff_time
        ]
        
        if not recent_history:
            return {"error": "指定时间范围内没有数据"}
        
        # 提取价格数据
        prices = []
        for record in recent_history:
            if "price" in record["price_data"]:
                try:
                    prices.append(float(record["price_data"]["price"]))
                except (ValueError, TypeError):
                    continue
        
        if not prices:
            return {"error": "没有有效的价格数据"}
        
        # 计算统计指标
        analysis = {
            "data_points": len(prices),
            "time_range": {
                "start": recent_history[0]["timestamp"],
                "end": recent_history[-1]["timestamp"]
            },
            "price_statistics": {
                "current": prices[-1],
                "min": min(prices),
                "max": max(prices),
                "average": sum(prices) / len(prices),
                "volatility": self.calculate_volatility(prices)
            },
            "price_changes": {
                "total_change": prices[-1] - prices[0],
                "total_change_percent": ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] != 0 else 0
            }
        }
        
        return analysis
    
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
    
    def generate_summary_statistics(self, detailed_analysis: Dict) -> Dict[str, Any]:
        """
        生成总体统计摘要
        
        参数:
            detailed_analysis: 详细分析结果
            
        返回:
            总体统计摘要
        """
        valid_analyses = [
            analysis for analysis in detailed_analysis.values()
            if "error" not in analysis
        ]
        
        if not valid_analyses:
            return {"error": "没有有效的分析数据"}
        
        # 收集所有价格变化
        price_changes = [
            analysis["price_changes"]["total_change_percent"]
            for analysis in valid_analyses
            if "price_changes" in analysis
        ]
        
        # 收集所有波动率
        volatilities = [
            analysis["price_statistics"]["volatility"]
            for analysis in valid_analyses
            if "price_statistics" in analysis and "volatility" in analysis["price_statistics"]
        ]
        
        summary = {
            "total_markets": len(detailed_analysis),
            "valid_markets": len(valid_analyses),
            "price_change_distribution": {
                "positive_changes": len([c for c in price_changes if c > 0]),
                "negative_changes": len([c for c in price_changes if c < 0]),
                "no_change": len([c for c in price_changes if c == 0])
            }
        }
        
        if price_changes:
            summary["price_change_statistics"] = {
                "average_change_percent": sum(price_changes) / len(price_changes),
                "max_increase_percent": max(price_changes),
                "max_decrease_percent": min(price_changes)
            }
        
        if volatilities:
            summary["volatility_statistics"] = {
                "average_volatility": sum(volatilities) / len(volatilities),
                "max_volatility": max(volatilities),
                "min_volatility": min(volatilities)
            }
        
        return summary

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="Polymarket价格数据收集器")
    
    parser.add_argument(
        "--mode",
        choices=["batch", "monitor", "report"],
        default="batch",
        help="运行模式: batch(批量收集), monitor(连续监控), report(生成报告)"
    )
    
    parser.add_argument(
        "--markets",
        nargs="+",
        help="市场ID列表"
    )
    
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="包含详细数据（订单簿、价差等）"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=DataFetchConfig.PRICE_UPDATE_INTERVAL,
        help="监控间隔（秒）"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=DataFetchConfig.PRICE_HISTORY_DAYS,
        help="报告分析天数"
    )
    
    args = parser.parse_args()
    
    # 初始化配置
    DataConfig.ensure_directories()
    
    # 创建收集器
    collector = PriceCollector()
    
    if args.mode == "batch":
        if not args.markets:
            print("批量模式需要指定市场ID列表")
            return
        
        print(f"开始批量收集 {len(args.markets)} 个市场的价格数据...")
        result = collector.collect_batch_prices(args.markets, args.detailed)
        
        print(f"\n=== 批量收集完成 ===")
        print(f"收集时间: {result['duration_seconds']:.2f} 秒")
        print(f"市场数量: {result['market_count']}")
        print(f"包含详细数据: {result['include_detailed']}")
        
    elif args.mode == "monitor":
        if not args.markets:
            print("监控模式需要指定市场ID列表")
            return
        
        print(f"开始监控 {len(args.markets)} 个市场，间隔 {args.interval} 秒...")
        print("按 Ctrl+C 停止监控")
        
        try:
            thread = collector.start_continuous_monitoring(args.markets, args.interval)
            thread.join()  # 等待监控线程结束
        except KeyboardInterrupt:
            collector.stop_monitoring()
            print("\n监控已停止")
        
    elif args.mode == "report":
        print(f"生成价格报告，分析 {args.days} 天的数据...")
        report = collector.generate_price_report(args.markets, args.days)
        
        print(f"\n=== 报告生成完成 ===")
        print(f"分析市场数量: {len(report['markets_analyzed'])}")
        print(f"分析天数: {report['analysis_period_days']}")
        if "summary" in report and "valid_markets" in report["summary"]:
            print(f"有效市场数量: {report['summary']['valid_markets']}")

if __name__ == "__main__":
    main() 
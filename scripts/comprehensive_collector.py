"""
综合数据收集器
整合所有数据收集模块，建立数据之间的关联关系
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone
import argparse
import asyncio
import threading
import time

# 添加当前目录到路径
sys.path.append(str(Path(__file__).parent))

from config import DataConfig, MarketTypes
from utils import Logger
from data_relationship_manager import DataRelationshipManager

# 导入各个收集器模块
from Poly_info.market_info_collector import MarketInfoCollector
from Poly_price_data.price_collector import PriceCollector
from Poly_order.order_collector import OrderCollector
from Poly_user_data.user_collector import UserCollector
from Poly_market_fluctuation.fluctuation_monitor import FluctuationMonitor

class ComprehensiveCollector:
    """综合数据收集器"""
    
    def __init__(self):
        """初始化综合数据收集器"""
        self.logger = Logger.setup_logger(
            "ComprehensiveCollector", 
            "comprehensive_collector.log"
        )
        
        # 初始化数据关联管理器
        self.relationship_manager = DataRelationshipManager()
        
        # 初始化各个收集器
        self.market_info_collector = MarketInfoCollector()
        self.price_collector = PriceCollector()
        self.order_collector = OrderCollector()
        self.user_collector = UserCollector()
        self.fluctuation_monitor = FluctuationMonitor()
        
        # 数据缓存
        self.collected_markets = set()
        self.collected_users = set()
        self.market_data_cache = {}
        
        self.logger.info("综合数据收集器初始化完成")
    
    def collect_test_data(self, max_markets: int = 3, max_users: int = 10, 
                         include_monitoring: bool = False, monitoring_duration: int = 5) -> Dict[str, Any]:
        """
        收集少量测试数据，用于验证系统可行性
        
        参数:
            max_markets: 最大市场数量（默认3个）
            max_users: 最大用户数量（默认10个）
            include_monitoring: 是否包含价格监控（默认关闭）
            monitoring_duration: 监控持续时间（分钟，默认5分钟）
            
        返回:
            测试收集结果摘要
        """
        self.logger.info(f"开始收集测试数据 - 最多{max_markets}个市场，{max_users}个用户")
        start_time = datetime.now(timezone.utc)
        
        test_summary = {
            "test_mode": True,
            "start_time": start_time.isoformat(),
            "max_markets": max_markets,
            "max_users": max_users,
            "include_monitoring": include_monitoring,
            "phases": {},
            "data_relationships": {},
            "errors": []
        }
        
        try:
            # 阶段1: 收集少量市场信息
            self.logger.info("阶段1: 收集少量市场信息")
            market_info_result = self._collect_test_market_info(max_markets)
            test_summary["phases"]["market_info"] = market_info_result
            
            # 提取测试市场ID
            test_market_ids = []
            if market_info_result.get("success"):
                events = market_info_result.get("events", [])
                for event in events[:max_markets]:  # 限制事件数量
                    markets = event.get("markets", [])
                    for market in markets[:1]:  # 每个事件只取第一个市场
                        market_id = market.get("id")
                        if market_id and market_id not in test_market_ids:
                            test_market_ids.append(market_id)
                            if len(test_market_ids) >= max_markets:
                                break
                    if len(test_market_ids) >= max_markets:
                        break
            
            self.collected_markets.update(test_market_ids)
            test_summary["test_market_ids"] = test_market_ids
            
            # 阶段2: 收集测试价格数据
            if test_market_ids:
                self.logger.info("阶段2: 收集测试价格数据")
                price_result = self._collect_price_data(test_market_ids)
                test_summary["phases"]["price_data"] = price_result
                
                # 阶段3: 收集测试订单数据
                self.logger.info("阶段3: 收集测试订单数据")
                order_result = self._collect_test_order_data(test_market_ids, max_orders_per_market=20)
                test_summary["phases"]["order_data"] = order_result
                
                # 阶段4: 收集测试用户数据
                self.logger.info("阶段4: 收集测试用户数据")
                user_result = self._collect_test_user_data_from_orders(order_result, max_users)
                test_summary["phases"]["user_data"] = user_result
                
                # 阶段5: 建立数据关联
                self.logger.info("阶段5: 建立数据关联")
                relationship_result = self._build_data_relationships(
                    market_info_result, price_result, order_result, user_result
                )
                test_summary["data_relationships"] = relationship_result
                
                # 阶段6: 测试价格监控（可选）
                if include_monitoring:
                    self.logger.info("阶段6: 启动测试价格监控")
                    monitoring_result = self._start_price_monitoring(test_market_ids, monitoring_duration)
                    test_summary["phases"]["price_monitoring"] = monitoring_result
            
            # 生成测试报告
            test_report = self._generate_test_report(test_summary)
            test_summary["test_report"] = test_report
            
        except Exception as e:
            self.logger.error(f"测试数据收集过程中发生错误: {e}")
            test_summary["errors"].append(str(e))
        
        end_time = datetime.now(timezone.utc)
        test_summary["end_time"] = end_time.isoformat()
        test_summary["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # 保存测试摘要
        summary_filename = f"test_collection_summary_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.relationship_manager.data_manager.save_json(test_summary, summary_filename)
        
        self.logger.info(f"测试数据收集完成，耗时 {test_summary['duration_seconds']:.2f} 秒")
        return test_summary
    
    def collect_market_ecosystem_data(self, market_ids: List[str] = None, 
                                    include_users: bool = True,
                                    include_price_monitoring: bool = False,
                                    monitoring_duration: int = None) -> Dict[str, Any]:
        """
        收集市场生态系统数据（市场信息、价格、订单、用户等）
        
        参数:
            market_ids: 指定的市场ID列表，如果为None则收集所有市场
            include_users: 是否包含用户数据收集
            include_price_monitoring: 是否包含价格监控
            monitoring_duration: 价格监控持续时间（分钟）
            
        返回:
            收集结果摘要
        """
        self.logger.info("开始收集市场生态系统数据")
        start_time = datetime.now(timezone.utc)
        
        collection_summary = {
            "start_time": start_time.isoformat(),
            "market_ids": market_ids,
            "include_users": include_users,
            "include_price_monitoring": include_price_monitoring,
            "phases": {},
            "data_relationships": {},
            "errors": []
        }
        
        try:
            # 阶段1: 收集市场基础信息
            self.logger.info("阶段1: 收集市场基础信息")
            market_info_result = self._collect_market_info(market_ids)
            collection_summary["phases"]["market_info"] = market_info_result
            
            # 从市场信息中提取实际的市场ID列表
            if not market_ids:
                market_ids = self._extract_market_ids_from_events(market_info_result.get("events", []))
            
            self.collected_markets.update(market_ids)
            
            # 阶段2: 收集价格数据
            self.logger.info("阶段2: 收集价格数据")
            price_result = self._collect_price_data(market_ids)
            collection_summary["phases"]["price_data"] = price_result
            
            # 阶段3: 收集订单和交易数据
            self.logger.info("阶段3: 收集订单和交易数据")
            order_result = self._collect_order_data(market_ids)
            collection_summary["phases"]["order_data"] = order_result
            
            # 阶段4: 提取并收集用户数据
            if include_users:
                self.logger.info("阶段4: 收集用户数据")
                user_result = self._collect_user_data_from_orders(order_result)
                collection_summary["phases"]["user_data"] = user_result
            
            # 阶段5: 建立数据关联
            self.logger.info("阶段5: 建立数据关联")
            relationship_result = self._build_data_relationships(
                market_info_result, price_result, order_result, 
                collection_summary["phases"].get("user_data")
            )
            collection_summary["data_relationships"] = relationship_result
            
            # 阶段6: 价格监控（可选）
            if include_price_monitoring and market_ids:
                self.logger.info("阶段6: 启动价格监控")
                monitoring_result = self._start_price_monitoring(market_ids, monitoring_duration)
                collection_summary["phases"]["price_monitoring"] = monitoring_result
            
            # 生成综合报告
            comprehensive_report = self.relationship_manager.export_comprehensive_report()
            collection_summary["comprehensive_report"] = comprehensive_report
            
        except Exception as e:
            self.logger.error(f"数据收集过程中发生错误: {e}")
            collection_summary["errors"].append(str(e))
        
        end_time = datetime.now(timezone.utc)
        collection_summary["end_time"] = end_time.isoformat()
        collection_summary["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # 保存收集摘要
        summary_filename = f"ecosystem_collection_summary_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.relationship_manager.data_manager.save_json(collection_summary, summary_filename)
        
        self.logger.info(f"市场生态系统数据收集完成，耗时 {collection_summary['duration_seconds']:.2f} 秒")
        return collection_summary
    
    def _collect_market_info(self, market_ids: List[str] = None) -> Dict[str, Any]:
        """收集市场信息"""
        try:
            # 收集事件和市场数据
            events = self.market_info_collector.fetch_all_events(MarketTypes.ACTIVE)
            markets = self.market_info_collector.fetch_markets(active=True)
            
            # 如果指定了特定市场，进行筛选
            if market_ids:
                filtered_events = []
                for event in events:
                    event_markets = event.get("markets", [])
                    if any(m.get("id") in market_ids for m in event_markets):
                        filtered_events.append(event)
                events = filtered_events
                
                markets = [m for m in markets if m.get("id") in market_ids]
            
            # 更新关联关系
            self.relationship_manager.update_market_relationships(events, markets)
            
            return {
                "events_count": len(events),
                "markets_count": len(markets),
                "events": events,
                "markets": markets,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"收集市场信息失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _collect_price_data(self, market_ids: List[str]) -> Dict[str, Any]:
        """收集价格数据（优先使用历史价格数据）"""
        try:
            # 首先尝试收集历史价格数据（使用可用的API端点）
            history_result = self.price_collector.collect_batch_price_history(market_ids, fidelity=60)  # 使用小时级数据
            
            # 如果历史数据收集成功，也尝试获取当前价格
            current_price_result = None
            try:
                current_price_result = self.price_collector.collect_batch_prices(market_ids, include_detailed=False)
            except Exception as e:
                self.logger.warning(f"获取当前价格失败，但历史数据收集成功: {e}")
            
            # 合并结果
            combined_result = {
                "history_data": history_result,
                "current_data": current_price_result,
                "successful_markets": history_result.get("successful_markets", []),
                "failed_markets": history_result.get("failed_markets", []),
                "duration_seconds": history_result.get("duration_seconds", 0)
            }
            
            # 更新价格快照（如果有当前价格数据）
            if current_price_result and "bulk_prices" in current_price_result:
                self.relationship_manager.update_market_price_snapshots(current_price_result["bulk_prices"])
            
            return {
                "success": True,
                "markets_count": len(market_ids),
                "successful_count": len(history_result.get("successful_markets", [])),
                "failed_count": len(history_result.get("failed_markets", [])),
                "success_rate": history_result.get("success_rate", 0),
                "duration": history_result.get("duration_seconds", 0),
                "price_data": combined_result
            }
            
        except Exception as e:
            self.logger.error(f"收集价格数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _collect_order_data(self, market_ids: List[str]) -> Dict[str, Any]:
        """收集订单数据"""
        try:
            all_orders = []
            all_trades = []
            
            # 为每个市场收集订单和交易数据
            for market_id in market_ids:
                orders = self.order_collector.fetch_all_orders(market_id)
                trades = self.order_collector.fetch_all_trades(market_id)
                
                all_orders.extend(orders)
                all_trades.extend(trades)
            
            return {
                "success": True,
                "orders_count": len(all_orders),
                "trades_count": len(all_trades),
                "orders": all_orders,
                "trades": all_trades
            }
            
        except Exception as e:
            self.logger.error(f"收集订单数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _collect_test_market_info(self, max_markets: int) -> Dict[str, Any]:
        """收集测试用的市场信息（限制数量）"""
        try:
            # 收集少量事件和市场数据
            events = self.market_info_collector.fetch_all_events(MarketTypes.ACTIVE)
            markets = self.market_info_collector.fetch_markets(active=True)
            
            # 限制数量
            events = events[:max_markets]
            markets = markets[:max_markets * 2]  # 市场数量稍多一些以确保有足够选择
            
            # 更新关联关系
            self.relationship_manager.update_market_relationships(events, markets)
            
            return {
                "events_count": len(events),
                "markets_count": len(markets),
                "events": events,
                "markets": markets,
                "success": True,
                "test_mode": True
            }
            
        except Exception as e:
            self.logger.error(f"收集测试市场信息失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _collect_test_order_data(self, market_ids: List[str], max_orders_per_market: int = 20) -> Dict[str, Any]:
        """收集测试用的订单数据（限制数量）"""
        try:
            all_orders = []
            all_trades = []
            
            # 为每个市场收集有限的订单和交易数据
            for market_id in market_ids:
                try:
                    orders = self.order_collector.fetch_all_orders(market_id)
                    trades = self.order_collector.fetch_all_trades(market_id)
                    
                    # 限制每个市场的数据量
                    orders = orders[:max_orders_per_market]
                    trades = trades[:max_orders_per_market]
                    
                    all_orders.extend(orders)
                    all_trades.extend(trades)
                    
                except Exception as e:
                    self.logger.warning(f"收集市场 {market_id} 的订单数据失败: {e}")
                    continue
            
            return {
                "success": True,
                "orders_count": len(all_orders),
                "trades_count": len(all_trades),
                "orders": all_orders,
                "trades": all_trades,
                "test_mode": True
            }
            
        except Exception as e:
            self.logger.error(f"收集测试订单数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _collect_test_user_data_from_orders(self, order_result: Dict[str, Any], max_users: int) -> Dict[str, Any]:
        """从订单数据中提取用户并收集测试用的用户数据（限制数量）"""
        try:
            if not order_result.get("success"):
                return {"success": False, "error": "订单数据收集失败"}
            
            # 提取用户地址
            user_addresses = set()
            
            for order in order_result.get("orders", []):
                if "maker" in order:
                    user_addresses.add(order["maker"])
                if "taker" in order:
                    user_addresses.add(order["taker"])
                
                # 限制用户数量
                if len(user_addresses) >= max_users:
                    break
            
            for trade in order_result.get("trades", []):
                if "maker" in trade:
                    user_addresses.add(trade["maker"])
                if "taker" in trade:
                    user_addresses.add(trade["taker"])
                
                # 限制用户数量
                if len(user_addresses) >= max_users:
                    break
            
            user_addresses = list(user_addresses)[:max_users]  # 确保不超过限制
            self.collected_users.update(user_addresses)
            
            # 批量收集用户数据
            user_batch_result = self.user_collector.batch_collect_users(user_addresses)
            
            # 更新用户市场活动
            for user_address, user_info in user_batch_result.get("users_data", {}).items():
                if user_info.get("success"):
                    # 加载用户数据文件
                    user_data_file = user_info.get("data_file")
                    if user_data_file:
                        user_data = self.user_collector.data_manager.load_json(user_data_file)
                        if user_data:
                            self.relationship_manager.update_user_market_activities(
                                user_data, 
                                order_result.get("orders", []),
                                order_result.get("trades", [])
                            )
            
            return {
                "success": True,
                "users_count": len(user_addresses),
                "batch_result": user_batch_result,
                "test_mode": True
            }
            
        except Exception as e:
            self.logger.error(f"收集测试用户数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_test_report(self, test_summary: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试报告"""
        try:
            report = {
                "test_summary": {
                    "total_duration": test_summary.get("duration_seconds", 0),
                    "markets_processed": len(test_summary.get("test_market_ids", [])),
                    "phases_completed": len([p for p in test_summary.get("phases", {}).values() if p.get("success")]),
                    "total_phases": len(test_summary.get("phases", {})),
                    "errors_count": len(test_summary.get("errors", []))
                },
                "data_collected": {},
                "system_status": "unknown",
                "recommendations": []
            }
            
            # 统计收集的数据
            phases = test_summary.get("phases", {})
            
            if "market_info" in phases and phases["market_info"].get("success"):
                report["data_collected"]["markets"] = phases["market_info"].get("markets_count", 0)
                report["data_collected"]["events"] = phases["market_info"].get("events_count", 0)
            
            if "price_data" in phases and phases["price_data"].get("success"):
                report["data_collected"]["price_markets"] = phases["price_data"].get("markets_count", 0)
            
            if "order_data" in phases and phases["order_data"].get("success"):
                report["data_collected"]["orders"] = phases["order_data"].get("orders_count", 0)
                report["data_collected"]["trades"] = phases["order_data"].get("trades_count", 0)
            
            if "user_data" in phases and phases["user_data"].get("success"):
                report["data_collected"]["users"] = phases["user_data"].get("users_count", 0)
            
            # 评估系统状态
            success_rate = report["test_summary"]["phases_completed"] / max(report["test_summary"]["total_phases"], 1)
            
            if success_rate >= 0.8 and report["test_summary"]["errors_count"] == 0:
                report["system_status"] = "excellent"
                report["recommendations"].append("系统运行良好，可以进行完整数据收集")
            elif success_rate >= 0.6:
                report["system_status"] = "good"
                report["recommendations"].append("系统基本正常，建议检查失败的阶段")
            elif success_rate >= 0.4:
                report["system_status"] = "fair"
                report["recommendations"].append("系统存在一些问题，建议先解决错误再进行大规模收集")
            else:
                report["system_status"] = "poor"
                report["recommendations"].append("系统存在严重问题，需要检查配置和网络连接")
            
            # 添加具体建议
            if report["test_summary"]["errors_count"] > 0:
                report["recommendations"].append("检查错误日志以了解具体问题")
            
            if report["data_collected"].get("users", 0) == 0:
                report["recommendations"].append("用户数据收集失败，可能需要检查订单数据或用户API")
            
            if report["test_summary"]["total_duration"] > 300:  # 5分钟
                report["recommendations"].append("测试耗时较长，完整收集可能需要更多时间")
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成测试报告失败: {e}")
            return {"error": str(e)}
    
    def _collect_user_data_from_orders(self, order_result: Dict[str, Any]) -> Dict[str, Any]:
        """从订单数据中提取用户并收集用户数据"""
        try:
            if not order_result.get("success"):
                return {"success": False, "error": "订单数据收集失败"}
            
            # 提取用户地址
            user_addresses = set()
            
            for order in order_result.get("orders", []):
                if "maker" in order:
                    user_addresses.add(order["maker"])
                if "taker" in order:
                    user_addresses.add(order["taker"])
            
            for trade in order_result.get("trades", []):
                if "maker" in trade:
                    user_addresses.add(trade["maker"])
                if "taker" in trade:
                    user_addresses.add(trade["taker"])
            
            user_addresses = list(user_addresses)[:50]  # 限制用户数量以避免过长时间
            self.collected_users.update(user_addresses)
            
            # 批量收集用户数据
            user_batch_result = self.user_collector.batch_collect_users(user_addresses)
            
            # 更新用户市场活动
            for user_address, user_info in user_batch_result.get("users_data", {}).items():
                if user_info.get("success"):
                    # 加载用户数据文件
                    user_data_file = user_info.get("data_file")
                    if user_data_file:
                        user_data = self.user_collector.data_manager.load_json(user_data_file)
                        if user_data:
                            self.relationship_manager.update_user_market_activities(
                                user_data, 
                                order_result.get("orders", []),
                                order_result.get("trades", [])
                            )
            
            return {
                "success": True,
                "users_count": len(user_addresses),
                "batch_result": user_batch_result
            }
            
        except Exception as e:
            self.logger.error(f"收集用户数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _build_data_relationships(self, market_info_result: Dict, price_result: Dict, 
                                order_result: Dict, user_result: Dict = None) -> Dict[str, Any]:
        """建立数据关联关系"""
        try:
            relationship_stats = {
                "markets_processed": 0,
                "users_processed": 0,
                "price_snapshots": 0,
                "relationships_created": 0
            }
            
            # 统计处理的数据量
            if market_info_result.get("success"):
                relationship_stats["markets_processed"] = market_info_result.get("markets_count", 0)
            
            if user_result and user_result.get("success"):
                relationship_stats["users_processed"] = user_result.get("users_count", 0)
            
            if price_result.get("success"):
                relationship_stats["price_snapshots"] = len(price_result.get("price_data", {}).get("bulk_prices", {}))
            
            # 计算关联关系数量
            relationship_stats["relationships_created"] = (
                relationship_stats["markets_processed"] * relationship_stats["users_processed"]
            )
            
            return {
                "success": True,
                "statistics": relationship_stats
            }
            
        except Exception as e:
            self.logger.error(f"建立数据关联失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _start_price_monitoring(self, market_ids: List[str], duration_minutes: int = None) -> Dict[str, Any]:
        """启动价格监控"""
        try:
            if duration_minutes:
                # 启动有限时间的监控
                monitoring_thread = self.fluctuation_monitor.start_background_monitoring(
                    market_ids, duration_minutes
                )
                
                return {
                    "success": True,
                    "monitoring_started": True,
                    "duration_minutes": duration_minutes,
                    "markets_count": len(market_ids)
                }
            else:
                return {
                    "success": True,
                    "monitoring_started": False,
                    "reason": "未指定监控时长"
                }
                
        except Exception as e:
            self.logger.error(f"启动价格监控失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_market_ids_from_events(self, events: List[Dict]) -> List[str]:
        """从事件数据中提取市场ID"""
        market_ids = set()
        
        for event in events:
            markets = event.get("markets", [])
            for market in markets:
                market_id = market.get("id")
                if market_id:
                    market_ids.add(market_id)
        
        return list(market_ids)
    
    def get_market_comprehensive_view(self, market_id: str) -> Dict[str, Any]:
        """
        获取市场的综合视图
        
        参数:
            market_id: 市场ID
            
        返回:
            市场综合视图数据
        """
        self.logger.info(f"获取市场 {market_id} 的综合视图")
        
        try:
            # 从关联管理器获取综合数据
            comprehensive_data = self.relationship_manager.get_market_comprehensive_data(market_id)
            
            # 添加实时数据
            current_prices = self.price_collector.fetch_market_prices([market_id])
            if current_prices and market_id in current_prices:
                comprehensive_data["current_price"] = current_prices[market_id]
            
            # 添加活跃订单
            active_orders = self.order_collector.fetch_active_orders(market_id)
            comprehensive_data["active_orders_count"] = len(active_orders)
            comprehensive_data["active_orders"] = active_orders[:10]  # 只显示前10个
            
            return comprehensive_data
            
        except Exception as e:
            self.logger.error(f"获取市场综合视图失败: {e}")
            return {"error": str(e)}
    
    def get_user_comprehensive_view(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户的综合视图
        
        参数:
            user_address: 用户地址
            
        返回:
            用户综合视图数据
        """
        self.logger.info(f"获取用户 {user_address} 的综合视图")
        
        try:
            # 从关联管理器获取综合数据
            comprehensive_data = self.relationship_manager.get_user_comprehensive_data(user_address)
            
            # 添加实时持仓信息
            current_positions = self.user_collector.fetch_user_positions(user_address)
            if current_positions:
                comprehensive_data["current_positions"] = current_positions
            
            # 添加最近订单
            recent_orders = self.user_collector.fetch_user_orders(user_address, limit=10)
            comprehensive_data["recent_orders"] = recent_orders
            
            return comprehensive_data
            
        except Exception as e:
            self.logger.error(f"获取用户综合视图失败: {e}")
            return {"error": str(e)}
    
    def get_market_correlations_analysis(self) -> Dict[str, Any]:
        """
        获取市场关联分析
        
        返回:
            市场关联分析结果
        """
        self.logger.info("获取市场关联分析")
        
        try:
            correlations = self.relationship_manager.get_market_correlations(limit=50)
            
            # 添加额外的分析
            analysis = {
                "correlations": correlations,
                "total_correlations": len(correlations),
                "strong_correlations": [c for c in correlations if c["common_users"] >= 10],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"获取市场关联分析失败: {e}")
            return {"error": str(e)}
    
    def export_ecosystem_report(self) -> Dict[str, Any]:
        """
        导出生态系统报告
        
        返回:
            生态系统报告
        """
        self.logger.info("导出生态系统报告")
        
        try:
            # 获取基础报告
            base_report = self.relationship_manager.export_comprehensive_report()
            
            # 添加额外的生态系统分析
            ecosystem_analysis = {
                "data_collection_status": {
                    "collected_markets": len(self.collected_markets),
                    "collected_users": len(self.collected_users),
                    "market_ids": list(self.collected_markets)[:20],  # 显示前20个
                    "user_addresses": list(self.collected_users)[:10]  # 显示前10个
                },
                "market_correlations": self.get_market_correlations_analysis(),
                "ecosystem_health": self._calculate_ecosystem_health()
            }
            
            # 合并报告
            base_report["ecosystem_analysis"] = ecosystem_analysis
            
            return base_report
            
        except Exception as e:
            self.logger.error(f"导出生态系统报告失败: {e}")
            return {"error": str(e)}
    
    def _calculate_ecosystem_health(self) -> Dict[str, Any]:
        """计算生态系统健康度"""
        try:
            health_metrics = {
                "market_activity_score": 0,
                "user_engagement_score": 0,
                "liquidity_score": 0,
                "overall_health": "unknown"
            }
            
            # 基于收集的数据计算健康度指标
            if self.collected_markets:
                health_metrics["market_activity_score"] = min(len(self.collected_markets) / 100, 1.0)
            
            if self.collected_users:
                health_metrics["user_engagement_score"] = min(len(self.collected_users) / 1000, 1.0)
            
            # 计算总体健康度
            avg_score = (
                health_metrics["market_activity_score"] + 
                health_metrics["user_engagement_score"] + 
                health_metrics["liquidity_score"]
            ) / 3
            
            if avg_score >= 0.8:
                health_metrics["overall_health"] = "excellent"
            elif avg_score >= 0.6:
                health_metrics["overall_health"] = "good"
            elif avg_score >= 0.4:
                health_metrics["overall_health"] = "fair"
            else:
                health_metrics["overall_health"] = "poor"
            
            return health_metrics
            
        except Exception as e:
            self.logger.error(f"计算生态系统健康度失败: {e}")
            return {"error": str(e)}

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="Polymarket综合数据收集器")
    
    parser.add_argument(
        "--mode",
        choices=["ecosystem", "test", "market-view", "user-view", "correlations", "report"],
        default="ecosystem",
        help="运行模式"
    )
    
    parser.add_argument(
        "--markets",
        nargs="+",
        help="指定的市场ID列表"
    )
    
    parser.add_argument(
        "--user",
        help="用户地址（用于用户视图模式）"
    )
    
    parser.add_argument(
        "--include-users",
        action="store_true",
        default=True,
        help="包含用户数据收集"
    )
    
    parser.add_argument(
        "--include-monitoring",
        action="store_true",
        help="包含价格监控"
    )
    
    parser.add_argument(
        "--monitoring-duration",
        type=int,
        default=30,
        help="价格监控持续时间（分钟）"
    )
    
    # 测试模式参数
    parser.add_argument(
        "--max-markets",
        type=int,
        default=3,
        help="测试模式：最大市场数量（默认3个）"
    )
    
    parser.add_argument(
        "--max-users",
        type=int,
        default=10,
        help="测试模式：最大用户数量（默认10个）"
    )
    
    args = parser.parse_args()
    
    # 初始化配置
    DataConfig.ensure_directories()
    
    # 创建综合收集器
    collector = ComprehensiveCollector()
    
    if args.mode == "ecosystem":
        print("开始收集市场生态系统数据...")
        result = collector.collect_market_ecosystem_data(
            market_ids=args.markets,
            include_users=args.include_users,
            include_price_monitoring=args.include_monitoring,
            monitoring_duration=args.monitoring_duration if args.include_monitoring else None
        )
        
        print(f"\n=== 生态系统数据收集完成 ===")
        print(f"收集时间: {result['duration_seconds']:.2f} 秒")
        print(f"市场数量: {len(result.get('market_ids', []))}")
        print(f"包含用户数据: {result['include_users']}")
        print(f"包含价格监控: {result['include_price_monitoring']}")
        
        for phase, phase_result in result.get("phases", {}).items():
            if phase_result.get("success"):
                print(f"✓ {phase}: 成功")
            else:
                print(f"✗ {phase}: 失败 - {phase_result.get('error', '未知错误')}")
    
    elif args.mode == "test":
        print("开始测试数据收集...")
        print(f"测试参数: 最多{args.max_markets}个市场, {args.max_users}个用户")
        
        result = collector.collect_test_data(
            max_markets=args.max_markets,
            max_users=args.max_users,
            include_monitoring=args.include_monitoring,
            monitoring_duration=args.monitoring_duration if args.include_monitoring else 5
        )
        
        print(f"\n=== 测试数据收集完成 ===")
        print(f"收集时间: {result['duration_seconds']:.2f} 秒")
        print(f"测试市场数: {len(result.get('test_market_ids', []))}")
        print(f"包含监控: {result['include_monitoring']}")
        
        # 显示各阶段结果
        for phase, phase_result in result.get("phases", {}).items():
            if phase_result.get("success"):
                print(f"✓ {phase}: 成功")
            else:
                print(f"✗ {phase}: 失败 - {phase_result.get('error', '未知错误')}")
        
        # 显示测试报告
        test_report = result.get("test_report", {})
        if test_report and "error" not in test_report:
            print(f"\n=== 测试报告 ===")
            summary = test_report.get("test_summary", {})
            print(f"阶段完成率: {summary.get('phases_completed', 0)}/{summary.get('total_phases', 0)}")
            print(f"错误数量: {summary.get('errors_count', 0)}")
            print(f"系统状态: {test_report.get('system_status', 'unknown')}")
            
            data_collected = test_report.get("data_collected", {})
            if data_collected:
                print(f"\n收集的数据:")
                print(f"  市场: {data_collected.get('markets', 0)}")
                print(f"  事件: {data_collected.get('events', 0)}")
                print(f"  订单: {data_collected.get('orders', 0)}")
                print(f"  交易: {data_collected.get('trades', 0)}")
                print(f"  用户: {data_collected.get('users', 0)}")
            
            recommendations = test_report.get("recommendations", [])
            if recommendations:
                print(f"\n建议:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"  {i}. {rec}")
        
    elif args.mode == "market-view":
        if not args.markets or len(args.markets) != 1:
            print("市场视图模式需要指定一个市场ID")
            return
        
        market_id = args.markets[0]
        print(f"获取市场 {market_id} 的综合视图...")
        
        view_data = collector.get_market_comprehensive_view(market_id)
        
        if "error" not in view_data:
            print(f"\n=== 市场 {market_id} 综合视图 ===")
            market_info = view_data.get("market_info", {})
            print(f"市场名称: {market_info.get('market_name', 'Unknown')}")
            print(f"市场状态: {market_info.get('market_status', 'Unknown')}")
            print(f"活跃用户数: {len(view_data.get('active_users', []))}")
            print(f"最近价格数据: {len(view_data.get('recent_prices', []))} 条")
            print(f"活跃订单数: {view_data.get('active_orders_count', 0)}")
        else:
            print(f"获取市场视图失败: {view_data['error']}")
        
    elif args.mode == "user-view":
        if not args.user:
            print("用户视图模式需要指定用户地址")
            return
        
        print(f"获取用户 {args.user} 的综合视图...")
        
        view_data = collector.get_user_comprehensive_view(args.user)
        
        if "error" not in view_data:
            print(f"\n=== 用户 {args.user} 综合视图 ===")
            trading_summary = view_data.get("trading_summary", {})
            print(f"活跃市场数: {trading_summary.get('active_markets', 0)}")
            print(f"总订单数: {trading_summary.get('total_orders', 0)}")
            print(f"总交易数: {trading_summary.get('total_trades', 0)}")
            print(f"总交易量: {trading_summary.get('total_volume', 0)}")
            print(f"持仓价值: {trading_summary.get('total_position_value', 0)}")
        else:
            print(f"获取用户视图失败: {view_data['error']}")
        
    elif args.mode == "correlations":
        print("获取市场关联分析...")
        
        correlations = collector.get_market_correlations_analysis()
        
        if "error" not in correlations:
            print(f"\n=== 市场关联分析 ===")
            print(f"总关联数: {correlations['total_correlations']}")
            print(f"强关联数: {len(correlations['strong_correlations'])}")
            
            print("\n前10个市场关联:")
            for i, corr in enumerate(correlations["correlations"][:10], 1):
                print(f"{i}. {corr['market1_name']} <-> {corr['market2_name']}")
                print(f"   共同用户: {corr['common_users']}, 平均交易量: {corr['avg_combined_volume']:.2f}")
        else:
            print(f"获取关联分析失败: {correlations['error']}")
        
    elif args.mode == "report":
        print("导出生态系统报告...")
        
        report = collector.export_ecosystem_report()
        
        if "error" not in report:
            print(f"\n=== 生态系统报告 ===")
            summary = report.get("summary", {})
            print(f"总市场数: {summary.get('total_markets', 0)}")
            print(f"总用户数: {summary.get('total_users', 0)}")
            print(f"总交易量: {summary.get('total_volume', 0)}")
            
            ecosystem = report.get("ecosystem_analysis", {})
            collection_status = ecosystem.get("data_collection_status", {})
            print(f"已收集市场数: {collection_status.get('collected_markets', 0)}")
            print(f"已收集用户数: {collection_status.get('collected_users', 0)}")
            
            health = ecosystem.get("ecosystem_health", {})
            print(f"生态系统健康度: {health.get('overall_health', 'unknown')}")
        else:
            print(f"导出报告失败: {report['error']}")

if __name__ == "__main__":
    main() 
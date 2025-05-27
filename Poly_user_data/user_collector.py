"""
用户数据收集器
用于获取Polymarket的用户持仓、交易历史等数据
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
import argparse

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config import APIConfig, DataConfig, DataFetchConfig
from utils import HTTPClient, DataManager, Logger, RateLimiter, format_timestamp

class UserCollector:
    """用户数据收集器"""
    
    def __init__(self):
        """初始化用户数据收集器"""
        self.logger = Logger.setup_logger(
            "UserCollector", 
            "user_data.log"
        )
        
        # 初始化HTTP客户端
        self.clob_client = HTTPClient(APIConfig.CLOB_BASE_URL, self.logger)
        
        # 初始化数据管理器
        self.data_manager = DataManager(DataConfig.USER_DATA_DIR, self.logger)
        
        # 初始化频率限制器
        self.rate_limiter = RateLimiter()
        
        self.logger.info("用户数据收集器初始化完成")
    
    def fetch_user_positions(self, user_address: str) -> Optional[Dict]:
        """
        获取用户持仓信息
        
        参数:
            user_address: 用户地址
            
        返回:
            用户持仓数据
        """
        self.logger.info(f"获取用户持仓: {user_address}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get(f"/positions", params={"user": user_address})
        
        if response:
            self.logger.info(f"成功获取用户 {user_address} 的持仓信息")
            return response
        
        self.logger.warning(f"获取用户 {user_address} 持仓信息失败")
        return None
    
    def fetch_user_orders(self, user_address: str, limit: int = None, 
                         offset: int = 0) -> List[Dict]:
        """
        获取用户订单历史
        
        参数:
            user_address: 用户地址
            limit: 每页数量
            offset: 分页偏移量
            
        返回:
            用户订单列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        params = {
            "maker": user_address,
            "limit": limit,
            "offset": offset
        }
        
        self.logger.info(f"获取用户订单历史: {user_address}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get("/orders", params=params)
        
        if response:
            # 处理响应格式
            if isinstance(response, dict) and "data" in response:
                orders = response["data"]
            elif isinstance(response, list):
                orders = response
            else:
                self.logger.warning(f"未知的订单响应格式: {type(response)}")
                orders = []
            
            self.logger.info(f"成功获取用户 {user_address} 的 {len(orders)} 个订单")
            return orders
        
        self.logger.error(f"获取用户 {user_address} 订单历史失败")
        return []
    
    def fetch_user_trades(self, user_address: str, limit: int = None, 
                         offset: int = 0) -> List[Dict]:
        """
        获取用户交易历史
        
        参数:
            user_address: 用户地址
            limit: 每页数量
            offset: 分页偏移量
            
        返回:
            用户交易列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        # 获取作为maker的交易
        maker_params = {
            "maker": user_address,
            "limit": limit,
            "offset": offset
        }
        
        # 获取作为taker的交易
        taker_params = {
            "taker": user_address,
            "limit": limit,
            "offset": offset
        }
        
        self.logger.info(f"获取用户交易历史: {user_address}")
        
        all_trades = []
        
        # 获取作为maker的交易
        self.rate_limiter.wait()
        maker_response = self.clob_client.get("/trades", params=maker_params)
        if maker_response:
            if isinstance(maker_response, dict) and "data" in maker_response:
                maker_trades = maker_response["data"]
            elif isinstance(maker_response, list):
                maker_trades = maker_response
            else:
                maker_trades = []
            
            for trade in maker_trades:
                trade["user_role"] = "maker"
            all_trades.extend(maker_trades)
        
        # 获取作为taker的交易
        self.rate_limiter.wait()
        taker_response = self.clob_client.get("/trades", params=taker_params)
        if taker_response:
            if isinstance(taker_response, dict) and "data" in taker_response:
                taker_trades = taker_response["data"]
            elif isinstance(taker_response, list):
                taker_trades = taker_response
            else:
                taker_trades = []
            
            for trade in taker_trades:
                trade["user_role"] = "taker"
            all_trades.extend(taker_trades)
        
        # 去重（同一笔交易可能在maker和taker中都出现）
        unique_trades = {}
        for trade in all_trades:
            trade_id = trade.get("id")
            if trade_id and trade_id not in unique_trades:
                unique_trades[trade_id] = trade
        
        final_trades = list(unique_trades.values())
        self.logger.info(f"成功获取用户 {user_address} 的 {len(final_trades)} 条交易记录")
        return final_trades
    
    def collect_comprehensive_user_data(self, user_address: str) -> Dict[str, Any]:
        """
        收集用户的综合数据
        
        参数:
            user_address: 用户地址
            
        返回:
            用户综合数据
        """
        self.logger.info(f"开始收集用户 {user_address} 的综合数据")
        
        start_time = datetime.now(timezone.utc)
        
        user_data = {
            "user_address": user_address,
            "collection_timestamp": start_time.isoformat(),
            "positions": None,
            "orders": [],
            "trades": [],
            "statistics": {}
        }
        
        # 获取持仓信息
        positions = self.fetch_user_positions(user_address)
        if positions:
            user_data["positions"] = positions
        
        # 获取所有订单（分页获取）
        all_orders = []
        offset = 0
        while True:
            orders = self.fetch_user_orders(user_address, offset=offset)
            if not orders:
                break
            all_orders.extend(orders)
            offset += DataFetchConfig.MARKETS_BATCH_SIZE
            
            # 如果获取的订单数量少于请求数量，说明已经到达末尾
            if len(orders) < DataFetchConfig.MARKETS_BATCH_SIZE:
                break
        
        user_data["orders"] = all_orders
        
        # 获取所有交易（分页获取）
        all_trades = []
        offset = 0
        while True:
            trades = self.fetch_user_trades(user_address, offset=offset)
            if not trades:
                break
            all_trades.extend(trades)
            offset += DataFetchConfig.MARKETS_BATCH_SIZE
            
            # 如果获取的交易数量少于请求数量，说明已经到达末尾
            if len(trades) < DataFetchConfig.MARKETS_BATCH_SIZE:
                break
        
        user_data["trades"] = all_trades
        
        # 生成统计信息
        user_data["statistics"] = self.generate_user_statistics(user_data)
        
        end_time = datetime.now(timezone.utc)
        user_data["completion_timestamp"] = end_time.isoformat()
        user_data["collection_duration_seconds"] = (end_time - start_time).total_seconds()
        
        # 保存用户数据
        filename = f"user_data_{user_address}_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.data_manager.save_json(user_data, filename)
        
        self.logger.info(f"用户 {user_address} 综合数据收集完成")
        return user_data
    
    def generate_user_statistics(self, user_data: Dict) -> Dict[str, Any]:
        """
        生成用户统计信息
        
        参数:
            user_data: 用户数据
            
        返回:
            用户统计信息
        """
        statistics = {
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "order_statistics": {},
            "trade_statistics": {},
            "position_statistics": {},
            "activity_analysis": {}
        }
        
        # 订单统计
        orders = user_data.get("orders", [])
        if orders:
            statistics["order_statistics"] = {
                "total_orders": len(orders),
                "status_distribution": {},
                "side_distribution": {},
                "market_distribution": {},
                "price_range": {},
                "size_statistics": {}
            }
            
            prices = []
            sizes = []
            
            for order in orders:
                # 状态分布
                status = order.get("status", "unknown")
                statistics["order_statistics"]["status_distribution"][status] = \
                    statistics["order_statistics"]["status_distribution"].get(status, 0) + 1
                
                # 买卖方向分布
                side = order.get("side", "unknown")
                statistics["order_statistics"]["side_distribution"][side] = \
                    statistics["order_statistics"]["side_distribution"].get(side, 0) + 1
                
                # 市场分布
                market = order.get("market", "unknown")
                statistics["order_statistics"]["market_distribution"][market] = \
                    statistics["order_statistics"]["market_distribution"].get(market, 0) + 1
                
                # 收集价格和数量
                if "price" in order:
                    try:
                        prices.append(float(order["price"]))
                    except (ValueError, TypeError):
                        pass
                
                if "size" in order:
                    try:
                        sizes.append(float(order["size"]))
                    except (ValueError, TypeError):
                        pass
            
            # 价格统计
            if prices:
                statistics["order_statistics"]["price_range"] = {
                    "min": min(prices),
                    "max": max(prices),
                    "average": sum(prices) / len(prices)
                }
            
            # 数量统计
            if sizes:
                statistics["order_statistics"]["size_statistics"] = {
                    "min": min(sizes),
                    "max": max(sizes),
                    "average": sum(sizes) / len(sizes),
                    "total": sum(sizes)
                }
        
        # 交易统计
        trades = user_data.get("trades", [])
        if trades:
            statistics["trade_statistics"] = {
                "total_trades": len(trades),
                "role_distribution": {},
                "market_distribution": {},
                "volume_statistics": {},
                "pnl_analysis": {}
            }
            
            volumes = []
            
            for trade in trades:
                # 角色分布
                role = trade.get("user_role", "unknown")
                statistics["trade_statistics"]["role_distribution"][role] = \
                    statistics["trade_statistics"]["role_distribution"].get(role, 0) + 1
                
                # 市场分布
                market = trade.get("market", "unknown")
                statistics["trade_statistics"]["market_distribution"][market] = \
                    statistics["trade_statistics"]["market_distribution"].get(market, 0) + 1
                
                # 收集交易量
                if "volume" in trade:
                    try:
                        volumes.append(float(trade["volume"]))
                    except (ValueError, TypeError):
                        pass
            
            # 交易量统计
            if volumes:
                statistics["trade_statistics"]["volume_statistics"] = {
                    "min": min(volumes),
                    "max": max(volumes),
                    "average": sum(volumes) / len(volumes),
                    "total": sum(volumes)
                }
        
        # 持仓统计
        positions = user_data.get("positions")
        if positions and isinstance(positions, dict):
            statistics["position_statistics"] = {
                "total_positions": len(positions.get("positions", [])),
                "total_value": 0,
                "market_exposure": {}
            }
            
            # 分析持仓
            for position in positions.get("positions", []):
                market = position.get("market", "unknown")
                value = position.get("value", 0)
                
                try:
                    value = float(value)
                    statistics["position_statistics"]["total_value"] += value
                    statistics["position_statistics"]["market_exposure"][market] = \
                        statistics["position_statistics"]["market_exposure"].get(market, 0) + value
                except (ValueError, TypeError):
                    pass
        
        # 活动分析
        statistics["activity_analysis"] = {
            "is_active_trader": len(trades) > 10,
            "is_active_maker": len([o for o in orders if o.get("side") == "maker"]) > 5,
            "preferred_markets": [],
            "trading_frequency": "low"
        }
        
        # 分析偏好市场
        all_markets = {}
        for order in orders:
            market = order.get("market", "unknown")
            all_markets[market] = all_markets.get(market, 0) + 1
        
        for trade in trades:
            market = trade.get("market", "unknown")
            all_markets[market] = all_markets.get(market, 0) + 1
        
        # 获取前3个最活跃的市场
        sorted_markets = sorted(all_markets.items(), key=lambda x: x[1], reverse=True)
        statistics["activity_analysis"]["preferred_markets"] = [
            {"market": market, "activity_count": count} 
            for market, count in sorted_markets[:3]
        ]
        
        # 判断交易频率
        total_activity = len(orders) + len(trades)
        if total_activity > 100:
            statistics["activity_analysis"]["trading_frequency"] = "high"
        elif total_activity > 20:
            statistics["activity_analysis"]["trading_frequency"] = "medium"
        
        return statistics
    
    def batch_collect_users(self, user_addresses: List[str]) -> Dict[str, Any]:
        """
        批量收集多个用户的数据
        
        参数:
            user_addresses: 用户地址列表
            
        返回:
            批量收集结果
        """
        self.logger.info(f"开始批量收集 {len(user_addresses)} 个用户的数据")
        
        start_time = datetime.now(timezone.utc)
        
        batch_result = {
            "collection_timestamp": start_time.isoformat(),
            "total_users": len(user_addresses),
            "successful_collections": 0,
            "failed_collections": 0,
            "users_data": {},
            "summary_statistics": {}
        }
        
        for i, user_address in enumerate(user_addresses):
            self.logger.info(f"处理用户 {i+1}/{len(user_addresses)}: {user_address}")
            
            try:
                user_data = self.collect_comprehensive_user_data(user_address)
                batch_result["users_data"][user_address] = {
                    "success": True,
                    "data_file": f"user_data_{user_address}_{start_time.strftime('%Y%m%d_%H%M%S')}.json",
                    "summary": {
                        "orders_count": len(user_data.get("orders", [])),
                        "trades_count": len(user_data.get("trades", [])),
                        "positions_count": len(user_data.get("positions", {}).get("positions", [])) if user_data.get("positions") else 0
                    }
                }
                batch_result["successful_collections"] += 1
                
            except Exception as e:
                self.logger.error(f"收集用户 {user_address} 数据失败: {e}")
                batch_result["users_data"][user_address] = {
                    "success": False,
                    "error": str(e)
                }
                batch_result["failed_collections"] += 1
        
        end_time = datetime.now(timezone.utc)
        batch_result["completion_timestamp"] = end_time.isoformat()
        batch_result["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # 生成汇总统计
        batch_result["summary_statistics"] = self.generate_batch_summary(batch_result)
        
        # 保存批量结果
        batch_filename = f"batch_user_collection_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.data_manager.save_json(batch_result, batch_filename)
        
        self.logger.info(f"批量用户数据收集完成，成功: {batch_result['successful_collections']}, 失败: {batch_result['failed_collections']}")
        return batch_result
    
    def generate_batch_summary(self, batch_result: Dict) -> Dict[str, Any]:
        """
        生成批量收集的汇总统计
        
        参数:
            batch_result: 批量收集结果
            
        返回:
            汇总统计
        """
        summary = {
            "total_orders": 0,
            "total_trades": 0,
            "total_positions": 0,
            "active_users": 0,
            "user_activity_distribution": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        for user_address, user_info in batch_result.get("users_data", {}).items():
            if user_info.get("success"):
                user_summary = user_info.get("summary", {})
                summary["total_orders"] += user_summary.get("orders_count", 0)
                summary["total_trades"] += user_summary.get("trades_count", 0)
                summary["total_positions"] += user_summary.get("positions_count", 0)
                
                # 判断用户活跃度
                total_activity = user_summary.get("orders_count", 0) + user_summary.get("trades_count", 0)
                if total_activity > 0:
                    summary["active_users"] += 1
                
                if total_activity > 100:
                    summary["user_activity_distribution"]["high"] += 1
                elif total_activity > 20:
                    summary["user_activity_distribution"]["medium"] += 1
                else:
                    summary["user_activity_distribution"]["low"] += 1
        
        return summary

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="Polymarket用户数据收集器")
    
    parser.add_argument(
        "--mode",
        choices=["single", "batch"],
        default="single",
        help="收集模式: single(单个用户), batch(批量用户)"
    )
    
    parser.add_argument(
        "--user",
        help="用户地址（单个用户模式）"
    )
    
    parser.add_argument(
        "--users-file",
        help="包含用户地址列表的文件路径（批量模式）"
    )
    
    parser.add_argument(
        "--users",
        nargs="+",
        help="用户地址列表（批量模式）"
    )
    
    args = parser.parse_args()
    
    # 初始化配置
    DataConfig.ensure_directories()
    
    # 创建收集器
    collector = UserCollector()
    
    if args.mode == "single":
        if not args.user:
            print("单个用户模式需要指定用户地址")
            return
        
        print(f"开始收集用户 {args.user} 的数据...")
        user_data = collector.collect_comprehensive_user_data(args.user)
        
        print(f"\n=== 用户数据收集完成 ===")
        print(f"用户地址: {user_data['user_address']}")
        print(f"收集时间: {user_data['collection_duration_seconds']:.2f} 秒")
        print(f"订单数量: {len(user_data['orders'])}")
        print(f"交易数量: {len(user_data['trades'])}")
        if user_data['positions']:
            print(f"持仓数量: {len(user_data['positions'].get('positions', []))}")
        
    elif args.mode == "batch":
        user_addresses = []
        
        if args.users_file:
            # 从文件读取用户地址
            try:
                with open(args.users_file, 'r') as f:
                    user_addresses = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                print(f"文件不存在: {args.users_file}")
                return
        elif args.users:
            user_addresses = args.users
        else:
            print("批量模式需要指定用户地址列表或文件")
            return
        
        print(f"开始批量收集 {len(user_addresses)} 个用户的数据...")
        batch_result = collector.batch_collect_users(user_addresses)
        
        print(f"\n=== 批量收集完成 ===")
        print(f"总用户数: {batch_result['total_users']}")
        print(f"成功收集: {batch_result['successful_collections']}")
        print(f"失败收集: {batch_result['failed_collections']}")
        print(f"收集时间: {batch_result['duration_seconds']:.2f} 秒")
        
        summary = batch_result.get('summary_statistics', {})
        if summary:
            print(f"总订单数: {summary.get('total_orders', 0)}")
            print(f"总交易数: {summary.get('total_trades', 0)}")
            print(f"活跃用户: {summary.get('active_users', 0)}")

if __name__ == "__main__":
    main() 
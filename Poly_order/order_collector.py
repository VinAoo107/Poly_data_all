"""
订单数据收集器
用于获取Polymarket的订单信息、交易记录等数据
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
import argparse
import time

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config import APIConfig, DataConfig, DataFetchConfig, OrderStatus, TradeStatus
from utils import HTTPClient, DataManager, Logger, RateLimiter, format_timestamp, validate_market_id

class OrderCollector:
    """订单数据收集器"""
    
    def __init__(self):
        """初始化订单数据收集器"""
        self.logger = Logger.setup_logger(
            "OrderCollector", 
            "order_data.log"
        )
        
        # 初始化HTTP客户端
        self.clob_client = HTTPClient(APIConfig.CLOB_BASE_URL, self.logger)
        
        # 初始化数据管理器
        self.data_manager = DataManager(DataConfig.ORDER_DATA_DIR, self.logger)
        
        # 初始化频率限制器
        self.rate_limiter = RateLimiter()
        
        self.logger.info("订单数据收集器初始化完成")
    
    def fetch_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        根据订单ID获取订单详情
        
        参数:
            order_id: 订单ID
            
        返回:
            订单详情
        """
        self.logger.info(f"获取订单详情: {order_id}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get(f"/order/{order_id}")
        
        if response:
            self.logger.info(f"成功获取订单 {order_id} 的详情")
            return response
        
        self.logger.warning(f"获取订单 {order_id} 详情失败")
        return None
    
    def fetch_orders(self, market: str = None, maker: str = None, 
                    taker: str = None, status: str = None,
                    limit: int = None, offset: int = 0) -> List[Dict]:
        """
        获取订单列表
        
        参数:
            market: 市场ID
            maker: 做市商地址
            taker: 接受者地址
            status: 订单状态
            limit: 每页数量
            offset: 分页偏移量
            
        返回:
            订单列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # 添加筛选条件
        if market:
            params["market"] = market
        if maker:
            params["maker"] = maker
        if taker:
            params["taker"] = taker
        if status:
            params["status"] = status
        
        self.logger.info(f"获取订单列表，参数: {params}")
        
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
            
            self.logger.info(f"成功获取 {len(orders)} 个订单")
            return orders
        
        self.logger.error("获取订单列表失败")
        return []
    
    def fetch_active_orders(self, market: str = None, maker: str = None) -> List[Dict]:
        """
        获取活跃订单
        
        参数:
            market: 市场ID
            maker: 做市商地址
            
        返回:
            活跃订单列表
        """
        self.logger.info(f"获取活跃订单，市场: {market}, 做市商: {maker}")
        
        params = {}
        if market:
            params["market"] = market
        if maker:
            params["maker"] = maker
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get("/orders/active", params=params)
        
        if response:
            # 处理响应格式
            if isinstance(response, dict) and "data" in response:
                orders = response["data"]
            elif isinstance(response, list):
                orders = response
            else:
                self.logger.warning(f"未知的活跃订单响应格式: {type(response)}")
                orders = []
            
            self.logger.info(f"成功获取 {len(orders)} 个活跃订单")
            return orders
        
        self.logger.error("获取活跃订单失败")
        return []
    
    def fetch_trades(self, market: str = None, maker: str = None, 
                    taker: str = None, limit: int = None, 
                    offset: int = 0) -> List[Dict]:
        """
        获取交易记录
        
        参数:
            market: 市场ID
            maker: 做市商地址
            taker: 接受者地址
            limit: 每页数量
            offset: 分页偏移量
            
        返回:
            交易记录列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # 添加筛选条件
        if market:
            params["market"] = market
        if maker:
            params["maker"] = maker
        if taker:
            params["taker"] = taker
        
        self.logger.info(f"获取交易记录，参数: {params}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.clob_client.get("/trades", params=params)
        
        if response:
            # 处理响应格式
            if isinstance(response, dict) and "data" in response:
                trades = response["data"]
            elif isinstance(response, list):
                trades = response
            else:
                self.logger.warning(f"未知的交易响应格式: {type(response)}")
                trades = []
            
            self.logger.info(f"成功获取 {len(trades)} 条交易记录")
            return trades
        
        self.logger.error("获取交易记录失败")
        return []
    
    def fetch_all_orders(self, market: str = None, status: str = None) -> List[Dict]:
        """
        获取所有订单（分页获取）
        
        参数:
            market: 市场ID
            status: 订单状态
            
        返回:
            所有订单列表
        """
        self.logger.info(f"开始获取所有订单，市场: {market}, 状态: {status}")
        
        # 加载已有进度
        progress_key = f"orders_{market or 'all'}_{status or 'all'}"
        progress_file = f"{progress_key}_progress.json"
        progress = self.data_manager.load_progress(progress_file)
        
        if progress:
            all_orders = progress.get("orders", [])
            offset = progress.get("offset", 0)
            self.logger.info(f"从进度文件恢复: {len(all_orders)} 个订单, offset={offset}")
        else:
            all_orders = []
            offset = 0
        
        try:
            while True:
                # 获取一批订单
                orders = self.fetch_orders(
                    market=market,
                    status=status,
                    limit=DataFetchConfig.MARKETS_BATCH_SIZE,
                    offset=offset
                )
                
                if not orders:
                    self.logger.info("没有更多订单数据")
                    break
                
                # 去重处理
                if all_orders:
                    existing_ids = set(o.get("id") for o in all_orders if o.get("id"))
                    new_orders = [o for o in orders if o.get("id") not in existing_ids]
                    
                    if len(new_orders) < len(orders):
                        self.logger.info(f"过滤掉 {len(orders) - len(new_orders)} 个重复订单")
                else:
                    new_orders = orders
                
                # 添加新订单
                all_orders.extend(new_orders)
                offset += DataFetchConfig.MARKETS_BATCH_SIZE
                
                self.logger.info(f"新增 {len(new_orders)} 个订单，总计: {len(all_orders)} 个")
                
                # 保存进度
                progress_data = {
                    "orders": all_orders,
                    "offset": offset,
                    "market": market,
                    "status": status,
                    "last_update": datetime.now(timezone.utc).isoformat()
                }
                self.data_manager.save_progress(progress_data, progress_file)
                
                # 如果获取的订单数量少于请求数量，说明已经到达末尾
                if len(orders) < DataFetchConfig.MARKETS_BATCH_SIZE:
                    self.logger.info("已获取所有可用订单")
                    break
                
        except KeyboardInterrupt:
            self.logger.info("用户中断，保存当前进度")
            progress_data = {
                "orders": all_orders,
                "offset": offset,
                "market": market,
                "status": status,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
            self.data_manager.save_progress(progress_data, progress_file)
        
        # 保存最终结果
        result_file = f"{progress_key}_final.json"
        self.data_manager.save_json(all_orders, result_file)
        
        self.logger.info(f"完成! 共获取 {len(all_orders)} 个订单")
        return all_orders
    
    def fetch_all_trades(self, market: str = None) -> List[Dict]:
        """
        获取所有交易记录（分页获取）
        
        参数:
            market: 市场ID
            
        返回:
            所有交易记录列表
        """
        self.logger.info(f"开始获取所有交易记录，市场: {market}")
        
        # 加载已有进度
        progress_key = f"trades_{market or 'all'}"
        progress_file = f"{progress_key}_progress.json"
        progress = self.data_manager.load_progress(progress_file)
        
        if progress:
            all_trades = progress.get("trades", [])
            offset = progress.get("offset", 0)
            self.logger.info(f"从进度文件恢复: {len(all_trades)} 条交易记录, offset={offset}")
        else:
            all_trades = []
            offset = 0
        
        try:
            while True:
                # 获取一批交易记录
                trades = self.fetch_trades(
                    market=market,
                    limit=DataFetchConfig.MARKETS_BATCH_SIZE,
                    offset=offset
                )
                
                if not trades:
                    self.logger.info("没有更多交易记录")
                    break
                
                # 去重处理
                if all_trades:
                    existing_ids = set(t.get("id") for t in all_trades if t.get("id"))
                    new_trades = [t for t in trades if t.get("id") not in existing_ids]
                    
                    if len(new_trades) < len(trades):
                        self.logger.info(f"过滤掉 {len(trades) - len(new_trades)} 条重复交易记录")
                else:
                    new_trades = trades
                
                # 添加新交易记录
                all_trades.extend(new_trades)
                offset += DataFetchConfig.MARKETS_BATCH_SIZE
                
                self.logger.info(f"新增 {len(new_trades)} 条交易记录，总计: {len(all_trades)} 条")
                
                # 保存进度
                progress_data = {
                    "trades": all_trades,
                    "offset": offset,
                    "market": market,
                    "last_update": datetime.now(timezone.utc).isoformat()
                }
                self.data_manager.save_progress(progress_data, progress_file)
                
                # 如果获取的交易记录数量少于请求数量，说明已经到达末尾
                if len(trades) < DataFetchConfig.MARKETS_BATCH_SIZE:
                    self.logger.info("已获取所有可用交易记录")
                    break
                
        except KeyboardInterrupt:
            self.logger.info("用户中断，保存当前进度")
            progress_data = {
                "trades": all_trades,
                "offset": offset,
                "market": market,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
            self.data_manager.save_progress(progress_data, progress_file)
        
        # 保存最终结果
        result_file = f"{progress_key}_final.json"
        self.data_manager.save_json(all_trades, result_file)
        
        self.logger.info(f"完成! 共获取 {len(all_trades)} 条交易记录")
        return all_trades
    
    def analyze_orders(self, orders: List[Dict]) -> Dict[str, Any]:
        """
        分析订单数据
        
        参数:
            orders: 订单列表
            
        返回:
            订单分析结果
        """
        if not orders:
            return {"error": "没有订单数据可分析"}
        
        analysis = {
            "total_orders": len(orders),
            "status_distribution": {},
            "side_distribution": {},
            "market_distribution": {},
            "maker_distribution": {},
            "price_statistics": {},
            "size_statistics": {},
            "time_analysis": {},
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 收集数据用于分析
        prices = []
        sizes = []
        timestamps = []
        
        # 统计各种分布
        for order in orders:
            # 状态分布
            status = order.get("status", "unknown")
            analysis["status_distribution"][status] = analysis["status_distribution"].get(status, 0) + 1
            
            # 买卖方向分布
            side = order.get("side", "unknown")
            analysis["side_distribution"][side] = analysis["side_distribution"].get(side, 0) + 1
            
            # 市场分布
            market = order.get("market", "unknown")
            analysis["market_distribution"][market] = analysis["market_distribution"].get(market, 0) + 1
            
            # 做市商分布
            maker = order.get("maker", "unknown")
            analysis["maker_distribution"][maker] = analysis["maker_distribution"].get(maker, 0) + 1
            
            # 收集价格和数量数据
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
            
            # 收集时间戳
            if "created_at" in order:
                try:
                    timestamps.append(order["created_at"])
                except:
                    pass
        
        # 价格统计
        if prices:
            analysis["price_statistics"] = {
                "count": len(prices),
                "min": min(prices),
                "max": max(prices),
                "average": sum(prices) / len(prices),
                "median": sorted(prices)[len(prices) // 2]
            }
        
        # 数量统计
        if sizes:
            analysis["size_statistics"] = {
                "count": len(sizes),
                "min": min(sizes),
                "max": max(sizes),
                "average": sum(sizes) / len(sizes),
                "total": sum(sizes)
            }
        
        # 时间分析
        if timestamps:
            analysis["time_analysis"] = {
                "earliest": min(timestamps),
                "latest": max(timestamps),
                "span_seconds": max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0
            }
        
        # 限制分布数据的大小（只保留前10个）
        for key in ["market_distribution", "maker_distribution"]:
            if key in analysis and len(analysis[key]) > 10:
                sorted_items = sorted(analysis[key].items(), key=lambda x: x[1], reverse=True)
                analysis[key] = dict(sorted_items[:10])
                analysis[key]["others"] = sum(count for _, count in sorted_items[10:])
        
        self.logger.info(f"订单分析完成: {analysis['total_orders']} 个订单")
        return analysis
    
    def analyze_trades(self, trades: List[Dict]) -> Dict[str, Any]:
        """
        分析交易数据
        
        参数:
            trades: 交易记录列表
            
        返回:
            交易分析结果
        """
        if not trades:
            return {"error": "没有交易数据可分析"}
        
        analysis = {
            "total_trades": len(trades),
            "status_distribution": {},
            "market_distribution": {},
            "volume_statistics": {},
            "price_statistics": {},
            "time_analysis": {},
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 收集数据用于分析
        volumes = []
        prices = []
        timestamps = []
        
        # 统计各种分布
        for trade in trades:
            # 状态分布
            status = trade.get("status", "unknown")
            analysis["status_distribution"][status] = analysis["status_distribution"].get(status, 0) + 1
            
            # 市场分布
            market = trade.get("market", "unknown")
            analysis["market_distribution"][market] = analysis["market_distribution"].get(market, 0) + 1
            
            # 收集交易量和价格数据
            if "volume" in trade:
                try:
                    volumes.append(float(trade["volume"]))
                except (ValueError, TypeError):
                    pass
            
            if "price" in trade:
                try:
                    prices.append(float(trade["price"]))
                except (ValueError, TypeError):
                    pass
            
            # 收集时间戳
            if "timestamp" in trade:
                try:
                    timestamps.append(trade["timestamp"])
                except:
                    pass
        
        # 交易量统计
        if volumes:
            analysis["volume_statistics"] = {
                "count": len(volumes),
                "min": min(volumes),
                "max": max(volumes),
                "average": sum(volumes) / len(volumes),
                "total": sum(volumes)
            }
        
        # 价格统计
        if prices:
            analysis["price_statistics"] = {
                "count": len(prices),
                "min": min(prices),
                "max": max(prices),
                "average": sum(prices) / len(prices),
                "median": sorted(prices)[len(prices) // 2]
            }
        
        # 时间分析
        if timestamps:
            analysis["time_analysis"] = {
                "earliest": min(timestamps),
                "latest": max(timestamps),
                "span_seconds": max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0
            }
        
        # 限制分布数据的大小
        if len(analysis["market_distribution"]) > 10:
            sorted_items = sorted(analysis["market_distribution"].items(), key=lambda x: x[1], reverse=True)
            analysis["market_distribution"] = dict(sorted_items[:10])
            analysis["market_distribution"]["others"] = sum(count for _, count in sorted_items[10:])
        
        self.logger.info(f"交易分析完成: {analysis['total_trades']} 条交易记录")
        return analysis
    
    def run_comprehensive_collection(self, market: str = None, 
                                   include_analysis: bool = True) -> Dict[str, Any]:
        """
        运行综合数据收集
        
        参数:
            market: 市场ID
            include_analysis: 是否包含数据分析
            
        返回:
            收集结果摘要
        """
        self.logger.info(f"开始运行综合订单数据收集，市场: {market}")
        
        start_time = datetime.now(timezone.utc)
        
        # 收集订单数据
        all_orders = self.fetch_all_orders(market)
        active_orders = self.fetch_active_orders(market)
        
        # 收集交易数据
        all_trades = self.fetch_all_trades(market)
        
        # 数据分析
        order_analysis = None
        trade_analysis = None
        
        if include_analysis:
            if all_orders:
                order_analysis = self.analyze_orders(all_orders)
                self.data_manager.save_json(
                    order_analysis, 
                    f"order_analysis_{market or 'all'}.json"
                )
            
            if all_trades:
                trade_analysis = self.analyze_trades(all_trades)
                self.data_manager.save_json(
                    trade_analysis, 
                    f"trade_analysis_{market or 'all'}.json"
                )
        
        # 保存活跃订单
        if active_orders:
            self.data_manager.save_json(
                active_orders, 
                f"active_orders_{market or 'all'}.json"
            )
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # 生成收集摘要
        summary = {
            "market": market,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "orders_collected": len(all_orders),
            "active_orders": len(active_orders),
            "trades_collected": len(all_trades),
            "analysis_included": include_analysis,
            "data_files": []
        }
        
        # 添加数据文件列表
        summary["data_files"].extend([
            f"orders_{market or 'all'}_all_final.json",
            f"active_orders_{market or 'all'}.json",
            f"trades_{market or 'all'}_final.json"
        ])
        
        if include_analysis:
            if order_analysis:
                summary["order_analysis_summary"] = {
                    "total_orders": order_analysis.get("total_orders", 0),
                    "status_types": len(order_analysis.get("status_distribution", {})),
                    "markets_involved": len(order_analysis.get("market_distribution", {}))
                }
                summary["data_files"].append(f"order_analysis_{market or 'all'}.json")
            
            if trade_analysis:
                summary["trade_analysis_summary"] = {
                    "total_trades": trade_analysis.get("total_trades", 0),
                    "status_types": len(trade_analysis.get("status_distribution", {})),
                    "markets_involved": len(trade_analysis.get("market_distribution", {}))
                }
                summary["data_files"].append(f"trade_analysis_{market or 'all'}.json")
        
        # 保存收集摘要
        self.data_manager.save_json(summary, f"collection_summary_{market or 'all'}.json")
        
        self.logger.info(f"综合订单数据收集完成，耗时 {duration:.2f} 秒")
        return summary

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="Polymarket订单数据收集器")
    
    parser.add_argument(
        "--mode",
        choices=["orders", "trades", "active", "comprehensive"],
        default="comprehensive",
        help="收集模式: orders(订单), trades(交易), active(活跃订单), comprehensive(综合)"
    )
    
    parser.add_argument(
        "--market",
        help="市场ID"
    )
    
    parser.add_argument(
        "--status",
        choices=[OrderStatus.LIVE, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.PARTIALLY_FILLED],
        help="订单状态筛选"
    )
    
    parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="跳过数据分析"
    )
    
    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置进度，从头开始收集"
    )
    
    args = parser.parse_args()
    
    # 初始化配置
    DataConfig.ensure_directories()
    
    # 创建收集器
    collector = OrderCollector()
    
    # 如果需要重置进度
    if args.reset:
        # 删除相关的进度文件
        progress_patterns = [
            f"orders_{args.market or 'all'}_{args.status or 'all'}_progress.json",
            f"trades_{args.market or 'all'}_progress.json"
        ]
        
        for pattern in progress_patterns:
            progress_path = DataConfig.ORDER_DATA_DIR / pattern
            if progress_path.exists():
                progress_path.unlink()
                print(f"已重置进度文件: {pattern}")
    
    if args.mode == "orders":
        print(f"开始收集订单数据，市场: {args.market}, 状态: {args.status}")
        orders = collector.fetch_all_orders(args.market, args.status)
        
        if not args.no_analysis and orders:
            analysis = collector.analyze_orders(orders)
            collector.data_manager.save_json(
                analysis, 
                f"order_analysis_{args.market or 'all'}_{args.status or 'all'}.json"
            )
        
        print(f"\n=== 订单收集完成 ===")
        print(f"订单数量: {len(orders)}")
        
    elif args.mode == "trades":
        print(f"开始收集交易数据，市场: {args.market}")
        trades = collector.fetch_all_trades(args.market)
        
        if not args.no_analysis and trades:
            analysis = collector.analyze_trades(trades)
            collector.data_manager.save_json(
                analysis, 
                f"trade_analysis_{args.market or 'all'}.json"
            )
        
        print(f"\n=== 交易收集完成 ===")
        print(f"交易数量: {len(trades)}")
        
    elif args.mode == "active":
        print(f"开始收集活跃订单，市场: {args.market}")
        active_orders = collector.fetch_active_orders(args.market)
        
        collector.data_manager.save_json(
            active_orders, 
            f"active_orders_{args.market or 'all'}.json"
        )
        
        print(f"\n=== 活跃订单收集完成 ===")
        print(f"活跃订单数量: {len(active_orders)}")
        
    elif args.mode == "comprehensive":
        print(f"开始综合数据收集，市场: {args.market}")
        summary = collector.run_comprehensive_collection(
            market=args.market,
            include_analysis=not args.no_analysis
        )
        
        print(f"\n=== 综合收集完成 ===")
        print(f"收集时间: {summary['duration_seconds']:.2f} 秒")
        print(f"订单数量: {summary['orders_collected']}")
        print(f"活跃订单: {summary['active_orders']}")
        print(f"交易数量: {summary['trades_collected']}")
        print(f"数据文件: {len(summary['data_files'])} 个")

if __name__ == "__main__":
    main() 
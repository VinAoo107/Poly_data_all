"""
市场信息收集器
用于获取Polymarket的市场基本信息、事件数据等
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import argparse

# 添加父目录到路径，以便导入配置和工具模块
sys.path.append(str(Path(__file__).parent.parent))

from config import APIConfig, DataConfig, MarketTypes, DataFetchConfig, APIEndpoints
from utils import HTTPClient, DataManager, Logger, RateLimiter, format_timestamp

class MarketInfoCollector:
    """市场信息收集器"""
    
    def __init__(self):
        """初始化市场信息收集器"""
        self.logger = Logger.setup_logger(
            "MarketInfoCollector", 
            "market_info.log"
        )
        
        # 初始化HTTP客户端
        self.gamma_client = HTTPClient(APIConfig.GAMMA_BASE_URL, self.logger)
        self.clob_client = HTTPClient(APIConfig.CLOB_BASE_URL, self.logger)
        
        # 初始化数据管理器
        self.data_manager = DataManager(DataConfig.INFO_DATA_DIR, self.logger)
        
        # 初始化频率限制器
        self.rate_limiter = RateLimiter()
        
        self.logger.info("市场信息收集器初始化完成")
    
    def fetch_events(self, market_type: str = MarketTypes.ALL, 
                    offset: int = 0, limit: int = None) -> List[Dict]:
        """
        获取事件数据
        
        参数:
            market_type: 市场类型 (all, active, closed, archived)
            offset: 分页偏移量
            limit: 每页数量
            
        返回:
            事件列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        # 构建请求参数
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # 根据市场类型添加筛选条件
        if market_type == MarketTypes.ACTIVE:
            params["active"] = "true"
        elif market_type == MarketTypes.CLOSED:
            params["closed"] = "true"
        elif market_type == MarketTypes.ARCHIVED:
            params["archived"] = "true"
        
        self.logger.info(f"获取 {market_type} 类型的事件，offset={offset}, limit={limit}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.gamma_client.get("/events", params=params)
        
        if response:
            # 处理不同的响应格式
            if isinstance(response, dict) and "events" in response:
                events = response["events"]
            elif isinstance(response, list):
                events = response
            else:
                self.logger.warning(f"未知的响应格式: {type(response)}")
                events = []
            
            self.logger.info(f"成功获取 {len(events)} 个事件")
            return events
        
        self.logger.error("获取事件失败")
        return []
    
    def fetch_all_events(self, market_type: str = MarketTypes.ALL) -> List[Dict]:
        """
        获取所有事件数据（分页获取）
        
        参数:
            market_type: 市场类型
            
        返回:
            所有事件列表
        """
        self.logger.info(f"开始获取所有 {market_type} 类型的事件")
        
        # 加载已有进度
        progress_file = f"events_{market_type}_progress.json"
        progress = self.data_manager.load_progress(progress_file)
        
        if progress:
            all_events = progress.get("events", [])
            offset = progress.get("offset", 0)
            self.logger.info(f"从进度文件恢复: {len(all_events)} 个事件, offset={offset}")
        else:
            all_events = []
            offset = 0
        
        try:
            while True:
                # 获取一批事件
                events = self.fetch_events(market_type, offset, DataFetchConfig.MARKETS_BATCH_SIZE)
                
                if not events:
                    self.logger.info("没有更多事件数据")
                    break
                
                # 去重处理
                if all_events:
                    existing_ids = set(e.get("id") for e in all_events if e.get("id"))
                    new_events = [e for e in events if e.get("id") not in existing_ids]
                    
                    if len(new_events) < len(events):
                        self.logger.info(f"过滤掉 {len(events) - len(new_events)} 个重复事件")
                else:
                    new_events = events
                
                # 添加新事件
                all_events.extend(new_events)
                offset += DataFetchConfig.MARKETS_BATCH_SIZE
                
                self.logger.info(f"新增 {len(new_events)} 个事件，总计: {len(all_events)} 个")
                
                # 保存进度
                progress_data = {
                    "events": all_events,
                    "offset": offset,
                    "market_type": market_type,
                    "last_update": datetime.now(timezone.utc).isoformat()
                }
                self.data_manager.save_progress(progress_data, progress_file)
                
                # 如果获取的事件数量少于请求数量，说明已经到达末尾
                if len(events) < DataFetchConfig.MARKETS_BATCH_SIZE:
                    self.logger.info("已获取所有可用事件")
                    break
                
        except KeyboardInterrupt:
            self.logger.info("用户中断，保存当前进度")
            progress_data = {
                "events": all_events,
                "offset": offset,
                "market_type": market_type,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
            self.data_manager.save_progress(progress_data, progress_file)
        
        # 保存最终结果
        result_file = f"events_{market_type}_final.json"
        self.data_manager.save_json(all_events, result_file)
        
        self.logger.info(f"完成! 共获取 {len(all_events)} 个 {market_type} 类型的事件")
        return all_events
    
    def fetch_markets(self, limit: int = None, offset: int = 0, 
                     active: bool = None, closed: bool = None) -> List[Dict]:
        """
        获取市场数据
        
        参数:
            limit: 每页数量
            offset: 分页偏移量
            active: 是否只获取活跃市场
            closed: 是否只获取已关闭市场
            
        返回:
            市场列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if active is not None:
            params["active"] = str(active).lower()
        if closed is not None:
            params["closed"] = str(closed).lower()
        
        self.logger.info(f"获取市场数据，offset={offset}, limit={limit}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.gamma_client.get("/markets", params=params)
        
        if response:
            # 处理响应格式
            if isinstance(response, dict) and "data" in response:
                markets = response["data"]
            elif isinstance(response, list):
                markets = response
            else:
                self.logger.warning(f"未知的市场响应格式: {type(response)}")
                markets = []
            
            self.logger.info(f"成功获取 {len(markets)} 个市场")
            return markets
        
        self.logger.error("获取市场数据失败")
        return []
    
    def fetch_single_market(self, market_id: str) -> Optional[Dict]:
        """
        获取单个市场的详细信息 (Get Single Market)
        
        参数:
            market_id: 市场ID
            
        返回:
            市场详细信息
        """
        self.logger.info(f"获取单个市场详细信息: {market_id}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求到gamma-api的markets端点
        response = self.gamma_client.get(f"/markets/{market_id}")
        
        if response:
            self.logger.info(f"成功获取市场 {market_id} 的详细信息")
            return response
        
        self.logger.error(f"获取市场 {market_id} 详细信息失败")
        return None
    
    def fetch_sampling_markets(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        获取采样市场数据 (Get Sampling Markets)
        
        参数:
            limit: 每页数量
            offset: 分页偏移量
            
        返回:
            采样市场列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        self.logger.info(f"获取采样市场数据，offset={offset}, limit={limit}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.gamma_client.get("/sampling-markets", params=params)
        
        if response:
            # 处理不同的响应格式
            if isinstance(response, dict) and "markets" in response:
                markets = response["markets"]
            elif isinstance(response, list):
                markets = response
            else:
                self.logger.warning(f"未知的响应格式: {type(response)}")
                markets = []
            
            self.logger.info(f"成功获取 {len(markets)} 个采样市场")
            return markets
        
        self.logger.error("获取采样市场数据失败")
        return []
    
    def fetch_simplified_markets(self, limit: int = None, offset: int = 0, 
                                active: bool = None, closed: bool = None) -> List[Dict]:
        """
        获取简化市场数据 (Get Simplified Markets)
        
        参数:
            limit: 每页数量
            offset: 分页偏移量
            active: 是否只获取活跃市场
            closed: 是否只获取已关闭市场
            
        返回:
            简化市场列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if active is not None:
            params["active"] = str(active).lower()
        if closed is not None:
            params["closed"] = str(closed).lower()
        
        self.logger.info(f"获取简化市场数据，offset={offset}, limit={limit}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.gamma_client.get("/simplified-markets", params=params)
        
        if response:
            # 处理不同的响应格式
            if isinstance(response, dict) and "markets" in response:
                markets = response["markets"]
            elif isinstance(response, list):
                markets = response
            else:
                self.logger.warning(f"未知的响应格式: {type(response)}")
                markets = []
            
            self.logger.info(f"成功获取 {len(markets)} 个简化市场")
            return markets
        
        self.logger.error("获取简化市场数据失败")
        return []
    
    def fetch_sampling_simplified_markets(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        获取采样简化市场数据 (Get Sampling Simplified Markets)
        
        参数:
            limit: 每页数量
            offset: 分页偏移量
            
        返回:
            采样简化市场列表
        """
        limit = limit or DataFetchConfig.MARKETS_BATCH_SIZE
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        self.logger.info(f"获取采样简化市场数据，offset={offset}, limit={limit}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.gamma_client.get("/sampling-simplified-markets", params=params)
        
        if response:
            # 处理不同的响应格式
            if isinstance(response, dict) and "markets" in response:
                markets = response["markets"]
            elif isinstance(response, list):
                markets = response
            else:
                self.logger.warning(f"未知的响应格式: {type(response)}")
                markets = []
            
            self.logger.info(f"成功获取 {len(markets)} 个采样简化市场")
            return markets
        
        self.logger.error("获取采样简化市场数据失败")
        return []
    
    def fetch_timeseries_data(self, market_id: str = None, interval: str = "1h", 
                             start_time: str = None, end_time: str = None) -> List[Dict]:
        """
        获取时间序列数据 (Timeseries Data)
        
        参数:
            market_id: 市场ID（可选）
            interval: 时间间隔 (1m, 5m, 15m, 1h, 4h, 1d)
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            
        返回:
            时间序列数据列表
        """
        params = {
            "interval": interval
        }
        
        if market_id:
            params["market_id"] = market_id
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        
        self.logger.info(f"获取时间序列数据，市场ID: {market_id}, 间隔: {interval}")
        
        # 频率限制
        self.rate_limiter.wait()
        
        # 发送请求
        response = self.gamma_client.get("/timeseries", params=params)
        
        if response:
            # 处理不同的响应格式
            if isinstance(response, dict) and "data" in response:
                timeseries = response["data"]
            elif isinstance(response, list):
                timeseries = response
            else:
                self.logger.warning(f"未知的响应格式: {type(response)}")
                timeseries = []
            
            self.logger.info(f"成功获取 {len(timeseries)} 个时间序列数据点")
            return timeseries
        
        self.logger.error("获取时间序列数据失败")
        return []
    
    def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        """
        获取单个市场的详细信息（兼容性方法，调用fetch_single_market）
        
        参数:
            market_id: 市场ID
            
        返回:
            市场详细信息
        """
        return self.fetch_single_market(market_id)
    
    def analyze_events(self, events: List[Dict]) -> Dict[str, Any]:
        """
        分析事件数据，生成统计信息
        
        参数:
            events: 事件列表
            
        返回:
            分析结果
        """
        if not events:
            return {"error": "没有事件数据可分析"}
        
        analysis = {
            "total_events": len(events),
            "event_types": {},
            "status_distribution": {},
            "date_range": {},
            "markets_per_event": {},
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 统计事件类型
        for event in events:
            event_type = event.get("type", "unknown")
            analysis["event_types"][event_type] = analysis["event_types"].get(event_type, 0) + 1
            
            # 统计状态分布
            status = event.get("status", "unknown")
            analysis["status_distribution"][status] = analysis["status_distribution"].get(status, 0) + 1
            
            # 统计每个事件的市场数量
            markets = event.get("markets", [])
            market_count = len(markets) if isinstance(markets, list) else 0
            analysis["markets_per_event"][str(market_count)] = analysis["markets_per_event"].get(str(market_count), 0) + 1
        
        # 计算日期范围
        timestamps = []
        for event in events:
            if "created_at" in event:
                try:
                    timestamps.append(event["created_at"])
                except:
                    pass
        
        if timestamps:
            analysis["date_range"] = {
                "earliest": min(timestamps),
                "latest": max(timestamps),
                "span_days": (max(timestamps) - min(timestamps)) / (24 * 3600) if len(timestamps) > 1 else 0
            }
        
        self.logger.info(f"事件分析完成: {analysis['total_events']} 个事件")
        return analysis
    
    def collect_comprehensive_market_data(self, include_timeseries: bool = False,
                                         timeseries_interval: str = "1h") -> Dict[str, Any]:
        """
        收集所有类型的市场数据（综合收集）
        
        参数:
            include_timeseries: 是否包含时间序列数据
            timeseries_interval: 时间序列数据间隔
            
        返回:
            综合收集结果
        """
        self.logger.info("开始综合收集所有类型的市场数据")
        start_time = datetime.now(timezone.utc)
        
        comprehensive_data = {
            "collection_timestamp": start_time.isoformat(),
            "data_types": {},
            "summary": {},
            "errors": []
        }
        
        try:
            # 1. 收集标准市场数据
            self.logger.info("收集标准市场数据...")
            markets = self.fetch_markets(active=True)
            comprehensive_data["data_types"]["standard_markets"] = {
                "count": len(markets),
                "data": markets[:100]  # 只保存前100个以节省空间
            }
            if markets:
                self.data_manager.save_json(markets, "comprehensive_standard_markets.json")
            
            # 2. 收集采样市场数据
            self.logger.info("收集采样市场数据...")
            sampling_markets = self.fetch_sampling_markets()
            comprehensive_data["data_types"]["sampling_markets"] = {
                "count": len(sampling_markets),
                "data": sampling_markets
            }
            if sampling_markets:
                self.data_manager.save_json(sampling_markets, "comprehensive_sampling_markets.json")
            
            # 3. 收集简化市场数据
            self.logger.info("收集简化市场数据...")
            simplified_markets = self.fetch_simplified_markets(active=True)
            comprehensive_data["data_types"]["simplified_markets"] = {
                "count": len(simplified_markets),
                "data": simplified_markets[:100]  # 只保存前100个
            }
            if simplified_markets:
                self.data_manager.save_json(simplified_markets, "comprehensive_simplified_markets.json")
            
            # 4. 收集采样简化市场数据
            self.logger.info("收集采样简化市场数据...")
            sampling_simplified = self.fetch_sampling_simplified_markets()
            comprehensive_data["data_types"]["sampling_simplified_markets"] = {
                "count": len(sampling_simplified),
                "data": sampling_simplified
            }
            if sampling_simplified:
                self.data_manager.save_json(sampling_simplified, "comprehensive_sampling_simplified_markets.json")
            
            # 5. 收集事件数据
            self.logger.info("收集事件数据...")
            events = self.fetch_events(MarketTypes.ACTIVE, limit=200)  # 限制数量
            comprehensive_data["data_types"]["events"] = {
                "count": len(events),
                "data": events
            }
            if events:
                self.data_manager.save_json(events, "comprehensive_events.json")
            
            # 6. 收集时间序列数据（可选）
            if include_timeseries:
                self.logger.info("收集时间序列数据...")
                timeseries = self.fetch_timeseries_data(interval=timeseries_interval)
                comprehensive_data["data_types"]["timeseries"] = {
                    "count": len(timeseries),
                    "interval": timeseries_interval,
                    "data": timeseries[:50]  # 只保存前50个数据点
                }
                if timeseries:
                    self.data_manager.save_json(timeseries, f"comprehensive_timeseries_{timeseries_interval}.json")
            
            # 7. 收集单个市场详细信息（选择几个市场作为示例）
            if markets:
                self.logger.info("收集单个市场详细信息示例...")
                market_details = []
                for market in markets[:5]:  # 只收集前5个市场的详细信息
                    market_id = market.get("id")
                    if market_id:
                        details = self.fetch_single_market(market_id)
                        if details:
                            market_details.append(details)
                
                comprehensive_data["data_types"]["market_details_samples"] = {
                    "count": len(market_details),
                    "data": market_details
                }
                if market_details:
                    self.data_manager.save_json(market_details, "comprehensive_market_details_samples.json")
            
        except Exception as e:
            error_msg = f"综合收集过程中发生错误: {str(e)}"
            self.logger.error(error_msg)
            comprehensive_data["errors"].append(error_msg)
        
        # 生成摘要
        end_time = datetime.now(timezone.utc)
        comprehensive_data["completion_timestamp"] = end_time.isoformat()
        comprehensive_data["duration_seconds"] = (end_time - start_time).total_seconds()
        
        # 计算总数据量
        total_items = sum(
            data_type.get("count", 0) 
            for data_type in comprehensive_data["data_types"].values()
        )
        
        comprehensive_data["summary"] = {
            "total_data_types": len(comprehensive_data["data_types"]),
            "total_items_collected": total_items,
            "include_timeseries": include_timeseries,
            "errors_count": len(comprehensive_data["errors"]),
            "success_rate": (len(comprehensive_data["data_types"]) - len(comprehensive_data["errors"])) / max(len(comprehensive_data["data_types"]), 1) * 100
        }
        
        # 保存综合收集结果
        self.data_manager.save_json(comprehensive_data, f"comprehensive_collection_{start_time.strftime('%Y%m%d_%H%M%S')}.json")
        
        self.logger.info(f"综合收集完成，耗时 {comprehensive_data['duration_seconds']:.2f} 秒")
        self.logger.info(f"收集了 {total_items} 个数据项，涵盖 {len(comprehensive_data['data_types'])} 种数据类型")
        
        return comprehensive_data
    
    def run_collection(self, market_type: str = MarketTypes.ALL, 
                      include_analysis: bool = True) -> Dict[str, Any]:
        """
        运行完整的数据收集流程
        
        参数:
            market_type: 市场类型
            include_analysis: 是否包含数据分析
            
        返回:
            收集结果摘要
        """
        self.logger.info(f"开始运行 {market_type} 类型的市场信息收集")
        
        start_time = datetime.now(timezone.utc)
        
        # 获取事件数据
        events = self.fetch_all_events(market_type)
        
        # 获取市场数据
        markets = self.fetch_markets()
        
        # 保存市场数据
        if markets:
            self.data_manager.save_json(markets, f"markets_{market_type}.json")
        
        # 数据分析
        analysis = None
        if include_analysis and events:
            analysis = self.analyze_events(events)
            self.data_manager.save_json(analysis, f"events_{market_type}_analysis.json")
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # 生成收集摘要
        summary = {
            "collection_type": market_type,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "events_collected": len(events),
            "markets_collected": len(markets),
            "analysis_included": include_analysis,
            "data_files": [
                f"events_{market_type}_final.json",
                f"markets_{market_type}.json"
            ]
        }
        
        if analysis:
            summary["analysis_summary"] = {
                "total_events": analysis.get("total_events", 0),
                "event_types_count": len(analysis.get("event_types", {})),
                "status_types_count": len(analysis.get("status_distribution", {}))
            }
            summary["data_files"].append(f"events_{market_type}_analysis.json")
        
        # 保存收集摘要
        self.data_manager.save_json(summary, f"collection_summary_{market_type}.json")
        
        self.logger.info(f"市场信息收集完成，耗时 {duration:.2f} 秒")
        return summary

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="Polymarket市场信息收集器")
    
    parser.add_argument(
        "--type",
        choices=[MarketTypes.ALL, MarketTypes.ACTIVE, MarketTypes.CLOSED, MarketTypes.ARCHIVED],
        default=MarketTypes.ALL,
        help="市场类型"
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
    collector = MarketInfoCollector()
    
    # 如果需要重置进度
    if args.reset:
        progress_file = f"events_{args.type}_progress.json"
        progress_path = DataConfig.INFO_DATA_DIR / progress_file
        if progress_path.exists():
            progress_path.unlink()
            print(f"已重置 {args.type} 类型的进度")
    
    # 运行收集
    summary = collector.run_collection(
        market_type=args.type,
        include_analysis=not args.no_analysis
    )
    
    print("\n=== 收集完成 ===")
    print(f"市场类型: {summary['collection_type']}")
    print(f"收集时间: {summary['duration_seconds']:.2f} 秒")
    print(f"事件数量: {summary['events_collected']}")
    print(f"市场数量: {summary['markets_collected']}")
    print(f"数据文件: {', '.join(summary['data_files'])}")

if __name__ == "__main__":
    main() 
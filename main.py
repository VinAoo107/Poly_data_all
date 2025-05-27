"""
Polymarket数据收集项目主启动文件
提供统一的入口点来运行各个数据收集模块
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timezone

# 添加当前目录到路径
sys.path.append(str(Path(__file__).parent))

from config import DataConfig, MarketTypes, OrderStatus
from utils import Logger

def main():
    """主函数，处理命令行参数并启动相应模块"""
    parser = argparse.ArgumentParser(
        description="Polymarket数据收集项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 收集市场信息
  python main.py market-info --type active
  
  # 批量收集价格数据
  python main.py price-data --mode batch --markets market1 market2
  
  # 监控价格变化
  python main.py price-data --mode monitor --markets market1 market2 --interval 30
  
  # 收集订单数据
  python main.py order-data --mode comprehensive --market market1
  
  # 收集用户数据
  python main.py user-data --mode single --user 0x1234...
  
  # 监控市场波动
  python main.py fluctuation --markets market1 market2 --duration 60
        """
    )
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='module', help='要运行的模块')
    
    # 综合数据收集模块
    comprehensive_parser = subparsers.add_parser('comprehensive', help='综合数据收集和关联分析')
    comprehensive_parser.add_argument(
        '--mode',
        choices=['ecosystem', 'test', 'market-view', 'user-view', 'correlations', 'report'],
        default='ecosystem',
        help='运行模式'
    )
    comprehensive_parser.add_argument('--markets', nargs='+', help='指定的市场ID列表')
    comprehensive_parser.add_argument('--user', help='用户地址（用于用户视图模式）')
    comprehensive_parser.add_argument('--include-users', action='store_true', default=True, help='包含用户数据收集')
    comprehensive_parser.add_argument('--include-monitoring', action='store_true', help='包含价格监控')
    comprehensive_parser.add_argument('--monitoring-duration', type=int, default=30, help='价格监控持续时间（分钟）')
    comprehensive_parser.add_argument('--max-markets', type=int, default=3, help='测试模式：最大市场数量（默认3个）')
    comprehensive_parser.add_argument('--max-users', type=int, default=10, help='测试模式：最大用户数量（默认10个）')
    
    # 市场信息收集模块
    market_info_parser = subparsers.add_parser('market-info', help='收集市场信息和事件数据')
    market_info_parser.add_argument(
        '--mode',
        choices=['standard', 'comprehensive', 'sampling', 'simplified', 'timeseries', 'single'],
        default='standard',
        help='收集模式'
    )
    market_info_parser.add_argument(
        '--type',
        choices=[MarketTypes.ALL, MarketTypes.ACTIVE, MarketTypes.CLOSED, MarketTypes.ARCHIVED],
        default=MarketTypes.ALL,
        help='市场类型（标准模式）'
    )
    market_info_parser.add_argument('--market-id', help='单个市场ID（单个市场模式）')
    market_info_parser.add_argument('--include-timeseries', action='store_true', help='包含时间序列数据（综合模式）')
    market_info_parser.add_argument('--timeseries-interval', default='1h', choices=['1m', '5m', '15m', '1h', '4h', '1d'], help='时间序列间隔')
    market_info_parser.add_argument('--no-analysis', action='store_true', help='跳过数据分析')
    market_info_parser.add_argument('--reset', action='store_true', help='重置进度')
    
    # 价格数据收集模块
    price_data_parser = subparsers.add_parser('price-data', help='收集价格数据')
    price_data_parser.add_argument(
        '--mode',
        choices=['batch', 'monitor', 'report', 'history'],
        default='batch',
        help='运行模式'
    )
    price_data_parser.add_argument('--markets', nargs='+', help='市场ID列表')
    price_data_parser.add_argument('--detailed', action='store_true', help='包含详细数据')
    price_data_parser.add_argument('--interval', type=int, default=60, help='监控间隔（秒）')
    price_data_parser.add_argument('--days', type=int, default=30, help='报告分析天数')
    price_data_parser.add_argument('--fidelity', type=int, choices=[1, 60, 1440], default=1, help='历史数据精度(1=分钟,60=小时,1440=天)')
    price_data_parser.add_argument('--max-markets', type=int, default=10, help='最大处理市场数量')
    
    # 订单数据收集模块
    order_data_parser = subparsers.add_parser('order-data', help='收集订单和交易数据')
    order_data_parser.add_argument(
        '--mode',
        choices=['orders', 'trades', 'active', 'comprehensive'],
        default='comprehensive',
        help='收集模式'
    )
    order_data_parser.add_argument('--market', help='市场ID')
    order_data_parser.add_argument(
        '--status',
        choices=[OrderStatus.LIVE, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.PARTIALLY_FILLED],
        help='订单状态筛选'
    )
    order_data_parser.add_argument('--no-analysis', action='store_true', help='跳过数据分析')
    order_data_parser.add_argument('--reset', action='store_true', help='重置进度')
    
    # 用户数据收集模块
    user_data_parser = subparsers.add_parser('user-data', help='收集用户数据')
    user_data_parser.add_argument(
        '--mode',
        choices=['single', 'batch'],
        default='single',
        help='收集模式'
    )
    user_data_parser.add_argument('--user', help='用户地址（单个用户模式）')
    user_data_parser.add_argument('--users-file', help='用户地址文件（批量模式）')
    user_data_parser.add_argument('--users', nargs='+', help='用户地址列表（批量模式）')
    
    # 市场波动监控模块
    fluctuation_parser = subparsers.add_parser('fluctuation', help='监控市场波动')
    fluctuation_parser.add_argument('--markets', nargs='+', required=True, help='要监控的市场ID列表')
    fluctuation_parser.add_argument('--duration', type=int, help='监控持续时间（分钟）')
    fluctuation_parser.add_argument('--threshold', type=float, default=0.05, help='价格变化阈值')
    fluctuation_parser.add_argument('--interval', type=int, default=10, help='检查间隔（秒）')
    fluctuation_parser.add_argument('--background', action='store_true', help='后台运行')
    
    # 通用参数
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        log_level = 'DEBUG'
    elif args.quiet:
        log_level = 'ERROR'
    else:
        log_level = 'INFO'
    
    # 初始化配置
    DataConfig.ensure_directories()
    
    # 设置主日志记录器
    logger = Logger.setup_logger("MainLauncher", "main.log")
    logger.info(f"启动Polymarket数据收集项目 - {datetime.now(timezone.utc).isoformat()}")
    
    if not args.module:
        parser.print_help()
        return
    
    try:
        if args.module == 'comprehensive':
            from comprehensive_collector import ComprehensiveCollector
            
            logger.info("启动综合数据收集模块")
            collector = ComprehensiveCollector()
            
            if args.mode == 'ecosystem':
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
            
            elif args.mode == 'test':
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
                        
            elif args.mode == 'market-view':
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
                    
            elif args.mode == 'user-view':
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
                    
            elif args.mode == 'correlations':
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
                    
            elif args.mode == 'report':
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
            
        elif args.module == 'market-info':
            from Poly_info.market_info_collector import MarketInfoCollector
            
            logger.info("启动市场信息收集模块")
            collector = MarketInfoCollector()
            
            if args.reset:
                # 重置进度逻辑
                progress_file = f"events_{args.type}_progress.json"
                progress_path = DataConfig.INFO_DATA_DIR / progress_file
                if progress_path.exists():
                    progress_path.unlink()
                    logger.info(f"已重置 {args.type} 类型的进度")
            
            if args.mode == 'standard':
                # 标准收集模式
                summary = collector.run_collection(
                    market_type=args.type,
                    include_analysis=not args.no_analysis
                )
                
                print(f"\n=== 标准市场信息收集完成 ===")
                print(f"市场类型: {summary['collection_type']}")
                print(f"收集时间: {summary['duration_seconds']:.2f} 秒")
                print(f"事件数量: {summary['events_collected']}")
                print(f"市场数量: {summary['markets_collected']}")
                
            elif args.mode == 'comprehensive':
                # 综合收集模式
                result = collector.collect_comprehensive_market_data(
                    include_timeseries=args.include_timeseries,
                    timeseries_interval=args.timeseries_interval
                )
                
                print(f"\n=== 综合市场信息收集完成 ===")
                print(f"收集时间: {result['duration_seconds']:.2f} 秒")
                print(f"数据类型数量: {result['summary']['total_data_types']}")
                print(f"总数据项: {result['summary']['total_items_collected']}")
                print(f"成功率: {result['summary']['success_rate']:.1f}%")
                print(f"包含时间序列: {result['summary']['include_timeseries']}")
                
                print(f"\n收集的数据类型:")
                for data_type, info in result['data_types'].items():
                    print(f"  {data_type}: {info['count']} 项")
                
                if result['errors']:
                    print(f"\n错误:")
                    for error in result['errors']:
                        print(f"  - {error}")
                        
            elif args.mode == 'sampling':
                # 采样市场收集
                markets = collector.fetch_sampling_markets()
                print(f"\n=== 采样市场收集完成 ===")
                print(f"采样市场数量: {len(markets)}")
                
                if markets:
                    collector.data_manager.save_json(markets, "sampling_markets.json")
                    print(f"数据已保存到: sampling_markets.json")
                    
            elif args.mode == 'simplified':
                # 简化市场收集
                markets = collector.fetch_simplified_markets(active=True)
                print(f"\n=== 简化市场收集完成 ===")
                print(f"简化市场数量: {len(markets)}")
                
                if markets:
                    collector.data_manager.save_json(markets, "simplified_markets.json")
                    print(f"数据已保存到: simplified_markets.json")
                    
            elif args.mode == 'timeseries':
                # 时间序列数据收集
                timeseries = collector.fetch_timeseries_data(interval=args.timeseries_interval)
                print(f"\n=== 时间序列数据收集完成 ===")
                print(f"时间序列数据点: {len(timeseries)}")
                print(f"时间间隔: {args.timeseries_interval}")
                
                if timeseries:
                    collector.data_manager.save_json(timeseries, f"timeseries_{args.timeseries_interval}.json")
                    print(f"数据已保存到: timeseries_{args.timeseries_interval}.json")
                    
            elif args.mode == 'single':
                # 单个市场详细信息
                if not args.market_id:
                    print("单个市场模式需要指定 --market-id 参数")
                    return
                
                market_details = collector.fetch_single_market(args.market_id)
                print(f"\n=== 单个市场信息收集完成 ===")
                print(f"市场ID: {args.market_id}")
                
                if market_details:
                    print(f"市场名称: {market_details.get('question', 'Unknown')}")
                    print(f"市场状态: {market_details.get('active', 'Unknown')}")
                    print(f"创建时间: {market_details.get('created_at', 'Unknown')}")
                    
                    collector.data_manager.save_json(market_details, f"market_{args.market_id}_details.json")
                    print(f"详细数据已保存到: market_{args.market_id}_details.json")
                else:
                    print("获取市场详细信息失败")
            
        elif args.module == 'price-data':
            from Poly_price_data.price_collector import PriceCollector
            
            logger.info("启动价格数据收集模块")
            collector = PriceCollector()
            
            if args.mode == 'batch':
                if not args.markets:
                    print("批量模式需要指定市场ID列表")
                    return
                
                result = collector.collect_batch_prices(args.markets, args.detailed)
                print(f"\n=== 批量价格收集完成 ===")
                print(f"收集时间: {result['duration_seconds']:.2f} 秒")
                print(f"市场数量: {result['market_count']}")
                
            elif args.mode == 'monitor':
                if not args.markets:
                    print("监控模式需要指定市场ID列表")
                    return
                
                print(f"开始监控 {len(args.markets)} 个市场，间隔 {args.interval} 秒...")
                print("按 Ctrl+C 停止监控")
                
                try:
                    thread = collector.start_continuous_monitoring(args.markets, args.interval)
                    thread.join()
                except KeyboardInterrupt:
                    collector.stop_monitoring()
                    print("\n监控已停止")
                    
            elif args.mode == 'report':
                report = collector.generate_price_report(args.markets, args.days)
                print(f"\n=== 价格报告生成完成 ===")
                print(f"分析市场数量: {len(report['markets_analyzed'])}")
                print(f"分析天数: {report['analysis_period_days']}")
                
            elif args.mode == 'history':
                if not args.markets:
                    print("历史数据模式需要指定市场ID列表")
                    return
                
                # 限制市场数量以避免过长的运行时间
                markets_to_process = args.markets[:args.max_markets]
                if len(args.markets) > args.max_markets:
                    print(f"注意: 限制处理前 {args.max_markets} 个市场（共 {len(args.markets)} 个）")
                
                fidelity_name = {1: "分钟", 60: "小时", 1440: "天"}.get(args.fidelity, f"精度{args.fidelity}")
                print(f"开始收集 {len(markets_to_process)} 个市场的历史价格数据（{fidelity_name}级别）...")
                
                result = collector.collect_batch_price_history(markets_to_process, args.fidelity)
                
                print(f"\n=== 历史价格数据收集完成 ===")
                print(f"收集时间: {result['duration_seconds']:.2f} 秒")
                print(f"处理市场数: {result['market_count']}")
                print(f"成功收集: {len(result['successful_markets'])}")
                print(f"失败收集: {len(result['failed_markets'])}")
                print(f"成功率: {result['success_rate']:.1f}%")
                print(f"数据精度: {fidelity_name}级别")
                
                if result['successful_markets']:
                    print(f"\n成功收集的市场:")
                    for market_id in result['successful_markets'][:5]:  # 只显示前5个
                        market_data = result['markets'].get(market_id, {})
                        data_points = market_data.get('data_points', 0)
                        print(f"  {market_id}: {data_points} 个数据点")
                    
                    if len(result['successful_markets']) > 5:
                        print(f"  ... 还有 {len(result['successful_markets']) - 5} 个市场")
                
                if result['failed_markets']:
                    print(f"\n失败的市场:")
                    for failed in result['failed_markets'][:3]:  # 只显示前3个失败的
                        print(f"  {failed['market_id']}: {failed['reason']}")
                    
                    if len(result['failed_markets']) > 3:
                        print(f"  ... 还有 {len(result['failed_markets']) - 3} 个失败")
                
        elif args.module == 'order-data':
            from Poly_order.order_collector import OrderCollector
            
            logger.info("启动订单数据收集模块")
            collector = OrderCollector()
            
            if args.reset:
                # 重置进度逻辑
                progress_patterns = [
                    f"orders_{args.market or 'all'}_{args.status or 'all'}_progress.json",
                    f"trades_{args.market or 'all'}_progress.json"
                ]
                
                for pattern in progress_patterns:
                    progress_path = DataConfig.ORDER_DATA_DIR / pattern
                    if progress_path.exists():
                        progress_path.unlink()
                        logger.info(f"已重置进度文件: {pattern}")
            
            if args.mode == 'comprehensive':
                summary = collector.run_comprehensive_collection(
                    market=args.market,
                    include_analysis=not args.no_analysis
                )
                
                print(f"\n=== 综合订单数据收集完成 ===")
                print(f"收集时间: {summary['duration_seconds']:.2f} 秒")
                print(f"订单数量: {summary['orders_collected']}")
                print(f"活跃订单: {summary['active_orders']}")
                print(f"交易数量: {summary['trades_collected']}")
                
            elif args.mode == 'orders':
                orders = collector.fetch_all_orders(args.market, args.status)
                print(f"\n=== 订单收集完成 ===")
                print(f"订单数量: {len(orders)}")
                
            elif args.mode == 'trades':
                trades = collector.fetch_all_trades(args.market)
                print(f"\n=== 交易收集完成 ===")
                print(f"交易数量: {len(trades)}")
                
            elif args.mode == 'active':
                active_orders = collector.fetch_active_orders(args.market)
                print(f"\n=== 活跃订单收集完成 ===")
                print(f"活跃订单数量: {len(active_orders)}")
                
        elif args.module == 'user-data':
            from Poly_user_data.user_collector import UserCollector
            
            logger.info("启动用户数据收集模块")
            collector = UserCollector()
            
            if args.mode == 'single':
                if not args.user:
                    print("单个用户模式需要指定用户地址")
                    return
                
                user_data = collector.collect_comprehensive_user_data(args.user)
                print(f"\n=== 用户数据收集完成 ===")
                print(f"用户地址: {user_data['user_address']}")
                print(f"收集时间: {user_data['collection_duration_seconds']:.2f} 秒")
                print(f"订单数量: {len(user_data['orders'])}")
                print(f"交易数量: {len(user_data['trades'])}")
                
            elif args.mode == 'batch':
                user_addresses = []
                
                if args.users_file:
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
                
                batch_result = collector.batch_collect_users(user_addresses)
                print(f"\n=== 批量用户数据收集完成 ===")
                print(f"总用户数: {batch_result['total_users']}")
                print(f"成功收集: {batch_result['successful_collections']}")
                print(f"失败收集: {batch_result['failed_collections']}")
                
        elif args.module == 'fluctuation':
            from Poly_market_fluctuation.fluctuation_monitor import FluctuationMonitor
            
            logger.info("启动市场波动监控模块")
            monitor = FluctuationMonitor()
            
            # 设置自定义参数
            monitor.price_change_threshold = args.threshold
            monitor.rate_limiter.delay = args.interval
            
            print(f"开始监控 {len(args.markets)} 个市场")
            print(f"价格变化阈值: {args.threshold * 100:.1f}%")
            print(f"检查间隔: {args.interval} 秒")
            
            try:
                if args.background:
                    thread = monitor.start_background_monitoring(args.markets, args.duration)
                    print("后台监控已启动，按 Ctrl+C 停止")
                    
                    try:
                        while monitor.is_monitoring:
                            import time
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\n正在停止监控...")
                        monitor.stop_monitoring()
                else:
                    print("开始监控，按 Ctrl+C 停止")
                    monitor.monitor_markets(args.markets, args.duration)
                    
            except KeyboardInterrupt:
                print("\n监控已停止")
            
            print("监控完成")
            
    except ImportError as e:
        logger.error(f"模块导入失败: {e}")
        print(f"错误: 无法导入模块 {args.module}")
        print("请确保所有依赖都已正确安装")
    except Exception as e:
        logger.error(f"运行模块 {args.module} 时发生错误: {e}")
        print(f"错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    logger.info("程序执行完成")

if __name__ == "__main__":
    main() 
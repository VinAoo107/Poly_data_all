"""
数据关联管理器
用于建立和维护Polymarket各个模块数据之间的关联关系
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict

# 添加当前目录到路径
sys.path.append(str(Path(__file__).parent))

from config import DataConfig
from utils import Logger, DataManager

@dataclass
class MarketRelationship:
    """市场关联关系数据结构"""
    market_id: str
    event_id: Optional[str] = None
    market_name: Optional[str] = None
    market_status: Optional[str] = None
    created_at: Optional[str] = None
    last_updated: Optional[str] = None

@dataclass
class UserMarketActivity:
    """用户市场活动数据结构"""
    user_address: str
    market_id: str
    total_orders: int = 0
    total_trades: int = 0
    total_volume: float = 0.0
    first_activity: Optional[str] = None
    last_activity: Optional[str] = None
    position_value: float = 0.0

@dataclass
class MarketPriceSnapshot:
    """市场价格快照数据结构"""
    market_id: str
    timestamp: str
    price: float
    volume_24h: float = 0.0
    price_change_24h: float = 0.0
    volatility: float = 0.0

class DataRelationshipManager:
    """数据关联管理器"""
    
    def __init__(self):
        """初始化数据关联管理器"""
        self.logger = Logger.setup_logger(
            "DataRelationshipManager", 
            "data_relationship.log"
        )
        
        # 初始化数据管理器
        self.relationship_dir = DataConfig.PROJECT_ROOT / "data_relationships"
        self.relationship_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_manager = DataManager(self.relationship_dir, self.logger)
        
        # 初始化SQLite数据库用于快速查询
        self.db_path = self.relationship_dir / "relationships.db"
        self.init_database()
        
        # 内存缓存
        self.market_cache = {}
        self.user_cache = {}
        self.price_cache = {}
        
        self.logger.info("数据关联管理器初始化完成")
    
    def init_database(self):
        """初始化SQLite数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建市场关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_relationships (
                    market_id TEXT PRIMARY KEY,
                    event_id TEXT,
                    market_name TEXT,
                    market_status TEXT,
                    created_at TEXT,
                    last_updated TEXT
                )
            ''')
            
            # 创建用户市场活动表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_market_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_address TEXT,
                    market_id TEXT,
                    total_orders INTEGER DEFAULT 0,
                    total_trades INTEGER DEFAULT 0,
                    total_volume REAL DEFAULT 0.0,
                    first_activity TEXT,
                    last_activity TEXT,
                    position_value REAL DEFAULT 0.0,
                    UNIQUE(user_address, market_id)
                )
            ''')
            
            # 创建市场价格快照表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_price_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT,
                    timestamp TEXT,
                    price REAL,
                    volume_24h REAL DEFAULT 0.0,
                    price_change_24h REAL DEFAULT 0.0,
                    volatility REAL DEFAULT 0.0
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_market ON user_market_activities(user_address, market_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_timestamp ON market_price_snapshots(market_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_status ON market_relationships(market_status)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("数据库初始化完成")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
    
    def update_market_relationships(self, events_data: List[Dict], markets_data: List[Dict] = None):
        """
        更新市场关联关系
        
        参数:
            events_data: 事件数据列表
            markets_data: 市场数据列表（可选）
        """
        self.logger.info(f"更新市场关联关系，事件数量: {len(events_data)}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 处理事件数据
            for event in events_data:
                event_id = event.get("id")
                markets = event.get("markets", [])
                
                for market in markets:
                    market_id = market.get("id")
                    if not market_id:
                        continue
                    
                    relationship = MarketRelationship(
                        market_id=market_id,
                        event_id=event_id,
                        market_name=market.get("question", ""),
                        market_status=market.get("status", ""),
                        created_at=event.get("created_at"),
                        last_updated=datetime.now(timezone.utc).isoformat()
                    )
                    
                    # 插入或更新数据库
                    cursor.execute('''
                        INSERT OR REPLACE INTO market_relationships 
                        (market_id, event_id, market_name, market_status, created_at, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        relationship.market_id,
                        relationship.event_id,
                        relationship.market_name,
                        relationship.market_status,
                        relationship.created_at,
                        relationship.last_updated
                    ))
                    
                    # 更新缓存
                    self.market_cache[market_id] = relationship
            
            # 处理额外的市场数据
            if markets_data:
                for market in markets_data:
                    market_id = market.get("id")
                    if not market_id:
                        continue
                    
                    # 检查是否已存在
                    cursor.execute('SELECT market_id FROM market_relationships WHERE market_id = ?', (market_id,))
                    if not cursor.fetchone():
                        relationship = MarketRelationship(
                            market_id=market_id,
                            market_name=market.get("question", ""),
                            market_status=market.get("status", ""),
                            created_at=market.get("created_at"),
                            last_updated=datetime.now(timezone.utc).isoformat()
                        )
                        
                        cursor.execute('''
                            INSERT INTO market_relationships 
                            (market_id, event_id, market_name, market_status, created_at, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            relationship.market_id,
                            relationship.event_id,
                            relationship.market_name,
                            relationship.market_status,
                            relationship.created_at,
                            relationship.last_updated
                        ))
                        
                        self.market_cache[market_id] = relationship
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"市场关联关系更新完成，共处理 {len(self.market_cache)} 个市场")
            
        except Exception as e:
            self.logger.error(f"更新市场关联关系失败: {e}")
    
    def update_user_market_activities(self, user_data: Dict, orders_data: List[Dict] = None, trades_data: List[Dict] = None):
        """
        更新用户市场活动数据
        
        参数:
            user_data: 用户数据
            orders_data: 订单数据列表
            trades_data: 交易数据列表
        """
        user_address = user_data.get("user_address")
        if not user_address:
            return
        
        self.logger.info(f"更新用户 {user_address} 的市场活动数据")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 统计用户在各个市场的活动
            market_activities = defaultdict(lambda: {
                'orders': 0,
                'trades': 0,
                'volume': 0.0,
                'first_activity': None,
                'last_activity': None,
                'position_value': 0.0
            })
            
            # 处理订单数据
            orders = orders_data or user_data.get("orders", [])
            for order in orders:
                market_id = order.get("market")
                if not market_id:
                    continue
                
                market_activities[market_id]['orders'] += 1
                
                # 更新活动时间
                order_time = order.get("created_at")
                if order_time:
                    if not market_activities[market_id]['first_activity'] or order_time < market_activities[market_id]['first_activity']:
                        market_activities[market_id]['first_activity'] = order_time
                    if not market_activities[market_id]['last_activity'] or order_time > market_activities[market_id]['last_activity']:
                        market_activities[market_id]['last_activity'] = order_time
            
            # 处理交易数据
            trades = trades_data or user_data.get("trades", [])
            for trade in trades:
                market_id = trade.get("market")
                if not market_id:
                    continue
                
                market_activities[market_id]['trades'] += 1
                
                # 累计交易量
                volume = trade.get("volume", 0)
                try:
                    market_activities[market_id]['volume'] += float(volume)
                except (ValueError, TypeError):
                    pass
                
                # 更新活动时间
                trade_time = trade.get("timestamp")
                if trade_time:
                    if not market_activities[market_id]['first_activity'] or trade_time < market_activities[market_id]['first_activity']:
                        market_activities[market_id]['first_activity'] = trade_time
                    if not market_activities[market_id]['last_activity'] or trade_time > market_activities[market_id]['last_activity']:
                        market_activities[market_id]['last_activity'] = trade_time
            
            # 处理持仓数据
            positions = user_data.get("positions", {})
            if isinstance(positions, dict) and "positions" in positions:
                for position in positions["positions"]:
                    market_id = position.get("market")
                    if not market_id:
                        continue
                    
                    try:
                        position_value = float(position.get("value", 0))
                        market_activities[market_id]['position_value'] = position_value
                    except (ValueError, TypeError):
                        pass
            
            # 保存到数据库
            for market_id, activity in market_activities.items():
                user_activity = UserMarketActivity(
                    user_address=user_address,
                    market_id=market_id,
                    total_orders=activity['orders'],
                    total_trades=activity['trades'],
                    total_volume=activity['volume'],
                    first_activity=activity['first_activity'],
                    last_activity=activity['last_activity'],
                    position_value=activity['position_value']
                )
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_market_activities 
                    (user_address, market_id, total_orders, total_trades, total_volume, 
                     first_activity, last_activity, position_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_activity.user_address,
                    user_activity.market_id,
                    user_activity.total_orders,
                    user_activity.total_trades,
                    user_activity.total_volume,
                    user_activity.first_activity,
                    user_activity.last_activity,
                    user_activity.position_value
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"用户 {user_address} 的市场活动数据更新完成，涉及 {len(market_activities)} 个市场")
            
        except Exception as e:
            self.logger.error(f"更新用户市场活动数据失败: {e}")
    
    def update_market_price_snapshots(self, price_data: Dict, market_analysis: Dict = None):
        """
        更新市场价格快照
        
        参数:
            price_data: 价格数据
            market_analysis: 市场分析数据（可选）
        """
        self.logger.info("更新市场价格快照")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # 处理价格数据
            if isinstance(price_data, dict):
                for market_id, price_info in price_data.items():
                    if market_id == "timestamp" or not isinstance(price_info, dict):
                        continue
                    
                    price = price_info.get("price", 0)
                    try:
                        price = float(price)
                    except (ValueError, TypeError):
                        continue
                    
                    # 获取额外的分析数据
                    volume_24h = 0.0
                    price_change_24h = 0.0
                    volatility = 0.0
                    
                    if market_analysis and market_id in market_analysis:
                        analysis = market_analysis[market_id]
                        volume_24h = analysis.get("volume_24h", 0.0)
                        price_change_24h = analysis.get("price_change_24h", 0.0)
                        volatility = analysis.get("volatility", 0.0)
                    
                    snapshot = MarketPriceSnapshot(
                        market_id=market_id,
                        timestamp=timestamp,
                        price=price,
                        volume_24h=volume_24h,
                        price_change_24h=price_change_24h,
                        volatility=volatility
                    )
                    
                    cursor.execute('''
                        INSERT INTO market_price_snapshots 
                        (market_id, timestamp, price, volume_24h, price_change_24h, volatility)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        snapshot.market_id,
                        snapshot.timestamp,
                        snapshot.price,
                        snapshot.volume_24h,
                        snapshot.price_change_24h,
                        snapshot.volatility
                    ))
            
            conn.commit()
            conn.close()
            
            self.logger.info("市场价格快照更新完成")
            
        except Exception as e:
            self.logger.error(f"更新市场价格快照失败: {e}")
    
    def get_market_comprehensive_data(self, market_id: str) -> Dict[str, Any]:
        """
        获取市场的综合数据
        
        参数:
            market_id: 市场ID
            
        返回:
            市场综合数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            comprehensive_data = {
                "market_id": market_id,
                "market_info": None,
                "recent_prices": [],
                "active_users": [],
                "trading_statistics": {},
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # 获取市场基本信息
            cursor.execute('SELECT * FROM market_relationships WHERE market_id = ?', (market_id,))
            market_row = cursor.fetchone()
            if market_row:
                comprehensive_data["market_info"] = {
                    "market_id": market_row[0],
                    "event_id": market_row[1],
                    "market_name": market_row[2],
                    "market_status": market_row[3],
                    "created_at": market_row[4],
                    "last_updated": market_row[5]
                }
            
            # 获取最近的价格数据
            cursor.execute('''
                SELECT timestamp, price, volume_24h, price_change_24h, volatility 
                FROM market_price_snapshots 
                WHERE market_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 100
            ''', (market_id,))
            
            price_rows = cursor.fetchall()
            comprehensive_data["recent_prices"] = [
                {
                    "timestamp": row[0],
                    "price": row[1],
                    "volume_24h": row[2],
                    "price_change_24h": row[3],
                    "volatility": row[4]
                }
                for row in price_rows
            ]
            
            # 获取活跃用户
            cursor.execute('''
                SELECT user_address, total_orders, total_trades, total_volume, position_value
                FROM user_market_activities 
                WHERE market_id = ? AND (total_orders > 0 OR total_trades > 0)
                ORDER BY total_volume DESC 
                LIMIT 50
            ''', (market_id,))
            
            user_rows = cursor.fetchall()
            comprehensive_data["active_users"] = [
                {
                    "user_address": row[0],
                    "total_orders": row[1],
                    "total_trades": row[2],
                    "total_volume": row[3],
                    "position_value": row[4]
                }
                for row in user_rows
            ]
            
            # 计算交易统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as user_count,
                    SUM(total_orders) as total_orders,
                    SUM(total_trades) as total_trades,
                    SUM(total_volume) as total_volume,
                    AVG(total_volume) as avg_volume_per_user
                FROM user_market_activities 
                WHERE market_id = ?
            ''', (market_id,))
            
            stats_row = cursor.fetchone()
            if stats_row:
                comprehensive_data["trading_statistics"] = {
                    "total_users": stats_row[0],
                    "total_orders": stats_row[1],
                    "total_trades": stats_row[2],
                    "total_volume": stats_row[3],
                    "avg_volume_per_user": stats_row[4]
                }
            
            conn.close()
            
            return comprehensive_data
            
        except Exception as e:
            self.logger.error(f"获取市场综合数据失败: {e}")
            return {}
    
    def get_user_comprehensive_data(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户的综合数据
        
        参数:
            user_address: 用户地址
            
        返回:
            用户综合数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            comprehensive_data = {
                "user_address": user_address,
                "market_activities": [],
                "trading_summary": {},
                "portfolio_overview": {},
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # 获取用户的市场活动
            cursor.execute('''
                SELECT uma.*, mr.market_name, mr.market_status
                FROM user_market_activities uma
                LEFT JOIN market_relationships mr ON uma.market_id = mr.market_id
                WHERE uma.user_address = ?
                ORDER BY uma.total_volume DESC
            ''', (user_address,))
            
            activity_rows = cursor.fetchall()
            comprehensive_data["market_activities"] = [
                {
                    "market_id": row[2],
                    "market_name": row[9],
                    "market_status": row[10],
                    "total_orders": row[3],
                    "total_trades": row[4],
                    "total_volume": row[5],
                    "first_activity": row[6],
                    "last_activity": row[7],
                    "position_value": row[8]
                }
                for row in activity_rows
            ]
            
            # 计算交易摘要
            cursor.execute('''
                SELECT 
                    COUNT(*) as markets_count,
                    SUM(total_orders) as total_orders,
                    SUM(total_trades) as total_trades,
                    SUM(total_volume) as total_volume,
                    SUM(position_value) as total_position_value,
                    MIN(first_activity) as first_activity,
                    MAX(last_activity) as last_activity
                FROM user_market_activities 
                WHERE user_address = ?
            ''', (user_address,))
            
            summary_row = cursor.fetchone()
            if summary_row:
                comprehensive_data["trading_summary"] = {
                    "active_markets": summary_row[0],
                    "total_orders": summary_row[1],
                    "total_trades": summary_row[2],
                    "total_volume": summary_row[3],
                    "total_position_value": summary_row[4],
                    "first_activity": summary_row[5],
                    "last_activity": summary_row[6]
                }
            
            # 投资组合概览
            cursor.execute('''
                SELECT market_id, position_value
                FROM user_market_activities 
                WHERE user_address = ? AND position_value > 0
                ORDER BY position_value DESC
            ''', (user_address,))
            
            portfolio_rows = cursor.fetchall()
            comprehensive_data["portfolio_overview"] = {
                "positions_count": len(portfolio_rows),
                "positions": [
                    {"market_id": row[0], "value": row[1]}
                    for row in portfolio_rows
                ]
            }
            
            conn.close()
            
            return comprehensive_data
            
        except Exception as e:
            self.logger.error(f"获取用户综合数据失败: {e}")
            return {}
    
    def get_market_correlations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取市场关联分析
        
        参数:
            limit: 返回结果数量限制
            
        返回:
            市场关联分析结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 找出共同用户最多的市场对
            cursor.execute('''
                SELECT 
                    uma1.market_id as market1,
                    uma2.market_id as market2,
                    COUNT(*) as common_users,
                    AVG(uma1.total_volume + uma2.total_volume) as avg_combined_volume
                FROM user_market_activities uma1
                JOIN user_market_activities uma2 ON uma1.user_address = uma2.user_address
                WHERE uma1.market_id < uma2.market_id
                GROUP BY uma1.market_id, uma2.market_id
                HAVING common_users >= 2
                ORDER BY common_users DESC, avg_combined_volume DESC
                LIMIT ?
            ''', (limit,))
            
            correlation_rows = cursor.fetchall()
            
            correlations = []
            for row in correlation_rows:
                # 获取市场名称
                cursor.execute('SELECT market_name FROM market_relationships WHERE market_id = ?', (row[0],))
                market1_name = cursor.fetchone()
                cursor.execute('SELECT market_name FROM market_relationships WHERE market_id = ?', (row[1],))
                market2_name = cursor.fetchone()
                
                correlations.append({
                    "market1_id": row[0],
                    "market1_name": market1_name[0] if market1_name else "Unknown",
                    "market2_id": row[1],
                    "market2_name": market2_name[0] if market2_name else "Unknown",
                    "common_users": row[2],
                    "avg_combined_volume": row[3]
                })
            
            conn.close()
            
            return correlations
            
        except Exception as e:
            self.logger.error(f"获取市场关联分析失败: {e}")
            return []
    
    def export_comprehensive_report(self) -> Dict[str, Any]:
        """
        导出综合报告
        
        返回:
            综合报告数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            report = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {},
                "top_markets": [],
                "top_users": [],
                "market_correlations": [],
                "recent_activity": {}
            }
            
            # 总体统计
            cursor.execute('SELECT COUNT(*) FROM market_relationships')
            total_markets = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT user_address) FROM user_market_activities')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(total_volume) FROM user_market_activities')
            total_volume = cursor.fetchone()[0] or 0
            
            report["summary"] = {
                "total_markets": total_markets,
                "total_users": total_users,
                "total_volume": total_volume
            }
            
            # 热门市场
            cursor.execute('''
                SELECT 
                    mr.market_id,
                    mr.market_name,
                    COUNT(DISTINCT uma.user_address) as user_count,
                    SUM(uma.total_volume) as total_volume
                FROM market_relationships mr
                LEFT JOIN user_market_activities uma ON mr.market_id = uma.market_id
                GROUP BY mr.market_id, mr.market_name
                ORDER BY user_count DESC, total_volume DESC
                LIMIT 10
            ''')
            
            top_market_rows = cursor.fetchall()
            report["top_markets"] = [
                {
                    "market_id": row[0],
                    "market_name": row[1],
                    "user_count": row[2],
                    "total_volume": row[3]
                }
                for row in top_market_rows
            ]
            
            # 活跃用户
            cursor.execute('''
                SELECT 
                    user_address,
                    COUNT(DISTINCT market_id) as markets_count,
                    SUM(total_volume) as total_volume,
                    SUM(total_trades) as total_trades
                FROM user_market_activities
                GROUP BY user_address
                ORDER BY total_volume DESC
                LIMIT 10
            ''')
            
            top_user_rows = cursor.fetchall()
            report["top_users"] = [
                {
                    "user_address": row[0],
                    "markets_count": row[1],
                    "total_volume": row[2],
                    "total_trades": row[3]
                }
                for row in top_user_rows
            ]
            
            # 市场关联
            report["market_correlations"] = self.get_market_correlations(10)
            
            conn.close()
            
            # 保存报告
            report_filename = f"comprehensive_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            self.data_manager.save_json(report, report_filename)
            
            self.logger.info(f"综合报告导出完成: {report_filename}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"导出综合报告失败: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        清理旧数据
        
        参数:
            days_to_keep: 保留数据的天数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).isoformat()
            
            # 清理旧的价格快照
            cursor.execute('DELETE FROM market_price_snapshots WHERE timestamp < ?', (cutoff_date,))
            deleted_snapshots = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"数据清理完成，删除了 {deleted_snapshots} 条旧的价格快照")
            
        except Exception as e:
            self.logger.error(f"数据清理失败: {e}") 
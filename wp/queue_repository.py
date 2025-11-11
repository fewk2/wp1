"""
队列存储层
提供转存和分享任务队列的数据库CRUD操作
"""
import json
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from config import get_config, Config
from logger import get_logger

logger = get_logger(__name__)


class QueueRepository:
    """队列数据库操作类"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化队列仓库
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
        
    def _get_db_connection(self):
        """获取数据库连接"""
        if self.config.DATABASE_TYPE == 'sqlite':
            conn = sqlite3.connect(self.config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            return conn
        elif self.config.DATABASE_TYPE == 'mysql':
            import pymysql
            import pymysql.cursors
            return pymysql.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DATABASE,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        elif self.config.DATABASE_TYPE == 'postgresql':
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(
                host=self.config.POSTGRES_HOST,
                port=self.config.POSTGRES_PORT,
                user=self.config.POSTGRES_USER,
                password=self.config.POSTGRES_PASSWORD,
                database=self.config.POSTGRES_DATABASE
            )
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            return conn
        else:
            raise ValueError(f"不支持的数据库类型: {self.config.DATABASE_TYPE}")
    
    def _format_placeholder(self, index: int = 0) -> str:
        """获取参数占位符"""
        if self.config.DATABASE_TYPE == 'postgresql':
            return f"${index + 1}"
        elif self.config.DATABASE_TYPE == 'mysql':
            return "%s"
        else:  # SQLite
            return "?"
    
    # ==================== 转存任务操作 ====================
    
    def fetch_transfer_queue(self, account: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取转存队列（按order_index排序）
        
        Args:
            account: 账户名
            status: 可选的状态过滤
            
        Returns:
            任务列表
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if status:
                if self.config.DATABASE_TYPE == 'postgresql':
                    query = "SELECT * FROM transfer_tasks WHERE account = $1 AND status = $2 ORDER BY order_index ASC, id ASC"
                elif self.config.DATABASE_TYPE == 'mysql':
                    query = "SELECT * FROM transfer_tasks WHERE account = %s AND status = %s ORDER BY order_index ASC, id ASC"
                else:  # SQLite
                    query = "SELECT * FROM transfer_tasks WHERE account = ? AND status = ? ORDER BY order_index ASC, id ASC"
                cursor.execute(query, (account, status))
            else:
                if self.config.DATABASE_TYPE == 'postgresql':
                    query = "SELECT * FROM transfer_tasks WHERE account = $1 ORDER BY order_index ASC, id ASC"
                elif self.config.DATABASE_TYPE == 'mysql':
                    query = "SELECT * FROM transfer_tasks WHERE account = %s ORDER BY order_index ASC, id ASC"
                else:  # SQLite
                    query = "SELECT * FROM transfer_tasks WHERE account = ? ORDER BY order_index ASC, id ASC"
                cursor.execute(query, (account,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            tasks = []
            for row in rows:
                task = dict(row)
                # 解析metadata
                if task.get('metadata'):
                    try:
                        task['metadata'] = json.loads(task['metadata'])
                    except:
                        task['metadata'] = {}
                else:
                    task['metadata'] = {}
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取转存队列失败: {e}")
            return []
    
    def insert_transfer_task(self, account: str, task: Dict[str, Any]) -> Optional[int]:
        """
        插入转存任务
        
        Args:
            account: 账户名
            task: 任务数据
            
        Returns:
            插入的任务ID，失败返回None
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # 序列化metadata
            metadata = json.dumps(task.get('metadata', {})) if task.get('metadata') else None
            
            # 获取下一个order_index
            if self.config.DATABASE_TYPE == 'postgresql':
                cursor.execute("SELECT COALESCE(MAX(order_index), -1) + 1 FROM transfer_tasks WHERE account = $1", (account,))
            elif self.config.DATABASE_TYPE == 'mysql':
                cursor.execute("SELECT COALESCE(MAX(order_index), -1) + 1 FROM transfer_tasks WHERE account = %s", (account,))
            else:  # SQLite
                cursor.execute("SELECT COALESCE(MAX(order_index), -1) + 1 FROM transfer_tasks WHERE account = ?", (account,))
            next_order = cursor.fetchone()
            if self.config.DATABASE_TYPE == 'sqlite':
                next_order = next_order[0] if isinstance(next_order, tuple) else next_order['COALESCE(MAX(order_index), -1) + 1']
            else:
                next_order = list(next_order.values())[0]
            
            # 插入任务
            if self.config.DATABASE_TYPE == 'postgresql':
                query = """
                    INSERT INTO transfer_tasks (
                        account, share_link, share_password, target_path, status,
                        error_message, filename, title, order_index, auto_share, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING id
                """
            elif self.config.DATABASE_TYPE == 'mysql':
                query = """
                    INSERT INTO transfer_tasks (
                        account, share_link, share_password, target_path, status,
                        error_message, filename, title, order_index, auto_share, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            else:  # SQLite
                query = """
                    INSERT INTO transfer_tasks (
                        account, share_link, share_password, target_path, status,
                        error_message, filename, title, order_index, auto_share, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            
            cursor.execute(query, (
                account,
                task.get('share_link', ''),
                task.get('share_password', ''),
                task.get('target_path', '/批量转存'),
                task.get('status', 'pending'),
                task.get('error_message', ''),
                task.get('filename', ''),
                task.get('title', ''),
                task.get('order_index', next_order),
                1 if task.get('auto_share', False) else 0,
                metadata
            ))
            
            if self.config.DATABASE_TYPE == 'postgresql':
                task_id = cursor.fetchone()['id']
            else:
                task_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return task_id
            
        except Exception as e:
            logger.error(f"插入转存任务失败: {e}")
            return None
    
    def update_transfer_task(self, task_id: int, updates: Dict[str, Any]) -> bool:
        """
        更新转存任务
        
        Args:
            task_id: 任务ID
            updates: 要更新的字段
            
        Returns:
            是否成功
        """
        try:
            if not updates:
                return True
            
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # 构建更新语句
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'metadata' and isinstance(value, dict):
                    value = json.dumps(value)
                if self.config.DATABASE_TYPE == 'sqlite':
                    set_clauses.append(f"{key} = ?")
                elif self.config.DATABASE_TYPE == 'mysql':
                    set_clauses.append(f"{key} = %s")
                else:  # PostgreSQL
                    set_clauses.append(f"{key} = ${len(values) + 1}")
                values.append(value)
            
            # 添加 updated_at
            if self.config.DATABASE_TYPE == 'sqlite':
                set_clauses.append(f"updated_at = ?")
            elif self.config.DATABASE_TYPE == 'mysql':
                set_clauses.append(f"updated_at = %s")
            else:  # PostgreSQL
                set_clauses.append(f"updated_at = ${len(values) + 1}")
            values.append(datetime.now())
            
            values.append(task_id)
            
            if self.config.DATABASE_TYPE == 'sqlite':
                where_clause = "WHERE id = ?"
            elif self.config.DATABASE_TYPE == 'mysql':
                where_clause = "WHERE id = %s"
            else:  # PostgreSQL
                where_clause = f"WHERE id = ${len(values)}"
            
            query = f"UPDATE transfer_tasks SET {', '.join(set_clauses)} {where_clause}"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"更新转存任务失败: {e}")
            return False
    
    def delete_transfer_task(self, task_id: int) -> bool:
        """
        删除转存任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.config.DATABASE_TYPE == 'postgresql':
                cursor.execute("DELETE FROM transfer_tasks WHERE id = $1", (task_id,))
            elif self.config.DATABASE_TYPE == 'mysql':
                cursor.execute("DELETE FROM transfer_tasks WHERE id = %s", (task_id,))
            else:  # SQLite
                cursor.execute("DELETE FROM transfer_tasks WHERE id = ?", (task_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"删除转存任务失败: {e}")
            return False
    
    def reorder_transfer_tasks(self, account: str, task_ids: List[int]) -> bool:
        """
        重新排序转存任务
        
        Args:
            account: 账户名
            task_ids: 任务ID列表（按新顺序）
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # 批量更新order_index
            for index, task_id in enumerate(task_ids):
                if self.config.DATABASE_TYPE == 'postgresql':
                    cursor.execute(
                        "UPDATE transfer_tasks SET order_index = $1 WHERE id = $2 AND account = $3",
                        (index, task_id, account)
                    )
                elif self.config.DATABASE_TYPE == 'mysql':
                    cursor.execute(
                        "UPDATE transfer_tasks SET order_index = %s WHERE id = %s AND account = %s",
                        (index, task_id, account)
                    )
                else:  # SQLite
                    cursor.execute(
                        "UPDATE transfer_tasks SET order_index = ? WHERE id = ? AND account = ?",
                        (index, task_id, account)
                    )
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"重新排序转存任务失败: {e}")
            return False
    
    def clear_transfer_tasks(self, account: str, status: Optional[str] = None) -> int:
        """
        清空转存任务
        
        Args:
            account: 账户名
            status: 可选的状态过滤
            
        Returns:
            删除的任务数量
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if status:
                if self.config.DATABASE_TYPE == 'postgresql':
                    cursor.execute("DELETE FROM transfer_tasks WHERE account = $1 AND status = $2", (account, status))
                elif self.config.DATABASE_TYPE == 'mysql':
                    cursor.execute("DELETE FROM transfer_tasks WHERE account = %s AND status = %s", (account, status))
                else:  # SQLite
                    cursor.execute("DELETE FROM transfer_tasks WHERE account = ? AND status = ?", (account, status))
            else:
                if self.config.DATABASE_TYPE == 'postgresql':
                    cursor.execute("DELETE FROM transfer_tasks WHERE account = $1", (account,))
                elif self.config.DATABASE_TYPE == 'mysql':
                    cursor.execute("DELETE FROM transfer_tasks WHERE account = %s", (account,))
                else:  # SQLite
                    cursor.execute("DELETE FROM transfer_tasks WHERE account = ?", (account,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"清空转存任务失败: {e}")
            return 0
    
    # ==================== 分享任务操作 ====================
    
    def fetch_share_queue(self, account: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取分享队列（按order_index排序）
        
        Args:
            account: 账户名
            status: 可选的状态过滤
            
        Returns:
            任务列表
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if status:
                if self.config.DATABASE_TYPE == 'postgresql':
                    query = "SELECT * FROM share_tasks WHERE account = $1 AND status = $2 ORDER BY order_index ASC, id ASC"
                elif self.config.DATABASE_TYPE == 'mysql':
                    query = "SELECT * FROM share_tasks WHERE account = %s AND status = %s ORDER BY order_index ASC, id ASC"
                else:  # SQLite
                    query = "SELECT * FROM share_tasks WHERE account = ? AND status = ? ORDER BY order_index ASC, id ASC"
                cursor.execute(query, (account, status))
            else:
                if self.config.DATABASE_TYPE == 'postgresql':
                    query = "SELECT * FROM share_tasks WHERE account = $1 ORDER BY order_index ASC, id ASC"
                elif self.config.DATABASE_TYPE == 'mysql':
                    query = "SELECT * FROM share_tasks WHERE account = %s ORDER BY order_index ASC, id ASC"
                else:  # SQLite
                    query = "SELECT * FROM share_tasks WHERE account = ? ORDER BY order_index ASC, id ASC"
                cursor.execute(query, (account,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            tasks = []
            for row in rows:
                task = dict(row)
                # 解析metadata
                if task.get('metadata'):
                    try:
                        task['metadata'] = json.loads(task['metadata'])
                    except:
                        task['metadata'] = {}
                else:
                    task['metadata'] = {}
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取分享队列失败: {e}")
            return []
    
    def insert_share_task(self, account: str, task: Dict[str, Any]) -> Optional[int]:
        """
        插入分享任务
        
        Args:
            account: 账户名
            task: 任务数据
            
        Returns:
            插入的任务ID，失败返回None
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # 序列化metadata
            metadata = json.dumps(task.get('metadata', {})) if task.get('metadata') else None
            
            # 获取下一个order_index
            if self.config.DATABASE_TYPE == 'postgresql':
                cursor.execute("SELECT COALESCE(MAX(order_index), -1) + 1 FROM share_tasks WHERE account = $1", (account,))
            elif self.config.DATABASE_TYPE == 'mysql':
                cursor.execute("SELECT COALESCE(MAX(order_index), -1) + 1 FROM share_tasks WHERE account = %s", (account,))
            else:  # SQLite
                cursor.execute("SELECT COALESCE(MAX(order_index), -1) + 1 FROM share_tasks WHERE account = ?", (account,))
            next_order = cursor.fetchone()
            if self.config.DATABASE_TYPE == 'sqlite':
                next_order = next_order[0] if isinstance(next_order, tuple) else next_order['COALESCE(MAX(order_index), -1) + 1']
            else:
                next_order = list(next_order.values())[0]
            
            # 插入任务
            if self.config.DATABASE_TYPE == 'postgresql':
                query = """
                    INSERT INTO share_tasks (
                        account, file_path, fs_id, expiry, password_mode,
                        share_password, share_link, status, error_message, title, order_index, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id
                """
            elif self.config.DATABASE_TYPE == 'mysql':
                query = """
                    INSERT INTO share_tasks (
                        account, file_path, fs_id, expiry, password_mode,
                        share_password, share_link, status, error_message, title, order_index, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            else:  # SQLite
                query = """
                    INSERT INTO share_tasks (
                        account, file_path, fs_id, expiry, password_mode,
                        share_password, share_link, status, error_message, title, order_index, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            
            cursor.execute(query, (
                account,
                task.get('file_path', ''),
                task.get('fs_id', ''),
                task.get('expiry', 7),
                task.get('password_mode', 'random'),
                task.get('share_password', ''),
                task.get('share_link', ''),
                task.get('status', 'pending'),
                task.get('error_message', ''),
                task.get('title', ''),
                task.get('order_index', next_order),
                metadata
            ))
            
            if self.config.DATABASE_TYPE == 'postgresql':
                task_id = cursor.fetchone()['id']
            else:
                task_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return task_id
            
        except Exception as e:
            logger.error(f"插入分享任务失败: {e}")
            return None
    
    def update_share_task(self, task_id: int, updates: Dict[str, Any]) -> bool:
        """
        更新分享任务
        
        Args:
            task_id: 任务ID
            updates: 要更新的字段
            
        Returns:
            是否成功
        """
        try:
            if not updates:
                return True
            
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # 构建更新语句
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'metadata' and isinstance(value, dict):
                    value = json.dumps(value)
                if self.config.DATABASE_TYPE == 'sqlite':
                    set_clauses.append(f"{key} = ?")
                elif self.config.DATABASE_TYPE == 'mysql':
                    set_clauses.append(f"{key} = %s")
                else:  # PostgreSQL
                    set_clauses.append(f"{key} = ${len(values) + 1}")
                values.append(value)
            
            # 添加 updated_at
            if self.config.DATABASE_TYPE == 'sqlite':
                set_clauses.append(f"updated_at = ?")
            elif self.config.DATABASE_TYPE == 'mysql':
                set_clauses.append(f"updated_at = %s")
            else:  # PostgreSQL
                set_clauses.append(f"updated_at = ${len(values) + 1}")
            values.append(datetime.now())
            
            values.append(task_id)
            
            if self.config.DATABASE_TYPE == 'sqlite':
                where_clause = "WHERE id = ?"
            elif self.config.DATABASE_TYPE == 'mysql':
                where_clause = "WHERE id = %s"
            else:  # PostgreSQL
                where_clause = f"WHERE id = ${len(values)}"
            
            query = f"UPDATE share_tasks SET {', '.join(set_clauses)} {where_clause}"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"更新分享任务失败: {e}")
            return False
    
    def delete_share_task(self, task_id: int) -> bool:
        """
        删除分享任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.config.DATABASE_TYPE == 'postgresql':
                cursor.execute("DELETE FROM share_tasks WHERE id = $1", (task_id,))
            elif self.config.DATABASE_TYPE == 'mysql':
                cursor.execute("DELETE FROM share_tasks WHERE id = %s", (task_id,))
            else:  # SQLite
                cursor.execute("DELETE FROM share_tasks WHERE id = ?", (task_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"删除分享任务失败: {e}")
            return False
    
    def reorder_share_tasks(self, account: str, task_ids: List[int]) -> bool:
        """
        重新排序分享任务
        
        Args:
            account: 账户名
            task_ids: 任务ID列表（按新顺序）
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # 批量更新order_index
            for index, task_id in enumerate(task_ids):
                if self.config.DATABASE_TYPE == 'postgresql':
                    cursor.execute(
                        "UPDATE share_tasks SET order_index = $1 WHERE id = $2 AND account = $3",
                        (index, task_id, account)
                    )
                elif self.config.DATABASE_TYPE == 'mysql':
                    cursor.execute(
                        "UPDATE share_tasks SET order_index = %s WHERE id = %s AND account = %s",
                        (index, task_id, account)
                    )
                else:  # SQLite
                    cursor.execute(
                        "UPDATE share_tasks SET order_index = ? WHERE id = ? AND account = ?",
                        (index, task_id, account)
                    )
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"重新排序分享任务失败: {e}")
            return False
    
    def clear_share_tasks(self, account: str, status: Optional[str] = None) -> int:
        """
        清空分享任务
        
        Args:
            account: 账户名
            status: 可选的状态过滤
            
        Returns:
            删除的任务数量
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if status:
                if self.config.DATABASE_TYPE == 'postgresql':
                    cursor.execute("DELETE FROM share_tasks WHERE account = $1 AND status = $2", (account, status))
                elif self.config.DATABASE_TYPE == 'mysql':
                    cursor.execute("DELETE FROM share_tasks WHERE account = %s AND status = %s", (account, status))
                else:  # SQLite
                    cursor.execute("DELETE FROM share_tasks WHERE account = ? AND status = ?", (account, status))
            else:
                if self.config.DATABASE_TYPE == 'postgresql':
                    cursor.execute("DELETE FROM share_tasks WHERE account = $1", (account,))
                elif self.config.DATABASE_TYPE == 'mysql':
                    cursor.execute("DELETE FROM share_tasks WHERE account = %s", (account,))
                else:  # SQLite
                    cursor.execute("DELETE FROM share_tasks WHERE account = ?", (account,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"清空分享任务失败: {e}")
            return 0

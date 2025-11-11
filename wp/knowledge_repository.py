"""
知识库存储层
提供文章与提取链接的聚合查询、过滤、排序和统计功能
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

from config import get_config, Config
from logger import get_logger

logger = get_logger(__name__)


class KnowledgeRepository:
    """知识库数据访问层"""
    
    ALLOWED_SORT_FIELDS = ['created_at', 'updated_at', 'title', 'status']
    ALLOWED_EXPORT_FIELDS = [
        'article_id', 'article_title', 'article_url', 
        'original_link', 'original_password',
        'new_link', 'new_password', 'new_title',
        'status', 'error_message', 'tag',
        'created_at', 'updated_at'
    ]
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化知识库存储层
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
    
    def _get_db_connection(self):
        """获取数据库连接"""
        if self.config.DATABASE_TYPE == 'sqlite':
            import sqlite3
            return sqlite3.connect(self.config.DATABASE_PATH)
        elif self.config.DATABASE_TYPE == 'mysql':
            import pymysql
            return pymysql.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DATABASE,
                charset='utf8mb4'
            )
        elif self.config.DATABASE_TYPE == 'postgresql':
            import psycopg2
            return psycopg2.connect(
                host=self.config.POSTGRES_HOST,
                port=self.config.POSTGRES_PORT,
                user=self.config.POSTGRES_USER,
                password=self.config.POSTGRES_PASSWORD,
                database=self.config.POSTGRES_DATABASE
            )
        else:
            raise ValueError(f"不支持的数据库类型: {self.config.DATABASE_TYPE}")
    
    def _derive_tag_from_url(self, url: str) -> str:
        """
        从文章URL中提取标签/分类
        规则：提取URL的第二级路径作为标签（jprj后的第一个路径段）
        例如：https://lewz.cn/jprj/category/article -> "category"
             https://lewz.cn/jprj/article -> "未分类"
        
        Args:
            url: 文章URL
            
        Returns:
            标签名称，如果无法提取则返回"未分类"
        """
        if not url:
            return "未分类"
        
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            parts = path.split('/')
            
            if len(parts) >= 3:
                return parts[1]
            else:
                return "未分类"
        except Exception as e:
            logger.warning(f"从URL提取标签失败: {url}, 错误: {e}")
            return "未分类"
    
    def list_entries(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'DESC'
    ) -> Dict[str, Any]:
        """
        列出知识库条目
        
        Args:
            limit: 每页条数
            offset: 偏移量
            search: 搜索关键词（应用于标题、文章ID、URL、原始链接、新链接、新标题）
            status: 状态过滤（pending/processing/transferred/completed/failed）
            tag: 标签过滤
            date_from: 起始日期（YYYY-MM-DD格式，基于extracted_links.created_at）
            date_to: 结束日期（YYYY-MM-DD格式，基于extracted_links.created_at）
            sort_by: 排序字段（created_at/updated_at/title/status）
            sort_order: 排序方向（ASC/DESC）
            
        Returns:
            包含entries列表、total总数和相关元数据的字典
        """
        if sort_by not in self.ALLOWED_SORT_FIELDS:
            logger.warning(f"非法排序字段: {sort_by}，使用默认值 created_at")
            sort_by = 'created_at'
        
        if sort_order.upper() not in ['ASC', 'DESC']:
            sort_order = 'DESC'
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            is_sqlite = self.config.DATABASE_TYPE == 'sqlite'
            param_placeholder = '?' if is_sqlite else '%s'
            
            conditions = []
            params = []
            
            if status:
                conditions.append(f"el.status = {param_placeholder}")
                params.append(status)
            
            if date_from:
                if is_sqlite:
                    conditions.append(f"DATE(el.created_at) >= {param_placeholder}")
                else:
                    conditions.append(f"DATE(el.created_at) >= {param_placeholder}")
                params.append(date_from)
            
            if date_to:
                if is_sqlite:
                    conditions.append(f"DATE(el.created_at) <= {param_placeholder}")
                else:
                    conditions.append(f"DATE(el.created_at) <= {param_placeholder}")
                params.append(date_to)
            
            if search:
                search_term = f"%{search}%"
                search_conditions = [
                    f"a.title LIKE {param_placeholder}",
                    f"a.article_id LIKE {param_placeholder}",
                    f"a.url LIKE {param_placeholder}",
                    f"el.original_link LIKE {param_placeholder}",
                    f"el.new_link LIKE {param_placeholder}",
                    f"el.new_title LIKE {param_placeholder}"
                ]
                conditions.append(f"({' OR '.join(search_conditions)})")
                params.extend([search_term] * 6)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            field_mapping = {
                'title': 'a.title',
                'status': 'el.status',
                'created_at': 'el.created_at',
                'updated_at': 'el.updated_at'
            }
            
            order_field = field_mapping.get(sort_by, 'el.created_at')
            order_by = f"ORDER BY {order_field} {sort_order}"
            
            count_query = f"""
                SELECT COUNT(*)
                FROM extracted_links el
                INNER JOIN articles a ON el.article_id = a.article_id
                {where_clause}
            """
            
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            query = f"""
                SELECT 
                    a.article_id,
                    a.title AS article_title,
                    a.url AS article_url,
                    el.original_link,
                    el.original_password,
                    el.new_link,
                    el.new_password,
                    el.new_title,
                    el.status,
                    el.error_message,
                    el.created_at,
                    el.updated_at
                FROM extracted_links el
                INNER JOIN articles a ON el.article_id = a.article_id
                {where_clause}
                {order_by}
                LIMIT {param_placeholder} OFFSET {param_placeholder}
            """
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            conn.close()
            
            entries = []
            for row in rows:
                article_url = row[2]
                tag_value = self._derive_tag_from_url(article_url)
                
                if tag and tag != tag_value:
                    continue
                
                entry = {
                    'article_id': row[0],
                    'article_title': row[1],
                    'article_url': article_url,
                    'original_link': row[3],
                    'original_password': row[4] or '',
                    'new_link': row[5] or '',
                    'new_password': row[6] or '',
                    'new_title': row[7] or '',
                    'status': row[8],
                    'error_message': row[9] or '',
                    'tag': tag_value,
                    'created_at': str(row[10]) if row[10] else '',
                    'updated_at': str(row[11]) if row[11] else ''
                }
                entries.append(entry)
            
            filtered_total = len(entries) if tag else total
            
            return {
                'entries': entries,
                'total': filtered_total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(entries)) < filtered_total
            }
            
        except Exception as e:
            logger.error(f"列出知识库条目失败: {e}")
            return {
                'entries': [],
                'total': 0,
                'limit': limit,
                'offset': offset,
                'has_more': False,
                'error': str(e)
            }
    
    def get_distinct_tags(self) -> List[str]:
        """
        获取所有不重复的标签列表
        标签从文章URL的第二级路径中提取
        
        Returns:
            排序后的标签列表
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT a.url
                FROM articles a
                INNER JOIN extracted_links el ON a.article_id = el.article_id
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            tags = set()
            for row in rows:
                url = row[0]
                tag = self._derive_tag_from_url(url)
                tags.add(tag)
            
            return sorted(list(tags))
            
        except Exception as e:
            logger.error(f"获取标签列表失败: {e}")
            return []
    
    def summaries_by_status(self) -> Dict[str, int]:
        """
        按状态统计条目数量
        
        Returns:
            状态统计字典，例如 {'pending': 10, 'completed': 5, ...}
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT status, COUNT(*) as count
                FROM extracted_links
                GROUP BY status
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            summaries = {}
            for row in rows:
                summaries[row[0]] = row[1]
            
            return summaries
            
        except Exception as e:
            logger.error(f"获取状态统计失败: {e}")
            return {}
    
    def prepare_export_rows(
        self,
        fields: List[str],
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'DESC'
    ) -> List[Dict[str, Any]]:
        """
        准备导出数据行
        验证字段名称并返回符合条件的记录
        
        Args:
            fields: 要导出的字段列表
            filters: 过滤条件字典（可选，同list_entries）
            sort_by: 排序字段
            sort_order: 排序方向
            
        Returns:
            符合条件的记录列表，每条记录只包含指定字段
        """
        invalid_fields = [f for f in fields if f not in self.ALLOWED_EXPORT_FIELDS]
        if invalid_fields:
            raise ValueError(f"非法导出字段: {', '.join(invalid_fields)}")
        
        filters = filters or {}
        
        result = self.list_entries(
            limit=100000,
            offset=0,
            search=filters.get('search'),
            status=filters.get('status'),
            tag=filters.get('tag'),
            date_from=filters.get('date_from'),
            date_to=filters.get('date_to'),
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        export_rows = []
        for entry in result.get('entries', []):
            row = {field: entry.get(field, '') for field in fields}
            export_rows.append(row)
        
        return export_rows

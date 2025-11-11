"""
百度网盘链接提取和转存服务
从文章中提取百度网盘分享链接，执行转存和分享操作，并更新数据库
"""
import re
import time
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from config import get_config, Config
from logger import get_logger

logger = get_logger(__name__)


class LinkExtractorService:
    """百度网盘链接提取服务"""
    
    # 百度网盘链接正则表达式
    BAIDU_LINK_PATTERNS = [
        # 标准格式：https://pan.baidu.com/s/xxxxx
        r'https?://pan\.baidu\.com/s/[A-Za-z0-9_-]+',
        # 短链接格式：https://pan.baidu.com/share/init?surl=xxxxx
        r'https?://pan\.baidu\.com/share/init\?surl=[A-Za-z0-9_-]+',
    ]
    
    # 提取码正则表达式（支持多种格式）
    PASSWORD_PATTERNS = [
        r'(?:提取码|密码|pwd|code)[:：\s]*([a-zA-Z0-9]{4})',
        r'(?:提取码|密码|pwd|code)[:：\s]*([a-zA-Z0-9]{4})',
        r'\?pwd=([a-zA-Z0-9]{4})',
    ]
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化链接提取服务
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
        
    def _get_db_connection(self):
        """获取数据库连接"""
        if self.config.DATABASE_TYPE == 'sqlite':
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
    
    def extract_links_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        从文本中提取百度网盘链接和密码
        
        Args:
            text: 文本内容
            
        Returns:
            提取的链接列表，每项包含 {'link': '...', 'password': '...'}
        """
        if not text:
            return []
        
        links = []
        found_urls = set()
        
        # 提取所有百度网盘链接
        for pattern in self.BAIDU_LINK_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                url = match.group(0)
                if url not in found_urls:
                    found_urls.add(url)
                    
                    # 尝试在链接附近查找密码
                    start_pos = max(0, match.start() - 200)
                    end_pos = min(len(text), match.end() + 200)
                    context = text[start_pos:end_pos]
                    
                    password = self._extract_password(context)
                    
                    links.append({
                        'link': url,
                        'password': password
                    })
        
        return links
    
    def _extract_password(self, text: str) -> str:
        """
        从文本中提取密码
        
        Args:
            text: 文本内容
            
        Returns:
            提取的密码，如果没有则返回空字符串
        """
        for pattern in self.PASSWORD_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return ''
    
    def get_articles_with_links(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取所有文章并提取其中的百度网盘链接
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            文章列表，每项包含文章信息和提取的链接
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.config.DATABASE_TYPE == 'sqlite':
                cursor.execute("""
                    SELECT id, article_id, url, title, content, crawled_at, updated_at
                    FROM articles
                    ORDER BY crawled_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor.execute("""
                    SELECT id, article_id, url, title, content, crawled_at, updated_at
                    FROM articles
                    ORDER BY crawled_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
            
            rows = cursor.fetchall()
            conn.close()
            
            articles = []
            for row in rows:
                article = {
                    'id': row[0],
                    'article_id': row[1],
                    'url': row[2],
                    'title': row[3],
                    'content': row[4],
                    'crawled_at': str(row[5]),
                    'updated_at': str(row[6])
                }
                
                # 提取链接
                links = self.extract_links_from_text(article['content'])
                article['extracted_links'] = links
                article['links_count'] = len(links)
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"获取文章失败: {e}")
            return []
    
    def save_extracted_link(self, article_id: str, original_link: str, original_password: str,
                           new_link: str = '', new_password: str = '', new_title: str = '',
                           status: str = 'pending', error_message: str = '') -> bool:
        """
        保存提取的链接信息到数据库
        
        Args:
            article_id: 文章ID
            original_link: 原始链接
            original_password: 原始密码
            new_link: 新生成的分享链接
            new_password: 新链接的密码
            new_title: 新链接的标题（从百度网盘返回）
            status: 状态 (pending/processing/completed/failed)
            error_message: 错误信息
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.config.DATABASE_TYPE == 'sqlite':
                cursor.execute("""
                    INSERT OR REPLACE INTO extracted_links
                    (article_id, original_link, original_password, new_link, new_password, 
                     new_title, status, error_message, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (article_id, original_link, original_password, new_link, new_password,
                      new_title, status, error_message,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            else:
                cursor.execute("""
                    INSERT INTO extracted_links
                    (article_id, original_link, original_password, new_link, new_password,
                     new_title, status, error_message, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    new_link = VALUES(new_link),
                    new_password = VALUES(new_password),
                    new_title = VALUES(new_title),
                    status = VALUES(status),
                    error_message = VALUES(error_message),
                    updated_at = VALUES(updated_at)
                """, (article_id, original_link, original_password, new_link, new_password,
                      new_title, status, error_message,
                      datetime.now(),
                      datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"保存提取链接成功: {article_id} - {original_link}")
            return True
            
        except Exception as e:
            logger.error(f"保存提取链接失败: {e}")
            return False
    
    def get_extracted_links(self, article_id: str = None, status: str = None,
                           limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取提取的链接列表
        
        Args:
            article_id: 筛选指定文章ID（可选）
            status: 筛选指定状态（可选）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            链接列表
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if article_id:
                conditions.append("article_id = " + ("?" if self.config.DATABASE_TYPE == 'sqlite' else "%s"))
                params.append(article_id)
            
            if status:
                conditions.append("status = " + ("?" if self.config.DATABASE_TYPE == 'sqlite' else "%s"))
                params.append(status)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            params.extend([limit, offset])
            
            if self.config.DATABASE_TYPE == 'sqlite':
                query = f"""
                    SELECT id, article_id, original_link, original_password, new_link,
                           new_password, new_title, status, error_message, created_at, updated_at
                    FROM extracted_links
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
            else:
                query = f"""
                    SELECT id, article_id, original_link, original_password, new_link,
                           new_password, new_title, status, error_message, created_at, updated_at
                    FROM extracted_links
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            links = []
            for row in rows:
                links.append({
                    'id': row[0],
                    'article_id': row[1],
                    'original_link': row[2],
                    'original_password': row[3],
                    'new_link': row[4],
                    'new_password': row[5],
                    'new_title': row[6],
                    'status': row[7],
                    'error_message': row[8],
                    'created_at': str(row[9]),
                    'updated_at': str(row[10])
                })
            
            return links
            
        except Exception as e:
            logger.error(f"获取提取链接列表失败: {e}")
            return []
    
    def update_extracted_link_status(self, article_id: str, original_link: str,
                                    new_link: str = '', new_password: str = '',
                                    new_title: str = '', status: str = 'completed',
                                    error_message: str = '') -> bool:
        """
        更新提取链接的状态
        
        Args:
            article_id: 文章ID
            original_link: 原始链接
            new_link: 新生成的分享链接
            new_password: 新链接的密码
            new_title: 新链接的标题
            status: 状态
            error_message: 错误信息
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.config.DATABASE_TYPE == 'sqlite':
                cursor.execute("""
                    UPDATE extracted_links
                    SET new_link = ?, new_password = ?, new_title = ?,
                        status = ?, error_message = ?, updated_at = ?
                    WHERE article_id = ? AND original_link = ?
                """, (new_link, new_password, new_title, status, error_message,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      article_id, original_link))
            else:
                cursor.execute("""
                    UPDATE extracted_links
                    SET new_link = %s, new_password = %s, new_title = %s,
                        status = %s, error_message = %s, updated_at = %s
                    WHERE article_id = %s AND original_link = %s
                """, (new_link, new_password, new_title, status, error_message,
                      datetime.now(),
                      article_id, original_link))
            
            conn.commit()
            conn.close()
            
            logger.info(f"更新提取链接状态成功: {article_id} - {original_link} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"更新提取链接状态失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM extracted_links")
            total_links = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM extracted_links WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM extracted_links WHERE status = 'processing'")
            processing = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM extracted_links WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM extracted_links WHERE status = 'failed'")
            failed = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_links': total_links,
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'failed': failed,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_links': 0,
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'error': str(e)
            }

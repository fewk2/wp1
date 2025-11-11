"""
爬虫服务模块
使用Crawl4AI框架爬取lewz.cn/jprj目录下的文章
"""
import os
import time
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import asyncio

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.chunking_strategy import RegexChunking
from bs4 import BeautifulSoup

from config import get_config, Config
from logger import get_logger

logger = get_logger(__name__)


class CrawlerService:
    """爬虫服务类"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化爬虫服务
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
        self.base_url = "https://lewz.cn/jprj"
        self.visited_urls = set()
        self.crawl_delay = 3  # 慢速爬取，每次请求间隔3秒
        
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
    
    def _generate_article_id(self, url: str) -> str:
        """
        生成文章唯一ID
        
        Args:
            url: 文章URL
            
        Returns:
            唯一ID
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _save_article(self, url: str, title: str, content: str) -> bool:
        """
        保存文章到数据库
        
        Args:
            url: 文章URL
            title: 文章标题
            content: 文章内容
            
        Returns:
            是否成功
        """
        try:
            article_id = self._generate_article_id(url)
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.config.DATABASE_TYPE == 'sqlite':
                cursor.execute("""
                    INSERT OR REPLACE INTO articles 
                    (article_id, url, title, content, crawled_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (article_id, url, title, content, 
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            else:
                cursor.execute("""
                    INSERT INTO articles 
                    (article_id, url, title, content, crawled_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    title = VALUES(title),
                    content = VALUES(content),
                    updated_at = VALUES(updated_at)
                """, (article_id, url, title, content,
                      datetime.now(),
                      datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"保存文章成功: {title} ({url})")
            return True
            
        except Exception as e:
            logger.error(f"保存文章失败: {e}")
            return False
    
    def _extract_article_links(self, html: str, base_url: str) -> List[str]:
        """
        从HTML中提取文章链接
        
        Args:
            html: HTML内容
            base_url: 基础URL
            
        Returns:
            文章链接列表
        """
        links = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(base_url, href)
                
                if full_url.startswith(self.base_url) and full_url not in self.visited_urls:
                    links.append(full_url)
            
            logger.info(f"从 {base_url} 提取到 {len(links)} 个链接")
            
        except Exception as e:
            logger.error(f"提取链接失败: {e}")
        
        return links
    
    def _extract_article_content(self, html: str, url: str) -> Dict[str, str]:
        """
        从HTML中提取文章标题和内容
        
        Args:
            html: HTML内容
            url: 文章URL
            
        Returns:
            包含标题和内容的字典
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取标题
            title = ""
            if soup.find('h1'):
                title = soup.find('h1').get_text(strip=True)
            elif soup.find('title'):
                title = soup.find('title').get_text(strip=True)
            else:
                title = url
            
            # 提取正文内容
            content = ""
            
            # 尝试常见的内容容器
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '#content',
                'main'
            ]
            
            content_element = None
            for selector in content_selectors:
                if '.' in selector:
                    content_element = soup.find(class_=selector.replace('.', ''))
                elif '#' in selector:
                    content_element = soup.find(id=selector.replace('#', ''))
                else:
                    content_element = soup.find(selector)
                
                if content_element:
                    break
            
            if content_element:
                # 移除脚本和样式标签
                for script in content_element.find_all(['script', 'style']):
                    script.decompose()
                
                content = content_element.get_text(separator='\n', strip=True)
            else:
                # 如果找不到特定容器，尝试提取body内容
                body = soup.find('body')
                if body:
                    for script in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        script.decompose()
                    content = body.get_text(separator='\n', strip=True)
            
            return {
                'title': title,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"提取文章内容失败: {e}")
            return {
                'title': url,
                'content': ''
            }
    
    async def _crawl_url(self, url: str, crawler: AsyncWebCrawler) -> Optional[str]:
        """
        爬取单个URL
        
        Args:
            url: 目标URL
            crawler: 爬虫实例
            
        Returns:
            HTML内容
        """
        try:
            result = await crawler.arun(url=url)
            
            if result.success:
                logger.info(f"爬取成功: {url}")
                return result.html
            else:
                logger.error(f"爬取失败: {url}")
                return None
                
        except Exception as e:
            logger.error(f"爬取URL出错 {url}: {e}")
            return None
    
    async def _crawl_page_and_extract_links(self, url: str, crawler: AsyncWebCrawler) -> List[str]:
        """
        爬取页面并提取链接
        
        Args:
            url: 目标URL
            crawler: 爬虫实例
            
        Returns:
            文章链接列表
        """
        html = await self._crawl_url(url, crawler)
        if html:
            return self._extract_article_links(html, url)
        return []
    
    async def _crawl_article_and_save(self, url: str, crawler: AsyncWebCrawler) -> bool:
        """
        爬取文章并保存
        
        Args:
            url: 文章URL
            crawler: 爬虫实例
            
        Returns:
            是否成功
        """
        if url in self.visited_urls:
            return False
        
        self.visited_urls.add(url)
        
        html = await self._crawl_url(url, crawler)
        if not html:
            return False
        
        article_data = self._extract_article_content(html, url)
        
        if article_data['content']:
            return self._save_article(url, article_data['title'], article_data['content'])
        else:
            logger.warning(f"文章内容为空，跳过保存: {url}")
            return False
    
    async def crawl_jprj_articles(self) -> Dict[str, Any]:
        """
        爬取lewz.cn/jprj目录下的所有文章
        
        Returns:
            爬取统计信息
        """
        start_time = time.time()
        crawled_count = 0
        saved_count = 0
        error_count = 0
        
        logger.info(f"开始爬取: {self.base_url}")
        
        async with AsyncWebCrawler(verbose=True) as crawler:
            # 首先爬取主页面，获取所有文章链接
            links_to_crawl = [self.base_url]
            all_article_links = set()
            
            # 第一阶段：收集所有文章链接
            while links_to_crawl:
                current_url = links_to_crawl.pop(0)
                
                if current_url in self.visited_urls:
                    continue
                
                logger.info(f"正在收集链接: {current_url}")
                
                links = await self._crawl_page_and_extract_links(current_url, crawler)
                
                for link in links:
                    if link not in all_article_links and link not in self.visited_urls:
                        all_article_links.add(link)
                        # 如果是目录页，继续收集
                        if link.count('/') <= self.base_url.count('/') + 1:
                            links_to_crawl.append(link)
                
                self.visited_urls.add(current_url)
                crawled_count += 1
                
                # 慢速爬取
                time.sleep(self.crawl_delay)
            
            # 清除visited_urls，准备爬取文章
            self.visited_urls.clear()
            
            # 第二阶段：爬取所有文章内容
            logger.info(f"共发现 {len(all_article_links)} 个文章链接，开始爬取内容")
            
            for article_url in all_article_links:
                try:
                    success = await self._crawl_article_and_save(article_url, crawler)
                    if success:
                        saved_count += 1
                    else:
                        error_count += 1
                    
                    crawled_count += 1
                    
                    # 慢速爬取
                    time.sleep(self.crawl_delay)
                    
                except Exception as e:
                    logger.error(f"爬取文章出错 {article_url}: {e}")
                    error_count += 1
        
        elapsed_time = time.time() - start_time
        
        result = {
            'success': True,
            'total_crawled': crawled_count,
            'saved_count': saved_count,
            'error_count': error_count,
            'elapsed_time': elapsed_time,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"爬取完成: {result}")
        
        return result
    
    def get_articles(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取已爬取的文章列表
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            文章列表
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.config.DATABASE_TYPE == 'sqlite':
                cursor.execute("""
                    SELECT id, article_id, url, title, 
                           substr(content, 1, 200) as content_preview,
                           crawled_at, updated_at
                    FROM articles
                    ORDER BY crawled_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor.execute("""
                    SELECT id, article_id, url, title, 
                           SUBSTRING(content, 1, 200) as content_preview,
                           crawled_at, updated_at
                    FROM articles
                    ORDER BY crawled_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
            
            rows = cursor.fetchall()
            conn.close()
            
            articles = []
            for row in rows:
                articles.append({
                    'id': row[0],
                    'article_id': row[1],
                    'url': row[2],
                    'title': row[3],
                    'content_preview': row[4],
                    'crawled_at': str(row[5]),
                    'updated_at': str(row[6])
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"获取文章列表失败: {e}")
            return []
    
    def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        根据文章ID获取完整文章
        
        Args:
            article_id: 文章唯一ID
            
        Returns:
            文章详情
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.config.DATABASE_TYPE == 'sqlite':
                cursor.execute("""
                    SELECT id, article_id, url, title, content, crawled_at, updated_at
                    FROM articles
                    WHERE article_id = ?
                """, (article_id,))
            else:
                cursor.execute("""
                    SELECT id, article_id, url, title, content, crawled_at, updated_at
                    FROM articles
                    WHERE article_id = %s
                """, (article_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'article_id': row[1],
                    'url': row[2],
                    'title': row[3],
                    'content': row[4],
                    'crawled_at': str(row[5]),
                    'updated_at': str(row[6])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文章详情失败: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取爬取统计信息
        
        Returns:
            统计信息
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT MIN(crawled_at), MAX(crawled_at)
                FROM articles
            """)
            row = cursor.fetchone()
            first_crawled = str(row[0]) if row[0] else None
            last_crawled = str(row[1]) if row[1] else None
            
            conn.close()
            
            return {
                'total_articles': total_articles,
                'first_crawled': first_crawled,
                'last_crawled': last_crawled
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_articles': 0,
                'first_crawled': None,
                'last_crawled': None
            }

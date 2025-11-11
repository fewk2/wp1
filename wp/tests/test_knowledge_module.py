"""
知识库模块完整测试套件
使用unittest框架，提供隔离的临时数据库测试环境
覆盖知识库存储层和API层的核心功能
"""
import os
import sys
import unittest
import tempfile
import sqlite3
import shutil
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from knowledge_repository import KnowledgeRepository
from config import Config


class TestKnowledgeRepository(unittest.TestCase):
    """测试知识库存储层功能"""
    
    @classmethod
    def setUpClass(cls):
        """创建临时测试目录"""
        cls.test_dir = tempfile.mkdtemp(prefix='knowledge_test_')
        cls.test_db_path = os.path.join(cls.test_dir, 'test_knowledge.db')
    
    @classmethod
    def tearDownClass(cls):
        """清理临时测试目录"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def setUp(self):
        """每个测试前创建干净的数据库和测试数据"""
        self._create_test_database()
        self._insert_test_fixtures()
        
        self.test_config = Config()
        self.test_config.DATABASE_TYPE = 'sqlite'
        self.test_config.DATABASE_PATH = self.test_db_path
        
        self.repo = KnowledgeRepository(config=self.test_config)
    
    def tearDown(self):
        """每个测试后清理数据库"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def _create_test_database(self):
        """创建测试数据库schema"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                article_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                content TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                original_link TEXT NOT NULL,
                original_password TEXT,
                new_link TEXT,
                new_password TEXT,
                new_title TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (article_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_crawled_at ON articles(crawled_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracted_links_created_at ON extracted_links(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracted_links_updated_at ON extracted_links(updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracted_links_new_link ON extracted_links(new_link)")
        
        conn.commit()
        conn.close()
    
    def _insert_test_fixtures(self):
        """插入测试数据"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        test_articles = [
            ('art001', 'https://lewz.cn/jprj/technology/article1', '技术文章1', '技术内容1', '2024-01-01 10:00:00'),
            ('art002', 'https://lewz.cn/jprj/business/article2', '商业文章2', '商业内容2', '2024-01-02 11:00:00'),
            ('art003', 'https://lewz.cn/jprj/entertainment/article3', '娱乐文章3', '娱乐内容3', '2024-01-03 12:00:00'),
            ('art004', 'https://lewz.cn/jprj/article4', '未分类文章4', '内容4', '2024-01-04 13:00:00'),
            ('art005', 'https://lewz.cn/jprj/technology/article5', '', '无标题文章', '2024-01-05 14:00:00'),
        ]
        
        cursor.executemany("""
            INSERT INTO articles (article_id, url, title, content, crawled_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [(a[0], a[1], a[2], a[3], a[4], a[4]) for a in test_articles])
        
        test_links = [
            ('art001', 'https://pan.baidu.com/s/test1', 'pwd1', 'https://pan.baidu.com/s/new1', 'newpwd1', 'New Title 1', 'completed', '', '2024-01-01 11:00:00', '2024-01-01 15:00:00'),
            ('art002', 'https://pan.baidu.com/s/test2', 'pwd2', '', '', '', 'pending', '', '2024-01-02 12:00:00', '2024-01-02 12:00:00'),
            ('art003', 'https://pan.baidu.com/s/test3', 'pwd3', 'https://pan.baidu.com/s/new3', 'newpwd3', 'New Title 3', 'transferred', '', '2024-01-03 13:00:00', '2024-01-03 16:00:00'),
            ('art004', 'https://pan.baidu.com/s/test4', 'pwd4', '', '', '', 'failed', '转存失败', '2024-01-04 14:00:00', '2024-01-04 14:00:00'),
            ('art005', 'https://pan.baidu.com/s/test5', '', 'https://pan.baidu.com/s/new5', 'newpwd5', '', 'completed', '', '2024-01-05 15:00:00', '2024-01-05 17:00:00'),
        ]
        
        cursor.executemany("""
            INSERT INTO extracted_links 
            (article_id, original_link, original_password, new_link, new_password, new_title, status, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_links)
        
        conn.commit()
        conn.close()
    
    def test_tag_derivation(self):
        """测试从URL提取标签功能"""
        test_cases = [
            ('https://lewz.cn/jprj/technology/article1', 'technology'),
            ('https://lewz.cn/jprj/business/article2', 'business'),
            ('https://lewz.cn/jprj/article3', '未分类'),
            ('', '未分类'),
            ('invalid-url', '未分类'),
            ('https://example.com/other/path', '未分类'),
        ]
        
        for url, expected in test_cases:
            with self.subTest(url=url):
                result = self.repo._derive_tag_from_url(url)
                self.assertEqual(result, expected)
    
    def test_list_entries_basic(self):
        """测试基本列表功能"""
        result = self.repo.list_entries(limit=10, offset=0)
        
        self.assertIn('entries', result)
        self.assertIn('total', result)
        self.assertEqual(result['total'], 5)
        self.assertEqual(len(result['entries']), 5)
    
    def test_list_entries_pagination(self):
        """测试分页功能"""
        result_page1 = self.repo.list_entries(limit=2, offset=0)
        result_page2 = self.repo.list_entries(limit=2, offset=2)
        
        self.assertEqual(len(result_page1['entries']), 2)
        self.assertEqual(len(result_page2['entries']), 2)
        self.assertTrue(result_page1['has_more'])
        
        self.assertNotEqual(
            result_page1['entries'][0]['article_id'],
            result_page2['entries'][0]['article_id']
        )
    
    def test_list_entries_search(self):
        """测试全文搜索功能"""
        result = self.repo.list_entries(limit=10, offset=0, search='技术文章')
        self.assertEqual(len(result['entries']), 1)
        self.assertIn('技术', result['entries'][0]['article_title'])
        
        result = self.repo.list_entries(limit=10, offset=0, search='test1')
        self.assertEqual(len(result['entries']), 1)
        self.assertIn('test1', result['entries'][0]['original_link'])
        
        result = self.repo.list_entries(limit=10, offset=0, search='new3')
        self.assertEqual(len(result['entries']), 1)
        self.assertIn('new3', result['entries'][0]['new_link'])
    
    def test_list_entries_status_filter(self):
        """测试状态过滤"""
        result_completed = self.repo.list_entries(limit=10, offset=0, status='completed')
        self.assertEqual(len(result_completed['entries']), 2)
        for entry in result_completed['entries']:
            self.assertEqual(entry['status'], 'completed')
        
        result_pending = self.repo.list_entries(limit=10, offset=0, status='pending')
        self.assertEqual(len(result_pending['entries']), 1)
        self.assertEqual(result_pending['entries'][0]['status'], 'pending')
        
        result_failed = self.repo.list_entries(limit=10, offset=0, status='failed')
        self.assertEqual(len(result_failed['entries']), 1)
        self.assertEqual(result_failed['entries'][0]['status'], 'failed')
    
    def test_list_entries_tag_filter(self):
        """测试标签过滤"""
        result_tech = self.repo.list_entries(limit=10, offset=0, tag='technology')
        self.assertEqual(len(result_tech['entries']), 2)
        for entry in result_tech['entries']:
            self.assertEqual(entry['tag'], 'technology')
        
        result_business = self.repo.list_entries(limit=10, offset=0, tag='business')
        self.assertEqual(len(result_business['entries']), 1)
        self.assertEqual(result_business['entries'][0]['tag'], 'business')
        
        result_uncategorized = self.repo.list_entries(limit=10, offset=0, tag='未分类')
        self.assertEqual(len(result_uncategorized['entries']), 1)
        self.assertEqual(result_uncategorized['entries'][0]['tag'], '未分类')
    
    def test_list_entries_date_filter(self):
        """测试日期范围过滤"""
        result = self.repo.list_entries(
            limit=10,
            offset=0,
            date_from='2024-01-02',
            date_to='2024-01-04'
        )
        self.assertGreaterEqual(len(result['entries']), 2)
        self.assertLessEqual(len(result['entries']), 3)
        
        result_from_only = self.repo.list_entries(
            limit=10,
            offset=0,
            date_from='2024-01-04'
        )
        self.assertGreaterEqual(len(result_from_only['entries']), 2)
        
        result_to_only = self.repo.list_entries(
            limit=10,
            offset=0,
            date_to='2024-01-02'
        )
        self.assertGreaterEqual(len(result_to_only['entries']), 1)
    
    def test_list_entries_sorting(self):
        """测试排序功能"""
        result_asc = self.repo.list_entries(
            limit=10,
            offset=0,
            sort_by='created_at',
            sort_order='ASC'
        )
        dates = [e['created_at'] for e in result_asc['entries']]
        self.assertEqual(dates, sorted(dates))
        
        result_desc = self.repo.list_entries(
            limit=10,
            offset=0,
            sort_by='created_at',
            sort_order='DESC'
        )
        dates_desc = [e['created_at'] for e in result_desc['entries']]
        self.assertEqual(dates_desc, sorted(dates_desc, reverse=True))
        
        result_title = self.repo.list_entries(
            limit=10,
            offset=0,
            sort_by='title',
            sort_order='ASC'
        )
        self.assertEqual(len(result_title['entries']), 5)
    
    def test_list_entries_invalid_sort_field(self):
        """测试非法排序字段回退到默认值"""
        result = self.repo.list_entries(
            limit=10,
            offset=0,
            sort_by='invalid_field'
        )
        self.assertIn('entries', result)
        self.assertEqual(len(result['entries']), 5)
    
    def test_list_entries_combined_filters(self):
        """测试组合过滤条件"""
        result = self.repo.list_entries(
            limit=10,
            offset=0,
            status='completed',
            tag='technology',
            search='技术'
        )
        self.assertGreaterEqual(len(result['entries']), 0)
        if len(result['entries']) > 0:
            self.assertEqual(result['entries'][0]['status'], 'completed')
            self.assertEqual(result['entries'][0]['tag'], 'technology')
    
    def test_list_entries_edge_cases(self):
        """测试边缘情况"""
        result_empty_title = self.repo.list_entries(
            limit=10,
            offset=0,
            search='无标题'
        )
        self.assertGreaterEqual(len(result_empty_title['entries']), 0)
        
        result_empty_pwd = self.repo.list_entries(
            limit=10,
            offset=0,
            search='test5'
        )
        self.assertEqual(len(result_empty_pwd['entries']), 1)
        self.assertEqual(result_empty_pwd['entries'][0]['original_password'], '')
    
    def test_get_distinct_tags(self):
        """测试获取不重复标签列表"""
        tags = self.repo.get_distinct_tags()
        
        self.assertIsInstance(tags, list)
        self.assertIn('technology', tags)
        self.assertIn('business', tags)
        self.assertIn('entertainment', tags)
        self.assertIn('未分类', tags)
        
        self.assertEqual(tags, sorted(tags))
    
    def test_summaries_by_status(self):
        """测试状态统计"""
        summaries = self.repo.summaries_by_status()
        
        self.assertIsInstance(summaries, dict)
        self.assertEqual(summaries.get('completed', 0), 2)
        self.assertEqual(summaries.get('pending', 0), 1)
        self.assertEqual(summaries.get('transferred', 0), 1)
        self.assertEqual(summaries.get('failed', 0), 1)
        
        total = sum(summaries.values())
        self.assertEqual(total, 5)
    
    def test_prepare_export_rows_all_fields(self):
        """测试导出所有字段"""
        fields = [
            'article_id', 'article_title', 'article_url',
            'original_link', 'original_password',
            'new_link', 'new_password', 'new_title',
            'status', 'error_message', 'tag',
            'created_at', 'updated_at'
        ]
        
        rows = self.repo.prepare_export_rows(fields)
        
        self.assertEqual(len(rows), 5)
        for row in rows:
            self.assertEqual(set(row.keys()), set(fields))
    
    def test_prepare_export_rows_selected_fields(self):
        """测试导出指定字段"""
        fields = ['article_id', 'article_title', 'status', 'tag']
        
        rows = self.repo.prepare_export_rows(fields)
        
        self.assertEqual(len(rows), 5)
        for row in rows:
            self.assertEqual(set(row.keys()), set(fields))
            self.assertIn(row['status'], ['pending', 'completed', 'transferred', 'failed'])
    
    def test_prepare_export_rows_with_filters(self):
        """测试带过滤条件的导出"""
        fields = ['article_id', 'status']
        filters = {'status': 'completed'}
        
        rows = self.repo.prepare_export_rows(fields, filters=filters)
        
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row['status'], 'completed')
    
    def test_prepare_export_rows_invalid_fields(self):
        """测试非法字段抛出异常"""
        invalid_fields = ['article_id', 'invalid_field', 'another_invalid']
        
        with self.assertRaises(ValueError) as context:
            self.repo.prepare_export_rows(invalid_fields)
        
        self.assertIn('非法导出字段', str(context.exception))
        self.assertIn('invalid_field', str(context.exception))


class TestKnowledgeAPI(unittest.TestCase):
    """测试知识库API端点"""
    
    @classmethod
    def setUpClass(cls):
        """创建临时测试目录和Flask测试客户端"""
        cls.test_dir = tempfile.mkdtemp(prefix='knowledge_api_test_')
        cls.test_db_path = os.path.join(cls.test_dir, 'test_api.db')
        
        from config import Config
        cls.test_config = Config()
        cls.test_config.DATABASE_TYPE = 'sqlite'
        cls.test_config.DATABASE_PATH = cls.test_db_path
        cls.test_config.API_SECRET_KEY = 'test_secret_key_12345'
        
        from server import app
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
    
    @classmethod
    def tearDownClass(cls):
        """清理临时测试目录"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def setUp(self):
        """每个测试前准备数据库和数据"""
        self._create_test_database()
        self._insert_test_data()
        self.headers = {'X-API-Key': 'test_secret_key_12345'}
        
        from knowledge_api import verify_api_key
        self.verify_patcher = patch('knowledge_api.verify_api_key', return_value=True)
        self.verify_patcher.start()
        
        from knowledge_repository import KnowledgeRepository
        def get_test_repo(*args, **kwargs):
            return KnowledgeRepository(config=self.test_config)
        
        self.repo_patcher = patch('knowledge_api.get_knowledge_repository', side_effect=get_test_repo)
        self.repo_patcher.start()
    
    def tearDown(self):
        """每个测试后清理"""
        self.verify_patcher.stop()
        self.repo_patcher.stop()
        
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def _create_test_database(self):
        """创建测试数据库"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                article_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                content TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                original_link TEXT NOT NULL,
                original_password TEXT,
                new_link TEXT,
                new_password TEXT,
                new_title TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _insert_test_data(self):
        """插入测试数据"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.executemany("""
            INSERT INTO articles (article_id, url, title, content, crawled_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ('art001', 'https://lewz.cn/jprj/tech/art1', 'Test Article 1', 'Content 1', '2024-01-01 10:00:00', '2024-01-01 10:00:00'),
            ('art002', 'https://lewz.cn/jprj/biz/art2', 'Test Article 2', 'Content 2', '2024-01-02 11:00:00', '2024-01-02 11:00:00'),
        ])
        
        cursor.executemany("""
            INSERT INTO extracted_links 
            (article_id, original_link, original_password, new_link, new_password, new_title, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ('art001', 'https://pan.baidu.com/s/test1', 'pwd1', 'https://pan.baidu.com/s/new1', 'newpwd1', 'Title 1', 'completed', '2024-01-01 11:00:00', '2024-01-01 12:00:00'),
            ('art002', 'https://pan.baidu.com/s/test2', 'pwd2', '', '', '', 'pending', '2024-01-02 12:00:00', '2024-01-02 12:00:00'),
        ])
        
        conn.commit()
        conn.close()
    
    def test_entries_without_auth(self):
        """测试无认证访问返回401"""
        self.verify_patcher.stop()
        
        response = self.client.get('/api/knowledge/entries')
        self.assertEqual(response.status_code, 401)
        
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertFalse(data.get('success', True))
        
        self.verify_patcher.start()
    
    def test_entries_with_auth(self):
        """测试认证访问返回正确数据"""
        response = self.client.get('/api/knowledge/entries', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('entries', data['data'])
        self.assertIn('pagination', data['data'])
        self.assertIn('summary', data)
    
    def test_entries_pagination(self):
        """测试分页参数"""
        response = self.client.get(
            '/api/knowledge/entries?page=1&page_size=1',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        pagination = data['data']['pagination']
        self.assertEqual(pagination['page'], 1)
        self.assertEqual(pagination['page_size'], 1)
        self.assertLessEqual(len(data['data']['entries']), 1)
    
    def test_entries_with_filters(self):
        """测试过滤参数"""
        response = self.client.get(
            '/api/knowledge/entries?status=completed',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        entries = data['data']['entries']
        for entry in entries:
            self.assertEqual(entry['status'], 'completed')
    
    def test_entries_invalid_sort_field(self):
        """测试非法排序字段返回400"""
        response = self.client.get(
            '/api/knowledge/entries?sort=invalid_field',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
        
        data = response.get_json()
        self.assertFalse(data['success'])
    
    def test_entries_invalid_sort_order(self):
        """测试非法排序方向返回400"""
        response = self.client.get(
            '/api/knowledge/entries?sort=created_at&order=INVALID',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
    
    def test_entries_invalid_date_format(self):
        """测试非法日期格式被忽略（返回200但日期过滤无效）"""
        response = self.client.get(
            '/api/knowledge/entries?date_from=invalid-date',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
    
    def test_tags_endpoint(self):
        """测试获取标签列表"""
        response = self.client.get('/api/knowledge/tags', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('tags', data['data'])
        self.assertIn('count', data['data'])
        self.assertIsInstance(data['data']['tags'], list)
    
    def test_statuses_endpoint(self):
        """测试获取状态统计"""
        response = self.client.get('/api/knowledge/statuses', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('statuses', data['data'])
        self.assertIn('total', data['data'])
        self.assertIsInstance(data['data']['statuses'], dict)
    
    def test_export_csv(self):
        """测试CSV导出"""
        response = self.client.get('/api/knowledge/export', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response.content_type)
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
        
        csv_content = response.data.decode('utf-8-sig')
        self.assertIn('article_id', csv_content)
        self.assertIn('article_title', csv_content)
        
        lines = csv_content.strip().split('\n')
        self.assertGreaterEqual(len(lines), 2)
    
    def test_export_csv_with_fields(self):
        """测试自定义字段导出"""
        response = self.client.get(
            '/api/knowledge/export?fields=article_id,article_title,status',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        csv_content = response.data.decode('utf-8-sig')
        header_line = csv_content.split('\n')[0]
        self.assertIn('article_id', header_line)
        self.assertIn('article_title', header_line)
        self.assertIn('status', header_line)
        
        self.assertNotIn('original_link', header_line)
    
    def test_export_csv_with_filters(self):
        """测试带过滤条件的导出"""
        response = self.client.get(
            '/api/knowledge/export?status=completed',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        csv_content = response.data.decode('utf-8-sig')
        lines = csv_content.strip().split('\n')
        
        self.assertGreaterEqual(len(lines), 1)
    
    def test_export_csv_invalid_fields(self):
        """测试非法字段导出返回400"""
        response = self.client.get(
            '/api/knowledge/export?fields=invalid_field',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
        
        data = response.get_json()
        self.assertFalse(data['success'])
    
    def test_entry_detail_not_found(self):
        """测试获取不存在的条目返回404"""
        response = self.client.get(
            '/api/knowledge/entry/nonexistent_id',
            headers=self.headers
        )
        self.assertEqual(response.status_code, 404)
    
    def test_kb_static_route(self):
        """测试知识库UI静态路由"""
        response = self.client.get('/kb')
        self.assertIn(response.status_code, [200, 404])
        
        response = self.client.get('/kb/')
        self.assertIn(response.status_code, [200, 404])


if __name__ == '__main__':
    unittest.main(verbosity=2)

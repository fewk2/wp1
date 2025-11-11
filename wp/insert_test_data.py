import sqlite3
import hashlib
from datetime import datetime

conn = sqlite3.connect('data/baidu_pan_deployment.db')
cursor = conn.cursor()

# 插入测试文章
test_articles = [
    {
        'url': 'https://lewz.cn/jprj/technology/article1',
        'title': '技术文章1 - Python开发最佳实践',
        'content': '本文介绍了Python开发的最佳实践，包含百度网盘链接：https://pan.baidu.com/s/1abcd1234 提取码：abc1'
    },
    {
        'url': 'https://lewz.cn/jprj/technology/article2',
        'title': '技术文章2 - Flask框架进阶',
        'content': '深入探讨Flask框架，分享链接：https://pan.baidu.com/share/init?surl=efgh5678 密码：efg2'
    },
    {
        'url': 'https://lewz.cn/jprj/business/article3',
        'title': '商业文章 - 创业经验分享',
        'content': '创业十年的经验总结，资源链接：https://pan.baidu.com/s/1ijkl9012 pwd:ijk3'
    },
    {
        'url': 'https://lewz.cn/jprj/entertainment/article4',
        'title': '娱乐文章 - 电影推荐',
        'content': '2024年必看电影推荐列表'
    },
    {
        'url': 'https://lewz.cn/jprj/article5',
        'title': '未分类文章 - 生活随笔',
        'content': '记录生活的点点滴滴'
    }
]

for article in test_articles:
    article_id = hashlib.md5(article['url'].encode()).hexdigest()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO articles (article_id, url, title, content, crawled_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            article_id,
            article['url'],
            article['title'],
            article['content'],
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    except Exception as e:
        print(f"插入文章失败: {e}")

# 插入提取的链接
test_links = [
    {
        'article_id': hashlib.md5('https://lewz.cn/jprj/technology/article1'.encode()).hexdigest(),
        'original_link': 'https://pan.baidu.com/s/1abcd1234',
        'original_password': 'abc1',
        'new_link': 'https://pan.baidu.com/s/1new_abcd1234',
        'new_password': 'new1',
        'new_title': '技术文章1 - Python开发最佳实践',
        'status': 'completed'
    },
    {
        'article_id': hashlib.md5('https://lewz.cn/jprj/technology/article2'.encode()).hexdigest(),
        'original_link': 'https://pan.baidu.com/share/init?surl=efgh5678',
        'original_password': 'efg2',
        'new_link': 'https://pan.baidu.com/s/1new_efgh5678',
        'new_password': 'new2',
        'new_title': '技术文章2 - Flask框架进阶',
        'status': 'completed'
    },
    {
        'article_id': hashlib.md5('https://lewz.cn/jprj/business/article3'.encode()).hexdigest(),
        'original_link': 'https://pan.baidu.com/s/1ijkl9012',
        'original_password': 'ijk3',
        'status': 'pending'
    },
    {
        'article_id': hashlib.md5('https://lewz.cn/jprj/technology/article1'.encode()).hexdigest(),
        'original_link': 'https://pan.baidu.com/s/1test_failed',
        'original_password': 'fail',
        'status': 'failed',
        'error_message': '链接已失效'
    }
]

for link in test_links:
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO extracted_links 
            (article_id, original_link, original_password, new_link, new_password, new_title, status, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            link['article_id'],
            link['original_link'],
            link.get('original_password'),
            link.get('new_link'),
            link.get('new_password'),
            link.get('new_title'),
            link['status'],
            link.get('error_message'),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    except Exception as e:
        print(f"插入链接失败: {e}")

conn.commit()

# 验证数据
cursor.execute('SELECT COUNT(*) FROM articles')
article_count = cursor.fetchone()[0]
print(f"文章数量: {article_count}")

cursor.execute('SELECT COUNT(*) FROM extracted_links')
link_count = cursor.fetchone()[0]
print(f"链接数量: {link_count}")

conn.close()
print("测试数据插入完成")

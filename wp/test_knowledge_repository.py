"""
测试知识库存储层
"""
import os
import sys
import sqlite3
from datetime import datetime

from knowledge_repository import KnowledgeRepository
from config import get_config


def setup_test_db():
    """创建测试数据库并插入测试数据"""
    config = get_config()
    
    if config.DATABASE_TYPE != 'sqlite':
        print("注意: 此测试脚本仅支持SQLite数据库")
        return False
    
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM extracted_links")
    cursor.execute("DELETE FROM articles")
    
    cursor.execute("""
        INSERT INTO articles (article_id, url, title, content, crawled_at, updated_at)
        VALUES 
            ('art001', 'https://lewz.cn/jprj/category1/article1', '测试文章1', '内容1', '2024-01-01 10:00:00', '2024-01-01 10:00:00'),
            ('art002', 'https://lewz.cn/jprj/category2/article2', '测试文章2', '内容2', '2024-01-02 10:00:00', '2024-01-02 10:00:00'),
            ('art003', 'https://lewz.cn/jprj/article3', '未分类文章', '内容3', '2024-01-03 10:00:00', '2024-01-03 10:00:00')
    """)
    
    cursor.execute("""
        INSERT INTO extracted_links 
        (article_id, original_link, original_password, new_link, new_password, new_title, status, created_at, updated_at)
        VALUES
            ('art001', 'https://pan.baidu.com/s/test1', 'pwd1', 'https://pan.baidu.com/s/new1', 'newpwd1', 'New Title 1', 'completed', '2024-01-01 11:00:00', '2024-01-01 12:00:00'),
            ('art002', 'https://pan.baidu.com/s/test2', 'pwd2', '', '', '', 'pending', '2024-01-02 11:00:00', '2024-01-02 11:00:00'),
            ('art003', 'https://pan.baidu.com/s/test3', 'pwd3', 'https://pan.baidu.com/s/new3', 'newpwd3', 'New Title 3', 'failed', '2024-01-03 11:00:00', '2024-01-03 11:00:00')
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ 测试数据已准备")
    return True


def test_tag_derivation():
    """测试标签提取功能"""
    print("\n=== 测试标签提取 ===")
    repo = KnowledgeRepository()
    
    test_cases = [
        ('https://lewz.cn/jprj/category1/article1', 'category1'),
        ('https://lewz.cn/jprj/category2/article2', 'category2'),
        ('https://lewz.cn/jprj/article3', '未分类'),
        ('', '未分类'),
        ('invalid-url', '未分类'),
    ]
    
    for url, expected in test_cases:
        result = repo._derive_tag_from_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} URL: {url[:40]:<40} => {result} (期望: {expected})")


def test_list_entries():
    """测试列出条目功能"""
    print("\n=== 测试列出条目 ===")
    repo = KnowledgeRepository()
    
    result = repo.list_entries(limit=10, offset=0)
    
    print(f"总数: {result['total']}")
    print(f"返回条数: {len(result['entries'])}")
    
    for entry in result['entries']:
        print(f"  - {entry['article_title']} | {entry['tag']} | {entry['status']}")


def test_search():
    """测试搜索功能"""
    print("\n=== 测试搜索 ===")
    repo = KnowledgeRepository()
    
    result = repo.list_entries(limit=10, offset=0, search='测试文章1')
    print(f"搜索 '测试文章1': 找到 {len(result['entries'])} 条")
    
    result = repo.list_entries(limit=10, offset=0, search='test1')
    print(f"搜索 'test1': 找到 {len(result['entries'])} 条")


def test_status_filter():
    """测试状态过滤"""
    print("\n=== 测试状态过滤 ===")
    repo = KnowledgeRepository()
    
    for status in ['pending', 'completed', 'failed']:
        result = repo.list_entries(limit=10, offset=0, status=status)
        print(f"状态 '{status}': 找到 {len(result['entries'])} 条")


def test_tag_filter():
    """测试标签过滤"""
    print("\n=== 测试标签过滤 ===")
    repo = KnowledgeRepository()
    
    for tag in ['category1', 'category2', '未分类']:
        result = repo.list_entries(limit=10, offset=0, tag=tag)
        print(f"标签 '{tag}': 找到 {len(result['entries'])} 条")


def test_get_distinct_tags():
    """测试获取标签列表"""
    print("\n=== 测试获取标签列表 ===")
    repo = KnowledgeRepository()
    
    tags = repo.get_distinct_tags()
    print(f"标签列表: {tags}")


def test_summaries_by_status():
    """测试状态统计"""
    print("\n=== 测试状态统计 ===")
    repo = KnowledgeRepository()
    
    summaries = repo.summaries_by_status()
    print("状态统计:")
    for status, count in summaries.items():
        print(f"  {status}: {count}")


def test_prepare_export_rows():
    """测试导出准备"""
    print("\n=== 测试导出准备 ===")
    repo = KnowledgeRepository()
    
    fields = ['article_id', 'article_title', 'tag', 'status', 'new_link']
    rows = repo.prepare_export_rows(fields)
    
    print(f"导出字段: {fields}")
    print(f"导出行数: {len(rows)}")
    
    if rows:
        print(f"示例行: {rows[0]}")
    
    try:
        invalid_fields = ['article_id', 'invalid_field']
        rows = repo.prepare_export_rows(invalid_fields)
        print("❌ 应该抛出异常但没有")
    except ValueError as e:
        print(f"✅ 正确抛出异常: {e}")


def test_date_range():
    """测试日期范围过滤"""
    print("\n=== 测试日期范围过滤 ===")
    repo = KnowledgeRepository()
    
    result = repo.list_entries(
        limit=10,
        offset=0,
        date_from='2024-01-02',
        date_to='2024-01-03'
    )
    print(f"日期范围 2024-01-02 到 2024-01-03: 找到 {len(result['entries'])} 条")


def test_sorting():
    """测试排序"""
    print("\n=== 测试排序 ===")
    repo = KnowledgeRepository()
    
    for sort_by in ['created_at', 'updated_at', 'title', 'status']:
        result = repo.list_entries(limit=10, offset=0, sort_by=sort_by, sort_order='ASC')
        print(f"按 {sort_by} 升序: {len(result['entries'])} 条")


if __name__ == '__main__':
    print("开始知识库存储层测试...")
    
    if not setup_test_db():
        sys.exit(1)
    
    test_tag_derivation()
    test_list_entries()
    test_search()
    test_status_filter()
    test_tag_filter()
    test_get_distinct_tags()
    test_summaries_by_status()
    test_prepare_export_rows()
    test_date_range()
    test_sorting()
    
    print("\n✅ 所有测试完成！")

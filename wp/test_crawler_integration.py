"""
爬虫集成测试 - 测试基本功能而不实际爬取网站
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from crawler_service import CrawlerService
from config import get_config


def test_crawler_initialization():
    """测试爬虫服务初始化"""
    print("测试爬虫服务初始化...")
    try:
        config = get_config()
        crawler = CrawlerService(config)
        print(f"✓ 爬虫服务初始化成功")
        print(f"  - 基础URL: {crawler.base_url}")
        print(f"  - 爬取延迟: {crawler.crawl_delay}秒")
        print(f"  - 数据库类型: {config.DATABASE_TYPE}")
        return True
    except Exception as e:
        print(f"✗ 爬虫服务初始化失败: {e}")
        return False


def test_article_id_generation():
    """测试文章ID生成"""
    print("\n测试文章ID生成...")
    try:
        config = get_config()
        crawler = CrawlerService(config)
        
        test_url = "https://example.com/test-article"
        article_id = crawler._generate_article_id(test_url)
        
        print(f"✓ 文章ID生成成功")
        print(f"  - URL: {test_url}")
        print(f"  - Article ID: {article_id}")
        print(f"  - ID长度: {len(article_id)}")
        
        # 验证相同URL生成相同ID
        article_id2 = crawler._generate_article_id(test_url)
        if article_id == article_id2:
            print(f"✓ 相同URL生成相同ID（一致性验证通过）")
        else:
            print(f"✗ 相同URL生成不同ID（一致性验证失败）")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 文章ID生成失败: {e}")
        return False


def test_database_connection():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    try:
        config = get_config()
        crawler = CrawlerService(config)
        
        conn = crawler._get_db_connection()
        cursor = conn.cursor()
        
        # 检查articles表是否存在
        if config.DATABASE_TYPE == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        else:
            cursor.execute("SHOW TABLES LIKE 'articles'")
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"✓ 数据库连接成功，articles表存在")
            return True
        else:
            print(f"✗ articles表不存在，请先运行 init_db.py")
            return False
            
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False


def test_statistics():
    """测试统计功能"""
    print("\n测试统计功能...")
    try:
        config = get_config()
        crawler = CrawlerService(config)
        
        stats = crawler.get_statistics()
        
        print(f"✓ 统计信息获取成功")
        print(f"  - 总文章数: {stats['total_articles']}")
        print(f"  - 首次爬取时间: {stats['first_crawled']}")
        print(f"  - 最后爬取时间: {stats['last_crawled']}")
        
        return True
    except Exception as e:
        print(f"✗ 统计信息获取失败: {e}")
        return False


def test_save_and_retrieve():
    """测试保存和检索文章"""
    print("\n测试保存和检索文章...")
    try:
        config = get_config()
        crawler = CrawlerService(config)
        
        # 保存测试文章
        test_url = "https://example.com/test-integration-article"
        test_title = "测试文章标题"
        test_content = "这是一篇测试文章的内容。用于验证数据库存储和检索功能。"
        
        success = crawler._save_article(test_url, test_title, test_content)
        
        if not success:
            print(f"✗ 保存文章失败")
            return False
        
        print(f"✓ 文章保存成功")
        
        # 检索文章
        article_id = crawler._generate_article_id(test_url)
        article = crawler.get_article_by_id(article_id)
        
        if not article:
            print(f"✗ 检索文章失败")
            return False
        
        print(f"✓ 文章检索成功")
        print(f"  - 文章ID: {article['article_id']}")
        print(f"  - URL: {article['url']}")
        print(f"  - 标题: {article['title']}")
        print(f"  - 内容长度: {len(article['content'])}字符")
        
        # 验证数据一致性
        if article['title'] == test_title and article['content'] == test_content:
            print(f"✓ 数据一致性验证通过")
        else:
            print(f"✗ 数据一致性验证失败")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 保存和检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_articles_list():
    """测试获取文章列表"""
    print("\n测试获取文章列表...")
    try:
        config = get_config()
        crawler = CrawlerService(config)
        
        articles = crawler.get_articles(limit=10, offset=0)
        
        print(f"✓ 文章列表获取成功")
        print(f"  - 返回文章数: {len(articles)}")
        
        if articles:
            print(f"  - 第一篇文章标题: {articles[0]['title']}")
        
        return True
    except Exception as e:
        print(f"✗ 获取文章列表失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 70)
    print("爬虫集成测试")
    print("=" * 70)
    
    tests = [
        ("初始化测试", test_crawler_initialization),
        ("ID生成测试", test_article_id_generation),
        ("数据库连接测试", test_database_connection),
        ("统计功能测试", test_statistics),
        ("保存和检索测试", test_save_and_retrieve),
        ("文章列表测试", test_get_articles_list),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n测试异常: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")
    
    print(f"\n通过率: {passed}/{total} ({passed*100//total if total > 0 else 0}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())

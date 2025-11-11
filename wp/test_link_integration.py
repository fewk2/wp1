"""
链接提取和处理功能集成测试
演示完整的工作流程
"""
import os
import sys
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from config import get_config
from link_extractor_service import LinkExtractorService
from crawler_service import CrawlerService
from init_db import initialize_database


def test_integration():
    """集成测试"""
    print("=" * 80)
    print("链接提取和处理功能 - 集成测试")
    print("=" * 80)
    
    config = get_config()
    
    # 1. 初始化数据库
    print("\n步骤 1: 初始化数据库")
    print("-" * 80)
    success = initialize_database(config)
    print(f"数据库初始化: {'成功' if success else '失败'}")
    
    # 2. 创建测试文章（模拟爬虫数据）
    print("\n步骤 2: 创建测试文章")
    print("-" * 80)
    
    crawler_service = CrawlerService(config)
    
    test_articles = [
        {
            'url': 'https://lewz.cn/jprj/test1',
            'title': '测试文章1 - Python教程',
            'content': '''
                这是一个Python教程的分享。
                下载地址：https://pan.baidu.com/s/1abcdef123456
                提取码：py01
                包含基础和进阶内容。
            '''
        },
        {
            'url': 'https://lewz.cn/jprj/test2',
            'title': '测试文章2 - Java资源',
            'content': '''
                Java学习资料分享
                链接: https://pan.baidu.com/share/init?surl=java123
                密码: jv02
                包含Spring Boot示例代码。
            '''
        },
        {
            'url': 'https://lewz.cn/jprj/test3',
            'title': '测试文章3 - 前端资料',
            'content': '''
                前端开发资料集合
                百度网盘: https://pan.baidu.com/s/frontend?pwd=fe03
                包含Vue、React、Angular等框架教程。
            '''
        },
        {
            'url': 'https://lewz.cn/jprj/test4',
            'title': '测试文章4 - 数据库教程',
            'content': '''
                数据库学习资料
                https://pan.baidu.com/s/database456
                这个资源没有提取码
                包含MySQL、PostgreSQL、MongoDB等。
            '''
        }
    ]
    
    for article in test_articles:
        success = crawler_service._save_article(
            url=article['url'],
            title=article['title'],
            content=article['content']
        )
        print(f"保存文章 '{article['title']}': {'成功' if success else '失败'}")
    
    # 3. 提取链接
    print("\n步骤 3: 从文章中提取百度网盘链接")
    print("-" * 80)
    
    extractor = LinkExtractorService(config)
    articles_with_links = extractor.get_articles_with_links(limit=10)
    
    total_links = 0
    for article in articles_with_links:
        links = article.get('extracted_links', [])
        if links:
            print(f"\n文章: {article['title']}")
            print(f"提取到 {len(links)} 个链接:")
            for link in links:
                print(f"  - 链接: {link['link']}")
                print(f"    密码: {link['password'] or '无'}")
                total_links += 1
                
                # 保存到数据库
                extractor.save_extracted_link(
                    article_id=article['article_id'],
                    original_link=link['link'],
                    original_password=link['password'],
                    status='pending'
                )
    
    print(f"\n总共提取并保存了 {total_links} 个链接")
    
    # 4. 查看数据库中的链接
    print("\n步骤 4: 查询数据库中的链接")
    print("-" * 80)
    
    all_links = extractor.get_extracted_links(limit=100)
    print(f"数据库中共有 {len(all_links)} 个链接:")
    
    for i, link in enumerate(all_links, 1):
        print(f"\n{i}. 链接: {link['original_link'][:60]}...")
        print(f"   文章ID: {link['article_id']}")
        print(f"   密码: {link['original_password'] or '无'}")
        print(f"   状态: {link['status']}")
    
    # 5. 模拟更新链接状态（实际转存需要有效Cookie）
    print("\n步骤 5: 模拟处理流程（更新状态）")
    print("-" * 80)
    
    if all_links:
        # 模拟第一个链接转存成功
        link = all_links[0]
        print(f"\n模拟转存第一个链接...")
        extractor.update_extracted_link_status(
            article_id=link['article_id'],
            original_link=link['original_link'],
            status='transferred'
        )
        print(f"状态已更新为: transferred")
        
        # 模拟分享成功
        time.sleep(0.5)
        print(f"\n模拟创建分享链接...")
        extractor.update_extracted_link_status(
            article_id=link['article_id'],
            original_link=link['original_link'],
            new_link='https://pan.baidu.com/s/new_share_link_123',
            new_password='abcd',
            new_title='Python教程完整版.zip',
            status='completed'
        )
        print(f"状态已更新为: completed")
    
    # 6. 查看统计信息
    print("\n步骤 6: 查看统计信息")
    print("-" * 80)
    
    stats = extractor.get_statistics()
    print(f"总链接数: {stats['total_links']}")
    print(f"待处理: {stats['pending']}")
    print(f"处理中: {stats['processing']}")
    print(f"已完成: {stats['completed']}")
    print(f"失败: {stats['failed']}")
    
    # 7. 查看已完成的链接详情
    print("\n步骤 7: 查看已完成的链接")
    print("-" * 80)
    
    completed_links = extractor.get_extracted_links(status='completed', limit=10)
    
    if completed_links:
        print(f"找到 {len(completed_links)} 个已完成的链接:")
        for link in completed_links:
            print(f"\n原始链接: {link['original_link']}")
            print(f"原始密码: {link['original_password'] or '无'}")
            print(f"新链接: {link['new_link']}")
            print(f"新密码: {link['new_password']}")
            print(f"文件标题: {link['new_title']}")
    else:
        print("暂无已完成的链接")
    
    print("\n" + "=" * 80)
    print("集成测试完成！")
    print("=" * 80)
    
    print("\n提示:")
    print("1. 要实际执行转存和分享，需要配置有效的百度网盘账户Cookie")
    print("2. 使用 API 接口 POST /api/links/process 可以执行完整流程")
    print("3. 查看 README_LINK_EXTRACTOR.md 了解更多使用方法")


if __name__ == '__main__':
    test_integration()

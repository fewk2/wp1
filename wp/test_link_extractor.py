"""
测试链接提取服务
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from config import get_config
from link_extractor_service import LinkExtractorService


def test_extract_links():
    """测试链接提取"""
    print("=" * 60)
    print("测试百度网盘链接提取")
    print("=" * 60)
    
    # 测试文本
    test_texts = [
        """
        这里有一个百度网盘分享链接：
        https://pan.baidu.com/s/1a2b3c4d5e6f
        提取码：abcd
        """,
        """
        资源下载地址：https://pan.baidu.com/share/init?surl=xyz123
        密码: 1234
        """,
        """
        链接：https://pan.baidu.com/s/testlink?pwd=test
        """,
        """
        百度云盘地址：https://pan.baidu.com/s/example
        没有密码
        """
    ]
    
    config = get_config()
    service = LinkExtractorService(config)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试文本 {i}:")
        print("-" * 40)
        print(text.strip())
        print("-" * 40)
        
        links = service.extract_links_from_text(text)
        
        if links:
            print(f"提取到 {len(links)} 个链接:")
            for link in links:
                print(f"  链接: {link['link']}")
                print(f"  密码: {link['password'] or '无'}")
                print()
        else:
            print("未提取到链接")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_database_operations():
    """测试数据库操作"""
    print("\n" + "=" * 60)
    print("测试数据库操作")
    print("=" * 60)
    
    config = get_config()
    service = LinkExtractorService(config)
    
    # 测试保存
    test_article_id = "test_article_001"
    test_link = "https://pan.baidu.com/s/test123"
    test_password = "abcd"
    
    print("\n1. 保存提取的链接...")
    success = service.save_extracted_link(
        article_id=test_article_id,
        original_link=test_link,
        original_password=test_password,
        status='pending'
    )
    print(f"   结果: {'成功' if success else '失败'}")
    
    # 测试查询
    print("\n2. 查询提取的链接...")
    links = service.get_extracted_links(article_id=test_article_id, limit=10)
    print(f"   找到 {len(links)} 个链接")
    for link in links:
        print(f"   - {link['original_link']} (状态: {link['status']})")
    
    # 测试更新
    print("\n3. 更新链接状态...")
    success = service.update_extracted_link_status(
        article_id=test_article_id,
        original_link=test_link,
        new_link="https://pan.baidu.com/s/new123",
        new_password="xyz",
        new_title="测试文件",
        status='completed'
    )
    print(f"   结果: {'成功' if success else '失败'}")
    
    # 测试统计
    print("\n4. 获取统计信息...")
    stats = service.get_statistics()
    print(f"   总链接数: {stats.get('total_links', 0)}")
    print(f"   待处理: {stats.get('pending', 0)}")
    print(f"   处理中: {stats.get('processing', 0)}")
    print(f"   已完成: {stats.get('completed', 0)}")
    print(f"   失败: {stats.get('failed', 0)}")
    
    print("\n" + "=" * 60)
    print("数据库测试完成")
    print("=" * 60)


if __name__ == '__main__':
    # 测试链接提取
    test_extract_links()
    
    # 测试数据库操作
    test_database_operations()

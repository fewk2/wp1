"""
知识库存储层使用示例
演示如何使用 KnowledgeRepository 进行查询和导出
"""
from knowledge_repository import KnowledgeRepository


def example_basic_query():
    """示例1：基本查询"""
    print("\n=== 示例1：基本查询 ===")
    repo = KnowledgeRepository()
    
    result = repo.list_entries(limit=10, offset=0)
    
    print(f"总条数: {result['total']}")
    print(f"返回条数: {len(result['entries'])}")
    print(f"是否有更多: {result['has_more']}")
    
    if result['entries']:
        print("\n前3条记录:")
        for i, entry in enumerate(result['entries'][:3], 1):
            print(f"{i}. {entry['article_title']}")
            print(f"   标签: {entry['tag']}, 状态: {entry['status']}")
            print(f"   原始链接: {entry['original_link']}")
            if entry['new_link']:
                print(f"   新链接: {entry['new_link']}")


def example_search():
    """示例2：搜索查询"""
    print("\n=== 示例2：搜索查询 ===")
    repo = KnowledgeRepository()
    
    search_term = "测试"
    result = repo.list_entries(search=search_term, limit=10)
    
    print(f"搜索关键词: '{search_term}'")
    print(f"找到 {len(result['entries'])} 条记录")
    
    for entry in result['entries']:
        print(f"- {entry['article_title']} ({entry['tag']})")


def example_filter_by_status():
    """示例3：按状态过滤"""
    print("\n=== 示例3：按状态过滤 ===")
    repo = KnowledgeRepository()
    
    for status in ['pending', 'completed', 'failed']:
        result = repo.list_entries(status=status, limit=100)
        print(f"{status}: {len(result['entries'])} 条")


def example_filter_by_tag():
    """示例4：按标签过滤"""
    print("\n=== 示例4：按标签过滤 ===")
    repo = KnowledgeRepository()
    
    tags = repo.get_distinct_tags()
    print(f"可用标签: {tags}")
    
    if tags:
        first_tag = tags[0]
        result = repo.list_entries(tag=first_tag, limit=100)
        print(f"\n标签 '{first_tag}' 的记录数: {len(result['entries'])}")


def example_date_range():
    """示例5：日期范围查询"""
    print("\n=== 示例5：日期范围查询 ===")
    repo = KnowledgeRepository()
    
    result = repo.list_entries(
        date_from='2024-01-01',
        date_to='2024-12-31',
        limit=100
    )
    
    print(f"2024年的记录数: {len(result['entries'])}")


def example_sorting():
    """示例6：排序"""
    print("\n=== 示例6：排序 ===")
    repo = KnowledgeRepository()
    
    result = repo.list_entries(
        limit=5,
        sort_by='updated_at',
        sort_order='DESC'
    )
    
    print("按更新时间倒序:")
    for entry in result['entries']:
        print(f"- {entry['article_title']}: {entry['updated_at']}")


def example_statistics():
    """示例7：统计信息"""
    print("\n=== 示例7：统计信息 ===")
    repo = KnowledgeRepository()
    
    stats = repo.summaries_by_status()
    total = sum(stats.values())
    
    print(f"总计: {total} 条记录")
    print("状态分布:")
    for status, count in stats.items():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {status}: {count} ({percentage:.1f}%)")


def example_export():
    """示例8：导出数据"""
    print("\n=== 示例8：导出数据 ===")
    repo = KnowledgeRepository()
    
    fields = [
        'article_title',
        'tag',
        'original_link',
        'new_link',
        'status',
        'created_at'
    ]
    
    rows = repo.prepare_export_rows(
        fields=fields,
        filters={'status': 'completed'},
        sort_by='created_at',
        sort_order='DESC'
    )
    
    print(f"准备导出 {len(rows)} 条记录")
    print(f"字段: {', '.join(fields)}")
    
    if rows:
        print("\n示例数据:")
        print(rows[0])


def example_complex_query():
    """示例9：复杂组合查询"""
    print("\n=== 示例9：复杂组合查询 ===")
    repo = KnowledgeRepository()
    
    result = repo.list_entries(
        search='网盘',
        status='completed',
        date_from='2024-01-01',
        limit=10,
        offset=0,
        sort_by='created_at',
        sort_order='DESC'
    )
    
    print(f"查询条件:")
    print(f"  - 搜索: '网盘'")
    print(f"  - 状态: completed")
    print(f"  - 日期: >= 2024-01-01")
    print(f"  - 排序: 创建时间倒序")
    print(f"\n结果: 找到 {len(result['entries'])} 条记录")


def example_pagination():
    """示例10：分页查询"""
    print("\n=== 示例10：分页查询 ===")
    repo = KnowledgeRepository()
    
    page_size = 10
    page = 0
    
    print(f"分页大小: {page_size}")
    
    result = repo.list_entries(limit=page_size, offset=page * page_size)
    total_pages = (result['total'] + page_size - 1) // page_size
    
    print(f"总记录数: {result['total']}")
    print(f"总页数: {total_pages}")
    print(f"当前页: {page + 1}")
    print(f"当前页记录数: {len(result['entries'])}")
    print(f"是否有下一页: {result['has_more']}")


if __name__ == '__main__':
    print("="*60)
    print("知识库存储层使用示例")
    print("="*60)
    
    try:
        example_basic_query()
        example_search()
        example_filter_by_status()
        example_filter_by_tag()
        example_date_range()
        example_sorting()
        example_statistics()
        example_export()
        example_complex_query()
        example_pagination()
        
        print("\n" + "="*60)
        print("✅ 所有示例执行完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

"""
知识库API使用示例
演示如何使用知识库REST API查询、筛选和导出数据
"""
import os
import sys
import requests
from datetime import datetime, timedelta

# API配置
API_KEY = os.getenv('API_SECRET_KEY', 'your_api_key_here')
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')


def get_headers():
    """获取请求头"""
    return {'X-API-Key': API_KEY}


def example_get_entries():
    """示例：获取知识库条目列表"""
    print("\n=== 示例1: 获取条目列表 ===")
    
    response = requests.get(
        f'{BASE_URL}/api/knowledge/entries',
        headers=get_headers(),
        params={
            'page': 1,
            'page_size': 10,
            'sort': 'created_at',
            'order': 'DESC'
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        entries = data['data']['entries']
        pagination = data['data']['pagination']
        summary = data['summary']
        
        print(f"状态: 成功")
        print(f"找到 {pagination['total']} 条记录")
        print(f"当前页: {pagination['page']}/{pagination['total_pages']}")
        print(f"状态统计: {summary}")
        
        if entries:
            print(f"\n前 {len(entries)} 条记录:")
            for i, entry in enumerate(entries[:3], 1):
                print(f"\n{i}. {entry['article_title']}")
                print(f"   ID: {entry['article_id']}")
                print(f"   状态: {entry['status']}")
                print(f"   标签: {entry['tag']}")
    else:
        print(f"错误: {response.status_code}")
        print(response.text)


def example_search_entries():
    """示例：搜索条目"""
    print("\n=== 示例2: 搜索条目 ===")
    
    search_term = input("请输入搜索关键词（留空跳过）: ").strip()
    
    if not search_term:
        print("跳过搜索示例")
        return
    
    response = requests.get(
        f'{BASE_URL}/api/knowledge/entries',
        headers=get_headers(),
        params={
            'search': search_term,
            'page_size': 5
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        entries = data['data']['entries']
        
        print(f"搜索关键词 '{search_term}' 找到 {len(entries)} 条结果")
        
        for i, entry in enumerate(entries, 1):
            print(f"\n{i}. {entry['article_title']}")
            print(f"   原始链接: {entry['original_link']}")
            if entry['new_link']:
                print(f"   新链接: {entry['new_link']}")
    else:
        print(f"错误: {response.status_code}")


def example_filter_by_status():
    """示例：按状态筛选"""
    print("\n=== 示例3: 按状态筛选 ===")
    
    response = requests.get(
        f'{BASE_URL}/api/knowledge/statuses',
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        statuses = data['data']['statuses']
        
        print("可用的状态:")
        for status, count in statuses.items():
            print(f"  - {status}: {count} 条")
        
        status_filter = input("\n请选择要筛选的状态（留空跳过）: ").strip()
        
        if status_filter:
            response = requests.get(
                f'{BASE_URL}/api/knowledge/entries',
                headers=get_headers(),
                params={'status': status_filter, 'page_size': 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                entries = data['data']['entries']
                print(f"\n状态为 '{status_filter}' 的记录: {len(entries)} 条")


def example_get_tags():
    """示例：获取标签列表"""
    print("\n=== 示例4: 获取标签列表 ===")
    
    response = requests.get(
        f'{BASE_URL}/api/knowledge/tags',
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        tags = data['data']['tags']
        
        print(f"共有 {len(tags)} 个标签:")
        for tag in tags:
            print(f"  - {tag}")
        
        tag_filter = input("\n请选择要筛选的标签（留空跳过）: ").strip()
        
        if tag_filter:
            response = requests.get(
                f'{BASE_URL}/api/knowledge/entries',
                headers=get_headers(),
                params={'tag': tag_filter, 'page_size': 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                entries = data['data']['entries']
                print(f"\n标签为 '{tag_filter}' 的记录: {len(entries)} 条")


def example_date_range_filter():
    """示例：日期范围筛选"""
    print("\n=== 示例5: 日期范围筛选 ===")
    
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    date_from = week_ago.strftime('%Y-%m-%d')
    date_to = today.strftime('%Y-%m-%d')
    
    print(f"筛选最近7天的记录 ({date_from} 至 {date_to})")
    
    response = requests.get(
        f'{BASE_URL}/api/knowledge/entries',
        headers=get_headers(),
        params={
            'date_from': date_from,
            'date_to': date_to,
            'page_size': 10
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        entries = data['data']['entries']
        print(f"找到 {len(entries)} 条最近7天的记录")


def example_export_csv():
    """示例：导出CSV"""
    print("\n=== 示例6: 导出CSV ===")
    
    fields = 'article_title,original_link,new_link,status'
    
    response = requests.get(
        f'{BASE_URL}/api/knowledge/export',
        headers=get_headers(),
        params={
            'fields': fields,
            'status': 'completed'
        }
    )
    
    if response.status_code == 200:
        filename = 'knowledge_export_example.csv'
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"CSV导出成功: {filename}")
        print(f"文件大小: {len(response.content)} 字节")
        print(f"导出字段: {fields}")
    else:
        print(f"导出失败: {response.status_code}")


def example_get_entry_detail():
    """示例：获取单个条目详情"""
    print("\n=== 示例7: 获取条目详情 ===")
    
    article_id = input("请输入文章ID（留空跳过）: ").strip()
    
    if not article_id:
        print("跳过详情查询")
        return
    
    response = requests.get(
        f'{BASE_URL}/api/knowledge/entry/{article_id}',
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        entry = data['data']
        
        print("\n条目详情:")
        print(f"  标题: {entry['article_title']}")
        print(f"  URL: {entry['article_url']}")
        print(f"  原始链接: {entry['original_link']}")
        print(f"  原始密码: {entry['original_password']}")
        print(f"  新链接: {entry['new_link']}")
        print(f"  新密码: {entry['new_password']}")
        print(f"  状态: {entry['status']}")
        print(f"  标签: {entry['tag']}")
        print(f"  创建时间: {entry['created_at']}")
        print(f"  更新时间: {entry['updated_at']}")
    elif response.status_code == 404:
        print(f"未找到ID为 '{article_id}' 的条目")
    else:
        print(f"查询失败: {response.status_code}")


def main():
    """主函数"""
    print("知识库API使用示例")
    print("=" * 60)
    print(f"API地址: {BASE_URL}")
    print(f"API密钥: {'已配置' if API_KEY != 'your_api_key_here' else '未配置'}")
    print("=" * 60)
    
    if API_KEY == 'your_api_key_here':
        print("\n⚠️  警告: 请设置环境变量 API_SECRET_KEY")
        print("示例: export API_SECRET_KEY='your_actual_api_key'")
        sys.exit(1)
    
    examples = [
        ("获取条目列表", example_get_entries),
        ("搜索条目", example_search_entries),
        ("按状态筛选", example_filter_by_status),
        ("获取标签列表", example_get_tags),
        ("日期范围筛选", example_date_range_filter),
        ("导出CSV", example_export_csv),
        ("获取条目详情", example_get_entry_detail),
    ]
    
    print("\n可用的示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("0. 运行所有示例")
    
    try:
        choice = input("\n请选择示例编号 (0-7): ").strip()
        
        if choice == '0':
            for name, func in examples:
                try:
                    func()
                except Exception as e:
                    print(f"示例 '{name}' 执行出错: {e}")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            name, func = examples[int(choice) - 1]
            func()
        else:
            print("无效的选择")
    
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == '__main__':
    main()

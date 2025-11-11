#!/usr/bin/env python3
"""
综合验证脚本 - 验证wp1知识库系统的所有功能
"""
import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:5000"
API_KEY = "test_deployment_key_12345"
HEADERS = {"X-API-Key": API_KEY}

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    print_section("1. 健康检查测试")
    try:
        resp = requests.get(f"{API_BASE}/api/health")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ 状态: {data.get('status')}")
            print(f"✓ 消息: {data.get('message')}")
            print(f"✓ 版本: {data.get('version')}")
            print(f"✓ 账户: {', '.join(data.get('accounts', []))}")
            return True
        else:
            print(f"✗ HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_knowledge_entries():
    print_section("2. 知识库列表测试")
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS,
            params={"page": 1, "page_size": 10}
        )
        if resp.status_code == 200:
            data = resp.json()
            entries = data['data']['entries']
            pagination = data['data'].get('pagination', {})
            total = pagination.get('total', len(entries))
            print(f"✓ 返回记录数: {len(entries)}")
            print(f"✓ 总记录数: {total}")
            print(f"✓ 当前页: {pagination.get('page', 1)}")
            print(f"✓ 页大小: {pagination.get('page_size', len(entries))}")
            if entries:
                print("\n示例记录:")
                entry = entries[0]
                print(f"  - 标题: {entry.get('article_title')}")
                print(f"  - 状态: {entry.get('status')}")
                print(f"  - 标签: {entry.get('tag')}")
                print(f"  - 原始链接: {entry.get('original_link')}")
                if entry.get('new_link'):
                    print(f"  - 新链接: {entry.get('new_link')}")
            return True
        else:
            print(f"✗ HTTP {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_search():
    print_section("3. 搜索功能测试")
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS,
            params={"search": "技术", "page": 1, "page_size": 10}
        )
        if resp.status_code == 200:
            data = resp.json()
            entries = data['data']['entries']
            print(f"✓ 搜索'技术'返回 {len(entries)} 条记录")
            for entry in entries:
                print(f"  - {entry.get('article_title')}")
            return True
        else:
            print(f"✗ HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_filters():
    print_section("4. 过滤功能测试")
    results = []
    
    # 测试状态过滤
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS,
            params={"status": "completed", "page": 1, "page_size": 10}
        )
        if resp.status_code == 200:
            data = resp.json()
            count = len(data['data']['entries'])
            print(f"✓ 状态过滤 (completed): {count} 条记录")
            results.append(True)
        else:
            print(f"✗ 状态过滤失败: HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        print(f"✗ 状态过滤错误: {e}")
        results.append(False)
    
    # 测试标签过滤
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS,
            params={"tag": "technology", "page": 1, "page_size": 10}
        )
        if resp.status_code == 200:
            data = resp.json()
            count = len(data['data']['entries'])
            print(f"✓ 标签过滤 (technology): {count} 条记录")
            results.append(True)
        else:
            print(f"✗ 标签过滤失败: HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        print(f"✗ 标签过滤错误: {e}")
        results.append(False)
    
    return all(results)

def test_tags():
    print_section("5. 标签列表测试")
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/tags",
            headers=HEADERS
        )
        if resp.status_code == 200:
            data = resp.json()
            tags = data.get('tags', [])
            print(f"✓ 标签数量: {len(tags)}")
            print(f"✓ 标签列表: {', '.join(tags)}")
            return True
        else:
            print(f"✗ HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_statuses():
    print_section("6. 状态统计测试")
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/statuses",
            headers=HEADERS
        )
        if resp.status_code == 200:
            data = resp.json()
            statuses = data.get('statuses', {})
            print(f"✓ 状态统计:")
            for status, count in statuses.items():
                print(f"  - {status}: {count}")
            return True
        else:
            print(f"✗ HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_export():
    print_section("7. CSV导出测试")
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/export",
            headers=HEADERS,
            params={
                "fields": "article_title,status,new_link,created_at"
            }
        )
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            print(f"✓ CSV导出成功")
            print(f"✓ 总行数: {len(lines)} (含表头)")
            print(f"✓ 数据行数: {len(lines) - 1}")
            print("\n前3行:")
            for i, line in enumerate(lines[:3], 1):
                print(f"  {i}. {line}")
            return True
        else:
            print(f"✗ HTTP {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_sorting():
    print_section("8. 排序功能测试")
    results = []
    
    # 测试按创建时间排序
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS,
            params={"sort_by": "created_at", "sort_order": "DESC", "page": 1, "page_size": 5}
        )
        if resp.status_code == 200:
            data = resp.json()
            entries = data['data']['entries']
            print(f"✓ 按创建时间降序: {len(entries)} 条记录")
            results.append(True)
        else:
            print(f"✗ 排序失败: HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        print(f"✗ 排序错误: {e}")
        results.append(False)
    
    # 测试按标题排序
    try:
        resp = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS,
            params={"sort_by": "title", "sort_order": "ASC", "page": 1, "page_size": 5}
        )
        if resp.status_code == 200:
            data = resp.json()
            entries = data['data']['entries']
            print(f"✓ 按标题升序: {len(entries)} 条记录")
            results.append(True)
        else:
            print(f"✗ 排序失败: HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        print(f"✗ 排序错误: {e}")
        results.append(False)
    
    return all(results)

def test_pagination():
    print_section("9. 分页功能测试")
    try:
        # 获取第1页
        resp1 = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS,
            params={"page": 1, "page_size": 2}
        )
        # 获取第2页
        resp2 = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS,
            params={"page": 2, "page_size": 2}
        )
        
        if resp1.status_code == 200 and resp2.status_code == 200:
            data1 = resp1.json()
            data2 = resp2.json()
            pagination1 = data1['data'].get('pagination', {})
            print(f"✓ 第1页: {len(data1['data']['entries'])} 条记录")
            print(f"✓ 第2页: {len(data2['data']['entries'])} 条记录")
            print(f"✓ 总记录数: {pagination1.get('total', 0)}")
            return True
        else:
            print(f"✗ 分页失败")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_ui():
    print_section("10. UI界面测试")
    try:
        resp = requests.get(f"{API_BASE}/kb")
        if resp.status_code == 200:
            html = resp.text
            checks = [
                ("知识库管理", "页面标题"),
                ("搜索", "搜索功能"),
                ("导出", "导出功能"),
                ("API Key", "API密钥输入")
            ]
            
            all_ok = True
            for keyword, desc in checks:
                if keyword in html:
                    print(f"✓ {desc}: 存在")
                else:
                    print(f"✗ {desc}: 缺失")
                    all_ok = False
            
            return all_ok
        else:
            print(f"✗ HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def test_auth():
    print_section("11. API认证测试")
    try:
        # 无认证请求
        resp = requests.get(f"{API_BASE}/api/knowledge/entries")
        if resp.status_code == 401:
            print("✓ 无认证请求正确返回401")
            no_auth_ok = True
        else:
            print(f"✗ 无认证请求返回 {resp.status_code}，期望401")
            no_auth_ok = False
        
        # 有认证请求
        resp = requests.get(
            f"{API_BASE}/api/knowledge/entries",
            headers=HEADERS
        )
        if resp.status_code == 200:
            print("✓ 有认证请求正确返回200")
            with_auth_ok = True
        else:
            print(f"✗ 有认证请求返回 {resp.status_code}，期望200")
            with_auth_ok = False
        
        return no_auth_ok and with_auth_ok
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("  wp1 知识库系统综合验证")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {API_BASE}")
    print(f"API密钥: {API_KEY[:10]}...")
    
    tests = [
        ("健康检查", test_health),
        ("知识库列表", test_knowledge_entries),
        ("搜索功能", test_search),
        ("过滤功能", test_filters),
        ("标签列表", test_tags),
        ("状态统计", test_statuses),
        ("CSV导出", test_export),
        ("排序功能", test_sorting),
        ("分页功能", test_pagination),
        ("UI界面", test_ui),
        ("API认证", test_auth),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name}测试异常: {e}")
            results[name] = False
    
    # 输出总结
    print_section("验证总结")
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"总测试数: {total}")
    print(f"通过: {passed} ✓")
    print(f"失败: {failed} ✗")
    print(f"\n成功率: {passed/total*100:.1f}%")
    
    print("\n详细结果:")
    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
    
    print("\n" + "=" * 60)
    if all(results.values()):
        print("  ✅ 所有验证通过！系统就绪。")
    else:
        print("  ⚠️ 部分验证失败，请检查上述输出。")
    print("=" * 60)
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())

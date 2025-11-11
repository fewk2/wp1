#!/usr/bin/env python3
"""
知识库UI测试脚本
验证静态文件和路由是否正确配置
"""
import os
import sys
from flask import Flask

sys.path.insert(0, os.path.dirname(__file__))

def test_knowledge_ui_files():
    """测试知识库UI文件是否存在"""
    base_dir = os.path.dirname(__file__)
    static_dir = os.path.join(base_dir, 'static', 'knowledge')
    
    required_files = ['index.html', 'style.css', 'app.js']
    
    print("=" * 60)
    print("知识库UI文件检查")
    print("=" * 60)
    
    all_exist = True
    for filename in required_files:
        filepath = os.path.join(static_dir, filename)
        exists = os.path.exists(filepath)
        
        if exists:
            size = os.path.getsize(filepath)
            print(f"✓ {filename:20s} - {size:,} bytes")
        else:
            print(f"✗ {filename:20s} - 文件不存在")
            all_exist = False
    
    print()
    return all_exist


def test_knowledge_ui_routes():
    """测试知识库UI路由是否配置"""
    from server import app
    
    print("=" * 60)
    print("知识库UI路由检查")
    print("=" * 60)
    
    required_routes = [
        ('/kb', 'GET'),
        ('/kb/', 'GET'),
        ('/api/knowledge/entries', 'GET'),
        ('/api/knowledge/tags', 'GET'),
        ('/api/knowledge/statuses', 'GET'),
        ('/api/knowledge/export', 'GET')
    ]
    
    all_found = True
    with app.test_client() as client:
        for route, method in required_routes:
            rules = [rule for rule in app.url_map.iter_rules() if rule.rule == route]
            
            if rules and method in rules[0].methods:
                print(f"✓ {method:6s} {route}")
            else:
                print(f"✗ {method:6s} {route} - 路由未找到")
                all_found = False
    
    print()
    return all_found


def test_ui_content():
    """测试UI内容包含必要元素"""
    base_dir = os.path.dirname(__file__)
    
    print("=" * 60)
    print("知识库UI内容检查")
    print("=" * 60)
    
    checks = []
    
    html_path = os.path.join(base_dir, 'static', 'knowledge', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        checks.append(('HTML包含style.css引用', 'style.css' in html_content))
        checks.append(('HTML包含app.js引用', 'app.js' in html_content))
        checks.append(('HTML包含API Key输入', 'apiKeyInput' in html_content))
        checks.append(('HTML包含筛选面板', 'filter-section' in html_content))
        checks.append(('HTML包含数据表格', 'data-table' in html_content))
    
    css_path = os.path.join(base_dir, 'static', 'knowledge', 'style.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
        checks.append(('CSS包含响应式布局', '@media' in css_content))
        checks.append(('CSS包含状态徽章样式', 'status-badge' in css_content))
        checks.append(('CSS包含模态框样式', 'modal' in css_content))
    
    js_path = os.path.join(base_dir, 'static', 'knowledge', 'app.js')
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
        checks.append(('JS包含KnowledgeApp类', 'class KnowledgeApp' in js_content))
        checks.append(('JS包含API调用', 'fetchAPI' in js_content))
        checks.append(('JS包含筛选功能', 'applyFilters' in js_content))
        checks.append(('JS包含导出功能', 'exportData' in js_content))
        checks.append(('JS包含列管理', 'applyColumnSettings' in js_content))
    
    all_passed = True
    for check_name, result in checks:
        if result:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
            all_passed = False
    
    print()
    return all_passed


def main():
    """主测试函数"""
    print("\n🧪 知识库UI完整性测试\n")
    
    test_results = []
    
    test_results.append(("文件存在性", test_knowledge_ui_files()))
    test_results.append(("路由配置", test_knowledge_ui_routes()))
    test_results.append(("内容完整性", test_ui_content()))
    
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20s}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✅ 所有测试通过！知识库UI已就绪。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == '__main__':
    sys.exit(main())

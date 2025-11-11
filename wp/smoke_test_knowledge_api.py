"""
知识库API冒烟测试
快速验证API端点是否可访问
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from server import app
from config import get_config

config = get_config()


def test_endpoints():
    """测试所有端点"""
    app.config['TESTING'] = True
    client = app.test_client()
    auth_headers = {'X-API-Key': config.API_SECRET_KEY}
    
    tests = [
        ('GET', '/api/knowledge/entries', auth_headers, [200]),
        ('GET', '/api/knowledge/tags', auth_headers, [200]),
        ('GET', '/api/knowledge/statuses', auth_headers, [200]),
        ('GET', '/api/knowledge/export', auth_headers, [200]),
        ('GET', '/api/knowledge/entry/test', auth_headers, [200, 404]),
        ('GET', '/kb', {}, [200, 404]),
        ('GET', '/api/knowledge/entries', {}, [401]),
    ]
    
    print("开始冒烟测试...")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for method, endpoint, headers, expected_codes in tests:
        try:
            if method == 'GET':
                response = client.get(endpoint, headers=headers)
            else:
                response = client.post(endpoint, headers=headers)
            
            status_ok = response.status_code in expected_codes
            
            if status_ok:
                print(f"✓ {method} {endpoint} -> {response.status_code}")
                passed += 1
            else:
                print(f"✗ {method} {endpoint} -> {response.status_code} (expected {expected_codes})")
                failed += 1
                
        except Exception as e:
            print(f"✗ {method} {endpoint} -> ERROR: {e}")
            failed += 1
    
    print("-" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    
    return failed == 0


if __name__ == '__main__':
    success = test_endpoints()
    sys.exit(0 if success else 1)

"""
知识库API集成测试
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from server import app
from config import get_config

config = get_config()


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    """获取认证头"""
    return {'X-API-Key': config.API_SECRET_KEY}


def test_get_entries_without_auth(client):
    """测试无认证访问条目列表"""
    response = client.get('/api/knowledge/entries')
    assert response.status_code == 401
    data = response.get_json()
    assert data['success'] is False
    assert 'API key' in data['error'] or 'API密钥' in data['message']


def test_get_entries_with_auth(client, auth_headers):
    """测试获取条目列表"""
    response = client.get('/api/knowledge/entries', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data
    assert 'entries' in data['data']
    assert 'pagination' in data['data']
    assert 'summary' in data


def test_get_entries_with_pagination(client, auth_headers):
    """测试分页参数"""
    response = client.get(
        '/api/knowledge/entries?page=1&page_size=10',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    pagination = data['data']['pagination']
    assert pagination['page'] == 1
    assert pagination['page_size'] == 10


def test_get_entries_with_filters(client, auth_headers):
    """测试过滤参数"""
    response = client.get(
        '/api/knowledge/entries?status=completed&sort=created_at&order=DESC',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True


def test_get_entries_invalid_sort_field(client, auth_headers):
    """测试非法排序字段"""
    response = client.get(
        '/api/knowledge/entries?sort=invalid_field',
        headers=auth_headers
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_get_entries_invalid_sort_order(client, auth_headers):
    """测试非法排序方向"""
    response = client.get(
        '/api/knowledge/entries?sort=created_at&order=INVALID',
        headers=auth_headers
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_get_tags(client, auth_headers):
    """测试获取标签列表"""
    response = client.get('/api/knowledge/tags', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data
    assert 'tags' in data['data']
    assert 'count' in data['data']
    assert isinstance(data['data']['tags'], list)


def test_get_statuses(client, auth_headers):
    """测试获取状态统计"""
    response = client.get('/api/knowledge/statuses', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'data' in data
    assert 'statuses' in data['data']
    assert 'total' in data['data']
    assert isinstance(data['data']['statuses'], dict)


def test_export_csv(client, auth_headers):
    """测试CSV导出"""
    response = client.get('/api/knowledge/export', headers=auth_headers)
    assert response.status_code == 200
    assert response.content_type == 'text/csv; charset=utf-8'
    assert 'attachment' in response.headers.get('Content-Disposition', '')


def test_export_csv_with_fields(client, auth_headers):
    """测试自定义字段导出"""
    response = client.get(
        '/api/knowledge/export?fields=article_id,article_title,status',
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.content_type == 'text/csv; charset=utf-8'


def test_export_csv_with_filters(client, auth_headers):
    """测试带过滤条件的导出"""
    response = client.get(
        '/api/knowledge/export?status=completed&date_from=2024-01-01',
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.content_type == 'text/csv; charset=utf-8'


def test_export_csv_invalid_fields(client, auth_headers):
    """测试非法字段导出"""
    response = client.get(
        '/api/knowledge/export?fields=invalid_field',
        headers=auth_headers
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_get_entry_detail(client, auth_headers):
    """测试获取条目详情"""
    response = client.get('/api/knowledge/entry/test_id', headers=auth_headers)
    assert response.status_code in [200, 404]
    data = response.get_json()
    assert 'success' in data


def test_kb_static_route(client):
    """测试知识库UI路由"""
    response = client.get('/kb')
    assert response.status_code in [200, 404]
    
    response = client.get('/kb/')
    assert response.status_code in [200, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
爬虫功能测试脚本
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_SECRET_KEY', 'default_insecure_key')
BASE_URL = 'http://localhost:5000'

headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}


def test_health():
    """测试健康检查"""
    print("测试健康检查...")
    response = requests.get(f'{BASE_URL}/api/health')
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()


def test_crawler_stats():
    """测试爬虫统计信息"""
    print("测试爬虫统计信息...")
    response = requests.get(f'{BASE_URL}/api/crawler/stats', headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def test_get_articles():
    """测试获取文章列表"""
    print("测试获取文章列表...")
    response = requests.get(f'{BASE_URL}/api/crawler/articles?limit=5', headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def test_start_crawling():
    """测试开始爬取"""
    print("测试开始爬取（这将需要一些时间）...")
    print("注意：此测试会实际访问 lewz.cn/jprj，请确保遵守网站的robots.txt")
    confirm = input("是否继续？(y/n): ")
    
    if confirm.lower() != 'y':
        print("已取消测试")
        return
    
    response = requests.post(f'{BASE_URL}/api/crawler/start', headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("爬虫功能测试")
    print("=" * 60)
    print()
    
    test_health()
    test_crawler_stats()
    test_get_articles()
    
    print("=" * 60)
    print("如需测试实际爬取功能，请运行 test_start_crawling()")
    print("=" * 60)

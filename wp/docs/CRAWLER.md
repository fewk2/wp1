# 爬虫功能文档

## 概述

本项目集成了 Crawl4AI 框架，用于爬取 lewz.cn/jprj 目录下的文章并存储到数据库中。

## 功能特性

- ✅ 使用 Crawl4AI 框架进行网页爬取
- ✅ 单线程慢速爬取，避免对目标网站造成压力
- ✅ 为每篇文章分配唯一 ID（基于 URL 的 MD5 哈希）
- ✅ 存储文章的完整信息（URL、标题、内容、唯一ID、爬取时间）
- ✅ 支持增量更新（避免重复爬取）
- ✅ 提供完整的 REST API 接口

## 数据库结构

### articles 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER/SERIAL | 自增主键 |
| article_id | TEXT/VARCHAR(255) | 文章唯一ID（URL的MD5哈希，UNIQUE） |
| url | TEXT | 文章URL（UNIQUE） |
| title | TEXT | 文章标题 |
| content | TEXT/LONGTEXT | 文章正文内容 |
| crawled_at | TIMESTAMP | 首次爬取时间 |
| updated_at | TIMESTAMP | 最后更新时间 |

**索引**:
- `idx_articles_article_id`: article_id 索引
- `idx_articles_url`: url 索引（SQLite）

## API 接口

### 1. 开始爬取

**请求**:
```http
POST /api/crawler/start
X-API-Key: your_api_key
```

**响应**:
```json
{
  "success": true,
  "message": "爬取任务完成",
  "data": {
    "success": true,
    "total_crawled": 50,
    "saved_count": 45,
    "error_count": 5,
    "elapsed_time": 180.5,
    "timestamp": "2024-01-01 12:00:00"
  }
}
```

**限流**: 每小时最多 5 次

### 2. 获取文章列表

**请求**:
```http
GET /api/crawler/articles?limit=10&offset=0
X-API-Key: your_api_key
```

**参数**:
- `limit` (可选): 返回数量限制，默认 100
- `offset` (可选): 偏移量，默认 0

**响应**:
```json
{
  "success": true,
  "data": {
    "articles": [
      {
        "id": 1,
        "article_id": "abc123def456",
        "url": "https://lewz.cn/jprj/article1",
        "title": "文章标题",
        "content_preview": "文章内容预览（前200字符）...",
        "crawled_at": "2024-01-01 12:00:00",
        "updated_at": "2024-01-01 12:00:00"
      }
    ],
    "limit": 10,
    "offset": 0,
    "count": 10
  }
}
```

### 3. 获取文章详情

**请求**:
```http
GET /api/crawler/articles/{article_id}
X-API-Key: your_api_key
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "article_id": "abc123def456",
    "url": "https://lewz.cn/jprj/article1",
    "title": "文章标题",
    "content": "完整的文章内容...",
    "crawled_at": "2024-01-01 12:00:00",
    "updated_at": "2024-01-01 12:00:00"
  }
}
```

### 4. 获取爬虫统计信息

**请求**:
```http
GET /api/crawler/stats
X-API-Key: your_api_key
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_articles": 45,
    "first_crawled": "2024-01-01 10:00:00",
    "last_crawled": "2024-01-01 12:00:00"
  }
}
```

## 使用示例

### Python 示例

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:5000"

headers = {
    "X-API-Key": API_KEY
}

# 开始爬取
response = requests.post(f"{BASE_URL}/api/crawler/start", headers=headers)
print(response.json())

# 获取统计信息
response = requests.get(f"{BASE_URL}/api/crawler/stats", headers=headers)
print(response.json())

# 获取文章列表
response = requests.get(f"{BASE_URL}/api/crawler/articles?limit=5", headers=headers)
print(response.json())

# 获取文章详情
article_id = "abc123def456"
response = requests.get(f"{BASE_URL}/api/crawler/articles/{article_id}", headers=headers)
print(response.json())
```

### cURL 示例

```bash
# 开始爬取
curl -X POST http://localhost:5000/api/crawler/start \
  -H "X-API-Key: your_api_key"

# 获取统计信息
curl -X GET http://localhost:5000/api/crawler/stats \
  -H "X-API-Key: your_api_key"

# 获取文章列表
curl -X GET "http://localhost:5000/api/crawler/articles?limit=10" \
  -H "X-API-Key: your_api_key"

# 获取文章详情
curl -X GET http://localhost:5000/api/crawler/articles/{article_id} \
  -H "X-API-Key: your_api_key"
```

## 爬取策略

### 慢速爬取
- 每次请求之间间隔 3 秒，避免对目标网站造成压力
- 单线程执行，确保顺序处理

### 增量更新
- 使用 URL 的 MD5 哈希作为唯一 ID
- 如果文章已存在（相同 URL），则更新内容和更新时间
- 避免重复爬取相同的 URL

### 内容提取
1. **标题提取**: 优先提取 `<h1>` 标签，其次是 `<title>` 标签
2. **正文提取**: 按以下顺序查找内容容器：
   - `<article>`
   - `.article-content`
   - `.post-content`
   - `.entry-content`
   - `#content`
   - `<main>`
3. **清理**: 自动移除脚本、样式、导航等非正文内容

## 注意事项

1. **遵守 robots.txt**: 爬取前请检查目标网站的 robots.txt 文件
2. **速率限制**: API 接口有速率限制，避免频繁调用
3. **资源消耗**: 爬取任务会占用一定的 CPU 和网络资源
4. **异常处理**: 爬取过程中的错误会被记录，但不会中断整个任务
5. **数据库支持**: 支持 SQLite、MySQL、PostgreSQL

## 后续扩展

根据需求描述，后续可以基于 article_id 进行：
- 正则表达式提取特定信息
- 转存到百度网盘分享
- 数据库更新和维护

## 依赖库

- `crawl4ai==0.3.74`: 网页爬取框架
- `beautifulsoup4==4.12.3`: HTML 解析
- 其他: Flask、requests 等（见 requirements.txt）

## 故障排查

### 爬取失败
- 检查网络连接
- 确认目标网站可访问
- 查看日志文件获取详细错误信息

### 数据库错误
- 确认数据库已正确初始化（运行 `python init_db.py`）
- 检查数据库连接配置
- 确认有足够的磁盘空间

### 内容为空
- 目标网站的 HTML 结构可能发生变化
- 可能需要调整内容提取策略
- 检查是否被目标网站拦截

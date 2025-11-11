# 知识库API文档

## 概述

知识库API提供了一套完整的REST接口，用于查询、筛选、统计和导出知识库条目。所有API端点都需要通过`X-API-Key`请求头进行身份验证。

## 基础URL

```
/api/knowledge
```

## 认证

所有API请求必须在请求头中包含有效的API密钥：

```http
X-API-Key: your_api_key_here
```

未通过认证的请求将返回`401 Unauthorized`响应。

## API端点

### 1. 获取知识库条目列表

获取知识库条目，支持分页、搜索、筛选和排序。

**端点:** `GET /api/knowledge/entries`

**查询参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码（从1开始） |
| `page_size` | integer | 50 | 每页条数（最大1000） |
| `search` | string | - | 搜索关键词（应用于标题、ID、URL、链接） |
| `status` | string | - | 状态过滤（pending/processing/transferred/completed/failed） |
| `tag` | string | - | 标签过滤 |
| `date_from` | string | - | 起始日期（YYYY-MM-DD格式） |
| `date_to` | string | - | 结束日期（YYYY-MM-DD格式） |
| `sort` | string | created_at | 排序字段（created_at/updated_at/title/status） |
| `order` | string | DESC | 排序方向（ASC/DESC） |

**响应示例:**

```json
{
  "success": true,
  "data": {
    "entries": [
      {
        "article_id": "abc123",
        "article_title": "示例文章",
        "article_url": "https://lewz.cn/jprj/category/article",
        "original_link": "https://pan.baidu.com/s/xxx",
        "original_password": "1234",
        "new_link": "https://pan.baidu.com/s/yyy",
        "new_password": "5678",
        "new_title": "新分享标题",
        "status": "completed",
        "error_message": "",
        "tag": "category",
        "created_at": "2024-01-01 12:00:00",
        "updated_at": "2024-01-01 13:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total": 100,
      "total_pages": 2
    }
  },
  "summary": {
    "pending": 10,
    "completed": 80,
    "failed": 10
  }
}
```

**错误响应:**

- `400 Bad Request` - 参数验证失败（如非法的排序字段）
- `401 Unauthorized` - 缺少或无效的API密钥
- `500 Internal Server Error` - 服务器内部错误

### 2. 获取标签列表

获取所有不重复的标签列表及其数量。

**端点:** `GET /api/knowledge/tags`

**响应示例:**

```json
{
  "success": true,
  "data": {
    "tags": ["未分类", "category1", "category2"],
    "count": 3
  }
}
```

### 3. 获取状态统计

获取所有状态及其对应的条目数量。

**端点:** `GET /api/knowledge/statuses`

**响应示例:**

```json
{
  "success": true,
  "data": {
    "statuses": {
      "pending": 10,
      "processing": 5,
      "transferred": 15,
      "completed": 80,
      "failed": 10
    },
    "total": 120
  }
}
```

### 4. 导出CSV

将知识库条目导出为CSV文件，支持自定义字段和过滤条件。

**端点:** `GET /api/knowledge/export`

**查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `fields` | string | 导出字段列表（逗号分隔），留空则导出所有字段 |
| `search` | string | 搜索关键词 |
| `status` | string | 状态过滤 |
| `tag` | string | 标签过滤 |
| `date_from` | string | 起始日期（YYYY-MM-DD） |
| `date_to` | string | 结束日期（YYYY-MM-DD） |
| `sort` | string | 排序字段 |
| `order` | string | 排序方向 |

**可用的导出字段:**

- `article_id` - 文章ID
- `article_title` - 文章标题
- `article_url` - 文章URL
- `original_link` - 原始百度网盘链接
- `original_password` - 原始提取码
- `new_link` - 新分享链接
- `new_password` - 新提取码
- `new_title` - 新分享标题
- `status` - 状态
- `error_message` - 错误信息
- `tag` - 标签
- `created_at` - 创建时间
- `updated_at` - 更新时间

**响应:**

- `Content-Type: text/csv; charset=utf-8`
- `Content-Disposition: attachment; filename="knowledge_export_YYYYMMDD_HHMMSS.csv"`
- CSV内容包含UTF-8 BOM以确保Excel兼容性

**示例请求:**

```bash
curl -H "X-API-Key: your_key" \
  "http://localhost:5000/api/knowledge/export?fields=article_id,article_title,status&status=completed" \
  > export.csv
```

**错误响应:**

- `400 Bad Request` - 包含非法字段名称
- `401 Unauthorized` - 缺少或无效的API密钥

### 5. 获取单个条目详情

获取特定文章ID的条目详细信息。

**端点:** `GET /api/knowledge/entry/{article_id}`

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `article_id` | string | 文章唯一ID |

**响应示例:**

```json
{
  "success": true,
  "data": {
    "article_id": "abc123",
    "article_title": "示例文章",
    "article_url": "https://lewz.cn/jprj/category/article",
    "original_link": "https://pan.baidu.com/s/xxx",
    "original_password": "1234",
    "new_link": "https://pan.baidu.com/s/yyy",
    "new_password": "5678",
    "new_title": "新分享标题",
    "status": "completed",
    "error_message": "",
    "tag": "category",
    "created_at": "2024-01-01 12:00:00",
    "updated_at": "2024-01-01 13:00:00"
  }
}
```

**错误响应:**

- `404 Not Found` - 条目不存在
- `401 Unauthorized` - 缺少或无效的API密钥

## 静态文件路由

### 知识库UI

**端点:** `GET /kb` 或 `GET /kb/{path}`

提供知识库前端UI的静态文件服务。如果静态文件目录不存在，返回404响应。

**文件位置:** `static/knowledge/`

## 使用示例

### Python示例

```python
import requests

API_KEY = 'your_api_key'
BASE_URL = 'http://localhost:5000'

headers = {'X-API-Key': API_KEY}

# 获取条目列表
response = requests.get(
    f'{BASE_URL}/api/knowledge/entries',
    headers=headers,
    params={
        'page': 1,
        'page_size': 20,
        'status': 'completed',
        'sort': 'created_at',
        'order': 'DESC'
    }
)

if response.status_code == 200:
    data = response.json()
    entries = data['data']['entries']
    print(f"找到 {len(entries)} 条记录")

# 导出CSV
response = requests.get(
    f'{BASE_URL}/api/knowledge/export',
    headers=headers,
    params={
        'fields': 'article_title,new_link,status',
        'status': 'completed'
    }
)

if response.status_code == 200:
    with open('export.csv', 'wb') as f:
        f.write(response.content)
```

### cURL示例

```bash
# 获取条目列表
curl -H "X-API-Key: your_key" \
  "http://localhost:5000/api/knowledge/entries?page=1&page_size=10"

# 获取标签列表
curl -H "X-API-Key: your_key" \
  "http://localhost:5000/api/knowledge/tags"

# 获取状态统计
curl -H "X-API-Key: your_key" \
  "http://localhost:5000/api/knowledge/statuses"

# 导出CSV（所有字段）
curl -H "X-API-Key: your_key" \
  "http://localhost:5000/api/knowledge/export" \
  -o export.csv

# 导出CSV（指定字段和过滤条件）
curl -H "X-API-Key: your_key" \
  "http://localhost:5000/api/knowledge/export?fields=article_title,status&status=completed" \
  -o export.csv

# 获取单个条目
curl -H "X-API-Key: your_key" \
  "http://localhost:5000/api/knowledge/entry/abc123"
```

### JavaScript/Fetch示例

```javascript
const API_KEY = 'your_api_key';
const BASE_URL = 'http://localhost:5000';

async function getEntries(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${BASE_URL}/api/knowledge/entries?${params}`,
    {
      headers: {
        'X-API-Key': API_KEY
      }
    }
  );
  
  if (response.ok) {
    const data = await response.json();
    return data;
  } else {
    throw new Error('API request failed');
  }
}

// 使用示例
getEntries({
  page: 1,
  page_size: 20,
  status: 'completed',
  search: '关键词'
}).then(data => {
  console.log('条目:', data.data.entries);
  console.log('分页:', data.data.pagination);
  console.log('统计:', data.summary);
});
```

## 数据模型

### Entry对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `article_id` | string | 文章唯一ID（MD5哈希） |
| `article_title` | string | 文章标题 |
| `article_url` | string | 文章URL |
| `original_link` | string | 原始百度网盘链接 |
| `original_password` | string | 原始提取码 |
| `new_link` | string | 新分享链接 |
| `new_password` | string | 新提取码 |
| `new_title` | string | 新分享标题 |
| `status` | string | 状态（pending/processing/transferred/completed/failed） |
| `error_message` | string | 错误信息（如果有） |
| `tag` | string | 标签（从URL路径提取） |
| `created_at` | string | 创建时间（ISO格式） |
| `updated_at` | string | 更新时间（ISO格式） |

### 状态说明

- `pending` - 待处理
- `processing` - 处理中
- `transferred` - 已转存
- `completed` - 已完成（转存+分享）
- `failed` - 失败

## 错误处理

所有API端点使用统一的错误响应格式：

```json
{
  "success": false,
  "error": "Error code or message",
  "message": "详细错误描述"
}
```

常见HTTP状态码：

- `200 OK` - 请求成功
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未授权（缺少或无效的API密钥）
- `404 Not Found` - 资源不存在
- `500 Internal Server Error` - 服务器内部错误

## 性能与限制

- **分页限制:** 每页最多返回1000条记录
- **导出限制:** CSV导出最多支持100,000条记录
- **搜索:** 使用LIKE查询，支持模糊匹配
- **日期过滤:** 基于`extracted_links.created_at`字段
- **标签提取:** 从文章URL的第二级路径自动提取

## 安全建议

1. **保护API密钥:** 不要在客户端代码或公开仓库中暴露API密钥
2. **使用HTTPS:** 生产环境中始终使用HTTPS加密传输
3. **访问控制:** 根据需要配置CORS策略
4. **速率限制:** 考虑启用速率限制防止滥用

## 相关文档

- [知识库存储层文档](README_KNOWLEDGE_REPO.md)
- [Swagger API文档](http://localhost:5000/docs)
- [链接提取功能文档](README_LINK_EXTRACTOR.md)

## 更新日志

### v1.0.0 (2024-11)

- 初始版本
- 实现基础CRUD端点
- 支持分页、搜索、筛选
- CSV导出功能
- 静态UI路由

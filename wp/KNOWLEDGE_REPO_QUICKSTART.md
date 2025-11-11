# 知识库存储层快速开始指南

## 快速上手（5分钟）

### 1. 导入模块

```python
from knowledge_repository import KnowledgeRepository

# 创建实例
repo = KnowledgeRepository()
```

### 2. 基本查询

```python
# 列出前10条记录
result = repo.list_entries(limit=10, offset=0)

print(f"总数: {result['total']}")
for entry in result['entries']:
    print(f"{entry['article_title']} - {entry['status']}")
```

### 3. 搜索

```python
# 搜索包含"网盘"的记录
result = repo.list_entries(search='网盘', limit=20)
```

### 4. 过滤

```python
# 按状态过滤
result = repo.list_entries(status='completed')

# 按标签过滤
result = repo.list_entries(tag='category1')

# 日期范围过滤
result = repo.list_entries(
    date_from='2024-01-01',
    date_to='2024-12-31'
)

# 组合过滤
result = repo.list_entries(
    search='资源',
    status='completed',
    tag='软件',
    date_from='2024-01-01'
)
```

### 5. 排序

```python
# 按创建时间降序
result = repo.list_entries(sort_by='created_at', sort_order='DESC')

# 按标题升序
result = repo.list_entries(sort_by='title', sort_order='ASC')
```

### 6. 获取标签列表

```python
tags = repo.get_distinct_tags()
print(f"可用标签: {tags}")
# 输出: ['category1', 'category2', '未分类']
```

### 7. 统计信息

```python
stats = repo.summaries_by_status()
print(stats)
# 输出: {'pending': 10, 'completed': 25, 'failed': 3}
```

### 8. 导出数据

```python
# 准备导出
fields = ['article_title', 'new_link', 'new_password', 'status']
rows = repo.prepare_export_rows(fields, filters={'status': 'completed'})

# 导出为CSV
import csv
with open('export.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
```

## 常见使用场景

### 场景1：构建API端点

```python
from flask import Flask, request, jsonify
from knowledge_repository import KnowledgeRepository

app = Flask(__name__)
repo = KnowledgeRepository()

@app.route('/api/knowledge/list', methods=['GET'])
def list_knowledge():
    result = repo.list_entries(
        limit=int(request.args.get('limit', 50)),
        offset=int(request.args.get('offset', 0)),
        search=request.args.get('search'),
        status=request.args.get('status'),
        tag=request.args.get('tag'),
        date_from=request.args.get('date_from'),
        date_to=request.args.get('date_to'),
        sort_by=request.args.get('sort_by', 'created_at'),
        sort_order=request.args.get('sort_order', 'DESC')
    )
    return jsonify(result)
```

### 场景2：仪表板数据

```python
from knowledge_repository import KnowledgeRepository

def get_dashboard_data():
    repo = KnowledgeRepository()
    
    # 统计概览
    stats = repo.summaries_by_status()
    
    # 最新记录
    recent = repo.list_entries(limit=10, sort_by='created_at', sort_order='DESC')
    
    # 标签列表
    tags = repo.get_distinct_tags()
    
    return {
        'overview': {
            'total': sum(stats.values()),
            'pending': stats.get('pending', 0),
            'completed': stats.get('completed', 0),
            'failed': stats.get('failed', 0)
        },
        'recent_entries': recent['entries'],
        'tags': tags
    }
```

### 场景3：分页列表

```python
def paginate_entries(page=1, page_size=20, **filters):
    repo = KnowledgeRepository()
    
    offset = (page - 1) * page_size
    result = repo.list_entries(limit=page_size, offset=offset, **filters)
    
    total_pages = (result['total'] + page_size - 1) // page_size
    
    return {
        'data': result['entries'],
        'pagination': {
            'current_page': page,
            'page_size': page_size,
            'total_items': result['total'],
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': result['has_more']
        }
    }
```

### 场景4：批量导出

```python
import csv
from knowledge_repository import KnowledgeRepository

def export_completed_links(output_file='completed.csv'):
    repo = KnowledgeRepository()
    
    fields = [
        'article_title',
        'article_url',
        'original_link',
        'new_link',
        'new_password',
        'tag',
        'created_at'
    ]
    
    rows = repo.prepare_export_rows(
        fields=fields,
        filters={'status': 'completed'},
        sort_by='created_at',
        sort_order='DESC'
    )
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    
    return len(rows)
```

## 返回数据格式

### list_entries() 返回格式

```python
{
    'entries': [
        {
            'article_id': 'abc123',
            'article_title': '文章标题',
            'article_url': 'https://lewz.cn/jprj/category/article',
            'original_link': 'https://pan.baidu.com/s/xxx',
            'original_password': 'pwd1',
            'new_link': 'https://pan.baidu.com/s/yyy',
            'new_password': 'newpwd',
            'new_title': '分享标题',
            'status': 'completed',
            'error_message': '',
            'tag': 'category',
            'created_at': '2024-01-01 10:00:00',
            'updated_at': '2024-01-01 12:00:00'
        },
        ...
    ],
    'total': 100,
    'limit': 20,
    'offset': 0,
    'has_more': True
}
```

## 参数说明

### list_entries() 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 50 | 每页条数 |
| offset | int | 0 | 偏移量 |
| search | str | None | 搜索关键词 |
| status | str | None | 状态过滤 |
| tag | str | None | 标签过滤 |
| date_from | str | None | 起始日期（YYYY-MM-DD） |
| date_to | str | None | 结束日期（YYYY-MM-DD） |
| sort_by | str | 'created_at' | 排序字段 |
| sort_order | str | 'DESC' | 排序方向 |

### 允许的排序字段

- `created_at` - 创建时间
- `updated_at` - 更新时间
- `title` - 文章标题
- `status` - 状态

### 允许的导出字段

- `article_id` - 文章ID
- `article_title` - 文章标题
- `article_url` - 文章URL
- `original_link` - 原始链接
- `original_password` - 原始密码
- `new_link` - 新链接
- `new_password` - 新密码
- `new_title` - 新标题
- `status` - 状态
- `error_message` - 错误信息
- `tag` - 派生标签
- `created_at` - 创建时间
- `updated_at` - 更新时间

## 标签派生规则

URL格式 → 标签
- `https://lewz.cn/jprj/category/article` → `"category"`
- `https://lewz.cn/jprj/subcategory/item` → `"subcategory"`
- `https://lewz.cn/jprj/article` → `"未分类"`
- `""` 或格式错误 → `"未分类"`

## 测试

```bash
# 运行测试
cd /home/engine/project/wp
python test_knowledge_repository.py

# 运行示例
python example_knowledge_repo.py
```

## 性能提示

1. **分页查询**：使用 limit 和 offset 避免一次加载过多数据
2. **索引优化**：已为常用查询字段添加索引
3. **标签过滤**：标签过滤在应用层实现，大数据集时性能可能受影响
4. **导出限制**：导出默认限制100,000条，超大数据集考虑分批导出

## 错误处理

所有方法都包含异常处理，错误会记录到日志但不会中断程序。查询失败时返回空结果或默认值。

## 更多信息

- 完整文档: `README_KNOWLEDGE_REPO.md`
- 使用示例: `example_knowledge_repo.py`
- 测试脚本: `test_knowledge_repository.py`

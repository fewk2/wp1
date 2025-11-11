# 知识库存储层 (Knowledge Repository)

## 概述

`knowledge_repository.py` 提供了一个专用的数据访问层，用于聚合和查询文章（articles）和提取链接（extracted_links）数据。该模块支持高级过滤、搜索、排序和导出功能，为知识库UI和API提供优化的数据访问接口。

## 主要特性

### 1. 数据聚合
- 自动关联 `articles` 和 `extracted_links` 表
- 返回合并的知识库条目，包含文章信息和链接详情
- 自动从文章URL提取标签/分类

### 2. 标签派生逻辑
标签从文章URL的路径中提取，规则如下：
- `https://lewz.cn/jprj/category/article` → 标签为 `"category"`
- `https://lewz.cn/jprj/article` → 标签为 `"未分类"`
- URL缺失或格式错误 → 标签为 `"未分类"`

实现细节：
- 提取URL路径的第二级部分（jprj后的第一个路径段）
- 路径不足3段时返回"未分类"
- 异常处理确保永不抛出错误

### 3. 多维度过滤

支持以下过滤条件的任意组合：

| 过滤器 | 类型 | 说明 |
|--------|------|------|
| `search` | 字符串 | 在标题、文章ID、URL、原始链接、新链接、新标题中搜索（不区分大小写） |
| `status` | 字符串 | 按状态过滤：pending/processing/transferred/completed/failed |
| `tag` | 字符串 | 按派生标签过滤 |
| `date_from` | 日期字符串 | 起始日期（YYYY-MM-DD，基于 extracted_links.created_at） |
| `date_to` | 日期字符串 | 结束日期（YYYY-MM-DD，基于 extracted_links.created_at） |

### 4. 排序支持

允许的排序字段（通过白名单验证）：
- `created_at` - 创建时间（默认）
- `updated_at` - 更新时间
- `title` - 文章标题
- `status` - 状态

排序方向：`ASC`（升序）或 `DESC`（降序，默认）

### 5. 导出功能

支持CSV导出准备，包含字段验证。允许的导出字段：
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

## API 接口

### KnowledgeRepository 类

```python
from knowledge_repository import KnowledgeRepository

repo = KnowledgeRepository()
```

#### list_entries()

列出知识库条目，支持分页和多维度过滤。

**参数：**
- `limit` (int, 默认50): 每页条数
- `offset` (int, 默认0): 偏移量
- `search` (str, 可选): 搜索关键词
- `status` (str, 可选): 状态过滤
- `tag` (str, 可选): 标签过滤
- `date_from` (str, 可选): 起始日期（YYYY-MM-DD）
- `date_to` (str, 可选): 结束日期（YYYY-MM-DD）
- `sort_by` (str, 默认'created_at'): 排序字段
- `sort_order` (str, 默认'DESC'): 排序方向

**返回：**
```python
{
    'entries': [
        {
            'article_id': str,
            'article_title': str,
            'article_url': str,
            'original_link': str,
            'original_password': str,
            'new_link': str,
            'new_password': str,
            'new_title': str,
            'status': str,
            'error_message': str,
            'tag': str,
            'created_at': str,
            'updated_at': str
        },
        ...
    ],
    'total': int,        # 总条数
    'limit': int,        # 请求的限制
    'offset': int,       # 请求的偏移
    'has_more': bool     # 是否有更多数据
}
```

**示例：**
```python
# 基本查询
result = repo.list_entries(limit=20, offset=0)

# 搜索查询
result = repo.list_entries(search='百度网盘', status='completed')

# 日期范围查询
result = repo.list_entries(
    date_from='2024-01-01',
    date_to='2024-01-31',
    tag='category1',
    sort_by='updated_at',
    sort_order='ASC'
)
```

#### get_distinct_tags()

获取所有不重复的标签列表。

**返回：** `List[str]` - 排序后的标签列表

**示例：**
```python
tags = repo.get_distinct_tags()
# ['category1', 'category2', '未分类']
```

#### summaries_by_status()

按状态统计条目数量。

**返回：** `Dict[str, int]` - 状态统计字典

**示例：**
```python
summaries = repo.summaries_by_status()
# {'pending': 10, 'completed': 25, 'failed': 3}
```

#### prepare_export_rows()

准备导出数据行，验证字段并返回符合条件的记录。

**参数：**
- `fields` (List[str]): 要导出的字段列表
- `filters` (Dict, 可选): 过滤条件（同 list_entries）
- `sort_by` (str, 默认'created_at'): 排序字段
- `sort_order` (str, 默认'DESC'): 排序方向

**返回：** `List[Dict[str, Any]]` - 导出行列表

**异常：** `ValueError` - 如果包含非法字段

**示例：**
```python
# 准备导出数据
fields = ['article_title', 'new_link', 'status', 'tag']
rows = repo.prepare_export_rows(
    fields=fields,
    filters={'status': 'completed'},
    sort_by='created_at'
)

# 转换为CSV（使用标准库）
import csv
with open('export.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
```

## 数据库优化

### 新增索引

为了优化查询性能，`init_db.py` 已添加以下索引：

**articles 表：**
- `idx_articles_title` - 支持标题搜索
- `idx_articles_crawled_at` - 支持按抓取时间排序

**extracted_links 表：**
- `idx_extracted_links_created_at` - 支持日期范围过滤和排序
- `idx_extracted_links_updated_at` - 支持按更新时间排序
- `idx_extracted_links_new_link` - 支持新链接搜索

所有索引使用 `CREATE INDEX IF NOT EXISTS` 确保幂等性，可安全重复执行。

### 跨数据库兼容性

模块完全支持以下数据库：
- **SQLite** - 使用 `?` 占位符
- **MySQL** - 使用 `%s` 占位符，TEXT列索引需指定长度
- **PostgreSQL** - 使用 `%s` 占位符

所有SQL查询都使用参数化，防止SQL注入。

## 使用示例

### 示例1：构建知识库API端点

```python
from flask import Flask, request, jsonify
from knowledge_repository import KnowledgeRepository

app = Flask(__name__)
repo = KnowledgeRepository()

@app.route('/api/knowledge/entries', methods=['GET'])
def get_entries():
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

@app.route('/api/knowledge/tags', methods=['GET'])
def get_tags():
    tags = repo.get_distinct_tags()
    return jsonify({'tags': tags})

@app.route('/api/knowledge/stats', methods=['GET'])
def get_stats():
    summaries = repo.summaries_by_status()
    return jsonify({'summaries': summaries})
```

### 示例2：批量导出

```python
import csv
from knowledge_repository import KnowledgeRepository

repo = KnowledgeRepository()

# 导出所有已完成的条目
fields = [
    'article_title', 'article_url', 'original_link',
    'new_link', 'new_password', 'status', 'tag', 'created_at'
]

rows = repo.prepare_export_rows(
    fields=fields,
    filters={'status': 'completed'},
    sort_by='created_at',
    sort_order='DESC'
)

with open('completed_links.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ 导出 {len(rows)} 条记录")
```

### 示例3：构建仪表板数据

```python
from knowledge_repository import KnowledgeRepository

repo = KnowledgeRepository()

# 获取统计概览
stats = repo.summaries_by_status()
total = sum(stats.values())

# 获取标签分布
tags = repo.get_distinct_tags()

# 获取最新条目
recent = repo.list_entries(limit=10, sort_by='created_at', sort_order='DESC')

dashboard_data = {
    'overview': {
        'total': total,
        'pending': stats.get('pending', 0),
        'completed': stats.get('completed', 0),
        'failed': stats.get('failed', 0)
    },
    'tags': tags,
    'recent_entries': recent['entries']
}

print(dashboard_data)
```

## 测试

### 运行完整测试套件

知识库模块提供基于unittest的完整测试套件，使用隔离的临时数据库：

```bash
cd /home/engine/project/wp

# 运行完整的知识库测试（推荐）
python -m unittest tests.test_knowledge_module.TestKnowledgeRepository -v

# 或运行所有知识库测试（包括API测试）
python -m unittest tests.test_knowledge_module -v
```

### 运行旧版测试脚本

也可以运行独立的测试脚本（会修改配置的数据库）：

```bash
python test_knowledge_repository.py
```

### 测试覆盖

完整测试套件涵盖：
- ✅ 标签派生逻辑（正常URL、短URL、空URL、非法URL）
- ✅ 列出条目（分页、搜索、过滤、排序）
- ✅ 搜索功能（多字段全文搜索）
- ✅ 状态过滤（pending/completed/transferred/failed）
- ✅ 标签过滤（动态标签提取）
- ✅ 日期范围过滤（起始/结束日期）
- ✅ 获取标签列表（去重排序）
- ✅ 状态统计
- ✅ 导出准备（字段验证）

## 注意事项

1. **标签过滤性能**：标签过滤在应用层实现（而非数据库层），因为标签是从URL动态派生的。对于大数据集，建议考虑将标签持久化到数据库。

2. **搜索性能**：搜索使用 `LIKE` 操作符，对于大数据集可能较慢。已添加相关索引优化性能。

3. **日期格式**：日期过滤使用 `YYYY-MM-DD` 格式，基于 `extracted_links.created_at` 字段。

4. **排序字段验证**：排序字段通过白名单验证，防止SQL注入。非法字段将回退到默认值（created_at）。

5. **导出限制**：`prepare_export_rows` 默认限制100,000条记录。对于更大数据集，建议实现流式导出或分批处理。

## 未来改进

1. **标签持久化**：考虑在数据库中添加 `tag` 列，避免重复计算
2. **全文搜索**：集成全文搜索引擎（如Elasticsearch）提升搜索性能
3. **缓存层**：添加Redis缓存常用查询结果
4. **异步导出**：实现后台任务处理大规模导出
5. **分析功能**：添加趋势分析、成功率统计等高级分析功能

## 相关文件

- `knowledge_repository.py` - 主模块
- `test_knowledge_repository.py` - 测试脚本
- `init_db.py` - 数据库初始化（包含索引）
- `config.py` - 配置管理
- `logger.py` - 日志工具

# Crawl4AI 集成功能实现总结

## 任务描述

在 wp1 中集成调用 Crawl4AI 框架，爬取 lewz.cn/jprj 目录下全部子页面文章，存入 wp1 数据库。

## 实现内容

### 1. 依赖更新 (requirements.txt)

添加了以下依赖：
- `crawl4ai==0.3.74` - 网页爬取框架
- `beautifulsoup4==4.12.3` - HTML 解析库

### 2. 数据库架构 (init_db.py)

为 SQLite、MySQL 和 PostgreSQL 三种数据库添加了 `articles` 表：

**字段结构**：
- `id`: 主键（自增）
- `article_id`: 文章唯一ID（URL的MD5哈希，UNIQUE）
- `url`: 文章URL（UNIQUE）
- `title`: 文章标题
- `content`: 文章正文内容
- `crawled_at`: 首次爬取时间
- `updated_at`: 最后更新时间

**索引**：
- `idx_articles_article_id`: article_id 索引
- `idx_articles_url`: url 索引

### 3. 爬虫服务模块 (crawler_service.py)

创建了完整的爬虫服务类 `CrawlerService`，主要功能：

**核心功能**：
- 使用 Crawl4AI 框架进行异步爬取
- 单线程慢速爬取（每次请求间隔 3 秒）
- 自动提取文章链接和内容
- 生成基于 URL 的唯一 MD5 哈希 ID
- 支持增量更新（避免重复爬取）

**主要方法**：
- `crawl_jprj_articles()`: 爬取 lewz.cn/jprj 目录下所有文章
- `get_articles()`: 获取已爬取的文章列表（分页）
- `get_article_by_id()`: 根据 article_id 获取完整文章
- `get_statistics()`: 获取爬取统计信息

**内容提取策略**：
- 标题：优先 `<h1>`，其次 `<title>`
- 正文：自动识别常见内容容器（article、.article-content 等）
- 清理：自动移除脚本、样式、导航等非正文内容

### 4. REST API 接口 (server.py)

添加了 4 个新的 API 端点：

#### POST /api/crawler/start
开始爬取 lewz.cn/jprj 文章
- 限流：每小时最多 5 次
- 需要 API Key 认证

#### GET /api/crawler/articles
获取已爬取的文章列表
- 参数：`limit`（默认100）、`offset`（默认0）
- 返回：文章列表（包含预览，前200字符）

#### GET /api/crawler/articles/{article_id}
获取文章详情
- 参数：`article_id`（文章唯一ID）
- 返回：完整的文章内容

#### GET /api/crawler/stats
获取爬虫统计信息
- 返回：总文章数、首次爬取时间、最后爬取时间

### 5. 文档和测试

**文档**：
- `wp/docs/CRAWLER.md`: 详细的功能文档，包含 API 说明、使用示例等

**测试脚本**：
- `wp/test_crawler.py`: 爬虫功能测试脚本

### 6. 其他改进

- 创建了 `.gitignore` 文件，忽略常见的临时文件和敏感信息
- 更新了 Swagger 文档，添加了"爬虫"标签

## 技术特点

### 1. 慢速单线程爬取
- 每次请求间隔 3 秒
- 避免对目标网站造成压力
- 符合网络爬虫礼仪

### 2. 唯一 ID 生成
```python
article_id = hashlib.md5(url.encode('utf-8')).hexdigest()
```

### 3. 增量更新支持
- 使用 `INSERT OR REPLACE` (SQLite) 或 `ON DUPLICATE KEY UPDATE` (MySQL)
- 避免重复存储相同 URL 的文章

### 4. 异步爬取
使用 Crawl4AI 的异步接口提高效率：
```python
async with AsyncWebCrawler(verbose=True) as crawler:
    result = await crawler.arun(url=url)
```

### 5. 多数据库支持
完全兼容项目现有的三种数据库：
- SQLite（默认）
- MySQL
- PostgreSQL

## 使用示例

### 1. 初始化数据库
```bash
cd wp
python init_db.py
```

### 2. 启动服务器
```bash
python server.py
```

### 3. 开始爬取
```bash
curl -X POST http://localhost:5000/api/crawler/start \
  -H "X-API-Key: your_api_key"
```

### 4. 查看统计信息
```bash
curl -X GET http://localhost:5000/api/crawler/stats \
  -H "X-API-Key: your_api_key"
```

### 5. 获取文章列表
```bash
curl -X GET "http://localhost:5000/api/crawler/articles?limit=10" \
  -H "X-API-Key: your_api_key"
```

## 后续扩展方向

根据任务描述，后续可以基于 `article_id` 进行：

1. **正则提取**：从文章内容中提取特定信息
2. **转存分享**：将文章转存到百度网盘并生成分享链接
3. **数据库更新**：定期更新文章内容，追踪变化

## 注意事项

1. **遵守 robots.txt**：爬取前请检查目标网站的爬虫协议
2. **速率限制**：API 接口有速率限制，避免频繁调用
3. **资源消耗**：爬取任务会占用 CPU 和网络资源
4. **异常处理**：爬取过程中的错误会被记录，但不会中断任务
5. **数据验证**：建议验证爬取的数据质量

## 文件清单

### 修改的文件
- `wp/requirements.txt`: 添加爬虫依赖
- `wp/init_db.py`: 添加 articles 表
- `wp/server.py`: 添加爬虫 API 接口

### 新增的文件
- `wp/crawler_service.py`: 爬虫服务核心模块
- `wp/docs/CRAWLER.md`: 爬虫功能文档
- `wp/test_crawler.py`: 测试脚本
- `.gitignore`: Git 忽略文件配置

## 技术栈

- **爬虫框架**: Crawl4AI 0.3.74
- **HTML 解析**: BeautifulSoup4 4.12.3
- **Web 框架**: Flask 3.0.0
- **数据库**: SQLite/MySQL/PostgreSQL
- **异步处理**: asyncio

## 性能考虑

- **延迟设置**: 3 秒/请求，可通过修改 `self.crawl_delay` 调整
- **单线程**: 避免并发请求，确保稳定性
- **内存优化**: 大文本内容直接存储到数据库，不在内存中缓存
- **数据库索引**: 对 URL 和 article_id 建立索引，提高查询效率

## 测试建议

1. 先测试健康检查和统计接口
2. 小规模测试爬取（可以先修改 base_url 指向测试页面）
3. 验证数据库存储是否正确
4. 检查日志文件了解爬取详情
5. 确认速率限制是否生效

## 维护建议

1. 定期检查目标网站的 HTML 结构变化
2. 监控爬取错误率，及时调整提取策略
3. 定期清理旧的或无效的文章数据
4. 备份数据库，避免数据丢失

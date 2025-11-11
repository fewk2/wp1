# 爬虫功能快速开始

## 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 安装系统依赖（Linux）
sudo apt-get install -y libnss3 libnspr4 libatk1.0-0t64 libatk-bridge2.0-0t64 \
  libcups2t64 libdrm2 libxkbcommon0 libatspi2.0-0t64 libxcomposite1 \
  libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2t64
```

## 初始化数据库

```bash
python init_db.py
```

## 运行测试

```bash
# 运行集成测试（不访问外部网站）
python test_crawler_integration.py

# 运行 API 测试（需要启动服务器）
python test_crawler.py

# 运行知识库模块完整测试（使用unittest）
python -m unittest tests.test_knowledge_module -v

# 或运行所有测试
python -m unittest discover tests -v
```

## 启动服务

```bash
python server.py
```

访问 http://localhost:5000/docs 查看 API 文档

## API 使用示例

### 1. 开始爬取
```bash
curl -X POST http://localhost:5000/api/crawler/start \
  -H "X-API-Key: your_api_key"
```

### 2. 查看统计
```bash
curl -X GET http://localhost:5000/api/crawler/stats \
  -H "X-API-Key: your_api_key"
```

### 3. 获取文章列表
```bash
curl -X GET "http://localhost:5000/api/crawler/articles?limit=10" \
  -H "X-API-Key: your_api_key"
```

### 4. 获取文章详情
```bash
curl -X GET http://localhost:5000/api/crawler/articles/{article_id} \
  -H "X-API-Key: your_api_key"
```

## 注意事项

1. **遵守 robots.txt**: 爬取前请检查目标网站的爬虫协议
2. **慢速爬取**: 默认每次请求间隔 3 秒
3. **API 限流**: `/api/crawler/start` 每小时最多 5 次
4. **资源消耗**: 爬取任务会占用 CPU 和网络资源

## 配置

在 `crawler_service.py` 中可以调整：
- `self.base_url`: 爬取的基础 URL
- `self.crawl_delay`: 请求间隔时间（秒）

## 知识库功能

爬虫系统集成了知识库模块，用于管理和查询已爬取的文章及提取的网盘链接。

### 知识库工作流程

1. **爬取文章** - 使用爬虫服务从 lewz.cn/jprj 爬取文章并存入 `articles` 表
2. **提取链接** - 从文章内容中提取百度网盘分享链接，存入 `extracted_links` 表
3. **转存分享** - 将链接转存到指定账户并生成新的分享链接
4. **知识库查询** - 通过知识库API查询、过滤、导出所有数据

### 访问知识库UI

启动服务后，访问 http://localhost:5000/kb 可以使用Web界面管理知识库。

### 知识库API端点

- `GET /api/knowledge/entries` - 获取条目列表（支持分页、搜索、过滤、排序）
- `GET /api/knowledge/tags` - 获取标签列表
- `GET /api/knowledge/statuses` - 获取状态统计
- `GET /api/knowledge/export` - 导出CSV文件
- `GET /api/knowledge/entry/{id}` - 获取单个条目详情

所有API端点需要使用 `X-API-Key` 请求头进行身份验证。

### 使用示例

```bash
# 获取完成状态的条目
curl -H "X-API-Key: your_api_key" \
  "http://localhost:5000/api/knowledge/entries?status=completed&page=1&page_size=20"

# 导出所有已完成条目为CSV
curl -H "X-API-Key: your_api_key" \
  "http://localhost:5000/api/knowledge/export?status=completed" \
  -o knowledge_export.csv
```

### 数据库索引

知识库模块自动创建以下性能索引：
- `idx_articles_title` - 文章标题索引
- `idx_articles_crawled_at` - 爬取时间索引
- `idx_extracted_links_created_at` - 链接创建时间索引
- `idx_extracted_links_updated_at` - 链接更新时间索引
- `idx_extracted_links_new_link` - 新链接索引

这些索引在运行 `init_db.py` 时自动创建。

## 详细文档

- **爬虫功能**: `docs/CRAWLER.md`
- **知识库API**: `README_KNOWLEDGE_API.md`
- **知识库存储层**: `README_KNOWLEDGE_REPO.md`
- **知识库UI**: `KNOWLEDGE_UI_README.md`
- **链接提取**: `README_LINK_EXTRACTOR.md`

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

## 详细文档

请参阅 `docs/CRAWLER.md` 获取完整文档。

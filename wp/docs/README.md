# 百度网盘自动化服务器

一个完整的、可直接部署的百度网盘自动化服务端项目，提供 REST API 接口，支持批量转存、批量分享、多账户管理等功能。

## 特性

- ✅ **无GUI依赖**：完全服务端运行，无需图形界面
- ✅ **REST API**：完整的HTTP API接口，支持各种自动化工作流
- ✅ **OpenAPI文档**：内置Swagger UI，方便接口调试和文档查看
- ✅ **多账户支持**：支持同时管理多个百度网盘账户
- ✅ **批量操作**：批量转存分享链接，批量生成分享链接
- ✅ **爬虫集成**：自动爬取网站文章和提取网盘链接
- ✅ **知识库管理**：统一管理文章和网盘链接，支持搜索、过滤、导出
- ✅ **Web界面**：提供知识库管理Web UI
- ✅ **速率限制**：内置API速率限制，防止滥用
- ✅ **智能节流**：自动控制请求频率，避免触发百度限制
- ✅ **Docker支持**：提供完整的Docker部署方案
- ✅ **数据持久化**：支持SQLite/MySQL/PostgreSQL
- ✅ **日志系统**：专业的日志记录和管理
- ✅ **健康检查**：内置健康检查接口
- ✅ **优雅关闭**：支持优雅关闭，不丢失数据
- ✅ **完整测试**：提供基于unittest的完整测试套件

## 快速开始

### 方式1：直接运行

#### 1. 环境要求

- Python 3.8+
- Linux/Windows/MacOS

#### 2. 安装依赖

```bash
cd wp
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，配置以下必要参数：
# - API_SECRET_KEY: API密钥（自定义，用于保护API）
# - ACCOUNT_MAIN_COOKIE: 百度网盘Cookie（BDUSS）
```

**获取百度网盘Cookie的方法：**

1. 在浏览器中登录百度网盘
2. 打开开发者工具（F12）
3. 切换到"网络"标签
4. 刷新页面，找到任意请求
5. 在请求头中找到Cookie，复制BDUSS部分
6. 格式：`BDUSS=xxxxxxxxxxxxxxxx`

#### 4. 初始化数据库

```bash
python3 init_db.py
```

#### 5. 启动服务

**开发模式：**
```bash
python3 server.py
```

**生产模式（Linux）：**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 server:app
```

**使用启动脚本（推荐）：**
```bash
chmod +x start.sh
./start.sh
```

#### 6. 访问服务

- 健康检查：http://localhost:5000/api/health
- API文档：http://localhost:5000/docs
- 知识库UI：http://localhost:5000/kb

#### 7. 运行测试

```bash
# 运行所有测试
python -m unittest discover tests -v

# 只运行知识库模块测试
python -m unittest tests.test_knowledge_module -v
```

### 方式2：Docker部署（推荐）

#### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，配置必要参数
```

#### 2. 使用Docker Compose启动

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 3. 单独使用Docker

```bash
# 构建镜像
docker build -t baidu-pan-server .

# 运行容器
docker run -d \
  --name baidu-pan-server \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  baidu-pan-server

# 查看日志
docker logs -f baidu-pan-server
```

### 方式3：Systemd服务（Linux生产环境）

```bash
# 1. 将项目部署到 /opt/baidu-pan-server
sudo cp -r wp /opt/baidu-pan-server

# 2. 创建虚拟环境并安装依赖
cd /opt/baidu-pan-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件

# 4. 初始化数据库
python3 init_db.py

# 5. 安装systemd服务
sudo cp baidu-pan-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable baidu-pan-server
sudo systemctl start baidu-pan-server

# 6. 查看状态
sudo systemctl status baidu-pan-server

# 查看日志
sudo journalctl -u baidu-pan-server -f
```

## API使用示例

所有API请求都需要在请求头中添加API密钥：
```
X-API-Key: your_secret_key
```

### 健康检查

```bash
curl http://localhost:5000/api/health
```

### 批量转存

#### 1. 导入CSV文件

```bash
curl -X POST http://localhost:5000/api/transfer/import \
  -H "X-API-Key: your_secret_key" \
  -F "file=@links.csv" \
  -F "default_target_path=/批量转存"
```

CSV文件格式：
```csv
链接,提取码,保存位置
https://pan.baidu.com/s/xxx,abcd,/目标目录1
https://pan.baidu.com/s/yyy,efgh,/目标目录2
```

#### 2. 添加单个转存任务

```bash
curl -X POST http://localhost:5000/api/transfer/add \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "share_link": "https://pan.baidu.com/s/xxxxx",
    "share_password": "1234",
    "target_path": "/我的文件"
  }'
```

#### 3. 开始转存

```bash
curl -X POST http://localhost:5000/api/transfer/start \
  -H "X-API-Key: your_secret_key"
```

#### 4. 查看转存状态

```bash
curl http://localhost:5000/api/transfer/status \
  -H "X-API-Key: your_secret_key"
```

#### 5. 导出转存结果

```bash
# JSON格式
curl http://localhost:5000/api/transfer/export?format=json \
  -H "X-API-Key: your_secret_key"

# CSV格式
curl http://localhost:5000/api/transfer/export?format=csv \
  -H "X-API-Key: your_secret_key" \
  -o results.csv
```

### 批量分享

#### 1. 从路径添加分享任务

```bash
curl -X POST http://localhost:5000/api/share/add_from_path \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/要分享的目录",
    "expiry": 7,
    "password": "1234"
  }'
```

#### 2. 开始分享

```bash
curl -X POST http://localhost:5000/api/share/start \
  -H "X-API-Key: your_secret_key"
```

#### 3. 查看分享状态

```bash
curl http://localhost:5000/api/share/status \
  -H "X-API-Key: your_secret_key"
```

### 文件管理

#### 列出文件

```bash
curl "http://localhost:5000/api/files/list?path=/" \
  -H "X-API-Key: your_secret_key"
```

#### 搜索文件

```bash
curl "http://localhost:5000/api/files/search?keyword=文档&path=/" \
  -H "X-API-Key: your_secret_key"
```

### 多账户管理

在请求中添加 `account` 参数来指定使用哪个账户：

```bash
curl -X POST http://localhost:5000/api/transfer/start \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "backup"
  }'
```

### 知识库功能

#### 1. 爬取文章

```bash
# 开始爬取 lewz.cn/jprj 网站
curl -X POST http://localhost:5000/api/crawler/start \
  -H "X-API-Key: your_secret_key"
```

#### 2. 提取链接

```bash
# 从文章中提取百度网盘分享链接
curl -X POST http://localhost:5000/api/links/extract \
  -H "X-API-Key: your_secret_key"
```

#### 3. 处理链接（转存+分享）

```bash
# 自动转存到wp1账户并生成新分享
curl -X POST http://localhost:5000/api/links/process \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "all"
  }'
```

#### 4. 查询知识库

```bash
# 获取完成状态的条目（支持分页、搜索、过滤）
curl "http://localhost:5000/api/knowledge/entries?status=completed&page=1&page_size=20" \
  -H "X-API-Key: your_secret_key"

# 获取标签列表
curl http://localhost:5000/api/knowledge/tags \
  -H "X-API-Key: your_secret_key"

# 导出CSV
curl "http://localhost:5000/api/knowledge/export?status=completed" \
  -H "X-API-Key: your_secret_key" \
  -o knowledge_export.csv
```

#### 5. 访问Web UI

在浏览器中访问 http://localhost:5000/kb 使用可视化界面管理知识库。

详细知识库文档：
- [知识库API文档](../README_KNOWLEDGE_API.md)
- [知识库存储层文档](../README_KNOWLEDGE_REPO.md)
- [知识库测试文档](KNOWLEDGE_TESTING.md)
- [爬虫功能文档](../README_CRAWLER.md)
- [链接提取文档](../README_LINK_EXTRACTOR.md)

## 配置说明

详细配置说明请参考 [CONFIG.md](CONFIG.md)

## API文档

详细API文档请参考 [API.md](API.md) 或访问 http://localhost:5000/docs

## 部署指南

详细部署指南请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

## 项目结构

```
wp/
├── server.py                    # 主服务器入口
├── api_server.py                # API路由定义
├── core_service.py              # 核心业务逻辑
├── baidu_pan_adapter.py         # 百度网盘适配器
├── crawler_service.py           # 爬虫服务
├── link_extractor_service.py    # 链接提取服务
├── link_processor_service.py    # 链接处理服务
├── knowledge_repository.py      # 知识库数据访问层
├── knowledge_api.py             # 知识库API
├── config.py                    # 配置管理
├── logger.py                    # 日志系统
├── init_db.py                   # 数据库初始化
├── requirements.txt             # Python依赖
├── .env.example                 # 环境变量模板
├── Dockerfile                   # Docker镜像
├── docker-compose.yml           # Docker Compose配置
├── start.sh                     # 启动脚本
├── baidu-pan-server.service     # Systemd服务配置
├── tests/
│   ├── __init__.py              # 测试模块初始化
│   └── test_knowledge_module.py # 知识库完整测试套件
├── static/
│   └── knowledge/               # 知识库Web UI
└── docs/
    ├── README.md                # 项目说明
    ├── API.md                   # API文档
    ├── CONFIG.md                # 配置说明
    ├── DEPLOYMENT.md            # 部署指南
    └── KNOWLEDGE_TESTING.md     # 知识库测试文档
```

## 常见问题

### 1. Cookie失效怎么办？

Cookie会在一段时间后失效，需要重新获取并更新.env文件中的配置。

### 2. 如何配置多个账户？

在.env文件中添加多个账户配置：
```bash
ACCOUNT_MAIN_COOKIE=BDUSS=xxx
ACCOUNT_BACKUP_COOKIE=BDUSS=yyy
ACCOUNT_TEST_COOKIE=BDUSS=zzz
```

### 3. 如何修改速率限制？

在.env文件中配置：
```bash
RATE_LIMIT_DEFAULT=200 per hour  # 每小时200次请求
```

### 4. 如何查看日志？

日志文件位于 `logs/app.log`，可以使用 `tail -f logs/app.log` 实时查看。

### 5. 数据存储在哪里？

默认使用SQLite数据库，数据文件位于 `data/baidu_pan.db`。也可以配置使用MySQL或PostgreSQL。

## 安全建议

1. **修改默认API密钥**：生产环境务必修改 `API_SECRET_KEY`
2. **启用HTTPS**：生产环境建议使用Nginx反向代理并配置SSL证书
3. **配置防火墙**：限制只允许必要的IP访问
4. **定期备份数据**：定期备份data目录
5. **更新Cookie**：定期更新百度网盘Cookie

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 相关项目

- [hxz393/BaiduPanFilesTransfers](https://github.com/hxz393/BaiduPanFilesTransfers) - 原始GUI项目

## 免责声明

本项目仅供学习交流使用，请勿用于非法用途。使用本项目产生的任何后果由使用者自行承担。

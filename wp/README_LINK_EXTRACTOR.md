# 百度网盘链接提取和转存功能

## 概述

基于已爬取的lewz文章数据，自动提取百度网盘分享链接，执行转存和分享操作，并将结果更新回数据库。

## 功能特性

1. **链接提取**：从文章内容中使用正则表达式提取百度网盘链接
2. **密码识别**：自动识别提取码（支持多种格式）
3. **批量转存**：调用wp1账户的转存功能批量转存文件
4. **自动分享**：为转存的文件创建新的分享链接
5. **数据持久化**：将原始链接、新链接、标题等信息存入数据库

## 数据库结构

### extracted_links 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER/SERIAL | 主键 |
| article_id | TEXT/VARCHAR | 文章唯一ID |
| original_link | TEXT | 原始百度网盘链接 |
| original_password | TEXT/VARCHAR | 原始链接密码 |
| new_link | TEXT | 新生成的分享链接 |
| new_password | TEXT/VARCHAR | 新链接的密码 |
| new_title | TEXT | 新链接的标题（文件名） |
| status | TEXT/VARCHAR | 状态：pending/processing/transferred/completed/failed |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## API接口

### 1. 提取链接

```http
POST /api/links/extract
X-API-Key: your_api_key

{
  "limit": 100,
  "offset": 0
}
```

从文章中提取百度网盘链接并保存到数据库。

### 2. 获取链接列表

```http
GET /api/links/list?status=pending&limit=100&offset=0
X-API-Key: your_api_key
```

查询提取的链接列表，可按状态、文章ID筛选。

### 3. 获取统计信息

```http
GET /api/links/stats
X-API-Key: your_api_key
```

获取链接提取和处理的统计信息。

### 4. 处理链接（完整流程）

```http
POST /api/links/process
X-API-Key: your_api_key

{
  "account": "wp1",
  "limit": 50,
  "target_path": "/批量转存",
  "expiry": 7,
  "password": null,
  "mode": "all"
}
```

执行完整的提取→转存→分享流程。

**参数说明：**
- `account`: 使用的账户名称（必需）
- `limit`: 处理数量限制（默认50）
- `target_path`: 转存目标路径（默认 /批量转存）
- `expiry`: 分享有效期，单位天（0=永久, 1=1天, 7=7天, 30=30天）
- `password`: 固定提取码（可选，不填则随机生成）
- `mode`: 处理模式
  - `extract`: 仅提取链接
  - `transfer`: 仅转存
  - `share`: 仅分享
  - `all`: 完整流程（默认）

## 处理流程

### 完整流程（mode=all）

```
1. 提取阶段
   ├─ 从数据库读取文章内容
   ├─ 使用正则表达式提取百度网盘链接
   ├─ 识别提取码（支持多种格式）
   └─ 保存到 extracted_links 表，状态为 pending

2. 转存阶段
   ├─ 查询状态为 pending 的链接
   ├─ 添加到 CoreService 的转存队列
   ├─ 启动转存工作线程
   ├─ 等待转存完成
   └─ 更新链接状态为 transferred 或 failed

3. 分享阶段
   ├─ 查询状态为 transferred 的链接
   ├─ 从转存目标路径添加分享任务
   ├─ 启动分享工作线程
   ├─ 等待分享完成
   └─ 更新数据库：new_link, new_password, new_title, 状态为 completed
```

## 正则表达式模式

### 链接模式

1. 标准格式：`https://pan.baidu.com/s/xxxxx`
2. 短链接格式：`https://pan.baidu.com/share/init?surl=xxxxx`

### 密码模式

支持以下多种格式：
- `提取码：abcd`
- `密码: 1234`
- `pwd: test`
- `code: xyz`
- `?pwd=abcd`（URL参数）

## 使用示例

### Python代码示例

```python
from link_extractor_service import LinkExtractorService
from link_processor_service import LinkProcessorService
from core_service import CoreService

# 1. 初始化服务
extractor = LinkExtractorService()
core_service = CoreService(cookie="your_cookie")
core_service.login("your_cookie")

processor = LinkProcessorService("wp1", core_service)

# 2. 提取链接
result = processor.extract_and_save_links(limit=100)
print(f"提取了 {result['total_links']} 个链接")

# 3. 执行完整处理流程
result = processor.process_all(
    limit=50,
    target_path="/批量转存",
    expiry=7,
    password=None
)
print(f"处理完成: {result}")
```

### cURL示例

```bash
# 1. 提取链接
curl -X POST http://localhost:5000/api/links/extract \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'

# 2. 查看提取的链接
curl -X GET "http://localhost:5000/api/links/list?status=pending" \
  -H "X-API-Key: your_secret_key"

# 3. 执行完整处理
curl -X POST http://localhost:5000/api/links/process \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "wp1",
    "limit": 50,
    "target_path": "/批量转存",
    "expiry": 7,
    "mode": "all"
  }'

# 4. 查看统计信息
curl -X GET http://localhost:5000/api/links/stats \
  -H "X-API-Key: your_secret_key"
```

## 测试

运行测试脚本：

```bash
cd wp
python test_link_extractor.py
```

## 状态说明

- **pending**: 已提取，等待转存
- **processing**: 转存中
- **transferred**: 已转存，等待分享
- **completed**: 已完成（转存+分享）
- **failed**: 失败

## 注意事项

1. **账户配置**：需要先在环境变量中配置账户Cookie
2. **数据库初始化**：首次使用前需运行 `python init_db.py` 创建表
3. **API密钥**：所有接口都需要在请求头中包含 `X-API-Key`
4. **节流控制**：转存和分享操作受 CoreService 的节流策略控制
5. **错误处理**：转存失败的链接状态会标记为 failed，可通过 error_message 查看详情

## 配置

在 `.env` 文件中添加：

```env
# 账户配置
ACCOUNT_WP1_COOKIE=your_cookie_here

# API密钥
API_SECRET_KEY=your_secret_key

# 数据库配置（默认使用SQLite）
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/baidu_pan.db
```

## 文件说明

- `link_extractor_service.py`: 链接提取服务，负责正则提取和数据库操作
- `link_processor_service.py`: 链接处理服务，协调提取、转存、分享流程
- `init_db.py`: 数据库初始化（已更新，包含 extracted_links 表）
- `server.py`: API服务器（已更新，包含链接提取接口）
- `test_link_extractor.py`: 测试脚本

## 扩展

### 自定义正则表达式

可以在 `LinkExtractorService` 类中修改 `BAIDU_LINK_PATTERNS` 和 `PASSWORD_PATTERNS` 来支持更多格式。

### 批量处理

可以通过定时任务（如cron）定期调用 `/api/links/process` 接口实现自动化处理。

## 常见问题

### Q: 提取不到链接？
A: 检查文章内容是否包含百度网盘链接，确认链接格式是否符合正则表达式。

### Q: 转存失败？
A: 检查账户Cookie是否有效，查看 error_message 字段了解详细错误。

### Q: 如何查看处理进度？
A: 调用 `/api/links/stats` 查看各状态的链接数量。

## 版本历史

- v1.0.0 (2024-01): 初始版本
  - 支持链接提取
  - 支持批量转存和分享
  - 支持SQLite/MySQL/PostgreSQL数据库

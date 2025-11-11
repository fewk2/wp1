"""
百度网盘自动化服务器
提供完整的REST API接口，支持多账户管理、任务调度、监控等功能
"""
import os
import sys
import signal
import csv
import json
import io
import time
from functools import wraps
from typing import Dict, Any, Optional
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger, swag_from

from config import get_config, Config
from logger import get_logger
from core_service import CoreService
from init_db import initialize_database
from crawler_service import CrawlerService

# 初始化配置
config = get_config()
config.ensure_directories()

# 初始化日志
from logger import Logger
Logger.initialize(config)
logger = get_logger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON响应

# 配置CORS
CORS(app, origins=config.CORS_ORIGINS)

# 配置速率限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[config.RATE_LIMIT_DEFAULT] if config.RATE_LIMIT_ENABLED else [],
    storage_uri=config.RATE_LIMIT_STORAGE_URL
)

# Swagger配置
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": config.APP_NAME,
        "description": "百度网盘批量工具API服务 - 支持批量转存、批量分享、多账户管理等功能",
        "version": config.APP_VERSION,
        "contact": {
            "name": "API Support"
        }
    },
    "securityDefinitions": {
        "ApiKeyAuth": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header",
            "description": "API密钥，在请求头中添加 X-API-Key"
        }
    },
    "security": [
        {
            "ApiKeyAuth": []
        }
    ],
    "schemes": ["http", "https"],
    "tags": [
        {
            "name": "系统",
            "description": "系统相关接口"
        },
        {
            "name": "转存",
            "description": "文件转存相关接口"
        },
        {
            "name": "分享",
            "description": "文件分享相关接口"
        },
        {
            "name": "文件管理",
            "description": "文件浏览和管理接口"
        },
        {
            "name": "账户",
            "description": "账户管理接口"
        },
        {
            "name": "爬虫",
            "description": "文章爬取相关接口"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# 全局变量
services: Dict[str, CoreService] = {}  # 账户名 -> 服务实例
accounts: Dict[str, str] = {}  # 账户名 -> Cookie
api_secret_key: str = config.API_SECRET_KEY
crawler_service: Optional[CrawlerService] = None  # 爬虫服务实例


def load_accounts_from_env():
    """从环境变量加载账户配置"""
    global accounts
    
    # 格式：ACCOUNT_{账户名}_COOKIE
    for key, value in os.environ.items():
        if key.startswith('ACCOUNT_') and key.endswith('_COOKIE'):
            account_name = key[8:-7].lower()
            accounts[account_name] = value
            logger.info(f"加载账户: {account_name}")
    
    if not accounts:
        logger.warning("未找到账户配置，请在.env中配置 ACCOUNT_xxx_COOKIE")
    
    return len(accounts) > 0


def verify_api_key(key: str) -> bool:
    """验证API密钥"""
    return key == api_secret_key


def require_auth(f):
    """装饰器：验证API密钥"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not verify_api_key(api_key):
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key',
                'message': '无效或缺失的API密钥'
            }), 401
        return f(*args, **kwargs)
    return decorated


def require_service(f):
    """装饰器：验证API密钥并获取服务实例"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 验证API密钥
        api_key = request.headers.get('X-API-Key')
        if not api_key or not verify_api_key(api_key):
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key',
                'message': '无效或缺失的API密钥'
            }), 401
        
        # 获取账户名
        account = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.is_json:
                data = request.get_json(silent=True) or {}
                account = data.get('account')
            elif request.form:
                account = request.form.get('account')
            else:
                account = request.args.get('account')
        else:
            account = request.args.get('account')
        
        # 获取服务实例
        service = get_or_create_service(account)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Account not found or login failed: {account or config.DEFAULT_ACCOUNT}',
                'message': f'账户未找到或登录失败: {account or config.DEFAULT_ACCOUNT}'
            }), 401
        
        # 传递服务实例给路由函数
        return f(service, *args, **kwargs)
    return decorated


def get_or_create_service(account: Optional[str] = None) -> Optional[CoreService]:
    """获取或创建服务实例"""
    if not account:
        account = config.DEFAULT_ACCOUNT
    
    # 如果服务实例已存在，直接返回
    if account in services and services[account].adapter:
        return services[account]
    
    # 获取Cookie
    if account not in accounts:
        logger.error(f"账户不存在: {account}")
        return None
    
    cookie = accounts[account]
    
    # 创建服务实例
    throttle_config = config.get_throttle_config()
    service = CoreService(cookie, throttle_config)
    success, error_msg = service.login(cookie)
    
    if success:
        services[account] = service
        logger.info(f"账户登录成功: {account}")
        return service
    else:
        logger.error(f"账户登录失败: {account}, 错误: {error_msg}")
        return None


# ============================================================================
# 系统接口
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查
    ---
    tags:
      - 系统
    responses:
      200:
        description: 服务正常运行
        schema:
          properties:
            status:
              type: string
              example: ok
            message:
              type: string
              example: 服务运行正常
            version:
              type: string
              example: 1.0.0
            accounts:
              type: array
              items:
                type: string
              example: ["main", "backup"]
            timestamp:
              type: string
              example: "2024-01-01 12:00:00"
    """
    return jsonify({
        'status': 'ok',
        'message': '服务运行正常',
        'version': config.APP_VERSION,
        'accounts': list(accounts.keys()),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/info', methods=['GET'])
@require_auth
def get_info():
    """
    获取系统信息
    ---
    tags:
      - 系统
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 系统信息
      401:
        description: 未授权
    """
    return jsonify({
        'success': True,
        'data': {
            'app_name': config.APP_NAME,
            'version': config.APP_VERSION,
            'environment': os.getenv('ENV', 'development'),
            'accounts': list(accounts.keys()),
            'active_services': list(services.keys()),
            'config': {
                'rate_limit_enabled': config.RATE_LIMIT_ENABLED,
                'log_level': config.LOG_LEVEL,
                'database_type': config.DATABASE_TYPE
            }
        }
    })


@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    """
    获取统计信息
    ---
    tags:
      - 系统
    security:
      - ApiKeyAuth: []
    parameters:
      - name: account
        in: query
        type: string
        required: false
        description: 账户名（不填则返回所有账户）
    responses:
      200:
        description: 统计信息
      401:
        description: 未授权
    """
    account = request.args.get('account')
    
    if account:
        # 获取单个账户的统计信息
        service = get_or_create_service(account)
        if not service:
            return jsonify({
                'success': False,
                'error': f'Account not found: {account}'
            }), 404
        
        stats = {
            'account': account,
            'transfer': service.get_transfer_status(),
            'share': service.get_share_status()
        }
    else:
        # 获取所有账户的统计信息
        stats = {}
        for acc in accounts.keys():
            service = get_or_create_service(acc)
            if service:
                stats[acc] = {
                    'transfer': service.get_transfer_status(),
                    'share': service.get_share_status()
                }
    
    return jsonify({
        'success': True,
        'data': stats
    })


# ============================================================================
# 转存接口
# ============================================================================

@app.route('/api/transfer/import', methods=['POST'])
@require_service
@limiter.limit("50 per hour")
def import_transfer_tasks(service):
    """
    批量导入转存任务
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    consumes:
      - application/json
      - multipart/form-data
    parameters:
      - in: body
        name: body
        description: 任务数据（JSON格式）
        schema:
          type: object
          properties:
            account:
              type: string
              description: 账户名
              example: main
            csv_data:
              type: array
              description: CSV数据
              items:
                type: object
                properties:
                  链接:
                    type: string
                  提取码:
                    type: string
                  保存位置:
                    type: string
            default_target_path:
              type: string
              description: 默认保存路径
              example: /批量转存
      - in: formData
        name: file
        type: file
        description: CSV文件（文件上传格式）
    responses:
      200:
        description: 导入成功
      400:
        description: 请求参数错误
      401:
        description: 未授权
    """
    # 支持JSON和文件上传两种方式
    if request.content_type and 'multipart/form-data' in request.content_type:
        # 文件上传方式
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400
        
        file = request.files['file']
        default_target_path = request.form.get('default_target_path', '/批量转存')
        
        try:
            content = file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(content))
            csv_data = list(reader)
        except Exception as e:
            logger.error(f"CSV解析失败: {e}")
            return jsonify({
                'success': False,
                'error': f'CSV解析失败: {str(e)}'
            }), 400
    else:
        # JSON方式
        data = request.get_json()
        if not data or 'csv_data' not in data:
            return jsonify({
                'success': False,
                'error': '缺少csv_data参数'
            }), 400
        
        csv_data = data['csv_data']
        default_target_path = data.get('default_target_path', '/批量转存')
    
    # 添加任务
    count = service.add_transfer_tasks_from_csv(csv_data, default_target_path)
    
    if count > 0:
        logger.info(f"导入转存任务成功: {count}个")
        return jsonify({
            'success': True,
            'message': f'已导入 {count} 个转存任务',
            'count': count
        })
    else:
        return jsonify({
            'success': False,
            'error': '没有有效的转存任务'
        }), 400


@app.route('/api/transfer/add', methods=['POST'])
@require_service
@limiter.limit("100 per hour")
def add_transfer_task(service):
    """
    添加单个转存任务
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - share_link
          properties:
            account:
              type: string
              description: 账户名
            share_link:
              type: string
              description: 分享链接
            share_password:
              type: string
              description: 提取码
            target_path:
              type: string
              description: 目标路径
              default: /批量转存
    responses:
      200:
        description: 添加成功
      400:
        description: 请求参数错误
      401:
        description: 未授权
    """
    data = request.get_json()
    if not data or 'share_link' not in data:
        return jsonify({
            'success': False,
            'error': '缺少share_link参数'
        }), 400
    
    share_link = data['share_link']
    share_password = data.get('share_password', '')
    target_path = data.get('target_path', '/批量转存')
    
    success = service.add_transfer_task(share_link, share_password, target_path)
    
    if success:
        logger.info(f"添加转存任务: {share_link}")
        return jsonify({
            'success': True,
            'message': '已添加转存任务'
        })
    else:
        return jsonify({
            'success': False,
            'error': '添加任务失败'
        }), 400


@app.route('/api/transfer/start', methods=['POST'])
@require_service
def start_transfer(service):
    """
    开始转存任务
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            account:
              type: string
    responses:
      200:
        description: 启动成功
      400:
        description: 启动失败
      401:
        description: 未授权
    """
    success, error_msg = service.start_transfer()
    
    if success:
        logger.info("转存任务已启动")
        return jsonify({
            'success': True,
            'message': '转存任务已启动'
        })
    else:
        logger.error(f"转存任务启动失败: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400


@app.route('/api/transfer/pause', methods=['POST'])
@require_service
def pause_transfer(service):
    """
    暂停转存任务
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 暂停成功
      401:
        description: 未授权
    """
    service.pause_transfer()
    logger.info("转存任务已暂停")
    return jsonify({
        'success': True,
        'message': '转存已暂停'
    })


@app.route('/api/transfer/resume', methods=['POST'])
@require_service
def resume_transfer(service):
    """
    继续转存任务
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 继续成功
      401:
        description: 未授权
    """
    service.resume_transfer()
    logger.info("转存任务已继续")
    return jsonify({
        'success': True,
        'message': '转存已继续'
    })


@app.route('/api/transfer/stop', methods=['POST'])
@require_service
def stop_transfer(service):
    """
    停止转存任务
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 停止成功
      401:
        description: 未授权
    """
    service.stop_transfer()
    logger.info("转存任务已停止")
    return jsonify({
        'success': True,
        'message': '转存已停止'
    })


@app.route('/api/transfer/status', methods=['GET'])
@require_service
def get_transfer_status(service):
    """
    获取转存状态
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    parameters:
      - name: account
        in: query
        type: string
        required: false
    responses:
      200:
        description: 状态信息
      401:
        description: 未授权
    """
    status = service.get_transfer_status()
    return jsonify({
        'success': True,
        'data': status
    })


@app.route('/api/transfer/queue', methods=['GET'])
@require_service
def get_transfer_queue(service):
    """
    获取转存队列
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    parameters:
      - name: account
        in: query
        type: string
        required: false
    responses:
      200:
        description: 队列数据
      401:
        description: 未授权
    """
    queue = service.get_transfer_queue()
    return jsonify({
        'success': True,
        'data': queue
    })


@app.route('/api/transfer/clear', methods=['POST'])
@require_service
def clear_transfer_queue(service):
    """
    清空转存队列
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 清空成功
      401:
        description: 未授权
    """
    service.clear_transfer_queue()
    logger.info("转存队列已清空")
    return jsonify({
        'success': True,
        'message': '转存队列已清空'
    })


@app.route('/api/transfer/export', methods=['GET'])
@require_service
def export_transfer_results(service):
    """
    导出转存结果
    ---
    tags:
      - 转存
    security:
      - ApiKeyAuth: []
    parameters:
      - name: account
        in: query
        type: string
        required: false
      - name: format
        in: query
        type: string
        enum: [json, csv]
        default: json
    responses:
      200:
        description: 导出成功
      401:
        description: 未授权
    """
    format_type = request.args.get('format', 'json')
    results = service.export_transfer_results()
    
    if format_type == 'csv':
        # 生成CSV
        output = io.StringIO()
        if results:
            writer = csv.DictWriter(output, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'transfer_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    else:
        # 返回JSON
        return jsonify({
            'success': True,
            'data': results
        })


# ============================================================================
# 分享接口
# ============================================================================

@app.route('/api/share/add_from_path', methods=['POST'])
@require_service
@limiter.limit("50 per hour")
def add_share_from_path(service):
    """
    从路径添加分享任务
    ---
    tags:
      - 分享
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - path
          properties:
            account:
              type: string
            path:
              type: string
              description: 文件路径
            expiry:
              type: integer
              description: 有效期（0=永久, 1=1天, 7=7天, 30=30天）
              default: 7
            password:
              type: string
              description: 固定提取码（不填则随机生成）
    responses:
      200:
        description: 添加成功
      400:
        description: 请求参数错误
      401:
        description: 未授权
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({
            'success': False,
            'error': '缺少path参数'
        }), 400
    
    path = data['path']
    expiry = data.get('expiry', 7)
    password = data.get('password', None)
    
    count = service.add_share_tasks_from_path(path, expiry=expiry, password=password)
    
    if count > 0:
        logger.info(f"添加分享任务: {count}个，路径: {path}")
        return jsonify({
            'success': True,
            'message': f'已添加 {count} 个分享任务',
            'count': count
        })
    else:
        return jsonify({
            'success': False,
            'error': '没有找到文件或添加失败'
        }), 400


@app.route('/api/share/start', methods=['POST'])
@require_service
def start_share(service):
    """
    开始分享任务
    ---
    tags:
      - 分享
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 启动成功
      400:
        description: 启动失败
      401:
        description: 未授权
    """
    success, error_msg = service.start_share()
    
    if success:
        logger.info("分享任务已启动")
        return jsonify({
            'success': True,
            'message': '分享任务已启动'
        })
    else:
        logger.error(f"分享任务启动失败: {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400


@app.route('/api/share/pause', methods=['POST'])
@require_service
def pause_share(service):
    """暂停分享任务"""
    service.pause_share()
    logger.info("分享任务已暂停")
    return jsonify({
        'success': True,
        'message': '分享已暂停'
    })


@app.route('/api/share/resume', methods=['POST'])
@require_service
def resume_share(service):
    """继续分享任务"""
    service.resume_share()
    logger.info("分享任务已继续")
    return jsonify({
        'success': True,
        'message': '分享已继续'
    })


@app.route('/api/share/stop', methods=['POST'])
@require_service
def stop_share(service):
    """停止分享任务"""
    service.stop_share()
    logger.info("分享任务已停止")
    return jsonify({
        'success': True,
        'message': '分享已停止'
    })


@app.route('/api/share/status', methods=['GET'])
@require_service
def get_share_status(service):
    """获取分享状态"""
    status = service.get_share_status()
    return jsonify({
        'success': True,
        'data': status
    })


@app.route('/api/share/queue', methods=['GET'])
@require_service
def get_share_queue(service):
    """获取分享队列"""
    queue = service.get_share_queue()
    return jsonify({
        'success': True,
        'data': queue
    })


@app.route('/api/share/clear', methods=['POST'])
@require_service
def clear_share_queue(service):
    """清空分享队列"""
    service.clear_share_queue()
    logger.info("分享队列已清空")
    return jsonify({
        'success': True,
        'message': '分享队列已清空'
    })


@app.route('/api/share/export', methods=['GET'])
@require_service
def export_share_results(service):
    """导出分享结果"""
    format_type = request.args.get('format', 'json')
    results = service.export_share_results()
    
    if format_type == 'csv':
        output = io.StringIO()
        if results:
            writer = csv.DictWriter(output, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'share_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    else:
        return jsonify({
            'success': True,
            'data': results
        })


# ============================================================================
# 文件管理接口
# ============================================================================

@app.route('/api/files/list', methods=['GET'])
@require_service
def list_files(service):
    """
    列出指定路径的文件
    ---
    tags:
      - 文件管理
    security:
      - ApiKeyAuth: []
    parameters:
      - name: account
        in: query
        type: string
      - name: path
        in: query
        type: string
        required: true
        description: 文件路径
        default: /
    responses:
      200:
        description: 文件列表
      401:
        description: 未授权
    """
    path = request.args.get('path', '/')
    files = service.list_dir(path)
    
    if isinstance(files, int):
        return jsonify({
            'success': False,
            'error': f'获取文件列表失败，错误码: {files}'
        }), 400
    
    return jsonify({
        'success': True,
        'data': files
    })


@app.route('/api/files/search', methods=['GET'])
@require_service
def search_files(service):
    """
    搜索文件
    ---
    tags:
      - 文件管理
    security:
      - ApiKeyAuth: []
    parameters:
      - name: account
        in: query
        type: string
      - name: keyword
        in: query
        type: string
        required: true
        description: 搜索关键词
      - name: path
        in: query
        type: string
        description: 搜索路径
        default: /
    responses:
      200:
        description: 搜索结果
      401:
        description: 未授权
    """
    keyword = request.args.get('keyword')
    path = request.args.get('path', '/')
    
    if not keyword:
        return jsonify({
            'success': False,
            'error': '缺少keyword参数'
        }), 400
    
    results = service.search_files(keyword, path)
    
    return jsonify({
        'success': True,
        'data': results
    })


# ============================================================================
# 账户管理接口
# ============================================================================

@app.route('/api/accounts', methods=['GET'])
@require_auth
def list_accounts():
    """
    列出所有账户
    ---
    tags:
      - 账户
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 账户列表
      401:
        description: 未授权
    """
    account_list = []
    for name in accounts.keys():
        is_active = name in services and services[name].adapter is not None
        account_list.append({
            'name': name,
            'is_active': is_active
        })
    
    return jsonify({
        'success': True,
        'data': account_list
    })


# ============================================================================
# 爬虫接口
# ============================================================================

def get_crawler_service() -> CrawlerService:
    """获取或创建爬虫服务实例"""
    global crawler_service
    if crawler_service is None:
        crawler_service = CrawlerService(config)
    return crawler_service


@app.route('/api/crawler/start', methods=['POST'])
@require_auth
@limiter.limit("5 per hour")
def start_crawling():
    """
    开始爬取lewz.cn/jprj文章
    ---
    tags:
      - 爬虫
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 爬取任务已启动
      401:
        description: 未授权
    """
    try:
        service = get_crawler_service()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(service.crawl_jprj_articles())
        loop.close()
        
        return jsonify({
            'success': True,
            'message': '爬取任务完成',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"爬取任务失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '爬取任务失败'
        }), 500


@app.route('/api/crawler/articles', methods=['GET'])
@require_auth
def get_articles():
    """
    获取已爬取的文章列表
    ---
    tags:
      - 爬虫
    security:
      - ApiKeyAuth: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 100
        description: 返回数量限制
      - name: offset
        in: query
        type: integer
        default: 0
        description: 偏移量
    responses:
      200:
        description: 文章列表
      401:
        description: 未授权
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        service = get_crawler_service()
        articles = service.get_articles(limit, offset)
        
        return jsonify({
            'success': True,
            'data': {
                'articles': articles,
                'limit': limit,
                'offset': offset,
                'count': len(articles)
            }
        })
        
    except Exception as e:
        logger.error(f"获取文章列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取文章列表失败'
        }), 500


@app.route('/api/crawler/articles/<article_id>', methods=['GET'])
@require_auth
def get_article(article_id):
    """
    获取文章详情
    ---
    tags:
      - 爬虫
    security:
      - ApiKeyAuth: []
    parameters:
      - name: article_id
        in: path
        type: string
        required: true
        description: 文章唯一ID
    responses:
      200:
        description: 文章详情
      404:
        description: 文章不存在
      401:
        description: 未授权
    """
    try:
        service = get_crawler_service()
        article = service.get_article_by_id(article_id)
        
        if article:
            return jsonify({
                'success': True,
                'data': article
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Article not found',
                'message': '文章不存在'
            }), 404
        
    except Exception as e:
        logger.error(f"获取文章详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取文章详情失败'
        }), 500


@app.route('/api/crawler/stats', methods=['GET'])
@require_auth
def get_crawler_stats():
    """
    获取爬虫统计信息
    ---
    tags:
      - 爬虫
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 统计信息
      401:
        description: 未授权
    """
    try:
        service = get_crawler_service()
        stats = service.get_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取统计信息失败'
        }), 500


# ============================================================================
# 错误处理
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': '请求的资源不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': '服务器内部错误'
    }), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    """速率限制错误处理"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': '请求过于频繁，请稍后再试'
    }), 429


# ============================================================================
# 应用初始化和启动
# ============================================================================

def initialize_app():
    """初始化应用"""
    logger.info("正在初始化应用...")
    
    # 检查API密钥
    if config.API_SECRET_KEY == 'default_insecure_key':
        logger.warning("⚠️  使用默认API密钥，生产环境请修改！")
    
    # 初始化数据库
    logger.info("初始化数据库...")
    if not initialize_database(config):
        logger.error("数据库初始化失败")
        sys.exit(1)
    
    # 加载账户
    logger.info("加载账户配置...")
    if not load_accounts_from_env():
        logger.warning("未加载到任何账户")
    
    logger.info("应用初始化完成")


def shutdown_handler(signum, frame):
    """优雅关闭处理"""
    logger.info("接收到关闭信号，正在关闭服务...")
    
    # 停止所有服务
    for account, service in services.items():
        logger.info(f"关闭账户服务: {account}")
        service.stop_transfer()
        service.stop_share()
    
    logger.info("服务已关闭")
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # 初始化应用
    initialize_app()
    
    # 启动服务器
    logger.info(f"启动服务器: http://{config.HOST}:{config.PORT}")
    logger.info(f"API文档: http://{config.HOST}:{config.PORT}/docs")
    logger.info(f"健康检查: http://{config.HOST}:{config.PORT}/api/health")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )


if __name__ == '__main__':
    main()

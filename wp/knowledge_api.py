"""
知识库API蓝图
提供知识库条目的查询、筛选、导出等REST接口
"""
import csv
import io
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, jsonify, Response, stream_with_context
from flasgger import swag_from

from config import get_config
from logger import get_logger
from knowledge_repository import KnowledgeRepository

logger = get_logger(__name__)
config = get_config()

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')


def verify_api_key(key: str) -> bool:
    """验证API密钥"""
    return key == config.API_SECRET_KEY


@knowledge_bp.before_request
def require_auth():
    """蓝图级别的API密钥验证"""
    api_key = request.headers.get('X-API-Key')
    if not api_key or not verify_api_key(api_key):
        return jsonify({
            'success': False,
            'error': 'Invalid or missing API key',
            'message': '无效或缺失的API密钥'
        }), 401


def get_knowledge_repository() -> KnowledgeRepository:
    """获取知识库存储层实例"""
    return KnowledgeRepository(config)


def validate_page_params(page: Optional[int], page_size: Optional[int]) -> tuple:
    """
    验证分页参数
    
    Args:
        page: 页码（从1开始）
        page_size: 每页条数
        
    Returns:
        (page, page_size, offset) 元组
    """
    page = max(1, page or 1)
    page_size = max(1, min(1000, page_size or 50))
    offset = (page - 1) * page_size
    
    return page, page_size, offset


def validate_date(date_str: Optional[str]) -> Optional[str]:
    """
    验证ISO日期格式 (YYYY-MM-DD)
    
    Args:
        date_str: 日期字符串
        
    Returns:
        验证后的日期字符串，失败返回None
    """
    if not date_str:
        return None
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        logger.warning(f"无效的日期格式: {date_str}")
        return None


@knowledge_bp.route('/entries', methods=['GET'])
def get_entries():
    """
    获取知识库条目列表
    ---
    tags:
      - 知识库
    security:
      - ApiKeyAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: 页码（从1开始）
      - name: page_size
        in: query
        type: integer
        default: 50
        description: 每页条数（最大1000）
      - name: search
        in: query
        type: string
        required: false
        description: 搜索关键词（应用于标题、ID、URL、链接）
      - name: status
        in: query
        type: string
        required: false
        enum: [pending, processing, transferred, completed, failed]
        description: 状态过滤
      - name: tag
        in: query
        type: string
        required: false
        description: 标签过滤
      - name: date_from
        in: query
        type: string
        required: false
        description: 起始日期（YYYY-MM-DD）
      - name: date_to
        in: query
        type: string
        required: false
        description: 结束日期（YYYY-MM-DD）
      - name: sort
        in: query
        type: string
        default: created_at
        enum: [created_at, updated_at, title, status]
        description: 排序字段
      - name: order
        in: query
        type: string
        default: DESC
        enum: [ASC, DESC]
        description: 排序方向
    responses:
      200:
        description: 条目列表及分页信息
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                entries:
                  type: array
                  items:
                    type: object
                pagination:
                  type: object
                  properties:
                    page:
                      type: integer
                    page_size:
                      type: integer
                    total:
                      type: integer
                    total_pages:
                      type: integer
            summary:
              type: object
              description: 状态统计
      400:
        description: 请求参数错误
      401:
        description: 未授权
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)
        search = request.args.get('search')
        status = request.args.get('status')
        tag = request.args.get('tag')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'DESC')
        
        page, page_size, offset = validate_page_params(page, page_size)
        
        date_from = validate_date(date_from)
        date_to = validate_date(date_to)
        
        if sort not in KnowledgeRepository.ALLOWED_SORT_FIELDS:
            return jsonify({
                'success': False,
                'error': 'Invalid sort field',
                'message': f'排序字段必须是: {", ".join(KnowledgeRepository.ALLOWED_SORT_FIELDS)}'
            }), 400
        
        if order.upper() not in ['ASC', 'DESC']:
            return jsonify({
                'success': False,
                'error': 'Invalid sort order',
                'message': '排序方向必须是 ASC 或 DESC'
            }), 400
        
        repo = get_knowledge_repository()
        
        result = repo.list_entries(
            limit=page_size,
            offset=offset,
            search=search,
            status=status,
            tag=tag,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort,
            sort_order=order.upper()
        )
        
        total = result.get('total', 0)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        summary = repo.summaries_by_status()
        
        return jsonify({
            'success': True,
            'data': {
                'entries': result.get('entries', []),
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages
                }
            },
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"获取知识库条目失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取知识库条目失败'
        }), 500


@knowledge_bp.route('/tags', methods=['GET'])
def get_tags():
    """
    获取所有不重复的标签列表
    ---
    tags:
      - 知识库
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 标签列表
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                tags:
                  type: array
                  items:
                    type: string
                count:
                  type: integer
      401:
        description: 未授权
    """
    try:
        repo = get_knowledge_repository()
        tags = repo.get_distinct_tags()
        
        return jsonify({
            'success': True,
            'data': {
                'tags': tags,
                'count': len(tags)
            }
        })
        
    except Exception as e:
        logger.error(f"获取标签列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取标签列表失败'
        }), 500


@knowledge_bp.route('/statuses', methods=['GET'])
def get_statuses():
    """
    获取所有状态及其对应的条目数量
    ---
    tags:
      - 知识库
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 状态统计
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                statuses:
                  type: object
                  additionalProperties:
                    type: integer
                total:
                  type: integer
      401:
        description: 未授权
    """
    try:
        repo = get_knowledge_repository()
        statuses = repo.summaries_by_status()
        total = sum(statuses.values())
        
        return jsonify({
            'success': True,
            'data': {
                'statuses': statuses,
                'total': total
            }
        })
        
    except Exception as e:
        logger.error(f"获取状态统计失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取状态统计失败'
        }), 500


@knowledge_bp.route('/export', methods=['GET'])
def export_entries():
    """
    导出知识库条目为CSV
    ---
    tags:
      - 知识库
    security:
      - ApiKeyAuth: []
    produces:
      - text/csv
    parameters:
      - name: fields
        in: query
        type: string
        required: false
        description: 导出字段列表（逗号分隔，可选字段见文档）
      - name: search
        in: query
        type: string
        required: false
        description: 搜索关键词
      - name: status
        in: query
        type: string
        required: false
        description: 状态过滤
      - name: tag
        in: query
        type: string
        required: false
        description: 标签过滤
      - name: date_from
        in: query
        type: string
        required: false
        description: 起始日期（YYYY-MM-DD）
      - name: date_to
        in: query
        type: string
        required: false
        description: 结束日期（YYYY-MM-DD）
      - name: sort
        in: query
        type: string
        default: created_at
        description: 排序字段
      - name: order
        in: query
        type: string
        default: DESC
        description: 排序方向
    responses:
      200:
        description: CSV文件
        headers:
          Content-Type:
            type: string
            description: text/csv; charset=utf-8
          Content-Disposition:
            type: string
            description: 'attachment; filename="knowledge_export.csv"'
      400:
        description: 请求参数错误
      401:
        description: 未授权
    """
    try:
        fields_param = request.args.get('fields', '')
        search = request.args.get('search')
        status = request.args.get('status')
        tag = request.args.get('tag')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'DESC')
        
        if fields_param:
            fields = [f.strip() for f in fields_param.split(',') if f.strip()]
        else:
            fields = KnowledgeRepository.ALLOWED_EXPORT_FIELDS
        
        date_from = validate_date(date_from)
        date_to = validate_date(date_to)
        
        if sort not in KnowledgeRepository.ALLOWED_SORT_FIELDS:
            sort = 'created_at'
        
        if order.upper() not in ['ASC', 'DESC']:
            order = 'DESC'
        
        repo = get_knowledge_repository()
        
        filters = {
            'search': search,
            'status': status,
            'tag': tag,
            'date_from': date_from,
            'date_to': date_to
        }
        
        try:
            rows = repo.prepare_export_rows(
                fields=fields,
                filters=filters,
                sort_by=sort,
                sort_order=order.upper()
            )
        except ValueError as ve:
            return jsonify({
                'success': False,
                'error': 'Invalid fields',
                'message': str(ve)
            }), 400
        
        def generate():
            output = io.StringIO()
            
            output.write('\ufeff')
            
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
            
            writer.writeheader()
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            
            for row in rows:
                writer.writerow(row)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'knowledge_export_{timestamp}.csv'
        
        response = Response(
            stream_with_context(generate()),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"导出知识库条目失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '导出知识库条目失败'
        }), 500


@knowledge_bp.route('/entry/<article_id>', methods=['GET'])
def get_entry_detail(article_id: str):
    """
    获取单个条目的详细信息
    ---
    tags:
      - 知识库
    security:
      - ApiKeyAuth: []
    parameters:
      - name: article_id
        in: path
        type: string
        required: true
        description: 文章ID
    responses:
      200:
        description: 条目详情
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
      404:
        description: 条目不存在
      401:
        description: 未授权
    """
    try:
        repo = get_knowledge_repository()
        
        result = repo.list_entries(
            limit=1,
            offset=0,
            search=article_id
        )
        
        entries = result.get('entries', [])
        
        matching_entry = None
        for entry in entries:
            if entry.get('article_id') == article_id:
                matching_entry = entry
                break
        
        if matching_entry:
            return jsonify({
                'success': True,
                'data': matching_entry
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Entry not found',
                'message': '条目不存在'
            }), 404
        
    except Exception as e:
        logger.error(f"获取条目详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取条目详情失败'
        }), 500

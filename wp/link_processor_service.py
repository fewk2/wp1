"""
百度网盘链接处理服务
协调链接提取、转存和分享的完整流程
"""
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import get_config, Config
from logger import get_logger
from link_extractor_service import LinkExtractorService
from core_service import CoreService

logger = get_logger(__name__)


class LinkProcessorService:
    """百度网盘链接处理服务 - 协调提取、转存、分享流程"""
    
    def __init__(self, account_name: str, core_service: CoreService, config: Optional[Config] = None):
        """
        初始化链接处理服务
        
        Args:
            account_name: 账户名称（用于标识）
            core_service: CoreService实例（已登录）
            config: 配置对象
        """
        self.account_name = account_name
        self.core_service = core_service
        self.config = config or get_config()
        self.extractor = LinkExtractorService(config)
        
    def extract_and_save_links(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        从文章中提取链接并保存到数据库
        
        Args:
            limit: 处理文章数量限制
            offset: 偏移量
            
        Returns:
            提取结果统计
        """
        logger.info(f"开始提取文章中的百度网盘链接 (limit={limit}, offset={offset})")
        
        articles = self.extractor.get_articles_with_links(limit, offset)
        
        total_articles = len(articles)
        total_links = 0
        saved_links = 0
        
        for article in articles:
            article_id = article['article_id']
            links = article.get('extracted_links', [])
            
            for link_data in links:
                total_links += 1
                success = self.extractor.save_extracted_link(
                    article_id=article_id,
                    original_link=link_data['link'],
                    original_password=link_data['password'],
                    status='pending'
                )
                if success:
                    saved_links += 1
        
        result = {
            'success': True,
            'total_articles': total_articles,
            'total_links': total_links,
            'saved_links': saved_links,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"提取完成: {result}")
        return result
    
    def process_pending_links(self, limit: int = 50, target_path: str = '/批量转存') -> Dict[str, Any]:
        """
        处理待处理的链接：执行转存操作
        
        Args:
            limit: 处理数量限制
            target_path: 转存目标路径
            
        Returns:
            处理结果
        """
        logger.info(f"开始处理待转存链接 (limit={limit}, target_path={target_path})")
        
        pending_links = self.extractor.get_extracted_links(status='pending', limit=limit)
        
        if not pending_links:
            return {
                'success': True,
                'message': '没有待处理的链接',
                'processed': 0
            }
        
        # 添加转存任务到队列
        for link in pending_links:
            self.extractor.update_extracted_link_status(
                article_id=link['article_id'],
                original_link=link['original_link'],
                status='processing'
            )
            
            csv_data = [{
                '标题': link['article_id'],
                '链接': link['original_link'],
                '提取码': link['original_password'],
                '保存位置': target_path
            }]
            
            self.core_service.add_transfer_tasks_from_csv(csv_data, target_path)
        
        # 启动转存任务
        success, error_msg = self.core_service.start_transfer()
        
        if not success:
            return {
                'success': False,
                'message': f'启动转存失败: {error_msg}',
                'processed': 0
            }
        
        # 等待转存完成
        logger.info("等待转存任务完成...")
        while True:
            status = self.core_service.get_transfer_status()
            if not status['is_running']:
                break
            time.sleep(2)
        
        logger.info(f"转存完成: {status}")
        
        # 更新链接状态
        transfer_status = self.core_service.get_transfer_status()
        for i, task in enumerate(transfer_status['tasks']):
            if i >= len(pending_links):
                break
            
            link = pending_links[i]
            
            if task['status'] == 'completed':
                self.extractor.update_extracted_link_status(
                    article_id=link['article_id'],
                    original_link=link['original_link'],
                    status='transferred'
                )
            elif task['status'] in ['failed', 'skipped']:
                self.extractor.update_extracted_link_status(
                    article_id=link['article_id'],
                    original_link=link['original_link'],
                    status='failed',
                    error_message=task.get('error_message', '')
                )
        
        return {
            'success': True,
            'processed': len(pending_links),
            'completed': transfer_status['completed'],
            'failed': transfer_status['failed'],
            'skipped': transfer_status['skipped'],
            'transfer_status': transfer_status
        }
    
    def share_transferred_links(self, expiry: int = 7, password: str = None) -> Dict[str, Any]:
        """
        为已转存的文件创建分享链接
        
        Args:
            expiry: 有效期（0=永久, 1=1天, 7=7天, 30=30天）
            password: 固定提取码，None则随机生成
            
        Returns:
            分享结果
        """
        logger.info(f"开始创建分享链接 (expiry={expiry})")
        
        transferred_links = self.extractor.get_extracted_links(status='transferred', limit=100)
        
        if not transferred_links:
            return {
                'success': True,
                'message': '没有已转存的链接需要分享',
                'shared': 0
            }
        
        # 从转存目标路径添加分享任务
        target_path = '/批量转存'
        count = self.core_service.add_share_tasks_from_path(target_path, expiry=expiry, password=password)
        
        if count == 0:
            return {
                'success': False,
                'message': '未找到可分享的文件',
                'shared': 0
            }
        
        # 启动分享任务
        success, error_msg = self.core_service.start_share()
        
        if not success:
            return {
                'success': False,
                'message': f'启动分享失败: {error_msg}',
                'shared': 0
            }
        
        # 等待分享完成
        logger.info("等待分享任务完成...")
        while True:
            status = self.core_service.get_share_status()
            if not status['is_running']:
                break
            time.sleep(2)
        
        logger.info(f"分享完成: {status}")
        
        # 更新链接状态 - 将分享结果关联到提取的链接
        share_status = self.core_service.get_share_status()
        for task in share_status['tasks']:
            if task['status'] == 'completed':
                title = task.get('title', '')
                new_link = task.get('share_link', '')
                new_password = task.get('share_password', '')
                
                # 通过title（即article_id）找到对应的提取链接
                for link in transferred_links:
                    if link['article_id'] == title:
                        self.extractor.update_extracted_link_status(
                            article_id=link['article_id'],
                            original_link=link['original_link'],
                            new_link=new_link,
                            new_password=new_password,
                            new_title=task['file_info'].get('name', ''),
                            status='completed'
                        )
                        break
        
        return {
            'success': True,
            'shared': share_status['completed'],
            'failed': share_status['failed'],
            'share_status': share_status
        }
    
    def process_all(self, limit: int = 50, target_path: str = '/批量转存',
                   expiry: int = 7, password: str = None) -> Dict[str, Any]:
        """
        完整处理流程：提取 → 转存 → 分享
        
        Args:
            limit: 处理数量限制
            target_path: 转存目标路径
            expiry: 分享有效期
            password: 固定提取码
            
        Returns:
            完整处理结果
        """
        logger.info("开始完整处理流程：提取 → 转存 → 分享")
        
        # 步骤1：提取链接
        extract_result = self.extract_and_save_links(limit=limit)
        
        # 步骤2：转存
        transfer_result = self.process_pending_links(limit=limit, target_path=target_path)
        
        if not transfer_result['success']:
            return {
                'success': False,
                'message': '转存失败',
                'extract_result': extract_result,
                'transfer_result': transfer_result
            }
        
        # 步骤3：分享
        share_result = self.share_transferred_links(expiry=expiry, password=password)
        
        result = {
            'success': True,
            'extract_result': extract_result,
            'transfer_result': transfer_result,
            'share_result': share_result,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"完整处理流程完成: {result}")
        return result

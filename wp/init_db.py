"""
数据库初始化脚本
支持SQLite、MySQL、PostgreSQL
"""
import os
import sqlite3
from typing import Optional
from config import get_config, Config
from logger import get_logger

logger = get_logger(__name__)


def init_sqlite(db_path: str) -> bool:
    """
    初始化SQLite数据库
    
    Args:
        db_path: 数据库文件路径
    
    Returns:
        是否成功
    """
    try:
        # 确保数据目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # 连接数据库（如果不存在会自动创建）
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建转存任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfer_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT NOT NULL,
                share_link TEXT NOT NULL,
                share_password TEXT,
                target_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建分享任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS share_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT NOT NULL,
                file_path TEXT NOT NULL,
                fs_id TEXT NOT NULL,
                expiry INTEGER DEFAULT 7,
                password_mode TEXT DEFAULT 'random',
                share_password TEXT,
                share_link TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建账户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT UNIQUE NOT NULL,
                cookie TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                last_login_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建操作日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT NOT NULL,
                operation TEXT NOT NULL,
                details TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建系统配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建文章表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT UNIQUE NOT NULL,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transfer_status ON transfer_tasks(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transfer_account ON transfer_tasks(account)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_share_status ON share_tasks(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_share_account ON share_tasks(account)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_article_id ON articles(article_id)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"SQLite数据库初始化成功: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"SQLite数据库初始化失败: {e}")
        return False


def init_mysql(config: Config) -> bool:
    """
    初始化MySQL数据库
    
    Args:
        config: 配置对象
    
    Returns:
        是否成功
    """
    try:
        import pymysql
        
        # 连接MySQL服务器
        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {config.MYSQL_DATABASE}")
        
        # 创建表（与SQLite类似，但使用MySQL语法）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfer_tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                account VARCHAR(255) NOT NULL,
                share_link TEXT NOT NULL,
                share_password VARCHAR(255),
                target_path TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                error_message TEXT,
                filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_account (account)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS share_tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                account VARCHAR(255) NOT NULL,
                file_path TEXT NOT NULL,
                fs_id VARCHAR(255) NOT NULL,
                expiry INT DEFAULT 7,
                password_mode VARCHAR(50) DEFAULT 'random',
                share_password VARCHAR(255),
                share_link TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_account (account)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                account_name VARCHAR(255) UNIQUE NOT NULL,
                cookie TEXT NOT NULL,
                is_active TINYINT DEFAULT 1,
                last_login_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                account VARCHAR(255) NOT NULL,
                operation VARCHAR(255) NOT NULL,
                details TEXT,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                `key` VARCHAR(255) PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                article_id VARCHAR(255) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                content LONGTEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_article_id (article_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"MySQL数据库初始化成功: {config.MYSQL_DATABASE}")
        return True
        
    except ImportError:
        logger.error("MySQL驱动未安装，请运行: pip install pymysql")
        return False
    except Exception as e:
        logger.error(f"MySQL数据库初始化失败: {e}")
        return False


def init_postgresql(config: Config) -> bool:
    """
    初始化PostgreSQL数据库
    
    Args:
        config: 配置对象
    
    Returns:
        是否成功
    """
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # 连接PostgreSQL服务器
        conn = psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 创建数据库（如果不存在）
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{config.POSTGRES_DATABASE}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {config.POSTGRES_DATABASE}")
        
        cursor.close()
        conn.close()
        
        # 连接到目标数据库
        conn = psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            database=config.POSTGRES_DATABASE
        )
        cursor = conn.cursor()
        
        # 创建表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfer_tasks (
                id SERIAL PRIMARY KEY,
                account VARCHAR(255) NOT NULL,
                share_link TEXT NOT NULL,
                share_password VARCHAR(255),
                target_path TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                error_message TEXT,
                filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS share_tasks (
                id SERIAL PRIMARY KEY,
                account VARCHAR(255) NOT NULL,
                file_path TEXT NOT NULL,
                fs_id VARCHAR(255) NOT NULL,
                expiry INTEGER DEFAULT 7,
                password_mode VARCHAR(50) DEFAULT 'random',
                share_password VARCHAR(255),
                share_link TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                account_name VARCHAR(255) UNIQUE NOT NULL,
                cookie TEXT NOT NULL,
                is_active SMALLINT DEFAULT 1,
                last_login_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id SERIAL PRIMARY KEY,
                account VARCHAR(255) NOT NULL,
                operation VARCHAR(255) NOT NULL,
                details TEXT,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                article_id VARCHAR(255) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                content TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfer_status ON transfer_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfer_account ON transfer_tasks(account)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_share_status ON share_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_share_account ON share_tasks(account)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_article_id ON articles(article_id)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"PostgreSQL数据库初始化成功: {config.POSTGRES_DATABASE}")
        return True
        
    except ImportError:
        logger.error("PostgreSQL驱动未安装，请运行: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"PostgreSQL数据库初始化失败: {e}")
        return False


def initialize_database(config: Optional[Config] = None) -> bool:
    """
    初始化数据库
    
    Args:
        config: 配置对象，如果为None则从环境变量加载
    
    Returns:
        是否成功
    """
    if config is None:
        config = get_config()
    
    logger.info(f"开始初始化数据库，类型: {config.DATABASE_TYPE}")
    
    if config.DATABASE_TYPE == 'sqlite':
        return init_sqlite(config.DATABASE_PATH)
    elif config.DATABASE_TYPE == 'mysql':
        return init_mysql(config)
    elif config.DATABASE_TYPE == 'postgresql':
        return init_postgresql(config)
    else:
        logger.error(f"不支持的数据库类型: {config.DATABASE_TYPE}")
        return False


if __name__ == '__main__':
    """命令行入口"""
    import sys
    
    # 初始化配置
    config = get_config()
    
    print(f"正在初始化数据库...")
    print(f"数据库类型: {config.DATABASE_TYPE}")
    
    if config.DATABASE_TYPE == 'sqlite':
        print(f"数据库路径: {config.DATABASE_PATH}")
    elif config.DATABASE_TYPE == 'mysql':
        print(f"MySQL地址: {config.MYSQL_HOST}:{config.MYSQL_PORT}")
        print(f"数据库名: {config.MYSQL_DATABASE}")
    elif config.DATABASE_TYPE == 'postgresql':
        print(f"PostgreSQL地址: {config.POSTGRES_HOST}:{config.POSTGRES_PORT}")
        print(f"数据库名: {config.POSTGRES_DATABASE}")
    
    success = initialize_database(config)
    
    if success:
        print("✅ 数据库初始化成功！")
        sys.exit(0)
    else:
        print("❌ 数据库初始化失败！")
        sys.exit(1)

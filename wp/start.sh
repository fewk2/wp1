#!/bin/bash
# 百度网盘自动化服务启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  百度网盘自动化服务 - 启动脚本"
echo "======================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python版本: $PYTHON_VERSION"

# 检查是否存在虚拟环境
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo ""
    echo -e "${YELLOW}未找到虚拟环境，正在创建...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} 虚拟环境创建成功"
fi

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo -e "${GREEN}✓${NC} 虚拟环境已激活"

# 安装/更新依赖
echo ""
echo "检查依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} 依赖已安装"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}警告: 未找到.env文件${NC}"
    echo "请复制 .env.example 为 .env 并配置相关参数"
    read -p "是否现在创建.env文件? (y/n): " create_env
    if [ "$create_env" = "y" ] || [ "$create_env" = "Y" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} 已创建.env文件，请编辑该文件并配置参数"
        echo ""
        echo "必须配置的参数："
        echo "  - API_SECRET_KEY: API密钥"
        echo "  - ACCOUNT_MAIN_COOKIE: 百度网盘Cookie（BDUSS）"
        echo ""
        read -p "按回车键继续..."
    else
        echo -e "${RED}错误: 必须配置.env文件才能运行${NC}"
        exit 1
    fi
fi

# 加载环境变量
export $(grep -v '^#' .env | xargs)

echo ""
echo "配置信息:"
echo "  环境: ${ENV:-development}"
echo "  监听地址: ${HOST:-0.0.0.0}"
echo "  监听端口: ${PORT:-5000}"
echo "  数据库类型: ${DATABASE_TYPE:-sqlite}"
echo ""

# 初始化数据库
echo "初始化数据库..."
python3 init_db.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 数据库初始化成功"
else
    echo -e "${RED}错误: 数据库初始化失败${NC}"
    exit 1
fi

echo ""
echo "======================================"
echo "  选择运行模式"
echo "======================================"
echo "1. 开发模式 (Flask内置服务器)"
echo "2. 生产模式 (Gunicorn - Linux)"
echo "3. 生产模式 (Waitress - Windows)"
echo ""
read -p "请选择 (1-3): " mode

case $mode in
    1)
        # 开发模式
        export ENV=development
        export DEBUG=True
        echo ""
        echo -e "${GREEN}启动开发模式...${NC}"
        echo "访问地址:"
        echo "  - 健康检查: http://${HOST:-0.0.0.0}:${PORT:-5000}/api/health"
        echo "  - API文档: http://${HOST:-0.0.0.0}:${PORT:-5000}/docs"
        echo "  - 知识库UI: http://${HOST:-0.0.0.0}:${PORT:-5000}/kb"
        echo ""
        echo "提示: 运行测试请使用 'python -m unittest discover tests -v'"
        echo ""
        python3 server.py
        ;;
    2)
        # 生产模式 - Gunicorn
        if ! command -v gunicorn &> /dev/null; then
            echo -e "${YELLOW}安装gunicorn...${NC}"
            pip install gunicorn
        fi
        
        WORKERS=${WORKERS:-4}
        TIMEOUT=${TIMEOUT:-120}
        
        echo ""
        echo -e "${GREEN}启动生产模式 (Gunicorn)...${NC}"
        echo "配置:"
        echo "  - Workers: $WORKERS"
        echo "  - Timeout: $TIMEOUT秒"
        echo ""
        echo "访问地址:"
        echo "  - 健康检查: http://${HOST:-0.0.0.0}:${PORT:-5000}/api/health"
        echo "  - API文档: http://${HOST:-0.0.0.0}:${PORT:-5000}/docs"
        echo "  - 知识库UI: http://${HOST:-0.0.0.0}:${PORT:-5000}/kb"
        echo ""
        
        gunicorn -w $WORKERS \
                 -b ${HOST:-0.0.0.0}:${PORT:-5000} \
                 --timeout $TIMEOUT \
                 --access-logfile - \
                 --error-logfile - \
                 --log-level info \
                 server:app
        ;;
    3)
        # 生产模式 - Waitress
        if ! python3 -c "import waitress" &> /dev/null; then
            echo -e "${YELLOW}安装waitress...${NC}"
            pip install waitress
        fi
        
        echo ""
        echo -e "${GREEN}启动生产模式 (Waitress)...${NC}"
        echo "访问地址:"
        echo "  - 健康检查: http://${HOST:-0.0.0.0}:${PORT:-5000}/api/health"
        echo "  - API文档: http://${HOST:-0.0.0.0}:${PORT:-5000}/docs"
        echo "  - 知识库UI: http://${HOST:-0.0.0.0}:${PORT:-5000}/kb"
        echo ""
        
        python3 -c "from waitress import serve; from server import app; serve(app, host='${HOST:-0.0.0.0}', port=${PORT:-5000})"
        ;;
    *)
        echo -e "${RED}无效的选择${NC}"
        exit 1
        ;;
esac

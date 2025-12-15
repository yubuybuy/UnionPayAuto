#!/bin/bash

# 云闪付自动领券工具启动脚本

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_menu() {
    clear
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${BLUE}    云闪付自动领券工具${NC}"
    echo -e "${BLUE}===============================================${NC}"
    echo ""
    echo "请选择运行模式："
    echo ""
    echo "1. 首次使用 - 从HAR文件提取配置"
    echo "2. 单账号模式"
    echo "3. 多账号并发模式"
    echo "4. 多账号顺序模式"
    echo "5. 多账号智能模式（推荐）"
    echo "6. 查看运行日志"
    echo "7. 安装依赖"
    echo "0. 退出"
    echo ""
}

extract_config() {
    echo -e "${YELLOW}===============================================${NC}"
    echo -e "${YELLOW}提取HAR文件配置${NC}"
    echo -e "${YELLOW}===============================================${NC}"
    echo ""
    read -p "请输入HAR文件路径: " har_file
    python3 har_parser.py "$har_file"
    echo ""
    echo -e "${GREEN}配置已提取到 extracted_config.py${NC}"
    echo "请将内容复制到 config.py 后运行脚本"
    echo ""
    read -p "按回车继续..."
}

install_deps() {
    echo -e "${YELLOW}===============================================${NC}"
    echo -e "${YELLOW}安装依赖${NC}"
    echo -e "${YELLOW}===============================================${NC}"
    echo ""
    python3 -m pip install -r requirements.txt
    echo ""
    echo -e "${GREEN}依赖安装完成！${NC}"
    echo ""
    read -p "按回车继续..."
}

run_single() {
    echo -e "${GREEN}===============================================${NC}"
    echo -e "${GREEN}启动单账号模式${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo ""
    python3 unionpay_auto.py
    read -p "按回车继续..."
}

run_concurrent() {
    echo -e "${GREEN}===============================================${NC}"
    echo -e "${GREEN}启动多账号并发模式${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo ""
    read -p "请输入并发数（默认3）: " workers
    workers=${workers:-3}
    python3 multi_account_runner.py --mode concurrent --workers $workers
    read -p "按回车继续..."
}

run_sequential() {
    echo -e "${GREEN}===============================================${NC}"
    echo -e "${GREEN}启动多账号顺序模式${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo ""
    read -p "请输入间隔秒数（默认2）: " delay
    delay=${delay:-2}
    python3 multi_account_runner.py --mode sequential --delay $delay
    read -p "按回车继续..."
}

run_smart() {
    echo -e "${GREEN}===============================================${NC}"
    echo -e "${GREEN}启动多账号智能模式（推荐）${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo ""
    python3 multi_account_runner.py --mode smart
    read -p "按回车继续..."
}

view_logs() {
    echo -e "${YELLOW}===============================================${NC}"
    echo -e "${YELLOW}查看运行日志${NC}"
    echo -e "${YELLOW}===============================================${NC}"
    echo ""
    echo "1. 单账号日志 (unionpay_auto.log)"
    echo "2. 多账号日志 (multi_account.log)"
    echo "3. 实时查看日志（单账号）"
    echo "4. 实时查看日志（多账号）"
    echo "5. 返回主菜单"
    echo ""
    read -p "请选择（1-5）: " log_choice

    case $log_choice in
        1)
            less unionpay_auto.log
            ;;
        2)
            less multi_account.log
            ;;
        3)
            tail -f unionpay_auto.log
            ;;
        4)
            tail -f multi_account.log
            ;;
        5)
            return
            ;;
    esac
    read -p "按回车继续..."
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项（0-7）: " choice

    case $choice in
        1)
            extract_config
            ;;
        2)
            run_single
            ;;
        3)
            run_concurrent
            ;;
        4)
            run_sequential
            ;;
        5)
            run_smart
            ;;
        6)
            view_logs
            ;;
        7)
            install_deps
            ;;
        0)
            echo ""
            echo -e "${GREEN}感谢使用！再见！${NC}"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}无效选项，请重新选择${NC}"
            sleep 1
            ;;
    esac
done

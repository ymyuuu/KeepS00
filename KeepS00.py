import os
import paramiko
import yaml
import logging
from datetime import datetime

def setup_logger():
    """配置日志格式"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)-8s │ %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def print_separator(message=""):
    """打印分隔线"""
    width = 80
    if message:
        left_padding = (width - len(message) - 4) // 2
        right_padding = width - len(message) - 4 - left_padding
        logging.info("─" * left_padding + f"[ {message} ]" + "─" * right_padding)
    else:
        logging.info("─" * width)

def load_config():
    """加载配置"""
    print_separator("配置加载")
    cfg = os.environ.get('CONFIG')
    if not cfg:
        logging.error("环境变量 CONFIG 未设置")
        return []
    try:
        config = yaml.safe_load(cfg)
        accounts = config.get('accounts', [])
        logging.info(f"已加载 {len(accounts)} 个账户配置")
        return accounts
    except Exception as e:
        logging.error(f"配置加载失败: {e}")
        return []

def run_account(acc, index, total):
    """处理单个账户"""
    if not isinstance(acc, dict):
        logging.error("无效的账户配置，跳过")
        return

    # 获取必填项
    username = acc.get('username', '').strip()
    password = acc.get('password', '').strip()
    
    # 检查必填项
    if not (username and password):
        logging.error("账户配置缺少必填字段（用户名或密码），跳过")
        return

    # 获取可选项
    tip = acc.get('tip', '').strip()
    cmd = acc.get('cmd', '').strip()
    
    # 构造显示名称
    disp = f"{username} ({tip})" if tip else username
    hostname = f"{username}.serv00.net"
    
    print_separator(f"账户 {index}/{total}: {disp}")
    
    try:
        # 建立 SSH 连接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        logging.info(f"连接到 {hostname}")
        ssh.connect(hostname, port=22, username=username, password=password)
        
        # 如果有命令需要执行
        if cmd:
            logging.info("开始执行命令")
            cmds = [
                "echo '' | crontab -",
                f'(crontab -l 2>/dev/null; echo "0 *  *{cmd}") | crontab -',
                f'(crontab -l 2>/dev/null; echo "@reboot {cmd}") | crontab -',
                f'(crontab -l 2>/dev/null; echo "0 0 * ** kill -9 -1 && {cmd}") | crontab -',
                cmd
            ]
            
            for i, c in enumerate(cmds, 1):
                try:
                    logging.info(f"执行命令 {i}/{len(cmds)}")
                    ssh.exec_command(c)[1].channel.recv_exit_status()
                except Exception as e:
                    logging.error(f"命令执行失败: {e}")
                    ssh.close()
                    return
            logging.info("命令执行完成")
        else:
            logging.info("无需执行命令")
        
        # 关闭连接
        ssh.close()
        logging.info(f"账户 {disp} 处理完成")
        
    except Exception as e:
        logging.error(f"连接失败: {e}")
        return

def main():
    """主函数"""
    setup_logger()
    
    print_separator("程序开始")
    accounts = load_config()
    
    if not accounts:
        logging.error("没有有效的账户配置")
        return
    
    total = len(accounts)
    for i, acc in enumerate(accounts, 1):
        run_account(acc, i, total)
    
    print_separator("程序完成")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_separator("程序被中断")
        logging.error("程序被用户中断")
    except Exception as e:
        logging.error(f"程序异常: {e}")

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

def mask_string(text):
    """将字符串的80%变成星号"""
    if not text:
        return text
    # 计算需要打码的字符数量
    mask_count = int(len(text) * 0.8)
    # 保留开头和结尾的字符
    remain_count = len(text) - mask_count
    head = text[:remain_count//2]
    tail = text[-remain_count//2:] if remain_count > 1 else ''
    return head + '*' * mask_count + tail

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

    username = acc.get('username', '').strip()
    password = acc.get('password', '').strip()
    cmd = acc.get('cmd', '').strip()
    tip = acc.get('tip', '')
    tip = tip.strip() if isinstance(tip, str) else ''

    # 如果没有命令，默认使用 ls
    if not cmd:
        cmd = 'ls'

    if not (username and password):
        logging.error("账户配置缺少必要字段，跳过")
        return

    # 对用户名和提示进行打码
    masked_username = mask_string(username)
    masked_tip = mask_string(tip) if tip else ''
    disp = f"{masked_username} ({masked_tip})" if masked_tip else masked_username
    hostname = f"{username}.serv00.net"
    
    print_separator(f"账户 {index}/{total}: {disp}")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        logging.info(f"连接到 {mask_string(hostname)}")
        ssh.connect(hostname, port=22, username=username, password=password)
    except Exception as e:
        logging.error(f"连接失败: {e}")
        return

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
    
    ssh.close()
    logging.info(f"账户 {disp} 处理完成")

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

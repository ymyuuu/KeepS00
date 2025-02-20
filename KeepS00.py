import os
import paramiko
import yaml
import logging
from typing import List, Dict, Any

# 设置日志格式及级别
logging.basicConfig(
    level=logging.INFO,
    format='╭──────── [%(asctime)s] ──────────╮\n│ %(levelname)-8s: %(message)-12s │\n╰───────────────────────────────────╯',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def mask_string(text: str) -> str:
    """
    将字符串中间80%的字符替换为星号
    """
    if not text:
        return text
    
    length = len(text)
    if length <= 2:
        return '*' * length
        
    # 计算保留的字符数量（首尾各保留10%）
    preserve = max(1, int(length * 0.1))
    mask_length = length - (2 * preserve)
    
    return text[:preserve] + '*' * mask_length + text[-preserve:]

def load_config() -> List[Dict[Any, Any]]:
    """
    从环境变量加载配置
    """
    cfg = os.environ.get('CONFIG')
    if not cfg:
        logging.error("┃ 环境变量 CONFIG 未设置")
        return []
    try:
        config = yaml.safe_load(cfg)
        return config.get('accounts', [])
    except Exception as e:
        logging.error(f"┃ 加载配置失败: {e}")
        return []

def run_account(acc: Dict[str, Any]) -> None:
    """
    处理单个账户
    """
    if not isinstance(acc, dict):
        logging.error("┃ 无效的账户配置，跳过")
        return

    username = acc.get('username', '').strip()
    password = acc.get('password', '').strip()
    cmd = acc.get('cmd', 'ls').strip()  # 默认执行 ls 命令
    tip = acc.get('tip', '')
    tip = tip.strip() if isinstance(tip, str) else ''

    if not (username and password):
        logging.error("┃ 账户配置缺少必要字段，跳过")
        return

    # 打码处理
    masked_username = mask_string(username)
    disp = f"{masked_username} ({tip})" if tip else masked_username
    hostname = f"{username}.serv00.net"
    
    logging.info(f"┃ 正在处理账户: {disp}")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port=22, username=username, password=password)
    except Exception as e:
        logging.error(f"┃ {disp} 连接失败: {e}")
        return

    cmds = [
        "echo '' | crontab -",
        f'(crontab -l 2>/dev/null; echo "0 *  *{cmd}") | crontab -',
        f'(crontab -l 2>/dev/null; echo "@reboot {cmd}") | crontab -',
        f'(crontab -l 2>/dev/null; echo "0 0 * ** kill -9 -1 && {cmd}") | crontab -',
        cmd
    ]
    
    for c in cmds:
        try:
            ssh.exec_command(c)[1].channel.recv_exit_status()
        except Exception as e:
            logging.error(f"┃ {disp} 执行命令失败: {e}")
            ssh.close()
            return
            
    ssh.close()
    logging.info(f"┃ {disp} 处理完成")

def main() -> None:
    """
    主函数
    """
    logging.info("┃ 开始执行任务")
    accounts = load_config()
    
    if not accounts:
        logging.error("┃ 没有有效的账户配置")
        return
        
    total = len(accounts)
    for index, acc in enumerate(accounts, 1):
        logging.info(f"┃ 处理进度: [{index}/{total}]")
        run_account(acc)
        
    logging.info("┃ 所有任务执行完成")

if __name__ == '__main__':
    main()

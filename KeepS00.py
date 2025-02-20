import os
import paramiko
import yaml
import logging
from datetime import datetime

# 设置日志格式及级别
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s | %(message)s',  # 使用竖线分隔符提升可读性
    datefmt='%Y-%m-%d %H:%M:%S'
)

def mask_string(text):
    """
    将字符串中80%的字符变成星号，保留首尾字符
    
    Args:
        text: 需要打码的字符串
    Returns:
        打码后的字符串
    """
    if not text or len(text) <= 2:
        return text
    
    # 计算需要打码的字符数量
    mask_count = int(len(text) * 0.8)
    # 保证至少保留首尾字符
    remain_count = len(text) - mask_count
    if remain_count < 2:
        remain_count = 2
        mask_count = len(text) - 2
    
    # 计算开头和结尾保留的字符数
    start_chars = remain_count // 2
    end_chars = remain_count - start_chars
    
    # 构建打码后的字符串
    masked = text[:start_chars] + '*' * mask_count + text[-end_chars:]
    return masked

def load_config():
    """加载环境变量中的配置"""
    cfg = os.environ.get('CONFIG')
    if not cfg:
        logging.error("⚠️ 环境变量 CONFIG 未设置")
        return []
    
    try:
        config = yaml.safe_load(cfg)
        return config.get('accounts', [])
    except Exception as e:
        logging.error(f"⚠️ 加载配置失败: {str(e)}")
        return []

def run_account(acc):
    """
    处理单个账户的操作
    
    Args:
        acc: 账户配置字典
    """
    if not isinstance(acc, dict):
        logging.error("⚠️ 无效的账户配置，跳过")
        return
    
    # 获取账户信息
    username = acc.get('username', '').strip()
    password = acc.get('password', '').strip()
    cmd = acc.get('cmd', 'ls').strip()  # 默认执行 ls 命令
    tip = acc.get('tip', '')
    tip = tip.strip() if isinstance(tip, str) else ''
    
    if not (username and password):
        logging.error("⚠️ 账户配置缺少必要字段，跳过")
        return
    
    # 打码后的显示名称
    masked_username = mask_string(username)
    disp = f"{masked_username} ({tip})" if tip else masked_username
    hostname = f"{username}.serv00.net"
    
    logging.info(f"► 开始处理账户 {disp}")
    
    try:
        # 建立 SSH 连接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port=22, username=username, password=password)
    except Exception as e:
        logging.error(f"⚠️ {disp} 连接失败: {str(e)}")
        return
    
    # 定义要执行的命令列表
    cmds = [
        "echo '' | crontab -",
        f'(crontab -l 2>/dev/null; echo "0 * * * * {cmd}") | crontab -',
        f'(crontab -l 2>/dev/null; echo "@reboot {cmd}") | crontab -',
        f'(crontab -l 2>/dev/null; echo "0 0 * * * kill -9 -1 && {cmd}") | crontab -',
        cmd
    ]
    
    # 执行命令
    for c in cmds:
        try:
            ssh.exec_command(c)[1].channel.recv_exit_status()
        except Exception as e:
            logging.error(f"⚠️ {disp} 执行失败: {str(e)}")
            ssh.close()
            return
    
    ssh.close()
    logging.info(f"✓ {disp} 处理完成")

def main():
    """主函数"""
    logging.info("=== 开始执行账户处理 ===")
    
    accounts = load_config()
    if not accounts:
        logging.error("⚠️ 没有有效的账户配置")
        return
    
    total = len(accounts)
    for idx, acc in enumerate(accounts, 1):
        logging.info(f"--- 处理进度 [{idx}/{total}] ---")
        run_account(acc)
    
    logging.info("=== 所有账户处理完成 ===")

if __name__ == '__main__':
    main()

import os, paramiko, yaml, logging

# 设置日志格式及级别
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config():
    """
    从环境变量 CONFIG 中加载 YAML 格式的配置数据，
    返回包含账户信息的列表。
    """
    cfg = os.environ.get('CONFIG')
    if not cfg:
        logging.error("环境变量 CONFIG 未设置")
        return []
    try:
        config = yaml.safe_load(cfg)
        return config.get('accounts', [])
    except Exception as e:
        logging.error(f"加载配置失败: {e}")
        return []

def run_account(acc):
    """
    处理单个账户：依次建立 SSH 连接，执行清空 crontab、
    添加定时任务和直接执行命令。
    """
    if not isinstance(acc, dict):
        logging.error("无效的账户配置，跳过")
        return

    username = acc.get('username', '').strip()
    password = acc.get('password', '').strip()
    cmd = acc.get('cmd', '').strip()
    tip = acc.get('tip', '')
    tip = tip.strip() if isinstance(tip, str) else ''

    if not (username and password and cmd):
        logging.error("账户配置缺少必要字段，跳过")
        return

    disp = f"{username} ({tip})" if tip else username
    hostname = f"{username}.serv00.net"
    logging.info(f"处理 {disp} ...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port=22, username=username, password=password)
    except Exception as e:
        logging.error(f"{disp} 连接失败: {e}")
        return

    cmds = [
        "echo '' | crontab -",
        f'(crontab -l 2>/dev/null; echo "0 * * * * {cmd}") | crontab -',
        f'(crontab -l 2>/dev/null; echo "@reboot {cmd}") | crontab -',
        f'(crontab -l 2>/dev/null; echo "0 0 * * * kill -9 -1 && {cmd}") | crontab -',
        cmd
    ]
    for c in cmds:
        try:
            ssh.exec_command(c)[1].channel.recv_exit_status()
        except Exception as e:
            logging.error(f"{disp} 执行失败: {e}")
            ssh.close()
            return
    ssh.close()
    logging.info(f"{disp} 完成")

def main():
    accounts = load_config()
    if not accounts:
        logging.error("没有有效的账户配置")
        return
    for acc in accounts:
        run_account(acc)
        # 每个账户处理完后，输出一条横线作为分隔符
        print("--------------------------------------------------")

if __name__ == '__main__':
    main()
